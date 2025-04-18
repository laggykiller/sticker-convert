#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption, InputOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.media.decrypt_kakao import DecryptKakao


class MetadataKakao:
    @staticmethod
    def share_link_to_public_link(share_link: str) -> str:
        # Share link redirect to preview link if use desktop headers
        headers_desktop = {"User-Agent": "Chrome"}
        r = requests.get(share_link, headers=headers_desktop, allow_redirects=True)
        return r.url

    @staticmethod
    def get_item_code_from_hash(hash: str, auth_token: str) -> Optional[str]:
        headers = {
            "Authorization": auth_token,
        }

        data = {"hashedItemCode": hash}

        response = requests.post(
            "https://talk-pilsner.kakao.com/emoticon/api/store/v3/item-code-by-hash",
            headers=headers,
            data=data,
        )

        if response.status_code != 200:
            return None

        response_json = json.loads(response.text)
        item_code = response_json["itemCode"]

        return item_code

    @staticmethod
    def get_item_code_from_search(
        pack_title: str, search_term: str, by_author: bool, auth_token: str
    ) -> str:
        headers = {
            "Authorization": auth_token,
        }

        data = {"query": search_term}

        response = requests.post(
            "https://talk-pilsner.kakao.com/emoticon/item_store/instant_search",
            headers=headers,
            data=data,
        )

        if response.status_code != 200:
            return "auth_error"

        def check_pack_match(pack_info: Dict[str, Any]) -> bool:
            share_link = pack_info["itemMetaInfo"]["shareData"]["linkUrl"]
            public_url = MetadataKakao.share_link_to_public_link(share_link)
            if pack_title == urlparse(public_url).path.split("/")[-1]:
                return True
            return False

        response_json = json.loads(response.text)
        for emoticon in response_json["emoticons"]:
            item_code = emoticon["item_code"]
            pack_info = MetadataKakao.get_pack_info_authed(item_code, auth_token)
            if pack_info is None:
                continue
            if check_pack_match(pack_info):
                return item_code
            if by_author:
                cid = pack_info["itemMetaInfo"]["itemMetaData"]["cid"]
                for item_code in MetadataKakao.get_items_by_creator(cid, auth_token):
                    pack_info = MetadataKakao.get_pack_info_authed(
                        item_code, auth_token
                    )
                    if pack_info is None:
                        continue
                    if check_pack_match(pack_info):
                        return item_code

        return "code_not_found"

    @staticmethod
    def get_items_by_creator(cid: str, auth_token: str) -> List[str]:
        headers = {"Authorization": auth_token}

        params = {
            "itemSort": "NEW",
            "offset": "0",
            "size": "30",
        }

        response = requests.get(
            f"https://talk-pilsner.kakao.com/emoticon/api/store/v3/creators/{cid}",
            headers=headers,
            params=params,
        )

        return [i["item_id"] for i in json.loads(response.text)["items"]]

    @staticmethod
    def get_pack_info_unauthed(
        pack_title: str,
    ) -> Optional[dict[str, Any]]:
        pack_meta_r = requests.get(f"https://e.kakao.com/api/v1/items/t/{pack_title}")

        if pack_meta_r.status_code == 200:
            pack_meta = json.loads(pack_meta_r.text)
        else:
            return None

        return pack_meta

    @staticmethod
    def get_pack_info_authed(
        item_code: str, auth_token: str
    ) -> Optional[dict[str, Any]]:
        headers = {
            "Authorization": auth_token,
            "Talk-Agent": "android/10.8.1",
            "Talk-Language": "en",
            "User-Agent": "okhttp/4.10.0",
        }

        response = requests.post(
            f"https://talk-pilsner.kakao.com/emoticon/api/store/v3/items/{item_code}",
            headers=headers,
        )

        if response.status_code != 200:
            return None

        response_json = json.loads(response.text)

        return response_json


class DownloadKakao(DownloadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.pack_title: Optional[str] = None
        self.author: Optional[str] = None
        self.auth_token: Optional[str] = None

        self.pack_info_unauthed: Optional[dict[str, Any]] = None
        self.pack_info_authed: Optional[dict[str, Any]] = None

    def download_stickers_kakao(self) -> Tuple[int, int]:
        self.auth_token = None
        if self.opt_cred:
            self.auth_token = self.opt_cred.kakao_auth_token

        if urlparse(self.url).netloc == "emoticon.kakao.com":
            item_code = None
            if self.auth_token is not None:
                hash = urlparse(self.url).path.split("/")[-1]
                item_code = MetadataKakao.get_item_code_from_hash(hash, self.auth_token)

            public_url = MetadataKakao.share_link_to_public_link(self.url)
            self.pack_title = urlparse(public_url).path.split("/")[-1]
            pack_info_unauthed = MetadataKakao.get_pack_info_unauthed(self.pack_title)
            if pack_info_unauthed is None:
                self.cb.put(
                    "Download failed: Cannot download metadata for sticker pack"
                )
                return 0, 0

            self.author = pack_info_unauthed["result"]["artist"]
            thumbnail_urls = pack_info_unauthed["result"]["thumbnailUrls"]

            if item_code is None:
                if self.auth_token is None:
                    self.cb.put(
                        "Warning: Downloading animated sticker requires auth_token"
                    )
                else:
                    self.cb.put(
                        "Warning: auth_token invalid, cannot download animated sticker"
                    )
                self.cb.put("Downloading static stickers...")
                return self.download_static(thumbnail_urls)
            else:
                return self.download_animated(item_code)

        if self.url.isnumeric():
            self.pack_title = None
            if self.auth_token:
                self.pack_info_authed = MetadataKakao.get_pack_info_authed(
                    self.url, self.auth_token
                )
                if self.pack_info_authed:
                    self.pack_title = self.pack_info_authed["itemUnitInfo"][0]["title"]
                else:
                    self.cb.put("Warning: Cannot get pack_title with auth_token.")
                    self.cb.put(
                        "Is auth_token invalid / expired? Try to regenerate it."
                    )
                    self.cb.put("Continuing without getting pack_title")

            return self.download_animated(self.url)

        if urlparse(self.url).netloc == "e.kakao.com":
            self.pack_title = urlparse(self.url).path.split("/")[-1]
            self.pack_info_unauthed = MetadataKakao.get_pack_info_unauthed(
                self.pack_title
            )

            if not self.pack_info_unauthed:
                self.cb.put(
                    "Download failed: Cannot download metadata for sticker pack"
                )
                return 0, 0

            self.author = self.pack_info_unauthed["result"]["artist"]
            title_ko = self.pack_info_unauthed["result"]["title"]
            thumbnail_urls = self.pack_info_unauthed["result"]["thumbnailUrls"]

            if self.auth_token:
                item_code = MetadataKakao.get_item_code_from_search(
                    self.pack_title, title_ko, False, self.auth_token
                )
                if item_code == "auth_error":
                    msg = "Warning: Cannot get item code.\n"
                    msg += "Is auth_token invalid / expired? Try to regenerate it.\n"
                    msg += "Continue to download static stickers instead?"
                elif item_code == "code_not_found":
                    self.cb.put(
                        "Cannot get item code, trying to search by author name, this may take long time..."
                    )
                    self.cb.put(
                        "Hint: Use share link instead to download more reliably"
                    )
                    if self.author is not None:
                        item_code = MetadataKakao.get_item_code_from_search(
                            self.pack_title, self.author, True, self.auth_token
                        )
                    if item_code == "code_not_found":
                        msg = "Warning: Cannot get item code.\n"
                        msg += "Please use share link instead.\n"
                        msg += "Continue to download static stickers instead?"
                    else:
                        return self.download_animated(item_code)
                else:
                    return self.download_animated(item_code)

                self.cb.put(("ask_bool", (msg,), None))
                if self.cb_return:
                    response = self.cb_return.get_response()
                else:
                    response = False

                if response is False:
                    return 0, 0

            return self.download_static(thumbnail_urls)

        self.cb.put("Download failed: Unrecognized URL")
        return 0, 0

    def download_static(self, thumbnail_urls: str) -> Tuple[int, int]:
        headers = {"User-Agent": "Android"}
        MetadataHandler.set_metadata(
            self.out_dir, title=self.pack_title, author=self.author
        )

        targets: List[Tuple[str, Path]] = []

        for num, url in enumerate(thumbnail_urls):
            dest = Path(self.out_dir, str(num).zfill(3) + ".png")
            targets.append((url, dest))

        results = self.download_multiple_files(targets, headers=headers)

        return sum(results.values()), len(targets)

    def download_animated(self, item_code: str) -> Tuple[int, int]:
        MetadataHandler.set_metadata(
            self.out_dir, title=self.pack_title, author=self.author
        )

        play_exts = [".webp", ".gif", ".png", ""]
        play_types = ["emot", "emoji", ""]  # emot = normal; emoji = mini
        play_path_format = None
        sound_exts = [".mp3", ""]
        sound_path_format = None
        stickers_count = 32  # https://emoticonstudio.kakao.com/pages/start

        headers = {"User-Agent": "Android"}

        if not self.pack_info_authed and self.auth_token:
            self.pack_info_authed = MetadataKakao.get_pack_info_authed(
                item_code, self.auth_token
            )
        if self.pack_info_authed:
            preview_data = self.pack_info_authed["itemUnitInfo"][0]["previewData"]
            play_path_format = preview_data["playPathFormat"]
            sound_path_format = preview_data["soundPathFormat"]
            stickers_count = preview_data["num"]
        else:
            if not self.pack_info_unauthed:
                public_url = None
                if urlparse(self.url).netloc == "emoticon.kakao.com":
                    public_url = MetadataKakao.share_link_to_public_link(self.url)
                elif urlparse(self.url).netloc == "e.kakao.com":
                    public_url = self.url
                if public_url:
                    pack_title = urlparse(public_url).path.split("/")[-1]
                    self.pack_info_unauthed = MetadataKakao.get_pack_info_unauthed(
                        pack_title
                    )

            if self.pack_info_unauthed:
                stickers_count = len(self.pack_info_unauthed["result"]["thumbnailUrls"])

        play_type = ""
        play_ext = ""
        if play_path_format is None:
            for play_type, play_ext in itertools.product(play_types, play_exts):
                r = requests.get(
                    f"https://item.kakaocdn.net/dw/{item_code}.{play_type}_001{play_ext}",
                    headers=headers,
                )
                if r.ok:
                    break
            if play_ext == "":
                self.cb.put(f"Failed to determine extension of {item_code}")
                return 0, 0
            else:
                play_path_format = f"dw/{item_code}.{play_type}_0##{play_ext}"
        else:
            play_ext = "." + play_path_format.split(".")[-1]

        sound_ext = ""
        if sound_path_format is None:
            for sound_ext in sound_exts:
                r = requests.get(
                    f"https://item.kakaocdn.net/dw/{item_code}.sound_001{sound_ext}",
                    headers=headers,
                )
                if r.ok:
                    break
            if sound_ext != "":
                sound_path_format = f"dw/{item_code}.sound_0##{sound_ext}"
        elif sound_path_format != "":
            sound_ext = "." + sound_path_format.split(".")[-1]

        assert play_path_format
        targets: list[tuple[str, Path]] = []
        for num in range(1, stickers_count + 1):
            play_url = "https://item.kakaocdn.net/" + play_path_format.replace(
                "##", str(num).zfill(2)
            )
            play_dl_path = Path(self.out_dir, str(num).zfill(3) + play_ext)
            targets.append((play_url, play_dl_path))

            if sound_path_format:
                sound_url = "https://item.kakaocdn.net/" + sound_path_format.replace(
                    "##", str(num).zfill(2)
                )
                sound_dl_path = Path(self.out_dir, str(num).zfill(3) + sound_ext)
                targets.append((sound_url, sound_dl_path))

        results = self.download_multiple_files(targets, headers=headers)

        for target in targets:
            f_path = target[1]
            ext = Path(f_path).suffix

            if ext not in (".gif", ".webp"):
                continue

            with open(f_path, "rb") as f:
                data = f.read()
            data = DecryptKakao.xor_data(data)
            self.cb.put(f"Decrypted {f_path}")
            with open(f_path, "wb+") as f:
                f.write(data)

        self.cb.put(f"Finished getting {item_code}")

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
