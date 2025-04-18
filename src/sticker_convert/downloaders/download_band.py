#!/usr/bin/env python3
from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import requests

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption, InputOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler


class DownloadBand(DownloadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def decompress(self, zip_file: bytes) -> int:
        with zipfile.ZipFile(BytesIO(zip_file)) as zf:
            self.cb.put("Unzipping...")

            zf_files = zf.namelist()
            animated = [i for i in zf_files if "animation/" in i]
            if len(animated) > 0:
                pack_files = animated
            else:
                pack_files = [
                    i
                    for i in zf_files
                    if i.endswith(".meta") is False and "_key" not in i
                ]

            self.cb.put(
                (
                    "bar",
                    None,
                    {"set_progress_mode": "determinate", "steps": len(pack_files)},
                )
            )

            for num, sticker in enumerate(pack_files):
                data = zf.read(sticker)
                self.cb.put(f"Read {sticker}")
                ext = sticker.split(".")[-1]

                out_path = Path(self.out_dir, str(num).zfill(3) + f".{ext}")
                with open(out_path, "wb") as f:
                    f.write(data)

                self.cb.put("update_bar")

        return len(pack_files)

    def get_metadata(self, pack_no: str) -> Optional[Dict[Any, Any]]:
        r = requests.get(
            f"https://sapi.band.us/v1.0.0/get_sticker_info?pack_no={pack_no}"
        )
        if r.text:
            return json.loads(r.text)
        else:
            return None

    def download_stickers_band(self) -> Tuple[int, int]:
        if urlparse(self.url).netloc != "www.band.us" and self.url.isnumeric() is False:
            self.cb.put("Download failed: Unsupported URL format")
            return 0, 0

        if self.url.isnumeric():
            pack_no = self.url
        else:
            pack_no = urlparse(self.url).path.split("/")[-1]
        metadata = self.get_metadata(pack_no)
        if metadata:
            self.title = metadata["result_data"]["sticker"]["name"]
        else:
            self.cb.put("Download failed: Failed to get metadata")
            return 0, 0

        MetadataHandler.set_metadata(self.out_dir, title=self.title)

        pack_url = f"http://s.cmstatic.net/band/sticker/v2/{pack_no}/shop/pack"
        zip_file = self.download_file(pack_url)

        if zip_file:
            self.cb.put(f"Downloaded {pack_url}")
        else:
            self.cb.put(f"Cannot download {pack_url}")
            return 0, 0

        pack_files_no = self.decompress(zip_file)

        cover_url = f"http://s.cmstatic.net/band/sticker/v2/{pack_no}/shop/main"
        self.download_file(cover_url, self.out_dir / "cover.png")

        return pack_files_no, pack_files_no

    @staticmethod
    def start(
        opt_input: InputOption,
        opt_cred: Optional[CredOption],
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int]:
        downloader = DownloadBand(opt_input, opt_cred, cb, cb_return)
        return downloader.download_stickers_band()
