#!/usr/bin/env python3
import importlib.util
import os
import platform
import re
import subprocess
import time
from functools import partial
from getpass import getpass
from pathlib import Path
from typing import Callable, List, Optional, Tuple, cast

from sticker_convert.utils.process import check_admin, find_pid_by_name, get_mem, killall

MSG_NO_BIN = """Kakao Desktop not detected.
Download and install Kakao Desktop,
then login to Kakao Desktop and try again."""
MSG_NO_AUTH = """Kakao Desktop installed,
but kakao_auth not found.
Please login to Kakao Desktop and try again."""
MSG_LAUNCH_FAIL = "Failed to launch Kakao"
MSG_PERMISSION_ERROR = "Failed to read Kakao process memory"
MSG_UNSUPPORTED = "Only Windows is supported for this method"


class GetKakaoDesktopAuth:
    def __init__(self, cb_ask_str: Callable[..., str] = input):
        self.cb_ask_str = cb_ask_str

    def relaunch_kakao(self, kakao_bin_path: str) -> Optional[int]:
        killed = killall("kakaotalk")
        if killed:
            time.sleep(5)

        subprocess.Popen([kakao_bin_path])
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
                    str, 15, "\x00authorization\x00"
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

        if relaunch:
            kakao_pid = self.relaunch_kakao(kakao_bin_path)
        else:
            kakao_pid = find_pid_by_name("kakaotalk")
        if kakao_pid is None:
            return None, MSG_LAUNCH_FAIL

        if self.cb_ask_str == input:
            pw_func = getpass
        else:
            pw_func = partial(
                self.cb_ask_str, initialvalue="", cli_show_initialvalue=False
            )
        s, msg = get_mem(kakao_pid, pw_func)

        if s is None:
            return None, msg

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

    def get_kakao_desktop(self) -> Optional[str]:
        kakao_bin_path = os.path.expandvars(
            "%programfiles(x86)%\\Kakao\\KakaoTalk\\KakaoTalk.exe"
        )
        if Path(kakao_bin_path).is_file():
            return kakao_bin_path

        return None

    def get_cred(
        self,
        kakao_bin_path: Optional[str] = None,
    ) -> Tuple[Optional[str], str]:
        if platform.system() != "Windows":
            return None, MSG_UNSUPPORTED

        if not kakao_bin_path:
            kakao_bin_path = self.get_kakao_desktop()

        if not kakao_bin_path:
            return None, MSG_NO_BIN

        # get_auth_by_dump()
        # + Fast
        # - Requires admin

        # get_auth_by_pme()
        # + No admin (If have permission to read process)
        # - Slow
        # - Cannot run on macOS

        # If admin, prefer get_auth_by_dump() over get_auth_by_pme(), vice versa
        methods: List[Callable[[str, bool], Tuple[Optional[str], str]]] = []
        relaunch = True
        kakao_auth = None
        msg = ""

        pme_present = importlib.util.find_spec("PyMemoryEditor") is not None
        methods.append(self.get_auth_by_dump)
        if pme_present:
            methods.append(self.get_auth_by_pme)
        if check_admin() is False:
            methods.reverse()

        for method in methods:
            kakao_auth, msg = method(kakao_bin_path, relaunch)
            relaunch = False
            if kakao_auth is not None:
                break

        return kakao_auth, msg
