#!/usr/bin/env python3
import json
import re
import unicodedata
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption, InputOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.files.sanitize_filename import sanitize_filename
from sticker_convert.utils.translate import I


class DownloadMisskey(DownloadBase):
    @staticmethod
    def _slugify(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-zA-Z0-9_]+", "_", ascii_value).strip("_").lower()
        return slug

    def _find_archive(self) -> Tuple[bytes, str]:
        response = requests.get(self.url, allow_redirects=True)
        if not response.ok:
            self.cb.put(I("Download failed: Cannot download {}").format(self.url))
            return b"", ""

        final_url = response.url
        content_type = response.headers.get("content-type", "").lower()
        if (
            final_url.lower().endswith(".zip")
            or "application/zip" in content_type
            or response.content.startswith(b"PK\x03\x04")
        ):
            return response.content, final_url

        soup = BeautifulSoup(response.text, "html.parser")
        zip_link = None
        for link in soup.find_all("a", href=True):
            href = str(link["href"])
            if href.lower().endswith(".zip"):
                zip_link = urljoin(final_url, href)
                break

        if zip_link is None:
            self.cb.put(I("Download failed: Cannot find Misskey ZIP archive"))
            return b"", ""

        archive = self.download_file(zip_link, show_progress=False)
        return archive, zip_link

    def _get_unique_path(self, stem: str, suffix: str) -> Path:
        candidate = sanitize_filename(f"{stem}{suffix}")
        if candidate in ("", "__"):
            candidate = sanitize_filename(f"emoji{suffix}")

        out_path = self.out_dir / candidate
        counter = 2
        while out_path.exists():
            out_path = self.out_dir / sanitize_filename(f"{stem}_{counter}{suffix}")
            counter += 1

        return out_path

    def download_stickers_misskey(self) -> Tuple[int, int]:
        archive_bytes, archive_url = self._find_archive()
        if not archive_bytes:
            return 0, 0

        with zipfile.ZipFile(BytesIO(archive_bytes)) as zf:
            meta_path = next(
                (name for name in zf.namelist() if Path(name).name == "meta.json"),
                None,
            )
            if meta_path is None:
                self.cb.put(I("Download failed: meta.json is missing in archive"))
                return 0, 0

            meta = json.loads(zf.read(meta_path))
            emojis = meta.get("emojis", [])
            if not isinstance(emojis, list):
                self.cb.put(I("Download failed: Invalid Misskey meta.json"))
                return 0, 0

            self.cb.put(
                (
                    "bar",
                    None,
                    {"set_progress_mode": "determinate", "steps": len(emojis)},
                )
            )

            extracted = 0
            names_seen = set()
            for entry in emojis:
                if not entry.get("downloaded", True):
                    self.cb.put("update_bar")
                    continue

                file_name = entry.get("fileName")
                if not isinstance(file_name, str):
                    self.cb.put("update_bar")
                    continue

                try:
                    data = zf.read(file_name)
                except KeyError:
                    self.cb.put(I("Warning: {} is missing from archive").format(file_name))
                    self.cb.put("update_bar")
                    continue

                emoji_meta = entry.get("emoji", {})
                emoji_name = ""
                if isinstance(emoji_meta, dict):
                    emoji_name = str(emoji_meta.get("name", "")).strip()

                stem = self._slugify(emoji_name) or self._slugify(Path(file_name).stem)
                if not stem:
                    stem = f"emoji_{str(extracted + 1).zfill(3)}"
                if stem in names_seen:
                    stem = f"{stem}_{str(extracted + 1).zfill(3)}"
                names_seen.add(stem)

                out_path = self._get_unique_path(stem, Path(file_name).suffix.lower())
                with open(out_path, "wb+") as f:
                    f.write(data)

                self.cb.put(I("Downloaded {}").format(out_path.name))
                extracted += 1
                self.cb.put("update_bar")

        archive_title = Path(archive_url).stem.replace(".tar", "")
        if archive_title:
            archive_title = archive_title.replace("_", " ").replace("-", " ").strip()
        MetadataHandler.set_metadata(
            self.out_dir,
            title=archive_title or self.out_dir.name,
            author=str(meta.get("host", "")).strip(),
        )

        return extracted, extracted

    @staticmethod
    def start(
        opt_input: InputOption,
        opt_cred: Optional[CredOption],
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int]:
        downloader = DownloadMisskey(opt_input, opt_cred, cb, cb_return)
        return downloader.download_stickers_misskey()
