#!/usr/bin/env python3
import json
import time
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
from urllib.parse import urlparse

import requests

from sticker_convert.auth.auth_base import AuthBase
from sticker_convert.definitions import CONFIG_DIR
from sticker_convert.utils.chrome_remotedebug import CRD
from sticker_convert.utils.process import find_pid_by_name, killall
from sticker_convert.utils.translate import I


class AuthMisskey(AuthBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.OK_MSG = I("Got Misskey storage successfully")
        self.FAIL_MSG = I("Failed to get Misskey token")
        self.NO_URL = I("Error: misskey_url required")

        super().__init__(*args, **kwargs)

    def get_cred(self) -> Tuple[Optional[str], str]:
        msg = I("Getting Misskey storage")
        self.cb.put(("msg_dynamic", (msg,), None))

        if self.opt_cred.misskey_url == "":
            return None, self.NO_URL
        scheme = urlparse(self.opt_cred.misskey_url).scheme
        if scheme == "":
            scheme = "https"
        netloc = urlparse(self.opt_cred.misskey_url).netloc
        url = f"{scheme}://{netloc}/"

        chrome_path = CRD.get_chromium_path()
        if chrome_path is None:
            self.cb.put(("msg_dynamic", (None,), None))
            return (
                None,
                I("Please install Chrome/Chromium and try again"),
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

        crd = CRD(
            chrome_path, args=[f"--user-data-dir={CONFIG_DIR}/chromium-user-data", url]
        )
        while True:
            crd.connect()
            account = crd.get_storage("account")
            if account is None:
                time.sleep(1)
                crd.disconnect()
                continue
            try:
                account_dict = json.loads(account)
            except json.JSONDecodeError:
                time.sleep(1)
                crd.disconnect()
                continue
            token = account_dict.get("token")
            if token is None:
                time.sleep(1)
                crd.disconnect()
                continue
            if AuthMisskey.validate_token(self.opt_cred.misskey_url, token) is False:
                time.sleep(1)
                crd.disconnect()
                continue
            crd.close()
            self.cb.put(("msg_dynamic", (None,), None))
            return token, self.OK_MSG

    @staticmethod
    def validate_token(
        url: str,
        token: Union[CookieJar, Dict[str, str]],
    ) -> bool:
        scheme = urlparse(url).scheme
        if scheme == "":
            scheme = "https"
        netloc = urlparse(url).netloc
        response = requests.post(
            f"{scheme}://{netloc}/api/i",
            headers={"Referer": f"{scheme}://{netloc}/"},
            json={"i": token},
        )
        if response.ok:
            return True
        return False
