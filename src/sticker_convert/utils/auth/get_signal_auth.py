#!/usr/bin/env python3
import json
import os
import platform
import shutil
import time
import webbrowser
from typing import Callable, Optional, Tuple, cast

from sticker_convert.definitions import CONFIG_DIR
from sticker_convert.utils.chrome_remotedebug import CRD
from sticker_convert.utils.process import killall


class GetSignalAuth:
    def __init__(
        self,
        cb_msg: Callable[..., None] = print,
        cb_ask_str: Callable[..., str] = input,
    ) -> None:
        chromedriver_download_dir = CONFIG_DIR / "bin"
        os.makedirs(chromedriver_download_dir, exist_ok=True)

        self.chromedriver_download_dir = chromedriver_download_dir

        self.cb_ask_str = cb_ask_str
        self.cb_msg = cb_msg

    def download_signal_desktop(self) -> None:
        download_url = "https://signal.org/en/download/"

        webbrowser.open(download_url)

        self.cb_msg(download_url)

        prompt = "Signal Desktop not detected.\n"
        prompt += "Download and install Signal Desktop version\n"
        prompt += "After installation, quit Signal Desktop before continuing"
        if self.cb_ask_str != input:
            self.cb_ask_str(
                prompt, initialvalue=download_url, cli_show_initialvalue=False
            )
        else:
            self.cb_msg(prompt)

    def get_signal_bin_path(self) -> Optional[str]:
        signal_paths: Tuple[Optional[str], ...]
        if platform.system() == "Windows":
            signal_paths = (
                os.path.expandvars("%localappdata%/Programs/signal-desktop/Signal.exe"),
                os.path.expandvars(
                    "%localappdata%/Programs/signal-desktop-beta/Signal Beta.exe"
                ),
            )
        elif platform.system() == "Darwin":
            signal_paths = (
                "/Applications/Signal.app/Contents/MacOS/Signal",
                "/Applications/Signal Beta.app/Contents/MacOS/Signal Beta",
            )
        else:
            signal_paths = (
                shutil.which("signal-desktop"),
                shutil.which("signal-desktop-beta"),
                shutil.which("org.signal.Signal"),  # Flatpak
                os.path.expanduser(
                    "~/.local/share/flatpak/exports/bin/org.signal.Signal"
                ),
                "/var/lib/flatpak/exports/bin/org.signal.Signal",
            )

        for signal_path in signal_paths:
            if signal_path is not None and os.path.isfile(signal_path):
                return signal_path
        return None

    def get_cred(self) -> Tuple[Optional[str], Optional[str]]:
        signal_bin_path = self.get_signal_bin_path()
        if signal_bin_path is None:
            self.download_signal_desktop()
            return None, None

        if platform.system() == "Windows":
            killall("signal")
        else:
            killall("signal-desktop")

        crd = CRD(signal_bin_path)
        crd.connect()
        # crd.runtime_enable()
        # crd.reload()
        # while True:
        #     r = crd.ws.recv()
        #     data = json.loads(r)
        #     if data.get("method") == "Runtime.executionContextCreated":
        #         print(data)
        #     if (data.get("method") == "Runtime.executionContextCreated" and
        #         data["params"]["context"]["name"] == "Electron Isolated Context"
        #     ):
        #         context_id = data["params"]["context"]["id"]
        #         break
        # crd.runtime_disable()
        context_id = 2

        uuid, password = None, None
        while True:
            try:
                r = crd.exec_js(
                    "window.reduxStore.getState().items.uuid_id", context_id
                )
            except RuntimeError:
                break
            if (
                json.loads(r).get("result", {}).get("result", {}).get("type", "")
                == "string"
            ):
                uuid = cast(str, json.loads(r)["result"]["result"]["value"])
                break
            time.sleep(1)
        while True:
            try:
                r = crd.exec_js(
                    "window.reduxStore.getState().items.password", context_id
                )
            except RuntimeError:
                break
            if (
                json.loads(r).get("result", {}).get("result", {}).get("type", "")
                == "string"
            ):
                password = cast(str, json.loads(r)["result"]["result"]["value"])
                break
            time.sleep(1)

        crd.close()
        return uuid, password
