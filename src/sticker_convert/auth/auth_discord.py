#!/usr/bin/env python3
import json
import os
import platform
import shutil
import time
from pathlib import Path
from typing import Any, Optional, Tuple
from urllib.parse import urlparse

from sticker_convert.auth.auth_base import AuthBase
from sticker_convert.definitions import CONFIG_DIR
from sticker_convert.utils.chrome_remotedebug import CRD
from sticker_convert.utils.process import find_pid_by_name, killall

OK_MSG = "Got token successfully:\ntoken={token}"
FAIL_MSG = "Failed to get token"


class AuthDiscord(AuthBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        chromedriver_download_dir = CONFIG_DIR / "bin"
        os.makedirs(chromedriver_download_dir, exist_ok=True)

        self.chromedriver_download_dir = chromedriver_download_dir

    def get_discord_bin_path(self) -> Optional[str]:
        discord_bin: Optional[str]
        if platform.system() == "Windows":
            discord_win_dirs: Tuple[Tuple[str, str], ...]
            discord_win_dirs = (
                (
                    os.path.expandvars("%localappdata%/Discord"),
                    "Discord.exe",
                ),
                (
                    os.path.expandvars("%localappdata%/DiscordCanary"),
                    "DiscordCanary.exe",
                ),
                (
                    os.path.expandvars("%localappdata%/DiscordPTB"),
                    "DiscordPTB.exe",
                ),
            )
            for discord_dir, discord_bin in discord_win_dirs:
                app_dir: Optional[str] = None
                chrome_path: Optional[str] = None
                if os.path.isdir(discord_dir) is False:
                    continue
                for i in [j for j in os.listdir(discord_dir) if j.startswith("app-")]:
                    app_dir = os.path.join(discord_dir, i)
                    chrome_path = os.path.join(app_dir, discord_bin)
                    if os.path.isfile(chrome_path):
                        return chrome_path
        else:
            discord_dirs: Tuple[Optional[str], ...]
            if platform.system() == "Darwin":
                discord_dirs = (
                    "/Applications/Discord.app/Contents/MacOS/Discord",
                    "/Applications/Discord Canary.app/Contents/MacOS/Discord Canary",
                    "/Applications/Discord PTB.app/Contents/MacOS/Discord PTB",
                )
            else:
                discord_dirs = (
                    shutil.which("discord"),
                    shutil.which("discord-canary"),
                    shutil.which("discord-ptb"),
                )
            for discord_bin in discord_dirs:
                if discord_bin is not None and os.path.isfile(discord_bin):
                    return discord_bin
        return None

    def get_cred(self) -> Tuple[Optional[str], str]:
        msg = "Getting Discord authorization token..."
        self.cb.put(("msg_dynamic", (msg,), None))

        using_discord_app = False
        chrome_path = self.get_discord_bin_path()
        if chrome_path is not None:
            using_discord_app = True
        else:
            chrome_path = CRD.get_chromium_path()
        if chrome_path is None:
            self.cb.put(("msg_dynamic", (None,), None))
            return (
                None,
                "Please install Discord Desktop or Chrome/Chromium and try again",
            )

        token = None

        if find_pid_by_name(Path(chrome_path).name):
            response = self.cb.put(
                (
                    "ask_bool",
                    (f"All {Path(chrome_path).name} will be closed. Continue?",),
                    None,
                )
            )
            if response is True:
                killall(Path(chrome_path).name.lower())
            else:
                return None, FAIL_MSG

        crd = CRD(chrome_path)
        while True:
            crd.connect()
            if using_discord_app is False:
                crd.navigate("https://discord.com/channels/@me")
                break
            else:
                curr_url = crd.get_curr_url()
                netloc = urlparse(curr_url).netloc
                if netloc in ("discordapp.com", "discord.com"):
                    break
                time.sleep(1)

        while True:
            try:
                if using_discord_app:
                    r = crd.exec_js(
                        "(webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken();"
                    )
                else:
                    r = crd.exec_js(
                        "const iframe=document.createElement('iframe');JSON.parse(document.body.appendChild(iframe).contentWindow.localStorage.token);"
                    )
            except RuntimeError:
                break
            if (
                json.loads(r).get("result", {}).get("result", {}).get("type", "")
                == "string"
            ):
                token = json.loads(r)["result"]["result"]["value"]
                break
            time.sleep(1)
        crd.close()

        self.cb.put(("msg_dynamic", (None,), None))
        if token is None:
            return None, FAIL_MSG

        return token, OK_MSG.format(token=token)
