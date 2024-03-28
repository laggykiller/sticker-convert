#!/usr/bin/env python3
import copy
import shutil
import zipfile
from pathlib import Path
from typing import Any, List

from sticker_convert.converter import StickerConvert
from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.uploaders.upload_base import UploadBase
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.cache_store import CacheStore
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.files.sanitize_filename import sanitize_filename
from sticker_convert.utils.media.codec_info import CodecInfo
from sticker_convert.utils.media.format_verify import FormatVerify


class CompressWastickers(UploadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.base_spec.size_max_img = 100000
        self.base_spec.size_max_vid = 500000
        self.base_spec.duration_min = 8
        self.base_spec.duration_max = 10000
        self.base_spec.square = True
        self.base_spec.set_res(512)
        self.base_spec.set_format((".webp",))

        self.spec_cover = CompOption(
            size_max_img=50000,
            size_max_vid=50000,
            animated=False,
        )
        self.spec_cover.set_res(96)
        self.spec_cover.set_res(96)
        self.spec_cover.set_fps(0)
        self.spec_cover.set_format((".png",))

        self.webp_spec = copy.deepcopy(self.base_spec)
        self.webp_spec.set_format((".webp",))
        self.webp_spec.animated = None if self.opt_comp.fake_vid else True

        self.png_spec = copy.deepcopy(self.base_spec)
        self.png_spec.set_format((".png",))
        self.png_spec.animated = False

        self.opt_comp_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_merged.merge(self.base_spec)

    def compress_wastickers(self) -> List[str]:
        urls: List[str] = []
        title, author, _ = MetadataHandler.get_metadata(
            self.opt_output.dir,
            title=self.opt_output.title,
            author=self.opt_output.author,
        )
        if not title:
            self.cb.put("Title is required for compressing .wastickers")
            return urls
        if not author:
            self.cb.put("Author is required for compressing .wastickers")
            return urls
        packs = MetadataHandler.split_sticker_packs(
            self.opt_output.dir,
            title=title,
            file_per_pack=30,
            separate_image_anim=not self.opt_comp.fake_vid,
        )

        for pack_title, stickers in packs.items():
            # Originally the Sticker Maker application name the files with int(time.time())
            with CacheStore.get_cache_store(path=self.opt_comp.cache_dir) as tempdir:
                for num, src in enumerate(stickers):
                    self.cb.put(f"Verifying {src} for compressing into .wastickers")

                    if self.opt_comp.fake_vid or CodecInfo.is_anim(src):
                        ext = ".webp"
                    else:
                        ext = ".png"

                    dst = Path(tempdir, f"sticker_{num+1}{ext}")

                    if FormatVerify.check_file(
                        src, spec=self.webp_spec
                    ) or FormatVerify.check_file(src, spec=self.png_spec):
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
                    self.opt_output.dir, sanitize_filename(pack_title + ".wastickers")
                ).as_posix()

                self.add_metadata(Path(tempdir), pack_title, author)
                with zipfile.ZipFile(out_f, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for file in Path(tempdir).iterdir():
                        file_path = Path(tempdir, file.name)
                        zipf.write(file_path, arcname=file_path.name)

            self.cb.put((out_f))
            urls.append(out_f)

        return urls

    def add_metadata(self, pack_dir: Path, title: str, author: str) -> None:
        opt_comp_merged = copy.deepcopy(self.opt_comp)
        opt_comp_merged.merge(self.spec_cover)

        cover_path_old = MetadataHandler.get_cover(self.opt_output.dir)
        cover_path_new = Path(pack_dir, "tray.png")
        if cover_path_old:
            if FormatVerify.check_file(cover_path_old, spec=self.spec_cover):
                shutil.copy(cover_path_old, cover_path_new)
            else:
                StickerConvert.convert(
                    cover_path_old,
                    cover_path_new,
                    opt_comp_merged,
                    self.cb,
                    self.cb_return,
                )
        else:
            # First image in the directory, extracting first frame
            first_image = [
                i
                for i in sorted(self.opt_output.dir.iterdir())
                if Path(self.opt_output.dir, i.name).is_file()
                and i.suffix not in (".txt", ".m4a", ".wastickers")
            ][0]
            StickerConvert.convert(
                Path(self.opt_output.dir, first_image),
                cover_path_new,
                opt_comp_merged,
                self.cb,
                self.cb_return,
            )

        MetadataHandler.set_metadata(pack_dir, author=author, title=title, newline=True)

    @staticmethod
    def start(
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> List[str]:
        exporter = CompressWastickers(opt_output, opt_comp, opt_cred, cb, cb_return)
        return exporter.compress_wastickers()
