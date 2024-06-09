#!/usr/bin/env python3
import copy
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, List

import requests

from sticker_convert.converter import StickerConvert
from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.uploaders.upload_base import UploadBase
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.cache_store import CacheStore
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.files.sanitize_filename import sanitize_filename
from sticker_convert.utils.media.format_verify import FormatVerify


class UploadViber(UploadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.base_spec.set_size_max(0)
        self.base_spec.square = True

        self.png_spec = copy.deepcopy(self.base_spec)
        self.png_spec.set_res_max(490)
        self.png_spec.set_format((".png",))

        self.png_cover_spec = copy.deepcopy(self.base_spec)
        self.png_cover_spec.set_res_max(120)
        self.png_spec.set_format((".png",))

        self.opt_comp_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_merged.merge(self.png_spec)

    def upload_stickers_viber(self) -> List[str]:
        urls: List[str] = []

        if not self.opt_cred.viber_auth:
            self.cb.put("Viber auth required for uploading to viber")
            return urls

        upload_data_base: Dict[str, str] = {}
        for i in self.opt_cred.viber_auth.split(";"):
            j = i.split(":")
            upload_data_base[j[0]] = j[1]

        if upload_data_base.get("member_id") is None:
            self.cb.put("Invalid Viber auth: Missing member_id")
            return urls
        if upload_data_base.get("m_token") is None:
            self.cb.put("Invalid Viber auth: Missing m_token")
            return urls
        if upload_data_base.get("m_ts") is None:
            self.cb.put("Invalid Viber auth: Missing m_ts")
            return urls

        title, author, _ = MetadataHandler.get_metadata(
            self.opt_output.dir,
            title=self.opt_output.title,
            author=self.opt_output.author,
        )
        if title is None:
            raise TypeError(f"title cannot be {title}")
        if author is None:
            author = ""

        packs = MetadataHandler.split_sticker_packs(
            self.opt_output.dir,
            title=title,
            file_per_pack=24,
            separate_image_anim=False,
        )

        cover_path_old = MetadataHandler.get_cover(self.opt_output.dir)
        if cover_path_old:
            cover_path = cover_path_old
        else:
            cover_path_old = MetadataHandler.get_stickers_present(self.opt_output.dir)[
                0
            ]
            cover_path = self.opt_output.dir / "cover.png"

        if not FormatVerify.check_file(cover_path_old, spec=self.png_cover_spec):
            StickerConvert.convert(
                cover_path_old,
                cover_path,
                self.opt_comp_merged,
                self.cb,
                self.cb_return,
            )

        for pack_title, stickers in packs.items():
            with CacheStore.get_cache_store(path=self.opt_comp.cache_dir) as tempdir:
                for num, src in enumerate(stickers):
                    self.cb.put(f"Verifying {src} for uploading to Viber")

                    dst = Path(tempdir, f"{str(num).zfill(2)}.png")

                    if FormatVerify.check_file(src, spec=self.png_spec):
                        shutil.copy(src, dst)
                    else:
                        StickerConvert.convert(
                            Path(src),
                            Path(dst),
                            self.opt_comp_merged,
                            self.cb,
                            self.cb_return,
                        )

                out_f = Path(
                    self.opt_output.dir, sanitize_filename(pack_title + ".zip")
                ).as_posix()

                with zipfile.ZipFile(out_f, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for file in Path(tempdir).iterdir():
                        file_path = Path(tempdir, file.name)
                        zipf.write(file_path, arcname=file_path.name)

            upload_data = copy.deepcopy(upload_data_base)
            upload_data["title"] = pack_title
            upload_data["description"] = author
            upload_data["shareable"] = "1"

            with open(out_f, "rb") as f, open(cover_path, "rb") as g:
                r = requests.post(
                    "https://market.api.viber.com/2/users/custom-sticker-packs/create",
                    files={
                        "file": ("upload.zip", f),
                        "file_icon": ("color_icon.png", g),
                    },
                    data=upload_data,
                )

            if r.ok:
                rjson = json.loads(r.text)
                if rjson["status"] == 1:
                    pack_id = rjson["custom_sticker_pack"]["id"]
                    url = f"https://stickers.viber.com/pages/custom-sticker-packs/{pack_id}"
                    urls.append(url)
                    self.cb.put(f"Uploaded {pack_title}")
                else:
                    self.cb.put(
                        f"Failed to upload {pack_title}: {r.status_code} {r.text}"
                    )
                if rjson["status"] == 103:
                    self.cb.put(
                        "Viber auth data may have expired. Try to regenerate it?"
                    )
            else:
                self.cb.put(f"Failed to upload {pack_title}: {r.status_code} {r.text}")

        return urls

    @staticmethod
    def start(
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> List[str]:
        exporter = UploadViber(opt_output, opt_comp, opt_cred, cb, cb_return)
        return exporter.upload_stickers_viber()
