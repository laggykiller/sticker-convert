#!/usr/bin/env python3
import copy
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

from sticker_convert.converter import StickerConvert
from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.uploaders.upload_base import UploadBase
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.files.sanitize_filename import sanitize_filename
from sticker_convert.utils.media.format_verify import FormatVerify


class UploadViber(UploadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.base_spec.set_size_max(0)

        self.png_spec = copy.deepcopy(self.base_spec)
        self.png_spec.set_res_max(490)
        self.png_spec.set_format((".png",))
        self.opt_comp_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_merged.merge(self.png_spec)

        self.png_cover_spec = copy.deepcopy(self.base_spec)
        self.png_cover_spec.set_res_max(120)
        self.png_cover_spec.set_format((".png",))
        self.opt_comp_cover_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_cover_merged.merge(self.png_cover_spec)

    def upload_stickers_viber(self) -> Tuple[int, int, List[str]]:
        urls: List[str] = []

        if not self.opt_cred.viber_auth:
            self.cb.put("Viber auth required for uploading to viber")
            return 0, 0, urls

        upload_data_base: Dict[str, str] = {}
        for i in self.opt_cred.viber_auth.split(";"):
            j = i.split(":")
            upload_data_base[j[0]] = j[1]

        if upload_data_base.get("member_id") is None:
            self.cb.put("Invalid Viber auth: Missing member_id")
            return 0, 0, urls
        if upload_data_base.get("m_token") is None:
            self.cb.put("Invalid Viber auth: Missing m_token")
            return 0, 0, urls
        if upload_data_base.get("m_ts") is None:
            self.cb.put("Invalid Viber auth: Missing m_ts")
            return 0, 0, urls

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

        cover_path = MetadataHandler.get_cover(self.opt_output.dir)
        if cover_path is None:
            cover_path = MetadataHandler.get_stickers_present(self.opt_output.dir)[0]

        if FormatVerify.check_file(cover_path, spec=self.png_cover_spec):
            with open(cover_path, "rb") as f:
                cover_bytes = f.read()
        else:
            _, _, cover_bytes, _ = StickerConvert.convert(  # type: ignore
                cover_path,
                Path("bytes.png"),
                self.opt_comp_cover_merged,
                self.cb,
                self.cb_return,
            )
            assert isinstance(cover_bytes, bytes)

        stickers_total = 0
        stickers_ok = 0
        for pack_title, stickers in packs.items():
            stickers_total += len(stickers)
            out_f = Path(
                self.opt_output.dir, sanitize_filename(pack_title + ".zip")
            ).as_posix()
            with zipfile.ZipFile(out_f, "w", zipfile.ZIP_DEFLATED) as zipf:
                for num, src in enumerate(stickers):
                    self.cb.put(f"Verifying {src} for uploading to Viber")

                    if not FormatVerify.check_file(src, spec=self.png_spec):
                        success, _, image_data, _ = StickerConvert.convert(
                            src,
                            Path("bytes.png"),
                            self.opt_comp_merged,
                            self.cb,
                            self.cb_return,
                        )
                        assert isinstance(image_data, bytes)
                        if not success:
                            self.cb.put(
                                f"Warning: Cannot compress file {src.name}, skip this file..."
                            )
                            continue
                    else:
                        with open(src, "rb") as f:
                            image_data = f.read()

                    zipf.writestr(f"{str(num).zfill(2)}.png", image_data)

            upload_data = copy.deepcopy(upload_data_base)
            upload_data["title"] = pack_title
            upload_data["description"] = author
            upload_data["shareable"] = "1"

            with open(out_f, "rb") as f:
                r = requests.post(
                    "https://market.api.viber.com/2/users/custom-sticker-packs/create",
                    files={
                        "file": ("upload.zip", f.read()),
                        "file_icon": ("color_icon.png", cover_bytes),
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
                    stickers_ok += len(stickers)
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

        return stickers_ok, stickers_total, urls

    @staticmethod
    def start(
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int, List[str]]:
        exporter = UploadViber(opt_output, opt_comp, opt_cred, cb, cb_return)
        return exporter.upload_stickers_viber()
