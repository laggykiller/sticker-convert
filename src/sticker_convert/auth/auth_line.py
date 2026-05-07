#!/usr/bin/env python3
import json
import time
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import requests

from sticker_convert.auth.auth_base import AuthBase
from sticker_convert.definitions import CONFIG_DIR
from sticker_convert.utils.chrome_remotedebug import CRD
from sticker_convert.utils.process import find_pid_by_name, killall
from sticker_convert.utils.translate import I


class AuthLine(AuthBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.OK_MSG = I("Got Line cookies successfully")
        self.FAIL_MSG = I("Failed to get Line cookies")

        super().__init__(*args, **kwargs)

    def get_cred(self) -> Tuple[Optional[str], str]:
        msg = I("Getting Line cookies")
        self.cb.put(("msg_dynamic", (msg,), None))

        msg = I("Getting Mastodon cookies")
        self.cb.put(("msg_dynamic", (msg,), None))

        chrome_path = CRD.get_chromium_path()
        if chrome_path is None:
            self.cb.put(("msg_dynamic", (None,), None))
            return (
                None,
                I("Please install Chrome/Chromium and try again"),
            )
        crd = CRD(
            chrome_path,
            args=[f"--user-data-dir={CONFIG_DIR}/chromium-user-data", "store.line.me"],
        )

        if find_pid_by_name(Path(chrome_path).name):
            response = self.cb.put(
                (
                    "ask_bool",
                    (
                        I("All {} will be closed. Continue?").format(
                            Path(chrome_path).name
                        ),
                    ),
                    None,
                )
            )
            if response is True:
                killall(Path(chrome_path).name.lower())
            else:
                return None, self.FAIL_MSG

        while True:
            crd.connect()
            cookies = crd.get_cookie(["store.line.me"])
            cookies_dict = {i["name"]: i["value"] for i in cookies}
            if cookies_dict["isLogin"] == "0":
                time.sleep(1)
                crd.disconnect()
                continue
            if AuthLine.validate_cookies(cookies_dict) is False:
                time.sleep(1)
                crd.disconnect()
                continue
            crd.close()
            self.cb.put(("msg_dynamic", (None,), None))
            cookies_list = ["%s=%s" % (i["name"], i["value"]) for i in cookies_dict]
            cookies = ";".join(cookies_list)
            return cookies, self.OK_MSG

    @staticmethod
    def validate_cookies(cookies: Union[CookieJar, Dict[str, str]]) -> bool:
        headers = {
            "x-requested-with": "XMLHttpRequest",
        }

        params = {"text": "test"}

        response = requests.get(
            "https://store.line.me/api/custom-sticker/validate/13782/en",
            params=params,
            cookies=cookies,  # type: ignore
            headers=headers,
        )

        response_dict = json.loads(response.text)

        if response_dict["errorMessage"]:
            return False
        return True
