#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from queue import Queue
from typing import Optional, Union, Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption
from sticker_convert.utils.callback import Callback, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.media.decrypt_kakao import DecryptKakao


class MetadataKakao:
    @staticmethod
    def get_info_from_share_link(url: str) -> tuple[Optional[str], Optional[str]]:
        headers = {"User-Agent": "Android"}

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        pack_title_tag = soup.find("title")  # type: ignore
        if not pack_title_tag:
            return None, None

        pack_title: str = pack_title_tag.string  # type: ignore

        app_scheme_link_tag = soup.find("a", id="app_scheme_link")  # type: ignore
        assert isinstance(app_scheme_link_tag, Tag)

        data_urls = app_scheme_link_tag.get("data-url")
        if not data_urls:
            return None, None
        elif isinstance(data_urls, list):
            data_url = data_urls[0]
        else:
            data_url = data_urls

        item_code = data_url.replace("kakaotalk://store/emoticon/", "").split("?")[0]

        return pack_title, item_code

    @staticmethod
    def get_info_from_pack_title(
        pack_title: str,
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        pack_meta_r = requests.get(f"https://e.kakao.com/api/v1/items/t/{pack_title}")

        if pack_meta_r.status_code == 200:
            pack_meta = json.loads(pack_meta_r.text)
        else:
            return None, None, None

        author = pack_meta["result"]["artist"]
        title_ko = pack_meta["result"]["title"]
        thumbnail_urls = pack_meta["result"]["thumbnailUrls"]

        return author, title_ko, thumbnail_urls

    @staticmethod
    def get_item_code(title_ko: str, auth_token: str) -> Optional[str]:
        headers = {
            "Authorization": auth_token,
        }

        data = {"query": title_ko}

        response = requests.post(
            "https://talk-pilsner.kakao.com/emoticon/item_store/instant_search",
            headers=headers,
            data=data,
        )

        if response.status_code != 200:
            return None

        response_json = json.loads(response.text)
        item_code = response_json["emoticons"][0]["item_code"]

        return item_code

    @staticmethod
    def get_title_from_id(item_code: str, auth_token: str) -> Optional[str]:
        headers = {
            "Authorization": auth_token,
        }

        response = requests.post(
            f"https://talk-pilsner.kakao.com/emoticon/api/store/v3/items/{item_code}",
            headers=headers,
        )

        if response.status_code != 200:
            return None

        response_json = json.loads(response.text)
        title = response_json["itemUnitInfo"][0]["title"]
        # play_path_format = response_json['itemUnitInfo'][0]['playPathFormat']
        # stickers_count = len(response_json['itemUnitInfo'][0]['sizes'])

        return title


class DownloadKakao(DownloadBase):
    def __init__(self, *args: Any, **kwargs: Any):
        super(DownloadKakao, self).__init__(*args, **kwargs)
        self.pack_title = None
        self.author = None

    def download_stickers_kakao(self) -> bool:
        auth_token = None
        if self.opt_cred:
            auth_token = self.opt_cred.kakao_auth_token

        if urlparse(self.url).netloc == "emoticon.kakao.com":
            self.pack_title, item_code = MetadataKakao.get_info_from_share_link(
                self.url
            )

            if item_code:
                return self.download_animated(item_code)
            else:
                self.cb.put(
                    "Download failed: Cannot download metadata for sticker pack"
                )
                return False

        elif self.url.isnumeric() or self.url.startswith("kakaotalk://store/emoticon/"):
            item_code = self.url.replace("kakaotalk://store/emoticon/", "")

            self.pack_title = None
            if auth_token:
                self.pack_title = MetadataKakao.get_title_from_id(item_code, auth_token)
                if not self.pack_title:
                    self.cb.put("Warning: Cannot get pack_title with auth_token.")
                    self.cb.put(
                        "Is auth_token invalid / expired? Try to regenerate it."
                    )
                    self.cb.put("Continuing without getting pack_title")

            return self.download_animated(item_code)

        elif urlparse(self.url).netloc == "e.kakao.com":
            self.pack_title = self.url.replace("https://e.kakao.com/t/", "")
            (
                self.author,
                title_ko,
                thumbnail_urls,
            ) = MetadataKakao.get_info_from_pack_title(self.pack_title)

            assert self.author
            assert title_ko
            assert thumbnail_urls

            if not thumbnail_urls:
                self.cb.put(
                    "Download failed: Cannot download metadata for sticker pack"
                )
                return False

            if auth_token:
                item_code = MetadataKakao.get_item_code(title_ko, auth_token)
                if item_code:
                    return self.download_animated(item_code)
                else:
                    msg = "Warning: Cannot get item code.\n"
                    msg += "Is auth_token invalid / expired? Try to regenerate it.\n"
                    msg += "Continue to download static stickers instead?"
                    self.cb.put(("msg_block", (msg,), None))
                    if self.cb_return:
                        response = self.cb_return.get_response()
                    else:
                        response = False

                    if response is False:
                        return False

            return self.download_static(thumbnail_urls)

        else:
            self.cb.put("Download failed: Unrecognized URL")
            return False

    def download_static(self, thumbnail_urls: str) -> bool:
        MetadataHandler.set_metadata(
            self.out_dir, title=self.pack_title, author=self.author
        )

        targets: list[tuple[str, Path]] = []

        for num, url in enumerate(thumbnail_urls):
            dest = Path(self.out_dir, str(num).zfill(3) + ".png")
            targets.append((url, dest))

        self.download_multiple_files(targets)

        return True

    def download_animated(self, item_code: str) -> bool:
        MetadataHandler.set_metadata(
            self.out_dir, title=self.pack_title, author=self.author
        )

        pack_url = f"http://item.kakaocdn.net/dw/{item_code}.file_pack.zip"

        zip_file = self.download_file(pack_url)
        if zip_file:
            self.cb.put(f"Downloaded {pack_url}")
        else:
            self.cb.put(f"Cannot download {pack_url}")
            return False

        with zipfile.ZipFile(io.BytesIO(zip_file)) as zf:
            self.cb.put("Unzipping...")
            self.cb.put(
                (
                    "bar",
                    None,
                    {"set_progress_mode": "determinate", "steps": len(zf.namelist())},
                )
            )

            for num, f_path in enumerate(sorted(zf.namelist())):
                ext = Path(f_path).suffix

                if ext in (".gif", ".webp"):
                    data = DecryptKakao.xor_data(zf.read(f_path))
                    self.cb.put(f"Decrypted {f_path}")
                else:
                    data = zf.read(f_path)
                    self.cb.put(f"Read {f_path}")

                out_path = Path(self.out_dir, str(num).zfill(3) + ext)
                with open(out_path, "wb") as f:
                    f.write(data)

                self.cb.put("update_bar")

        self.cb.put(f"Finished getting {pack_url}")

        return True

    @staticmethod
    def start(
        url: str,
        out_dir: Path,
        opt_cred: Optional[CredOption],
        cb: Union[
            Queue[
                Union[
                    tuple[str, Optional[tuple[str]], Optional[dict[str, str]]],
                    str,
                    None,
                ]
            ],
            Callback,
        ],
        cb_return: CallbackReturn,
    ) -> bool:
        downloader = DownloadKakao(url, out_dir, opt_cred, cb, cb_return)
        return downloader.download_stickers_kakao()
