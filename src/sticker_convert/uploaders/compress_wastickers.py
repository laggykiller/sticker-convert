#!/usr/bin/env python3
import copy
import zipfile
from pathlib import Path
from typing import Any, List, Tuple

from sticker_convert.converter import StickerConvert
from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.uploaders.upload_base import UploadBase
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
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

    def compress_wastickers(self) -> Tuple[int, int, List[str]]:
        urls: List[str] = []
        title, author, _ = MetadataHandler.get_metadata(
            self.opt_output.dir,
            title=self.opt_output.title,
            author=self.opt_output.author,
        )
        if not title:
            self.cb.put("Title is required for compressing .wastickers")
            return 0, 0, urls
        if not author:
            self.cb.put("Author is required for compressing .wastickers")
            return 0, 0, urls
        packs = MetadataHandler.split_sticker_packs(
            self.opt_output.dir,
            title=title,
            file_per_pack=30,
            separate_image_anim=not self.opt_comp.fake_vid,
        )

        stickers_total = 0
        for pack_title, stickers in packs.items():
            stickers_total += len(stickers)
            out_f = Path(
                self.opt_output.dir, sanitize_filename(pack_title + ".wastickers")
            ).as_posix()

            MetadataHandler.set_metadata(
                self.opt_output.dir, author=author, title=title, newline=True
            )
            with zipfile.ZipFile(out_f, "w", zipfile.ZIP_DEFLATED) as zipf:
                cover_opt_comp_merged = copy.deepcopy(self.opt_comp)
                cover_opt_comp_merged.merge(self.spec_cover)

                cover_path_old = MetadataHandler.get_cover(self.opt_output.dir)
                cover_path_new = Path("bytes.png")
                if cover_path_old is None:
                    # First image in the directory, extracting first frame
                    first_image = [
                        i
                        for i in sorted(self.opt_output.dir.iterdir())
                        if Path(self.opt_output.dir, i.name).is_file()
                        and i.suffix not in (".txt", ".m4a", ".wastickers")
                    ][0]
                    self.cb.put(f"Creating cover using {first_image.name}")
                    success, _, cover_data, _ = StickerConvert.convert(
                        Path(self.opt_output.dir, first_image),
                        cover_path_new,
                        cover_opt_comp_merged,
                        self.cb,
                        self.cb_return,
                    )
                    if not success:
                        self.cb.put(
                            f"Warning: Cannot compress cover {first_image.name}, unable to create .wastickers"
                        )
                        continue
                else:
                    if not FormatVerify.check_file(
                        cover_path_old, spec=self.spec_cover
                    ):
                        success, _, cover_data, _ = StickerConvert.convert(
                            cover_path_old,
                            cover_path_new,
                            cover_opt_comp_merged,
                            self.cb,
                            self.cb_return,
                        )
                        if not success:
                            self.cb.put(
                                f"Warning: Cannot compress cover {cover_path_old.name}, unable to create .wastickers"
                            )
                            continue
                    else:
                        with open(cover_path_old, "rb") as f:
                            cover_data = f.read()

                assert isinstance(cover_data, bytes)
                zipf.writestr("tray.png", cover_data)
                zipf.write(Path(self.opt_output.dir, "author.txt"), "author.txt")
                zipf.write(Path(self.opt_output.dir, "title.txt"), "title.txt")

                for num, src in enumerate(stickers):
                    self.cb.put(f"Verifying {src} for compressing into .wastickers")

                    if self.opt_comp.fake_vid or CodecInfo.is_anim(src):
                        ext = ".webp"
                    else:
                        ext = ".png"
                    dst = f"bytes{ext}"

                    if not (
                        FormatVerify.check_file(src, spec=self.webp_spec)
                        or FormatVerify.check_file(src, spec=self.png_spec)
                    ):
                        success, _, image_data, _ = StickerConvert.convert(
                            Path(src),
                            Path(dst),
                            self.opt_comp_merged,
                            self.cb,
                            self.cb_return,
                        )
                        assert isinstance(image_data, bytes)
                        if not success:
                            self.cb.put(
                                f"Warning: Cannot compress file {Path(src).name}, skip this file..."
                            )
                            continue
                    else:
                        with open(src, "rb") as f:
                            image_data = f.read()

                    # Originally the Sticker Maker application name the files with int(time.time())
                    zipf.writestr(f"sticker_{num + 1}{ext}", image_data)

            self.cb.put((out_f))
            urls.append(out_f)

        return stickers_total, stickers_total, urls

    @staticmethod
    def start(
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int, List[str]]:
        exporter = CompressWastickers(opt_output, opt_comp, opt_cred, cb, cb_return)
        return exporter.compress_wastickers()
