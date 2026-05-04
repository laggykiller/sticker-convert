#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption, InputOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.media.format_detect import format_detect
from sticker_convert.utils.translate import I


class MetadataKakao:
    @staticmethod
    def get_pack_info(
        pack_title: str,
    ) -> Optional[dict[str, Any]]:
        pack_meta_r = requests.get(f"https://e.kakao.com/api/items/{pack_title}")

        if pack_meta_r.status_code == 200:
            pack_meta = json.loads(pack_meta_r.text)
        else:
            return None

        return pack_meta


class DownloadKakao(DownloadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.MSG_CODE_NOT_FOUND = I(
            "Warning: Cannot get item code.\n"
            "Please use share link instead.\n"
            "Continue to download static stickers instead?"
        )

        super().__init__(*args, **kwargs)
        self.pack_title: Optional[str] = None
        self.author: Optional[str] = None

        self.pack_info: Optional[dict[str, Any]] = None

    def download_stickers_kakao(self) -> Tuple[int, int]:
        if urlparse(self.url).netloc == "emoticon.kakao.com":
            # Redirect to e.kakao.com
            self.url = requests.get(self.url).url

        if urlparse(self.url).netloc != "e.kakao.com":
            self.cb.put(I("Download failed: Unrecognized URL"))
            return 0, 0

        self.pack_title = urlparse(self.url).path.split("/")[-1]
        self.pack_info = MetadataKakao.get_pack_info(self.pack_title)

        if not self.pack_info:
            self.cb.put(I("Download failed: Cannot download metadata for sticker pack"))
            return 0, 0

        self.author = self.pack_info["creator"]["name"]
        self.pack_title = self.pack_info["hero"]["title"]
        MetadataHandler.set_metadata(
            self.out_dir, title=self.pack_title, author=self.author
        )

        targets: List[Tuple[str, Path]] = []
        targets.append(
            (self.pack_info["hero"]["imageUrl"], Path(self.out_dir, "cover"))
        )

        for num, info in enumerate(self.pack_info["contents"]["items"]):
            dest = Path(self.out_dir, str(num).zfill(3) + ".unknown_ext")
            targets.append((info["animatedUrl"], dest))

            if info.get("soundUrl"):
                dest = Path(self.out_dir, str(num).zfill(3) + ".mp3")
                targets.append((info["soundUrl"], dest))

        results = self.download_multiple_files(
            targets,
            headers={"User-Agent": "Mozilla/5.0"},
            semaphore_cnt=2,
        )

        ext: Optional[str] = None
        for i in self.out_dir.iterdir():
            if i.suffix == ".unknown_ext":
                ext = format_detect(i, [".webp", ".gif", ".png"])
                i.rename(i.with_suffix(ext))

        return sum(results.values()), len(targets)

    @staticmethod
    def start(
        opt_input: InputOption,
        opt_cred: Optional[CredOption],
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int]:
        downloader = DownloadKakao(opt_input, opt_cred, cb, cb_return)
        return downloader.download_stickers_kakao()
