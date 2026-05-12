#!/usr/bin/env python3
import json
import os
import platform
import subprocess
import time
from collections.abc import Generator
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast
import stat

import qrcode
import requests

from sticker_convert.auth.auth_base import AuthBase
from sticker_convert.definitions import CONFIG_DIR
from sticker_convert.utils.translate import I


class SWB:
    def __init__(self, try_download: bool = False):
        self.process: Optional[subprocess.Popen[str]] = None
        swb_dir = CONFIG_DIR / "SWB"
        swb_fname = "swb.exe" if platform.system() == "Windows" else "swb"
        swb_dir.mkdir(exist_ok=True)
        self.swb_bin = swb_dir / swb_fname
        self.success = False

        if self.swb_bin.is_file():
            swb_ver = subprocess.run(
                [self.swb_bin, "-v"], capture_output=True, text=True
            ).stdout.strip()
        else:
            swb_ver = None
        latest_tag = self.get_swb_latest_tag()
        if latest_tag is None:
            if swb_ver is None:
                self.msg = I(
                    "Error: Failed to get latest tag of sticker-whatsapp-bridge"
                )
                return
        elif (swb_ver is None or swb_ver != latest_tag) and try_download is True:
            self.success, self.msg = self.get_swb(latest_tag, self.swb_bin)
            return
        self.success = False if swb_ver is None else True
        self.msg = I("Found sticker-whatsapp-bridge at {}").format(self.swb_bin)

    def get_swb_latest_tag(self) -> Optional[str]:
        r = requests.get(
            "https://api.github.com/repos/laggykiller/sticker-whatsapp-bridge/tags"
        )
        if r.ok == False:
            return None
        try:
            tags_lst = json.loads(r.text)
            return tags_lst[0].get("name")
        except json.JSONDecodeError:
            return None

    def get_swb_arch(self) -> Optional[str]:
        archs = {
            "x64": ["amd64", "x86_64", "x64"],
            "arm64": ["arm64", "aarch64", "aarch64_be", "armv8b", "armv8l"],
        }

        for k, v in archs.items():
            if platform.machine().lower() in v:
                return k
        return None

    def get_swb(self, tag: str, dest: Path) -> Tuple[bool, str]:
        if platform.system() == "Windows":
            plat = "windows"
            suffix = ".exe"
        elif platform.system() == "Darwin":
            plat = "darwin"
            suffix = ""
        elif platform.system() == "Linux":
            plat = "linux"
            libc_name, _ = platform.libc_ver()
            suffix = "-musl" if libc_name == "musl" else ""
        else:
            return False, I("Error: {} is not supported").format(platform.system())

        arch = self.get_swb_arch()
        if arch == None:
            return False, I("Error: {} is not supported").format(platform.machine())
        fname = f"swb-{tag}-{plat}-{arch}{suffix}"

        r = requests.get(
            f"https://github.com/laggykiller/sticker-whatsapp-bridge/releases/download/{tag}/{fname}"
        )

        if r.ok is False:
            return False, I("Failed to download sticker-whatsapp-bridge {}").format(
                fname
            )

        with open(dest, "wb+") as f:
            f.write(r.content)
        os.chmod(dest, os.stat(dest).st_mode | stat.S_IXUSR)
        return True, I("Downloaded sticker-whatsapp-bridge {}").format(fname)

    def run(self, cmd: List[str]) -> Generator[Optional[Dict[str, str]], None, int]:
        cmds = [str(self.swb_bin)]
        cmds.extend(cmd)
        self.process = subprocess.Popen(
            cmds,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        os.set_blocking(cast(StringIO, self.process.stdout).fileno(), False)

        while True:
            returncode = self.process.poll()
            line = cast(StringIO, self.process.stdout).readline()
            if line == "":
                if returncode is not None:
                    return returncode
                else:
                    yield None
                    time.sleep(1)
            else:
                try:
                    r = cast(Dict[str, str], json.loads(line))
                    yield r
                except json.JSONDecodeError:
                    yield None

    def kill(self):
        if self.process is not None:
            self.process.kill()


class AuthWhatsapp(AuthBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_cred(self) -> Tuple[bool, str]:
        self.cb.put(
            ("msg_dynamic", (I("Downloading sticker-whatsapp-bridge..."),), None)
        )

        swb = SWB(try_download=True)
        if swb.success is False:
            return False, swb.msg
        cmds = ["login", "--json", "--auth-info", str(CONFIG_DIR / "SWB/auth")]
        if self.opt_cred.whatsapp_phone_number:
            cmds.append("-o")
            cmds.append(self.opt_cred.whatsapp_phone_number)

        success = False
        msg = I("Failed to login: whatsapp-sticker-bridge returned nothing")
        for r in swb.run(cmds):
            if r is None:
                continue
            if r["event"] == "login":
                if self.opt_cred.whatsapp_phone_number:
                    prompt = I("Please enter {} on WhatsApp mobile").format(r["code"])
                    self.cb.put(("msg_dynamic", (None,), None))
                    self.cb.put(("msg_dynamic", (prompt,), None))
                else:
                    qr = qrcode.QRCode()
                    qr.add_data(r["code"])
                    with StringIO() as qr_ascii_io:
                        qr.print_ascii(qr_ascii_io)
                        qr_ascii_io.seek(0)
                        qr_ascii = qr_ascii_io.read()
                    prompt = (
                        I("Please scan WhatsApp Web login QR code") + "\n" + qr_ascii
                    )
                    self.cb.put(("msg_dynamic", (None,), None))
                    self.cb.put(("msg_dynamic", (prompt,), {"monospace": True}))
            elif r["event"] == "login_success":
                success = True
                msg = I("Login WhatsApp success")
            elif r["event"] == "error":
                msg = I("Failed to login: {}").format(r["message"])
        self.cb.put(("msg_dynamic", (None,), None))

        return success, msg
