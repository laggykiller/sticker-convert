#!/usr/bin/env python3
import json
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, cast
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption, InputOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler


class DownloadViber(DownloadBase):
    # def __init__(self, *args: Any, **kwargs: Any) -> None:
    #     super().__init__(*args, **kwargs)

    def get_pack_info(self, url: str) -> Optional[Tuple[str, str, str, str]]:
        r = requests.get(url, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")

        is_custom = urlparse(url).path.startswith("/pages/custom-sticker-packs/")
        if is_custom:
            tag_text_search = "window.CUSTOM_STICKER_PACK"
        else:
            tag_text_search = "window.PRODUCT"

        script_tag = soup.find(
            lambda tag: tag.name == "script" and tag.text.startswith(tag_text_search)
        )
        if script_tag is None:
            return None

        pack_json = script_tag.text.replace(f"{tag_text_search} = ", "", 1)[:-1]
        pack_dict = json.loads(pack_json)

        title = pack_dict["title"]
        first_sticker_url = cast(str, pack_dict["stickerFirstItemUrl"])
        zip_url = "/".join(first_sticker_url.split("/")[:-1]) + ".zip"
        pack_id = pack_dict["id"].split(".")[-1]
        if is_custom:
            cover_url = (
                "https://custom-sticker-pack.cdn.viber.com/custom-stickers/{}/thumb.png"
            )
        else:
            cover_url = (
                "https://sm-content.viber.com/static/images/product/{}/sticker.png"
            )
        cover_url = cover_url.format(pack_dict["id"])

        return title, zip_url, cover_url, pack_id

    def decompress(
        self, zip_file: bytes, exts: Optional[Tuple[str, ...]] = None
    ) -> int:
        with zipfile.ZipFile(BytesIO(zip_file)) as zf:
            self.cb.put("Unzipping...")

            zf_files = zf.namelist()
            self.cb.put(
                (
                    "bar",
                    None,
                    {"set_progress_mode": "determinate", "steps": len(zf_files)},
                )
            )

            for sticker in zf_files:
                ext = Path(sticker).suffix
                if "frame" in sticker or ".db" in sticker or sticker.endswith("/"):
                    continue
                if exts is not None and ext not in exts:
                    continue
                num = sticker.split(".")[0][-2:].zfill(3)
                data = zf.read(sticker)

                self.cb.put(f"Read {sticker}")

                out_path = Path(self.out_dir, num + ext)
                with open(out_path, "wb") as f:
                    f.write(data)

                self.cb.put("update_bar")

            return len(zf_files)

    def download_stickers_viber(self) -> Tuple[int, int]:
        pack_info = self.get_pack_info(self.url)
        if pack_info is None:
            self.cb.put("Download failed: Cannot get pack info")
            return 0, 0
        title, zip_url, cover_url, pack_id = pack_info

        anim_url = f"https://content.cdn.viber.com/stickers/ASVG/{pack_id}.zip"
        anim_file = self.download_file(anim_url)
        zip_file = self.download_file(zip_url)
        if anim_file:
            count = self.decompress(anim_file, (".svg",))
            count += self.decompress(zip_file, (".mp3",))
        else:
            count = self.decompress(zip_file, (".mp3", ".png"))
        self.download_file(cover_url, self.out_dir / "cover.png")

        MetadataHandler.set_metadata(self.out_dir, title=title)

        return count, count

    @staticmethod
    def start(
        opt_input: InputOption,
        opt_cred: Optional[CredOption],
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int]:
        downloader = DownloadViber(opt_input, opt_cred, cb, cb_return)
        return downloader.download_stickers_viber()
