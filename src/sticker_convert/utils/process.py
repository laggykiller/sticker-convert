#!/usr/bin/env python3
import os
import platform
import shutil
import subprocess
import time
from getpass import getpass
from typing import Callable, Optional, Tuple

import psutil

from sticker_convert.definitions import ROOT_DIR


def killall(name: str) -> bool:
    result = False

    for proc in psutil.process_iter():
        if name in proc.name().lower():
            proc.kill()
            result = True

    return result


def find_pid_by_name(name: str) -> Optional[int]:
    for proc in psutil.process_iter():
        if name in proc.name().lower():
            return proc.pid

    return None


def check_admin() -> bool:
    return True


if platform.system() == "Windows":

    def check_admin() -> bool:
        username = os.getenv("username")
        if username is None:
            return False

        s = subprocess.run(
            ["net", "user", username],
            capture_output=True,
            text=True,
        ).stdout

        return True if "*Administrators" in s else False

elif platform.system() == "Linux":

    def check_admin() -> bool:
        if shutil.which("sudo") is None:
            return True

        s = subprocess.run(
            ["sudo", "-l"],
            capture_output=True,
            text=True,
        ).stdout

        return True if "may run the following commands" in s else False


def get_mem(
    pid: int, pw_func: Optional[Callable[..., str]] = None
) -> Tuple[Optional[bytes], str]:
    return b"", ""


if platform.system() == "Windows":

    def get_mem(
        pid: int, pw_func: Optional[Callable[..., str]] = None
    ) -> Tuple[Optional[bytes], str]:
        from pathlib import WindowsPath

        memdump_ps_path = str(WindowsPath(ROOT_DIR / "resources/memdump_windows.ps1"))
        arglist = f'-NoProfile -ExecutionPolicy Bypass -File "{memdump_ps_path}" {pid}'
        dump_fpath = os.path.expandvars(f"%temp%/memdump.bin.{pid}")

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

elif platform.system() == "Darwin":

    def get_mem(
        pid: int, pw_func: Optional[Callable[..., str]] = None
    ) -> Tuple[Optional[bytes], str]:
        subprocess.run(
            [
                "lldb",
                "--attach-pid",
                str(pid),
                "-o",
                f"process save-core /tmp/memdump.{pid}.dmp",
                "-o",
                "quit",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        with open(f"/tmp/memdump.{pid}.dmp", "rb") as f:
            s = f.read()

        os.remove(f"/tmp/memdump.{pid}.dmp")

        return s, ""

else:

    def get_mem(
        pid: int, pw_func: Optional[Callable[..., str]] = None
    ) -> Tuple[Optional[bytes], str]:
        memdump_sh_path = (ROOT_DIR / "resources/memdump_linux.sh").as_posix()

        s = subprocess.run(
            [
                memdump_sh_path,
                str(pid),
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
                    str(pid),
                ],
                capture_output=True,
            ).stdout
        else:
            prompt = "Enter sudo password: "
            if pw_func:
                sudo_password = pw_func(prompt)
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
                    str(pid),
                ],
                capture_output=True,
                stdin=sudo_password_pipe.stdout,
            ).stdout

        return s, ""
