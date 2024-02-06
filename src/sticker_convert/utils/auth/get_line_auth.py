#!/usr/bin/env python3
import json
import platform
from http.cookiejar import CookieJar
from typing import Optional, Union, Callable, Any

import requests
import rookiepy


class GetLineAuth:
    def get_cred(self) -> Optional[str]:
        browsers: list[Callable[..., Any]] = [
            rookiepy.load,  # type: ignore # Supposed to load from any browser, but may fail
            rookiepy.firefox,  # type: ignore
            rookiepy.libre_wolf,  # type: ignore
            rookiepy.chrome,  # type: ignore
            rookiepy.chromium,  # type: ignore
            rookiepy.brave,  # type: ignore
            rookiepy.edge,  # type: ignore
            rookiepy.opera,  # type: ignore
            rookiepy.vivaldi,  # type: ignore
        ]

        if platform.system() == "Windows":
            browsers.extend(
                [
                    rookiepy.opera_gx,  # type: ignore
                    rookiepy.internet_explorer,  # type: ignore
                ]
            )
        elif platform.system() == "Darwin":
            browsers.extend(
                [
                    rookiepy.opera_gx,  # type: ignore
                    rookiepy.safari,  # type: ignore
                ]
            )

        cookies_dict = None
        cookies_jar = None
        for browser in browsers:
            try:
                cookies_dict = browser(["store.line.me"])
                cookies_jar = rookiepy.to_cookiejar(cookies_dict)  # type: ignore

                if GetLineAuth.validate_cookies(cookies_jar):
                    break

            except Exception:
                continue

        if cookies_dict is None or cookies_jar is None:
            return None

        cookies_list = ["%s=%s" % (i["name"], i["value"]) for i in cookies_dict]
        cookies = ";".join(cookies_list)

        return cookies

    @staticmethod
    def validate_cookies(cookies: Union[CookieJar, dict[str, str]]) -> bool:
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
        else:
            return True
