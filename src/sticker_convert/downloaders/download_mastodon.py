#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption, InputOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.files.sanitize_filename import sanitize_filename
from sticker_convert.utils.translate import I


class DownloadMastodon(DownloadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_metadata(self, domain: str) -> Optional[Dict[Any, Any]]:
        r = requests.get(f"{domain}/api/v1/custom_emojis")
        if r.text:
            return json.loads(r.text)
        else:
            return None

    def download_stickers_mastodon(self) -> Tuple[int, int]:
        parsed = urlparse(self.url)
        if parsed.scheme:
            domain = parsed.scheme + "://" + parsed.netloc
        else:
            domain = "https://" + parsed.netloc

        metadata = self.get_metadata(domain)
        if metadata is None:
            self.cb.put(I("Download failed: Failed to get metadata"))
            return 0, 0

        self.title = parsed.netloc
        self.author = parsed.netloc
        MetadataHandler.set_metadata(self.out_dir, title=self.title, author=self.author)

        targets: List[Tuple[str, Path]] = []
        for info in metadata:
            category = info.get("category", "").replace("-", "_")
            name = sanitize_filename(info.get("shortcode", "").replace("-", "_"))
            if category != "":
                fname = sanitize_filename(category).replace(".", "_") + "-" + name
            else:
                fname = name
            fmt = info["url"].split(".")[-1]
            dest = Path(self.out_dir, f"{fname}.{fmt}")
            targets.append((info["url"], dest))

        results = self.download_multiple_files(targets)

        return sum(results.values()), len(targets)

    @staticmethod
    def start(
        opt_input: InputOption,
        opt_cred: Optional[CredOption],
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int]:
        downloader = DownloadMastodon(opt_input, opt_cred, cb, cb_return)
        return downloader.download_stickers_mastodon()
