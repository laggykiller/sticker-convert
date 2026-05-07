#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast
from urllib.parse import urlparse

import requests

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption, InputOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.files.sanitize_filename import sanitize_filename
from sticker_convert.utils.media.format_detect import format_detect
from sticker_convert.utils.translate import I


class DownloadMisskey(DownloadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_metadata(self, domain: str) -> Optional[Dict[Any, Any]]:
        r = requests.get(f"{domain}/api/emojis")
        if r.text:
            metadata = json.loads(r.text)
        else:
            return None

        return metadata

    def download_stickers_misskey(self) -> Tuple[int, int]:
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
        for info in metadata["emojis"]:
            info: Dict[str, Any]
            category = cast(str, info.get("category", "")).replace("-", "_")
            name = sanitize_filename(cast(str, info.get("name", "")).replace("-", "_"))
            if category != "":
                fname = sanitize_filename(category).replace(".", "_") + "-" + name
            else:
                fname = name
            info["fileName"] = fname
            dest = Path(self.out_dir, f"{fname}.unknown_ext")
            targets.append((info["url"], dest))

        results = self.download_multiple_files(targets)

        ext: Optional[str] = None
        emojis_new: List[Dict[str, Any]] = []
        for info in metadata["emojis"]:
            info: Dict[str, Any]
            fpath = Path(self.out_dir, info["fileName"])
            if fpath.suffix == ".unknown_ext":
                ext = format_detect(fpath, [".png", ".gif"])
                fpath.rename(fpath.with_suffix(ext))

            del info["url"]
            emojis_new.append(
                {
                    "downloaded": True,
                    "fileName": fpath.name,
                    "emoji": info,
                }
            )

        metadata["metaVersion"] = 2
        metadata["host"] = urlparse(domain).netloc
        metadata["exportedAt"] = (
            datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        )
        metadata["emojis"] = emojis_new
        with open(Path(self.out_dir, "misskey_meta.json"), "w+", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)

        return sum(results.values()), len(targets)

    @staticmethod
    def start(
        opt_input: InputOption,
        opt_cred: Optional[CredOption],
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int]:
        downloader = DownloadMisskey(opt_input, opt_cred, cb, cb_return)
        return downloader.download_stickers_misskey()
