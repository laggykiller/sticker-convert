#!/usr/bin/env python3
import string
from typing import Optional
from urllib.parse import urlparse


class UrlDetect:
    @staticmethod
    def detect(url: str) -> Optional[str]:
        domain = urlparse(url).netloc

        if domain == "signal.art" or url.startswith("sgnl://addstickers/"):
            return "signal"

        if domain in ("telegram.me", "t.me"):
            return "telegram"

        if (
            domain in ("store.line.me", "line.me")
            or url.startswith("line://shop/detail/")
            or (len(url) == 24 and all(c in string.hexdigits for c in url))
        ):
            return "line"

        if domain in ("e.kakao.com", "emoticon.kakao.com"):
            return "kakao"

        if domain == "www.band.us":
            return "band"

        if domain == "stickers.viber.com":
            return "viber"

        if domain == "discord.com":
            return "discord"

        return None
