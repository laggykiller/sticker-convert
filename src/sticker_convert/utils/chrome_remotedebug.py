#!/usr/bin/env python3
import base64
import io
import json
import os
import platform
import shutil
import signal
import socket
import subprocess
import time
from typing import Any, Dict, List, Optional, Union, cast

import requests
import websocket
from PIL import Image

# References
# https://github.com/yeongbin-jo/python-chromedriver-autoinstaller/blob/master/chromedriver_autoinstaller/utils.py
# https://chromedevtools.github.io/devtools-protocol/


BROWSER_PREF = [
    "chrome",
    "chrome-canary",
    "chromium",
    "msedge",
    "msedge-beta",
    "msedge-dev",
    "msedge-canary",
    "brave",
    "brave-beta",
    "brave-nightly",
    "opera",
    "opera-beta",
    "opera-developer",
]


def get_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("", 0))
        port = sock.getsockname()[1]
    return port


class CRD:
    def __init__(
        self,
        chrome_bin: str,
        port: Optional[int] = None,
        args: Optional[List[str]] = None,
    ) -> None:
        if port is None:
            port = get_free_port()
        self.port = port

        launch_cmd: List[str] = []
        if (
            platform.system() == "Linux"
            and os.environ.get("DISPLAY", False) is False
            and shutil.which("xvfb-run")
        ):
            launch_cmd += ["xvfb-run", "--server-args='-screen 0, 1024x768x24'"]

        launch_cmd += [
            chrome_bin,
            f"--remote-debugging-port={port}",
            f"--remote-allow-origins=http://127.0.0.1:{port}",
        ]
        if args:
            launch_cmd += args

        # Adding --no-sandbox in Windows may cause Signal fail to launch
        # https://github.com/laggykiller/sticker-convert/issues/274
        if (
            platform.system() != "Windows"
            and "geteuid" in dir(os)
            and os.geteuid() == 0
        ) or os.path.isfile("/.dockerenv"):
            launch_cmd.append("--no-sandbox")

        self.chrome_proc = subprocess.Popen(launch_cmd)

    @staticmethod
    def get_chromium_path() -> Optional[str]:
        if platform.system() == "Windows":
            from sticker_convert.utils.chromiums.windows import get_chromium_path
        elif platform.system() == "Darwin":
            from sticker_convert.utils.chromiums.osx import get_chromium_path
        else:
            from sticker_convert.utils.chromiums.linux import get_chromium_path
        return get_chromium_path()

    def connect(self, target_id: int = 0) -> None:
        self.cmd_id = 1
        r = None
        targets: List[Any] = []
        for _ in range(30):
            try:
                r = requests.get(f"http://127.0.0.1:{self.port}/json")
                targets = json.loads(r.text)
                if len(targets) == 0:
                    time.sleep(1)
                    continue
                break
            except requests.exceptions.ConnectionError:
                time.sleep(1)

        if r is None:
            raise RuntimeError("Cannot connect to chrome debugging port")

        if len(targets) == 0:
            raise RuntimeError("Cannot create websocket connection with debugger")

        self.ws = websocket.create_connection(  # type: ignore
            targets[target_id]["webSocketDebuggerUrl"]
        )

    def send_cmd(self, command: Dict[Any, Any]) -> Union[str, bytes]:
        if command.get("id") is None:
            command["id"] = self.cmd_id
        for _ in range(3):
            try:
                self.ws.send(json.dumps(command))
                r = self.ws.recv()
                self.cmd_id += 1
                return r
            except BrokenPipeError:
                self.connect()

        raise RuntimeError("Websocket keep disconnecting")

    def exec_js(self, js: str, context_id: Optional[int] = None) -> Union[str, bytes]:
        command: Dict[str, Any] = {
            "id": self.cmd_id,
            "method": "Runtime.evaluate",
            "params": {"expression": js},
        }
        if context_id is not None:
            command["params"]["contextId"] = context_id
        return self.send_cmd(command)

    def set_transparent_bg(self) -> Union[str, bytes]:
        command: Dict[str, Any] = {
            "id": self.cmd_id,
            "method": "Emulation.setDefaultBackgroundColorOverride",
            "params": {"color": {"r": 0, "g": 0, "b": 0, "a": 0}},
        }
        return self.send_cmd(command)

    def screenshot(self, clip: Optional[Dict[str, int]] = None) -> Image.Image:
        command: Dict[str, Any] = {
            "id": self.cmd_id,
            "method": "Page.captureScreenshot",
            "params": {"captureBeyondViewport": True, "optimizeForSpeed": True},
        }
        if clip:
            command["params"]["clip"] = clip
        result = self.send_cmd(command)
        return Image.open(
            io.BytesIO(base64.b64decode(json.loads(result)["result"]["data"]))
        )

    def get_curr_url(self) -> str:
        r = self.exec_js("window.location.href")
        return cast(
            str, json.loads(r).get("result", {}).get("result", {}).get("value", "")
        )

    def navigate(self, url: str) -> None:
        command = {"id": self.cmd_id, "method": "Page.navigate", "params": {"url": url}}
        self.send_cmd(command)

    def open_html_str(self, html: str) -> None:
        command: Dict[str, Any] = {
            "id": self.cmd_id,
            "method": "Page.navigate",
            "params": {"url": "about:blank"},
        }
        result = cast(str, self.send_cmd(command))
        frame_id = json.loads(result).get("result", {}).get("frameId", None)
        if frame_id is None:
            raise RuntimeError(f"Cannot navigate to about:blank ({result})")

        self.exec_js('document.getElementsByTagName("html")[0].remove()')

        command = {
            "id": self.cmd_id,
            "method": "Page.setDocumentContent",
            "params": {"frameId": frame_id, "html": html},
        }
        self.send_cmd(command)

    def runtime_enable(self) -> None:
        command = {
            "method": "Runtime.enable",
        }
        self.send_cmd(command)

    def runtime_disable(self) -> None:
        command = {
            "method": "Runtime.disable",
        }
        self.send_cmd(command)

    def reload(self) -> None:
        command = {
            "method": "Page.reload",
        }
        self.send_cmd(command)

    def close(self) -> None:
        command = {
            "method": "Browser.close",
        }
        self.send_cmd(command)
        self.ws.close()
        os.kill(self.chrome_proc.pid, signal.SIGTERM)
