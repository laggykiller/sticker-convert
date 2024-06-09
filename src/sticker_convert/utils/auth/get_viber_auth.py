#!/usr/bin/env python3
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple, cast

import psutil
from PyMemoryEditor import OpenProcess  # type: ignore

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


def killall(name: str) -> bool:
    result = False
    for proc in psutil.process_iter():
        if proc.name() == name:
            proc.kill()
            result = True

    return result


class GetViberAuth:
    def get_auth(self, viber_bin_path: str) -> Tuple[Optional[str], str]:
        member_id = None
        m_token = None
        m_ts = None

        viber_process_name = Path(viber_bin_path).name.replace(".AppImage", "")

        killed = killall(viber_process_name)
        if killed:
            time.sleep(5)
        subprocess.Popen([viber_bin_path])
        time.sleep(10)

        with OpenProcess(process_name=viber_process_name) as process:
            for address in process.search_by_value(str, 18, "X-Viber-Auth-Mid: "):  # type: ignore
                member_id_addr = cast(int, address) + 18
                member_id = process.read_process_memory(member_id_addr, str, 12)
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

        killall(viber_process_name)

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

        killed = killall("Viber")
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
        killall("Viber")

        member_id_addr = s.find(b"X-Viber-Auth-Mid: ") + 18
        m_token_addr = s.find(b"X-Viber-Auth-Token: ") + 20
        m_ts_addr = s.find(b"X-Viber-Auth-Timestamp: ") + 24

        if member_id_addr == -1 or m_token_addr == -1 or m_ts_addr == -1:
            return None, MSG_NO_AUTH

        member_id = s[member_id_addr : member_id_addr + 12].decode(encoding="ascii")
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

        if Path(viber_bin_path).is_file():
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

        if platform.system() == "Darwin":
            return self.get_auth_darwin(viber_bin_path)
        else:
            return self.get_auth(viber_bin_path)
