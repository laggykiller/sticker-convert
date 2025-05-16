#!/usr/bin/env python3
import os
import platform
import shutil
import subprocess
import time
from getpass import getpass
from io import BytesIO
from typing import Callable, Optional, Union
from zipfile import ZipFile

import psutil
import requests

from sticker_convert.definitions import CONFIG_DIR, ROOT_DIR


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


def _get_mem_win_procdump(
    pid: Union[str, int],
    pw_func: Optional[Callable[..., str]] = None,
    is_wine: bool = False,
) -> Optional[bytes]:
    procdump_dir = CONFIG_DIR / "ProcDump"
    procdump_bin = procdump_dir / "procdump.exe"
    if procdump_bin.is_file() is False:
        r = requests.get("https://download.sysinternals.com/files/Procdump.zip")
        if r.ok is False:
            return None
        with ZipFile(BytesIO(r.content)) as zf:
            zf.extractall(procdump_dir)

    if procdump_bin.is_file() is False:
        return None

    if is_wine:
        cmd = ["wine"]
        dump_fpath = f"/tmp/memdump.{pid}.dmp"
    else:
        cmd = []
        dump_fpath = os.path.expandvars(f"%temp%/memdump.{pid}.dmp")
    cmd += [str(procdump_bin), "-accepteula", "-ma", str(pid), dump_fpath]

    subprocess.run(cmd)

    with open(dump_fpath, "rb") as f:
        s = f.read()
    os.remove(dump_fpath)

    return s


def _get_mem_win_builtin(
    pid: Union[str, int], pw_func: Optional[Callable[..., str]] = None
) -> Optional[bytes]:
    from pathlib import WindowsPath

    memdump_ps_path = str(WindowsPath(ROOT_DIR / "resources/memdump_windows.ps1"))
    arglist = f'-NoProfile -ExecutionPolicy Bypass -File "{memdump_ps_path}" {pid}'
    dump_fpath = os.path.expandvars(f"%temp%/memdump.{pid}.dmp")

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

    return s


def _get_mem_darwin(
    pid: Union[str, int], pw_func: Optional[Callable[..., str]] = None
) -> Optional[bytes]:
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

    return s


def _get_mem_linux(
    pid: Union[str, int], pw_func: Optional[Callable[..., str]] = None
) -> Optional[bytes]:
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

    return s


def get_mem(
    pid: Union[str, int],
    pw_func: Optional[Callable[..., str]] = None,
    is_wine: bool = False,
) -> Optional[bytes]:
    if is_wine or platform.system() == "Windows":
        dump = _get_mem_win_procdump(pid, pw_func, is_wine)
        if dump is not None or is_wine:
            return dump
        else:
            return _get_mem_win_builtin(pid, pw_func)
    elif platform.system() == "Darwin":
        return _get_mem_darwin(pid, pw_func)
    else:
        return _get_mem_linux(pid, pw_func)
