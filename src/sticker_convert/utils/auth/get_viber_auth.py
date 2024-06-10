#!/usr/bin/env python3
import os
import platform
import shutil
import subprocess
import time
from getpass import getpass
from pathlib import Path
from typing import Callable, Optional, Tuple, cast

from sticker_convert.definitions import ROOT_DIR

# psutil is missing on arm64 linux appimage
# Note: There is no Viber Desktop on arm64 linux anyway
try:
    import psutil

    PSUTIL_LOADED = True
except ModuleNotFoundError:
    PSUTIL_LOADED = False  # type: ignore

MSG_NO_BIN = """Viber Desktop not detected.
Download and install Viber Desktop,
then login to Viber Desktop and try again."""

MSG_NO_AUTH = """Viber Desktop installed,
but viber_auth not found.
Please login to Viber Desktop and try again."""

MSG_SIP_ENABLED = """You need to disable SIP:
1. Restart computer in Recovery mode
2. Launch Terminal from the Utilities menu
3. Run the command `csrutil disable`
4. Restart your computer"""

MSG_NO_PSUTIL = "Python package psutil is necessary"


def killall(name: str) -> bool:
    if not PSUTIL_LOADED:
        return False

    result = False

    for proc in psutil.process_iter():  # type: ignore
        if name in proc.name().lower():
            proc.kill()
            result = True

    return result


def find_pid_by_name(name: str) -> Optional[int]:
    if not PSUTIL_LOADED:
        return None

    for proc in psutil.process_iter():  # type: ignore
        if name in proc.name().lower():
            return proc.pid

    return None


class GetViberAuth:
    def __init__(self, cb_ask_str: Callable[..., str] = input):
        self.cb_ask_str = cb_ask_str

    def get_auth_windows(self, viber_bin_path: str) -> Tuple[Optional[str], str]:
        if not PSUTIL_LOADED:
            return None, MSG_NO_PSUTIL

        member_id = None
        m_token = None
        m_ts = None

        killed = killall("viber")
        if killed:
            time.sleep(5)
        subprocess.Popen([viber_bin_path])
        time.sleep(10)

        from PyMemoryEditor import OpenProcess  # type: ignore

        viber_pid = find_pid_by_name("viber")
        with OpenProcess(pid=viber_pid) as process:
            for address in process.search_by_value(str, 18, "X-Viber-Auth-Mid: "):  # type: ignore
                member_id_addr = cast(int, address) + 18
                member_id_bytes = process.read_process_memory(member_id_addr, bytes, 20)
                member_id_term = member_id_bytes.find(b"\x0d\x0a")
                if member_id_term == -1:
                    continue
                member_id = member_id_bytes[:member_id_term].decode(encoding="ascii")
                break
            if member_id is None:
                return None, MSG_NO_AUTH

            for address in process.search_by_value(str, 20, "X-Viber-Auth-Token: "):  # type: ignore
                m_token_addr = cast(int, address) + 20
                m_token = process.read_process_memory(m_token_addr, str, 64)
                break
            if m_token is None:
                return None, MSG_NO_AUTH

            for address in process.search_by_value(str, 24, "X-Viber-Auth-Timestamp: "):  # type: ignore
                m_ts_addr = cast(int, address) + 24
                m_ts = process.read_process_memory(m_ts_addr, str, 13)
                break
            if m_ts is None:
                return None, MSG_NO_AUTH

        killall("viber")

        viber_auth = f"member_id:{member_id};m_token:{m_token};m_ts:{m_ts}"
        msg = "Got viber_auth successfully:\n"
        msg += f"{viber_auth=}\n"

        return viber_auth, msg

    def get_auth_linux(self, viber_bin_path: str) -> Tuple[Optional[str], str]:
        if not PSUTIL_LOADED:
            return None, MSG_NO_PSUTIL

        member_id = None
        m_token = None
        m_ts = None

        killed = killall("viber")
        if killed:
            time.sleep(5)
        subprocess.Popen([viber_bin_path])
        time.sleep(10)

        viber_pid = find_pid_by_name("viber")
        memdump_sh_path = (ROOT_DIR / "resources/memdump.sh").as_posix()

        s = subprocess.run(
            [
                memdump_sh_path,
                str(viber_pid),
            ],
            capture_output=True,
        ).stdout

        if s.find(b"X-Viber-Auth-Mid: ") != -1:
            pass
        elif shutil.which("pkexec") and os.getenv("DISPLAY"):
            s = subprocess.run(
                [
                    "pkexec",
                    memdump_sh_path,
                    str(viber_pid),
                ],
                capture_output=True,
            ).stdout
        else:
            prompt = "Enter sudo password: "
            if self.cb_ask_str != input:
                sudo_password = self.cb_ask_str(
                    prompt, initialvalue="", cli_show_initialvalue=False
                )
            else:
                sudo_password = getpass(prompt)
            sudo_password_pipe = subprocess.Popen(
                ("echo", sudo_password), stdout=subprocess.PIPE
            )
            s = subprocess.run(
                [
                    "sudo",
                    "-S",
                    memdump_sh_path,
                    str(viber_pid),
                ],
                capture_output=True,
                stdin=sudo_password_pipe.stdout,
            ).stdout

        member_id_addr = s.find(b"X-Viber-Auth-Mid: ")
        m_token_addr = s.find(b"X-Viber-Auth-Token: ")
        m_ts_addr = s.find(b"X-Viber-Auth-Timestamp: ")

        if member_id_addr == -1 or m_token_addr == -1 or m_ts_addr == -1:
            return None, MSG_NO_AUTH

        member_id_addr += 18
        m_token_addr += 20
        m_ts_addr += 24

        member_id_bytes = s[member_id_addr : member_id_addr + 20]
        member_id_term = member_id_bytes.find(b"\x0d\x0a")
        if member_id_term == -1:
            return None, MSG_NO_AUTH
        member_id = member_id_bytes[:member_id_term].decode(encoding="ascii")

        m_token = s[m_token_addr : m_token_addr + 64].decode(encoding="ascii")
        m_ts = s[m_ts_addr : m_ts_addr + 13].decode(encoding="ascii")

        killall("viber")

        viber_auth = f"member_id:{member_id};m_token:{m_token};m_ts:{m_ts}"
        msg = "Got viber_auth successfully:\n"
        msg += f"{viber_auth=}\n"

        return viber_auth, msg

    def get_auth_darwin(self, viber_bin_path: str) -> Tuple[Optional[str], str]:
        member_id = None
        m_token = None
        m_ts = None

        csrutil_status = subprocess.run(
            ["csrutil", "status"], capture_output=True, text=True
        ).stdout

        if "enabled" in csrutil_status:
            return None, MSG_SIP_ENABLED

        killed = killall("viber")
        if killed:
            time.sleep(5)
        subprocess.run(
            ["open", "-n", viber_bin_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(10)

        viber_pid = subprocess.run(
            ["pgrep", "Viber"], capture_output=True, text=True
        ).stdout.strip()
        subprocess.run(
            [
                "lldb",
                "--attach-pid",
                viber_pid,
                "-o",
                "process save-core /tmp/viber.dmp",
                "-o",
                "quit",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        with open("/tmp/viber.dmp", "rb") as f:
            s = f.read()

        os.remove("/tmp/viber.dmp")
        killall("viber")

        member_id_addr = s.find(b"X-Viber-Auth-Mid: ")
        m_token_addr = s.find(b"X-Viber-Auth-Token: ")
        m_ts_addr = s.find(b"X-Viber-Auth-Timestamp: ")

        if member_id_addr == -1 or m_token_addr == -1 or m_ts_addr == -1:
            return None, MSG_NO_AUTH

        member_id_addr += 18
        m_token_addr += 20
        m_ts_addr += 24

        member_id_bytes = s[member_id_addr : member_id_addr + 20]
        member_id_term = member_id_bytes.find(b"\x0d\x0a")
        if member_id_term == -1:
            return None, MSG_NO_AUTH
        member_id = member_id_bytes[:member_id_term].decode(encoding="ascii")

        m_token = s[m_token_addr : m_token_addr + 64].decode(encoding="ascii")
        m_ts = s[m_ts_addr : m_ts_addr + 13].decode(encoding="ascii")

        viber_auth = f"member_id:{member_id};m_token:{m_token};m_ts:{m_ts}"
        msg = "Got viber_auth successfully:\n"
        msg += f"{viber_auth=}\n"

        return viber_auth, msg

    def get_viber_desktop(self) -> Optional[str]:
        if platform.system() == "Windows":
            viber_bin_path = os.path.expandvars("%localappdata%/Viber/Viber.exe")
        elif platform.system() == "Darwin":
            viber_bin_path = "/Applications/Viber.app"
        else:
            if os.path.isfile("/opt/viber/Viber"):
                viber_bin_path = "/opt/viber/Viber"
            else:
                viber_which = shutil.which("Viber")
                if viber_which is None:
                    viber_which = shutil.which("viber")
                if viber_which is None:
                    viber_which = shutil.which("viber.AppImage")
                if viber_which is None:
                    viber_bin_path = "viber"
                else:
                    viber_bin_path = viber_which

        if Path(viber_bin_path).is_file() or Path(viber_bin_path).is_dir():
            return viber_bin_path

        return None

    def get_cred(
        self,
        viber_bin_path: Optional[str] = None,
    ) -> Tuple[Optional[str], str]:
        if not viber_bin_path:
            viber_bin_path = self.get_viber_desktop()

        if not viber_bin_path:
            return None, MSG_NO_BIN

        if platform.system() == "Windows":
            return self.get_auth_windows(viber_bin_path)
        elif platform.system() == "Darwin":
            return self.get_auth_darwin(viber_bin_path)
        else:
            return self.get_auth_linux(viber_bin_path)
