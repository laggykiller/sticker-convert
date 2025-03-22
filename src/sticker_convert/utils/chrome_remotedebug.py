#!/usr/bin/env python3
import json
import os
import platform
import shutil
import socket
import subprocess
import time
from typing import Any, Dict, Optional, Union, cast

import requests
import websocket

# References
# https://github.com/yeongbin-jo/python-chromedriver-autoinstaller/blob/master/chromedriver_autoinstaller/utils.py
# https://chromedevtools.github.io/devtools-protocol/


def get_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("", 0))
        port = sock.getsockname()[1]
    return port


class CRD:
    def __init__(self, chrome_bin: str, port: Optional[int] = None):
        if port is None:
            port = get_free_port()
        self.port = port
        launch_cmd = [
            chrome_bin,
            f"--remote-debugging-port={port}",
            f"--remote-allow-origins=http://localhost:{port}",
        ]

        # Adding --no-sandbox in Windows may cause Signal fail to launch
        # https://github.com/laggykiller/sticker-convert/issues/274
        if (
            platform.system() != "Windows"
            and "geteuid" in dir(os)
            and os.geteuid() == 0
        ):
            launch_cmd.append("--no-sandbox")

        self.chrome_proc = subprocess.Popen(launch_cmd)

    @staticmethod
    def get_chrome_path() -> Optional[str]:
        chrome_bin: Optional[str]
        if platform.system() == "Darwin":
            chrome_bin = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

            if os.path.isfile(chrome_bin) is False:
                return None

            return chrome_bin

        elif platform.system() == "Windows":
            chrome_x64 = f"{os.environ.get('PROGRAMW6432') or os.environ.get('PROGRAMFILES')}\\Google\\Chrome\\Application"
            chrome_x86 = (
                f"{os.environ.get('PROGRAMFILES(X86)')}\\Google\\Chrome\\Application"
            )

            chrome_dir = (
                chrome_x64
                if os.path.isdir(chrome_x64)
                else chrome_x86
                if os.path.isdir(chrome_x86)
                else None
            )

            if chrome_dir is None:
                return None

            return chrome_dir + "\\chrome.exe"

        else:
            for executable in (
                "google-chrome",
                "google-chrome-stable",
                "google-chrome-beta",
                "google-chrome-dev",
                "chromium-browser",
                "chromium",
            ):
                chrome_bin = shutil.which(executable)
                if chrome_bin is not None:
                    return chrome_bin
            return None

    def connect(self):
        self.cmd_id = 1
        r = None
        for _ in range(30):
            try:
                r = requests.get(f"http://localhost:{self.port}/json")
                break
            except requests.exceptions.ConnectionError:
                time.sleep(1)

        if r is None:
            raise RuntimeError("Cannot connect to chrome debugging port")

        targets = json.loads(r.text)
        for _ in range(30):
            if len(targets) == 0:
                time.sleep(1)
            else:
                break

        if len(targets) == 0:
            raise RuntimeError("Cannot create websocket connection with debugger")

        self.ws = websocket.create_connection(targets[0]["webSocketDebuggerUrl"])  # type: ignore

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

    def exec_js(self, js: str, context_id: Optional[int] = None):
        command: Dict[str, Any] = {
            "id": self.cmd_id,
            "method": "Runtime.evaluate",
            "params": {"expression": js},
        }
        if context_id is not None:
            command["params"]["contextId"] = context_id
        return self.send_cmd(command)

    def get_curr_url(self) -> str:
        r = self.exec_js("window.location.href")
        return cast(
            str, json.loads(r).get("result", {}).get("result", {}).get("value", "")
        )

    def navigate(self, url: str):
        command = {"id": self.cmd_id, "method": "Page.navigate", "params": {"url": url}}
        self.send_cmd(command)

    def runtime_enable(self):
        command = {
            "method": "Runtime.enable",
        }
        self.send_cmd(command)

    def runtime_disable(self):
        command = {
            "method": "Runtime.disable",
        }
        self.send_cmd(command)

    def reload(self):
        command = {
            "method": "Page.reload",
        }
        self.send_cmd(command)

    def close(self):
        self.ws.close()
        self.chrome_proc.kill()
