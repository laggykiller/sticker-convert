#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import string
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import parse

import requests
from bs4 import BeautifulSoup
from PIL import Image

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption, InputOption
from sticker_convert.utils.auth.get_line_auth import GetLineAuth
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.media.apple_png_normalize import ApplePngNormalize

# Reference: https://github.com/doubleplusc/Line-sticker-downloader/blob/master/sticker_dl.py


class MetadataLine:
    @staticmethod
    def analyze_url(url: str) -> Optional[Tuple[str, str, bool]]:
        region = ""
        is_emoji = False
        if url.startswith("line://shop/detail/"):
            pack_id = url.replace("line://shop/detail/", "")
            if len(url) == 24 and all(c in string.hexdigits for c in url):
                is_emoji = True
        elif url.startswith("https://store.line.me/stickershop/product/"):
            pack_id = url.replace(
                "https://store.line.me/stickershop/product/", ""
            ).split("/")[0]
            region = url.replace(
                "https://store.line.me/stickershop/product/", ""
            ).split("/")[1]
        elif url.startswith("https://line.me/S/sticker"):
            url_parsed = parse.urlparse(url)
            pack_id = url.replace("https://line.me/S/sticker/", "").split("/")[0]
            region = parse.parse_qs(url_parsed.query)["lang"][0]
        elif url.startswith("https://store.line.me/officialaccount/event/sticker/"):
            pack_id = url.replace(
                "https://store.line.me/officialaccount/event/sticker/", ""
            ).split("/")[0]
            region = url.replace(
                "https://store.line.me/officialaccount/event/sticker/", ""
            ).split("/")[1]
        elif url.startswith("https://store.line.me/emojishop/product/"):
            pack_id = url.replace("https://store.line.me/emojishop/product/", "").split(
                "/"
            )[0]
            region = url.replace("https://store.line.me/emojishop/product/", "").split(
                "/"
            )[1]
            is_emoji = True
        elif url.startswith("https://line.me/S/emoji"):
            url_parsed = parse.urlparse(url)
            pack_id = parse.parse_qs(url_parsed.query)["id"][0]
            region = parse.parse_qs(url_parsed.query)["lang"][0]
            is_emoji = True
        elif len(url) == 24 and all(c in string.hexdigits for c in url):
            pack_id = url
            is_emoji = True
        elif url.isnumeric():
            pack_id = url
        else:
            return None

        return pack_id, region, is_emoji

    @staticmethod
    def get_metadata_sticon(
        pack_id: str, region: str
    ) -> Optional[Tuple[str, str, List[Dict[str, Any]], str, bool, bool]]:
        pack_meta_r = requests.get(
            f"https://stickershop.line-scdn.net/sticonshop/v1/{pack_id}/sticon/iphone/meta.json"
        )

        if pack_meta_r.status_code == 200:
            pack_meta = json.loads(pack_meta_r.text)
        else:
            return None

        if region == "":
            region = "en"

        pack_store_page = requests.get(
            f"https://store.line.me/emojishop/product/{pack_id}/{region}"
        )

        if pack_store_page.status_code != 200:
            return None

        pack_store_page_soup = BeautifulSoup(pack_store_page.text, "html.parser")

        title_tag = pack_store_page_soup.find(class_="mdCMN38Item01Txt")  # type: ignore
        if title_tag:
            title = title_tag.text
        else:
            return None

        author_tag = pack_store_page_soup.find(class_="mdCMN38Item01Author")  # type: ignore
        if author_tag:
            author = author_tag.text
        else:
            return None

        files = pack_meta["orders"]

        resource_type = pack_meta.get("sticonResourceType")
        has_animation = True if resource_type == "ANIMATION" else False
        has_sound = False

        return title, author, files, resource_type, has_animation, has_sound

    @staticmethod
    def get_metadata_stickers(
        pack_id: str, region: str
    ) -> Optional[Tuple[str, str, List[Dict[str, Any]], str, bool, bool]]:
        pack_meta_r = requests.get(
            f"https://stickershop.line-scdn.net/stickershop/v1/product/{pack_id}/android/productInfo.meta"
        )

        if pack_meta_r.status_code == 200:
            pack_meta = json.loads(pack_meta_r.text)
        else:
            return None

        if region == "":
            if "en" in pack_meta["title"]:
                # Prefer en release
                region = "en"
            else:
                # If no en release, use whatever comes first
                region = pack_meta["title"].keys()[0]

        if region == "zh-Hant":
            region = "zh_TW"

        title = pack_meta["title"].get("en")
        if title is None:
            title = pack_meta["title"][region]

        author = pack_meta["author"].get("en")
        if author is None:
            author = pack_meta["author"][region]

        files = pack_meta["stickers"]

        resource_type = pack_meta.get("stickerResourceType")
        has_animation = pack_meta.get("hasAnimation")
        has_sound = pack_meta.get("hasSound")

        return title, author, files, resource_type, has_animation, has_sound


class DownloadLine(DownloadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.headers = {
            "referer": "https://store.line.me",
            "user-agent": "Android",
            "x-requested-with": "XMLHttpRequest",
        }
        self.cookies = self.load_cookies()
        self.sticker_text_dict: Dict[int, Any] = {}

    def load_cookies(self) -> Dict[str, str]:
        cookies: Dict[str, str] = {}
        if self.opt_cred and self.opt_cred.line_cookies:
            line_cookies = self.opt_cred.line_cookies

            try:
                line_cookies_dict = json.loads(line_cookies)
                for c in line_cookies_dict:
                    cookies[c["name"]] = c["value"]
            except json.decoder.JSONDecodeError:
                try:
                    for i in line_cookies.split(";"):
                        c_key, c_value = i.split("=")
                        cookies[c_key] = c_value
                except ValueError:
                    self.cb.put(
                        'Warning: Line cookies invalid, you will not be able to add text to "Custom stickers"'
                    )

            if not GetLineAuth.validate_cookies(cookies):
                self.cb.put(
                    'Warning: Line cookies invalid, you will not be able to add text to "Custom stickers"'
                )
                cookies = {}

        return cookies

    def get_pack_url(self) -> str:
        # Reference: https://sora.vercel.app/line-sticker-download
        if self.is_emoji:
            if self.resource_type == "ANIMATION":
                pack_url = f"https://stickershop.line-scdn.net/sticonshop/v1/{self.pack_id}/sticon/iphone/package_animation.zip"
            else:
                pack_url = f"https://stickershop.line-scdn.net/sticonshop/v1/{self.pack_id}/sticon/iphone/package.zip"
        else:
            if (
                self.resource_type in ("ANIMATION", "ANIMATION_SOUND", "POPUP")
                or self.has_sound is True
                or self.has_animation is True
            ):
                pack_url = f"https://stickershop.line-scdn.net/stickershop/v1/product/{self.pack_id}/iphone/stickerpack@2x.zip"
            elif self.resource_type == "PER_STICKER_TEXT":
                pack_url = f"https://stickershop.line-scdn.net/stickershop/v1/product/{self.pack_id}/iphone/sticker_custom_plus_base@2x.zip"
            elif self.resource_type == "NAME_TEXT":
                pack_url = f"https://stickershop.line-scdn.net/stickershop/v1/product/{self.pack_id}/iphone/sticker_name_base@2x.zip"
            else:
                pack_url = f"https://stickershop.line-scdn.net/stickershop/v1/product/{self.pack_id}/iphone/stickers@2x.zip"

        return pack_url

    def decompress(
        self,
        zf: zipfile.ZipFile,
        f_path: str,
        num: int,
        prefix: str = "",
        suffix: str = "",
    ) -> None:
        data = zf.read(f_path)
        ext = Path(f_path).suffix
        if ext == ".png" and not self.is_emoji and int() < 775:
            data = ApplePngNormalize.normalize(data)
        self.cb.put(f"Read {f_path}")

        out_path = Path(self.out_dir, prefix + str(num).zfill(3) + suffix + ext)
        with open(out_path, "wb") as f:
            f.write(data)

    def decompress_emoticon(self, zip_file: bytes) -> None:
        with zipfile.ZipFile(BytesIO(zip_file)) as zf:
            self.cb.put("Unzipping...")

            self.cb.put(
                (
                    "bar",
                    None,
                    {"set_progress_mode": "determinate", "steps": len(self.pack_files)},
                )
            )

            for num, sticker in enumerate(self.pack_files):
                if self.has_animation is True:
                    f_path = str(sticker) + "_animation.png"
                else:
                    f_path = str(sticker) + ".png"
                self.decompress(zf, f_path, num)

                self.cb.put("update_bar")

    def decompress_stickers(self, zip_file: bytes) -> None:
        with zipfile.ZipFile(BytesIO(zip_file)) as zf:
            self.cb.put("Unzipping...")

            self.cb.put(
                (
                    "bar",
                    None,
                    {"set_progress_mode": "determinate", "steps": len(self.pack_files)},
                )
            )

            for num, sticker in enumerate(self.pack_files):
                if self.resource_type == "POPUP":
                    if sticker.get("popup", {}).get("layer") == "BACKGROUND":
                        f_path = str(sticker["id"]) + "@2x.png"
                        self.decompress(zf, f_path, num, "preview-")
                    f_path = "popup/" + str(sticker["id"]) + ".png"
                elif self.has_animation is True:
                    f_path = "animation@2x/" + str(sticker["id"]) + "@2x.png"
                else:
                    f_path = str(sticker["id"]) + "@2x.png"
                self.decompress(zf, f_path, num)

                if self.resource_type == "PER_STICKER_TEXT":
                    self.sticker_text_dict[num] = {
                        "sticker_id": sticker["id"],
                        "sticker_text": sticker["customPlus"]["defaultText"],
                    }

                elif self.resource_type == "NAME_TEXT":
                    self.sticker_text_dict[num] = {
                        "sticker_id": sticker["id"],
                        "sticker_text": "",
                    }

                if self.has_sound:
                    f_path = "sound/" + str(sticker["id"]) + ".m4a"
                    self.decompress(zf, f_path, num)

                self.cb.put("update_bar")

    def edit_custom_sticker_text(self) -> None:
        line_sticker_text_path = Path(self.out_dir, "line-sticker-text.txt")

        if not line_sticker_text_path.is_file():
            with open(line_sticker_text_path, "w+", encoding="utf-8") as f:
                json.dump(self.sticker_text_dict, f, indent=4, ensure_ascii=False)

            msg_block = (
                "The Line sticker pack you are downloading can have customized text.\n"
            )
            msg_block += "line-sticker-text.txt has been created in input directory.\n"
            msg_block += "Please edit line-sticker-text.txt, then continue."
            self.cb.put(("msg_block", (msg_block,), None))
            if self.cb_return:
                self.cb_return.get_response()

        with open(line_sticker_text_path, "r", encoding="utf-8") as f:
            self.sticker_text_dict = json.load(f)

    def get_custom_sticker_text_urls(self) -> List[Tuple[str, Path]]:
        custom_sticker_text_urls: List[Tuple[str, Path]] = []
        name_text_key_cache: Dict[str, str] = {}

        for num, data in self.sticker_text_dict.items():
            out_path = Path(self.out_dir, str(num).zfill(3))
            sticker_id = data["sticker_id"]
            sticker_text = data["sticker_text"]

            if self.resource_type == "PER_STICKER_TEXT":
                out_path_text = out_path.with_name(out_path.name + "-text.png")
                custom_sticker_text_urls.append(
                    (
                        f"https://store.line.me/overlay/sticker/{self.pack_id}/{sticker_id}/iPhone/sticker.png?text={parse.quote(sticker_text)}",
                        out_path_text,
                    )
                )

            elif self.resource_type == "NAME_TEXT" and sticker_text:
                out_path_text = out_path.with_name(out_path.name + "-text.png")
                name_text_key = name_text_key_cache.get(sticker_text, None)
                if not name_text_key:
                    name_text_key = self.get_name_text_key(sticker_text)
                if name_text_key:
                    name_text_key_cache[sticker_text] = name_text_key
                else:
                    continue

                custom_sticker_text_urls.append(
                    (
                        f"https://stickershop.line-scdn.net/stickershop/v1/sticker/{sticker_id}/iPhone/overlay/name/{name_text_key}/sticker@2x.png",
                        out_path_text,
                    )
                )

        return custom_sticker_text_urls

    def get_name_text_key(self, sticker_text: str) -> Optional[str]:
        params = {"text": sticker_text}

        response = requests.get(
            f"https://store.line.me/api/custom-sticker/preview/{self.pack_id}/{self.region}",
            params=params,
            cookies=self.cookies,
            headers=self.headers,
        )

        response_dict = json.loads(response.text)

        if response_dict["errorMessage"]:
            self.cb.put(
                f"Failed to generate customized text {sticker_text} due to: {response_dict['errorMessage']}"
            )
            return None

        name_text_key = (
            response_dict["productPayload"]["customOverlayUrl"]
            .split("name/")[-1]
            .split("/main.png")[0]
        )

        return name_text_key

    def combine_custom_text(self) -> None:
        for i in sorted(self.out_dir.iterdir()):
            if i.name.endswith("-text.png"):
                base_path = Path(self.out_dir, i.name.replace("-text.png", ".png"))
                text_path = Path(self.out_dir, i.name)

                with Image.open(base_path) as im:
                    base_img: Image.Image = im.convert("RGBA")

                with Image.open(text_path) as im:
                    text_img = im.convert("RGBA")

                with Image.alpha_composite(base_img, text_img) as im:
                    im.save(base_path)

                os.remove(text_path)

                self.cb.put(f"Combined {i.name.replace('-text.png', '.png')}")

    def download_stickers_line(self) -> Tuple[int, int]:
        url_data = MetadataLine.analyze_url(self.url)
        if url_data:
            self.pack_id, self.region, self.is_emoji = url_data
        else:
            self.cb.put("Download failed: Unsupported URL format")
            return 0, 0

        if self.is_emoji:
            metadata = MetadataLine.get_metadata_sticon(self.pack_id, self.region)
        else:
            metadata = MetadataLine.get_metadata_stickers(self.pack_id, self.region)

        if metadata:
            (
                self.title,
                self.author,
                self.pack_files,
                self.resource_type,
                self.has_animation,
                self.has_sound,
            ) = metadata
        else:
            self.cb.put("Download failed: Failed to get metadata")
            return 0, 0

        MetadataHandler.set_metadata(self.out_dir, title=self.title, author=self.author)

        pack_url = self.get_pack_url()
        zip_file = self.download_file(pack_url)

        if zip_file:
            self.cb.put(f"Downloaded {pack_url}")
        else:
            self.cb.put(f"Cannot download {pack_url}")
            return 0, 0

        if self.is_emoji:
            self.decompress_emoticon(zip_file)
        else:
            self.decompress_stickers(zip_file)

        custom_sticker_text_urls: List[Tuple[str, Path]] = []
        if self.sticker_text_dict and (
            self.resource_type == "PER_STICKER_TEXT"
            or (self.resource_type == "NAME_TEXT" and self.cookies)
        ):
            self.edit_custom_sticker_text()
            custom_sticker_text_urls = self.get_custom_sticker_text_urls()
        elif self.resource_type == "NAME_TEXT" and not self.cookies:
            self.cb.put('Warning: Line "Custom stickers" is supplied as input')
            self.cb.put(
                "However, adding custom message requires Line cookies, and it is not supplied"
            )
            self.cb.put("Continuing without adding custom text to stickers")

        self.download_multiple_files(custom_sticker_text_urls, headers=self.headers)
        self.combine_custom_text()

        return len(self.pack_files), len(self.pack_files)

    @staticmethod
    def start(
        opt_input: InputOption,
        opt_cred: Optional[CredOption],
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int]:
        downloader = DownloadLine(opt_input, opt_cred, cb, cb_return)
        return downloader.download_stickers_line()
