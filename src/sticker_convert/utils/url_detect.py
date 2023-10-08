#!/usr/bin/env python3
import string
from urllib.parse import urlparse
from typing import Optional


class UrlDetect:
    @staticmethod
    def detect(url: str) -> Optional[str]:
        domain = urlparse(url).netloc

        if domain == "signal.art":
            return "signal"

        elif domain in ("telegram.me", "t.me"):
            return "telegram"

        elif (
            domain in ("store.line.me", "line.me")
            or url.startswith("line://shop/detail/")
            or (len(url) == 24 and all(c in string.hexdigits for c in url))
        ):
            return "line"

        elif domain in ("e.kakao.com", "emoticon.kakao.com") or url.startswith(
            "kakaotalk://store/emoticon/"
        ):
            return "kakao"

        else:
            return None
