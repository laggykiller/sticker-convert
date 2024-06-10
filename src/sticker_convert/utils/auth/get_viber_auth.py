#!/usr/bin/env python3
import importlib.util
import os
import platform
import shutil
import signal
import subprocess
import time
from getpass import getpass
from pathlib import Path
from typing import Callable, List, Optional, Tuple, cast

from sticker_convert.definitions import ROOT_DIR

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
MSG_NO_PGREP = "pgrep command or psutil python package is necessary"
MSG_LAUNCH_FAIL = "Failed to launch Viber"
MSG_PERMISSION_ERROR = "Failed to read Viber process memory"


def check_admin_windows() -> bool:
    username = os.getenv("username")
    if username is None:
        return False

    s = subprocess.run(
        ["net", "user", username],
        capture_output=True,
        text=True,
    ).stdout

    return True if "*Administrators" in s else False


def check_admin_linux() -> bool:
    s = subprocess.run(
        ["sudo", "-l"],
        capture_output=True,
        text=True,
    ).stdout

    return True if "may run the following commands" in s else False


def killall(name: str) -> bool:
    result = False

    while True:
        pid = find_pid_by_name(name)
        if pid is not None:
            os.kill(pid, signal.SIGTERM)
            result = True
        else:
            break

    return result


def find_pid_by_name(name: str) -> Optional[int]:
    if platform.system() == "Windows":
        s = subprocess.run(
            ["powershell", "-c", "Get-Process", f"*{name}*"],
            capture_output=True,
            text=True,
        ).stdout

        for line in s.split("\n"):
            if name in line.lower():
                info = name.split()
                pid = info[5]
                if pid.isnumeric():
                    return int(pid)

        return None
    else:
        if platform.system() == "Darwin":
            pattern = "Viber"
        else:
            pattern = ".*[Vv]iber.*"
        pid = (
            subprocess.run(["pgrep", pattern], capture_output=True, text=True)
            .stdout.split("\n")[0]
            .strip()
        )
        if pid == "" or pid.isnumeric() is False:
            return None
        else:
            return int(pid)


if importlib.util.find_spec("psutil"):
    import psutil

    def killall(name: str) -> bool:
        result = False

        for proc in psutil.process_iter():  # type: ignore
            if name in proc.name().lower():
                proc.kill()
                result = True

        return result

    def find_pid_by_name(name: str) -> Optional[int]:
        for proc in psutil.process_iter():  # type: ignore
            if name in proc.name().lower():
                return proc.pid

        return None


class GetViberAuth:
    def __init__(self, cb_ask_str: Callable[..., str] = input):
        self.cb_ask_str = cb_ask_str

    def relaunch_viber(self, viber_bin_path: str) -> Optional[int]:
        killed = killall("viber")
        if killed:
            time.sleep(5)

        if platform.system() == "Darwin":
            cmd = ["open", "-n", viber_bin_path]
        else:
            cmd = [viber_bin_path]
        subprocess.Popen(cmd)
        time.sleep(10)

        return find_pid_by_name("viber")

    def get_mem_windows(self, viber_pid: int) -> Tuple[Optional[bytes], str]:
        from pathlib import WindowsPath

        memdump_ps_path = str(WindowsPath(ROOT_DIR / "resources/memdump_windows.ps1"))
        arglist = (
            f'-NoProfile -ExecutionPolicy Bypass -File "{memdump_ps_path}" {viber_pid}'
        )
        dump_fpath = os.path.expandvars(f"%temp%/memdump.bin.{viber_pid}")

        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"Start-Process -Verb RunAs powershell -ArgumentList '{arglist}'",
        ]

        subprocess.run(cmd, capture_output=True, text=True)

        while True:
            try:
                with open(dump_fpath, "rb") as f:
                    s = f.read()
                if len(s) != 0:
                    break
                time.sleep(1)
            except (FileNotFoundError, PermissionError):
                pass

        while True:
            try:
                os.remove(dump_fpath)
                break
            except PermissionError:
                pass

        return s, ""

    def get_mem_linux(self, viber_pid: int) -> Tuple[Optional[bytes], str]:
        memdump_sh_path = (ROOT_DIR / "resources/memdump_linux.sh").as_posix()

        s = subprocess.run(
            [
                memdump_sh_path,
                str(viber_pid),
            ],
            capture_output=True,
        ).stdout

        if len(s) > 1000:
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

        return s, ""

    def get_mem_darwin(self, viber_pid: int) -> Tuple[Optional[bytes], str]:
        subprocess.run(
            [
                "lldb",
                "--attach-pid",
                str(viber_pid),
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

        return s, ""

    def get_auth_by_pme(
        self, viber_bin_path: str, relaunch: bool = True
    ) -> Tuple[Optional[str], str]:
        from PyMemoryEditor import OpenProcess  # type: ignore

        member_id = None
        m_token = None
        m_ts = None

        if relaunch:
            viber_pid = self.relaunch_viber(viber_bin_path)
        else:
            viber_pid = find_pid_by_name("viber")
        if viber_pid is None:
            return None, MSG_LAUNCH_FAIL

        try:
            with OpenProcess(pid=int(viber_pid)) as process:
                for address in process.search_by_value(str, 18, "X-Viber-Auth-Mid: "):  # type: ignore
                    member_id_addr = cast(int, address) + 18
                    member_id_bytes = process.read_process_memory(
                        member_id_addr, bytes, 20
                    )
                    member_id_term = member_id_bytes.find(b"\x0d\x0a")
                    if member_id_term == -1:
                        continue
                    member_id = member_id_bytes[:member_id_term].decode(
                        encoding="ascii"
                    )
                    break
                if member_id is None:
                    return None, MSG_NO_AUTH

                for address in process.search_by_value(str, 20, "X-Viber-Auth-Token: "):  # type: ignore
                    m_token_addr = cast(int, address) + 20
                    m_token = process.read_process_memory(m_token_addr, str, 64)
                    break
                if m_token is None:
                    return None, MSG_NO_AUTH

                for address in process.search_by_value(  # type: ignore
                    str, 24, "X-Viber-Auth-Timestamp: "
                ):
                    m_ts_addr = cast(int, address) + 24
                    m_ts = process.read_process_memory(m_ts_addr, str, 13)
                    break
                if m_ts is None:
                    return None, MSG_NO_AUTH
        except PermissionError:
            return None, MSG_PERMISSION_ERROR

        viber_auth = f"member_id:{member_id};m_token:{m_token};m_ts:{m_ts}"
        msg = "Got viber_auth successfully:\n"
        msg += f"{viber_auth=}\n"

        return viber_auth, msg

    def get_auth_by_dump(
        self, viber_bin_path: str, relaunch: bool = True
    ) -> Tuple[Optional[str], str]:
        member_id = None
        m_token = None
        m_ts = None

        if platform.system() == "Darwin":
            csrutil_status = subprocess.run(
                ["csrutil", "status"], capture_output=True, text=True
            ).stdout

            if "enabled" in csrutil_status:
                return None, MSG_SIP_ENABLED
        elif (
            platform.system() != "Windows"
            and shutil.which("pgrep") is None
            and importlib.find_loader("psutil") is None
        ):
            return None, MSG_NO_PGREP

        if relaunch:
            viber_pid = self.relaunch_viber(viber_bin_path)
        else:
            viber_pid = find_pid_by_name("viber")
        if viber_pid is None:
            return None, MSG_LAUNCH_FAIL

        if platform.system() == "Windows":
            s, msg = self.get_mem_windows(viber_pid)
        elif platform.system() == "Darwin":
            s, msg = self.get_mem_darwin(viber_pid)
        else:
            s, msg = self.get_mem_linux(viber_pid)

        if s is None:
            return None, msg

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
        viber_auth = None
        msg = ""

        pme_present = importlib.util.find_spec("PyMemoryEditor") is not None
        if platform.system() == "Darwin":
            methods.append(self.get_auth_by_dump)
        elif platform.system() == "Windows":
            methods.append(self.get_auth_by_dump)
            if pme_present:
                methods.append(self.get_auth_by_pme)
            if check_admin_windows() is False:
                methods.reverse()
        else:
            if not os.path.isfile("/.dockerenv"):
                methods.append(self.get_auth_by_dump)
            if pme_present:
                methods.append(self.get_auth_by_pme)
            if check_admin_linux() is False:
                methods.reverse()

        for method in methods:
            viber_auth, msg = method(viber_bin_path, relaunch)
            relaunch = False
            if viber_auth is not None:
                break

        killall("viber")
        return viber_auth, msg
