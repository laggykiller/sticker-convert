#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Tuple
from urllib import parse

import requests
from bs4 import BeautifulSoup

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption, InputOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler

# Reference: https://github.com/star-39/moe-sticker-bot/issues/49


class DownloadOgq(DownloadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def download_stickers_ogq(self) -> Tuple[int, int]:
        url_parse = parse.urlparse(self.url)
        if (
            url_parse.netloc != "ogqmarket.naver.com"
            or url_parse.path.startswith("/artworks/sticker/detail") is False
        ):
            self.cb.put(f"Invalid url: {self.url}")
        artwork_id = {
            i.split("=")[0]: i.split("=")[1] for i in url_parse.query.split("&")
        }["artworkId"]

        html = requests.get(self.url, headers=self.headers).text
        soup = BeautifulSoup(html, "html.parser")

        author_tag = soup.select_one("div.info div.nickname span")  # type: ignore
        author = author_tag.text.strip() if author_tag else "OGQ"
        title_tag = soup.select_one("div.header div div.title p")  # type: ignore
        title = title_tag.text.strip() if title_tag else artwork_id

        seen: List[str] = []
        imgs: List[str] = []
        targets: List[Tuple[str, Path]] = []
        n = 0
        for img in soup.find_all("img", alt="sticker-detail-image-prevew"):
            src = img.get("src")
            if not src:
                continue
            src = src.split("?")[0]
            if src in seen:
                continue
            seen.append(src)
            imgs.append(src)
            sticker_url = f"{src}?type=ma480_480"
            sticker_url_parse = parse.urlparse(sticker_url)
            ext = sticker_url_parse.path.split(".")[-1]
            if sticker_url_parse.path.split("/")[-1].startswith("original_"):
                path = self.out_dir / f"{n}.{ext}"
            else:
                path = self.out_dir / f"cover.{ext}"
            targets.append((sticker_url, path))
            n += 1

        results = self.download_multiple_files(targets)
        MetadataHandler.set_metadata(self.out_dir, title=title, author=author)

        return len(results.values()), len(targets)

    @staticmethod
    def start(
        opt_input: InputOption,
        opt_cred: Optional[CredOption],
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int]:
        downloader = DownloadOgq(opt_input, opt_cred, cb, cb_return)
        return downloader.download_stickers_ogq()
