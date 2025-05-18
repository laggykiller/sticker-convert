#!/usr/bin/env python3
import os
import platform
import re
import subprocess
import time
from functools import partial
from getpass import getpass
from pathlib import Path
from typing import Callable, Optional, Tuple, Union, cast

from sticker_convert.utils.process import find_pid_by_name, get_mem, killall

MSG_NO_BIN = """Kakao Desktop not detected.
Download and install Kakao Desktop,
then login to Kakao Desktop and try again."""
MSG_NO_AUTH = """Kakao Desktop installed,
but kakao_auth not found.
Please login to Kakao Desktop and try again."""
MSG_SIP_ENABLED = """You need to disable SIP:
1. Restart computer in Recovery mode
2. Launch Terminal from the Utilities menu
3. Run the command `csrutil disable`
4. Restart your computer"""
MSG_LAUNCH_FAIL = "Failed to launch Kakao"
MSG_PERMISSION_ERROR = "Failed to read Kakao process memory"


class GetKakaoDesktopAuth:
    def __init__(self, cb_ask_str: Callable[..., str] = input) -> None:
        self.cb_ask_str = cb_ask_str

    def launch_kakao(self, kakao_bin_path: str) -> None:
        if platform.system() == "Windows":
            subprocess.Popen([kakao_bin_path])
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", kakao_bin_path])
        else:
            subprocess.Popen(["wine", kakao_bin_path])

    def relaunch_kakao(self, kakao_bin_path: str) -> Optional[int]:
        killed = killall("kakaotalk")
        if killed:
            time.sleep(5)

        self.launch_kakao(kakao_bin_path)
        time.sleep(20)

        return find_pid_by_name("kakaotalk")

    def get_auth_by_pme(
        self, kakao_bin_path: str, relaunch: bool = True
    ) -> Tuple[Optional[str], str]:
        from PyMemoryEditor import OpenProcess  # type: ignore

        auth_token = None

        if relaunch:
            kakao_pid = self.relaunch_kakao(kakao_bin_path)
        else:
            kakao_pid = find_pid_by_name("kakaotalk")
        if kakao_pid is None:
            return None, MSG_LAUNCH_FAIL

        try:
            with OpenProcess(pid=int(kakao_pid)) as process:
                for address in process.search_by_value(  # type: ignore
                    str, 15, "authorization: "
                ):
                    auth_token_addr = cast(int, address) + 15
                    auth_token_bytes = process.read_process_memory(
                        auth_token_addr, bytes, 200
                    )
                    auth_token_term = auth_token_bytes.find(b"\x00")
                    if auth_token_term == -1:
                        continue
                    auth_token_candidate = auth_token_bytes[:auth_token_term].decode(
                        encoding="ascii"
                    )
                    if len(auth_token_candidate) > 150:
                        auth_token = auth_token_candidate
                        break
        except PermissionError:
            return None, MSG_PERMISSION_ERROR

        if auth_token is None:
            return None, MSG_NO_AUTH
        else:
            msg = "(Note: auth_token will be invalid if you quit Kakao Desktop)"
            msg += "Got auth_token successfully:\n"
            msg += f"{auth_token=}\n"

            return auth_token, msg

    def get_auth_by_dump(
        self, kakao_bin_path: str, relaunch: bool = True
    ) -> Tuple[Optional[str], str]:
        auth_token = None
        kakao_pid: Union[str, int, None]
        if platform.system() == "Windows":
            is_wine = False
            if relaunch:
                kakao_pid = self.relaunch_kakao(kakao_bin_path)
            else:
                kakao_pid = find_pid_by_name("kakaotalk")
            if kakao_pid is None:
                return None, MSG_LAUNCH_FAIL
        else:
            is_wine = True
            kakao_pid = "KakaoTalk.exe"
            if relaunch and self.relaunch_kakao(kakao_bin_path) is None:
                return None, MSG_LAUNCH_FAIL

        if self.cb_ask_str == input:
            pw_func = getpass
        else:
            pw_func = partial(
                self.cb_ask_str, initialvalue="", cli_show_initialvalue=False
            )
        s = get_mem(kakao_pid, pw_func, is_wine)

        if s is None:
            return None, "Failed to dump memory"

        auth_token = None
        for i in re.finditer(b"authorization: ", s):
            auth_token_addr = i.start() + 15

            auth_token_bytes = s[auth_token_addr : auth_token_addr + 200]
            auth_token_term = auth_token_bytes.find(b"\x00")
            if auth_token_term == -1:
                return None, MSG_NO_AUTH
            auth_token_candidate = auth_token_bytes[:auth_token_term].decode(
                encoding="ascii"
            )
            if len(auth_token_candidate) > 150:
                auth_token = auth_token_candidate
                break

        if auth_token is None:
            return None, MSG_NO_AUTH
        else:
            msg = "Got auth_token successfully:\n"
            msg += f"{auth_token=}\n"

            return auth_token, msg

    def get_auth_darwin(self, kakao_bin_path: str) -> Tuple[Optional[str], str]:
        csrutil_status = subprocess.run(
            ["csrutil", "status"], capture_output=True, text=True
        ).stdout

        if "enabled" in csrutil_status:
            return None, MSG_SIP_ENABLED

        killall("kakaotalk")

        subprocess.run(
            [
                "lldb",
                kakao_bin_path,
                "-o",
                "b ptrace",
                "-o",
                "r",
                "-o",
                "thread return",
                "-o",
                "con",
                "-o",
                "process save-core /tmp/memdump.kakaotalk.dmp",
                "-o",
                "con",
                "-o",
                "quit",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        with open("/tmp/memdump.kakaotalk.dmp", "rb") as f:
            mem = f.read()

        os.remove("/tmp/memdump.kakaotalk.dmp")

        auth_token = None
        for i in re.finditer(b"]mac/", mem):
            auth_token_term = i.start()

            auth_token_bytes = mem[auth_token_term - 200 : auth_token_term]
            auth_token_start = auth_token_bytes.find(b"application/json_\x10\x8a") + 19
            if auth_token_start == -1:
                continue
            try:
                auth_token_candidate = auth_token_bytes[auth_token_start:].decode(
                    encoding="ascii"
                )
            except UnicodeDecodeError:
                continue

            if 150 > len(auth_token_candidate) > 100:
                auth_token = auth_token_candidate
                break

        if auth_token is None:
            return None, MSG_NO_AUTH
        else:
            msg = "Got auth_token successfully:\n"
            msg += f"{auth_token=}\n"

            return auth_token, msg

    def get_kakao_desktop(self) -> Optional[str]:
        if platform.system() == "Windows":
            kakao_bin_path = os.path.expandvars(
                "%programfiles(x86)%\\Kakao\\KakaoTalk\\KakaoTalk.exe"
            )
        elif platform.system() == "Darwin":
            kakao_bin_path = "/Applications/KakaoTalk.app"
        else:
            wineprefix = os.environ.get("WINEPREFIX")
            if not (wineprefix and Path(wineprefix).exists()):
                wineprefix = os.path.expanduser("~/.wine")
            kakao_bin_path = f"{wineprefix}/drive_c/Program Files (x86)/Kakao/KakaoTalk/KakaoTalk.exe"

        if Path(kakao_bin_path).exists():
            return kakao_bin_path

        return None

    def get_cred(
        self,
        kakao_bin_path: Optional[str] = None,
    ) -> Tuple[Optional[str], str]:
        # get_auth_by_dump()
        # + Fast
        # - Requires downloading procdump, or builtin method that needs admin

        # get_auth_by_pme()
        # + No admin (If have permission to read process)
        # - Slow
        # - Cannot run on macOS

        if not kakao_bin_path:
            kakao_bin_path = self.get_kakao_desktop()

        if not kakao_bin_path:
            return None, MSG_NO_BIN

        if platform.system() == "Windows":
            kakao_auth, msg = self.get_auth_by_dump(kakao_bin_path)
            if kakao_auth is None:
                kakao_auth, msg = self.get_auth_by_pme(kakao_bin_path, False)
        elif platform.system() == "Darwin":
            kakao_auth, msg = self.get_auth_darwin(kakao_bin_path)
        else:
            kakao_auth, msg = self.get_auth_by_dump(kakao_bin_path)

        return kakao_auth, msg
