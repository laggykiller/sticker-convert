#!/usr/bin/env python3
import shutil
import os
import copy
import zipfile
from typing import Optional

from .upload_base import UploadBase  # type: ignore
from ..converter import StickerConvert  # type: ignore
from ..utils.media.format_verify import FormatVerify  # type: ignore
from ..utils.files.metadata_handler import MetadataHandler  # type: ignore
from ..utils.media.codec_info import CodecInfo  # type: ignore
from ..utils.files.cache_store import CacheStore  # type: ignore
from ..job_option import CompOption, OutputOption, CredOption # type: ignore


class CompressWastickers(UploadBase):
    def __init__(self, *args, **kwargs):
        super(CompressWastickers, self).__init__(*args, **kwargs)
        base_spec = CompOption({
            "size_max": {"img": 100000, "vid": 500000},
            "res": 512,
            "duration": {"min": 8, "max": 10000},
            "format": ".webp",
            "square": True,
        })

        self.spec_cover = CompOption({
            "size_max": {"img": 50000, "vid": 50000},
            "res": 96,
            "format": ".png",
            "animated": False,
        })

        self.webp_spec = copy.deepcopy(base_spec)
        self.webp_spec.format = ".webp"
        self.webp_spec.animated = None if self.fake_vid else True

        self.png_spec = copy.deepcopy(base_spec)
        self.png_spec.format = ".png"
        self.png_spec.animated = False

        self.opt_comp_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_merged.merge(base_spec)

    def compress_wastickers(self) -> list[str]:
        urls = []
        title, author, emoji_dict = MetadataHandler.get_metadata(
            self.in_dir,
            title=self.opt_output.title,
            author=self.opt_output.author,
        )
        packs = MetadataHandler.split_sticker_packs(
            self.in_dir,
            title=title,
            file_per_pack=30,
            separate_image_anim=not self.fake_vid,
        )

        for pack_title, stickers in packs.items():
            num = 0  # Originally the Sticker Maker application name the files with int(time.time())
            with CacheStore.get_cache_store(
                path=self.opt_comp.cache_dir
            ) as tempdir:
                for src in stickers:
                    self.cb_msg(f"Verifying {src} for compressing into .wastickers")

                    if self.fake_vid or CodecInfo.is_anim(src):
                        ext = ".webp"
                    else:
                        ext = ".png"

                    dst = os.path.join(tempdir, str(num) + ext)
                    num += 1

                    if (FormatVerify.check_file(src, spec=self.webp_spec) or
                        FormatVerify.check_file(src, spec=self.png_spec)):
                        shutil.copy(src, dst)
                    else:
                        StickerConvert(src, dst, self.opt_comp_merged, self.cb_msg).convert()

                out_f = os.path.join(
                    self.out_dir,
                    FormatVerify.sanitize_filename(pack_title + ".wastickers"),
                )

                self.add_metadata(tempdir, pack_title, author)
                with zipfile.ZipFile(out_f, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for file in os.listdir(tempdir):
                        file_path = os.path.join(tempdir, file)
                        file_name = os.path.basename(file_path)
                        zipf.write(file_path, arcname=file_name)

            self.cb_msg(out_f)
            urls.append(out_f)

        return urls

    def add_metadata(self, pack_dir: str, title: str, author: str):
        opt_comp_merged = copy.deepcopy(self.opt_comp)
        opt_comp_merged.merge(self.spec_cover)

        cover_path_old = MetadataHandler.get_cover(self.in_dir)
        cover_path_new = os.path.join(pack_dir, "100.png")
        if cover_path_old:
            if FormatVerify.check_file(cover_path_old, spec=self.spec_cover):
                shutil.copy(cover_path_old, cover_path_new)
            else:
                StickerConvert(
                    cover_path_old, cover_path_new, opt_comp_merged, self.cb_msg
                ).convert()
        else:
            # First image in the directory, extracting first frame
            first_image = [
                i
                for i in sorted(os.listdir(self.in_dir))
                if os.path.isfile(os.path.join(self.in_dir, i))
                and not i.endswith((".txt", ".m4a", ".wastickers"))
            ][0]
            StickerConvert(
                os.path.join(self.in_dir, f"{first_image}"),
                cover_path_new,
                opt_comp_merged,
                self.cb_msg,
            ).convert()

        MetadataHandler.set_metadata(pack_dir, author=author, title=title)

    @staticmethod
    def start(
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb_msg=print,
        cb_msg_block=input,
        cb_ask_bool=input,
        cb_bar=None,
        out_dir: Optional[str] = None,
        **kwargs,
    ) -> list[str]:
        exporter = CompressWastickers(
            opt_output,
            opt_comp,
            opt_cred,
            cb_msg,
            cb_msg_block,
            cb_ask_bool,
            cb_bar,
            out_dir,
        )
        return exporter.compress_wastickers()
