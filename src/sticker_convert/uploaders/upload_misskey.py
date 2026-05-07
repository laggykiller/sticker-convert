#!/usr/bin/env python3
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.uploaders.upload_base import UploadBase
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.translate import I


class UploadMisskey(UploadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def generate_meta_json(
        self, emojis: List[Path], host: Optional[str]
    ) -> Dict[str, Any]:
        meta_json: Dict[str, Any] = {
            "metaVersion": 2,
            "host": "example.misskey.domain" if host is None else host,
            "exportedAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "emojis": [],
        }

        for i in emojis:
            emoji: Dict[str, Any]
            if "-" in i.name:
                emoji = {
                    "name": i.stem.split("-", 1)[-1],
                    "category": i.stem.split("-", 1)[0],
                    "aliases": [],
                }
            else:
                emoji = {
                    "name": i.stem,
                    "aliases": [],
                }
            meta_json["emojis"].append(
                {
                    "downloaded": True,
                    "fileName": i.name,
                    "emoji": emoji,
                }
            )

        return meta_json

    def upload_misskey(self) -> Tuple[int, int, List[str]]:
        emojis = MetadataHandler.get_stickers_present(self.opt_output.dir)
        self.title, _, _ = MetadataHandler.get_metadata(
            self.opt_output.dir,
            title=self.opt_output.title,
            author=self.opt_output.author,
        )

        meta_json: Dict[str, Any]
        meta_json_path = Path(self.opt_output.dir, "misskey_meta.json")
        if meta_json_path.exists():
            with open(meta_json_path, encoding="utf-8") as f:
                meta_json = json.load(f)
        else:
            meta_json = self.generate_meta_json(emojis, self.title)

        zipf_name = self.title.replace(".", "_") if self.title else "result"
        zipf_path = Path(self.opt_output.dir, f"{zipf_name}.zip")
        with zipfile.ZipFile(zipf_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for emoji in emojis:
                zipf.write(emoji, emoji.name)
            zipf.writestr(
                "meta.json", json.dumps(meta_json, ensure_ascii=False, indent=4)
            )

        if self.opt_cred.misskey_token == "":
            self.cb.put(I("Note: misskey_token required for uploading to Misskey"))
            return len(emojis), len(emojis), [str(zipf_path)]
        if self.opt_cred.misskey_url == "":
            self.cb.put(I("Note: misskey_url required for uploading to Misskey"))
            return len(emojis), len(emojis), [str(zipf_path)]

        scheme = urlparse(self.opt_cred.misskey_url).scheme
        scheme = scheme if scheme != "" else "https"
        netloc = urlparse(self.opt_cred.misskey_url).netloc
        domain = f"{scheme}://{netloc}"

        # Try bulk upload first
        response = requests.post(
            f"{domain}/api/drive/files/create",
            headers={"Referer": f"{domain}/admin/emojis"},
            data={
                "i": self.opt_cred.misskey_token,
                "force": "true",
                "name": zipf_name,
                "isSensitive": "false",
            },
            files={
                "file": (
                    zipf_name,
                    open(zipf_path, "rb"),
                    "application/x-zip-compressed",
                )
            },
        )

        try:
            zip_id = json.loads(response.text).get("id")
        except json.JSONDecodeError:
            self.cb.put(
                I("Failed to bulk upload to misskey: {}").format(str(response.text))
            )
            return 0, len(emojis), [str(zipf_path)]

        response = requests.post(
            f"{domain}/api/admin/emoji/import-zip",
            headers={"Referer": f"{domain}/admin/emojis"},
            json={
                "fileId": zip_id,
                "i": self.opt_cred.misskey_token,
            },
        )

        if response.ok:
            return len(emojis), len(emojis), [str(zipf_path)]
        else:
            self.cb.put(I("Failed to bulk upload to misskey: {}").format(response.text))

        # Upload one-by-one
        success = 0
        for emoji in emojis:
            self.cb.put("update_bar")
            if emoji.name.count("-") == 1:
                name = emoji.name.split("-", 1)[-1].split(".")[0]
                category = emoji.name.split("-", 1)[0]
            else:
                name = emoji.name.replace("-", "_").split(".")[0]
                category = None

            if emoji.suffix == ".gif":
                content_type = "image/gif"
            elif emoji.suffix == ".png":
                content_type = "image/png"
            else:
                self.cb.put(
                    I("Failed to upload {} to Misskey as not png or gif").format(
                        emoji.name
                    )
                )
                continue

            response = requests.post(
                f"{domain}/api/drive/files/create",
                headers={"Referer": f"{domain}/admin/emojis"},
                data={
                    "i": self.opt_cred.misskey_token,
                    "force": "true",
                    "name": emoji.name,
                    "isSensitive": "false",
                },
                files={
                    "file": (
                        emoji.name,
                        open(emoji, "rb"),
                        content_type,
                    )
                },
            )

            try:
                file_id = json.loads(response.text).get("id")
            except json.JSONDecodeError:
                self.cb.put(
                    I("Failed to upload {} to misskey: {}").format(
                        emoji.name, str(response.text)
                    )
                )
                continue

            emoji_meta = next(
                i
                for i in meta_json.get("emojis", [])
                if i.get("fileName") == emoji.name
            )
            response = requests.post(
                f"{domain}/api/admin/emoji/add",
                headers={"Referer": f"{domain}/admin/emojis"},
                json={
                    "aliases": emoji_meta.get("emoji", {}).get("aliases", []),
                    "category": emoji_meta.get("emoji", {}).get("category", category),
                    "fileId": file_id,
                    "i": self.opt_cred.misskey_token,
                    "isSensitive": False,
                    "license": None,
                    "localOnly": False,
                    "name": emoji_meta.get("emoji", {}).get("name", name),
                    "roleIdsThatCanBeUsedThisEmojiAsReaction": [],
                },
            )

            if response.ok:
                self.cb.put(I("Uploaded {}").format(emoji.name))
                success += 1
            else:
                self.cb.put(
                    I("Failed to upload {} to misskey: {} {}").format(
                        emoji.name, str(response.status_code), response.text
                    )
                )

        return success, len(emojis), [str(zipf_path)]

    @staticmethod
    def start(
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int, List[str]]:
        exporter = UploadMisskey(opt_output, opt_comp, opt_cred, cb, cb_return)
        return exporter.upload_misskey()
