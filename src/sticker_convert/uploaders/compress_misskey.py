#!/usr/bin/env python3
import copy
import json
import re
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from sticker_convert.converter import StickerConvert
from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.uploaders.upload_base import UploadBase
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.files.sanitize_filename import sanitize_filename
from sticker_convert.utils.media.codec_info import CodecInfo
from sticker_convert.utils.media.format_verify import FormatVerify
from sticker_convert.utils.translate import I


class CompressMisskey(UploadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.base_spec.set_size_max(50000)
        self.base_spec.set_format((".png", ".gif"))

        self.png_spec = copy.deepcopy(self.base_spec)
        self.png_spec.animated = False
        self.png_spec.set_format((".png",))

        self.gif_spec = copy.deepcopy(self.base_spec)
        self.gif_spec.animated = True
        self.gif_spec.set_format((".gif",))

        self.opt_comp_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_merged.merge(self.base_spec)

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-zA-Z0-9_]+", "_", ascii_value).strip("_").lower()
        return slug

    def _get_category(self, title: str) -> str:
        category = self._slugify(title)
        return category or "sticker_convert"

    def _get_name(self, stem: str, category: str, index: int, names_seen: Set[str]) -> str:
        name = self._slugify(stem)
        if not name or name.isdigit() or name in names_seen:
            name = f"{category}_{str(index).zfill(3)}"

        while name in names_seen:
            name = f"{name}_{str(index).zfill(3)}"

        names_seen.add(name)
        return name

    def compress_misskey(self) -> Tuple[int, int, List[str]]:
        urls: List[str] = []
        title, author, _ = MetadataHandler.get_metadata(
            self.opt_output.dir,
            title=self.opt_output.title,
            author=self.opt_output.author,
        )
        title = title or self.opt_output.dir.name or "misskey-export"
        category = self._get_category(title)

        out_f = Path(self.opt_output.dir, sanitize_filename(title + ".zip")).as_posix()
        stickers = MetadataHandler.get_stickers_present(self.opt_output.dir)

        meta: Dict[str, Any] = {
            "metaVersion": 2,
            "host": author or "",
            "exportedAt": datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "emojis": [],
        }

        stickers_ok = 0
        stickers_total = len(stickers)
        names_seen: Set[str] = set()
        file_names_seen: Set[str] = set()

        with zipfile.ZipFile(out_f, "w", zipfile.ZIP_DEFLATED) as zipf:
            for num, src in enumerate(stickers, start=1):
                self.cb.put(I("Verifying {} for compressing into Misskey ZIP").format(src))

                if CodecInfo.is_anim(src):
                    expected_name = Path("bytes.gif")
                    spec = self.gif_spec
                else:
                    expected_name = Path("bytes.png")
                    spec = self.png_spec

                if not FormatVerify.check_file(src, spec=spec):
                    success, _, image_data, _ = StickerConvert.convert(
                        src,
                        expected_name,
                        self.opt_comp_merged,
                        self.cb,
                        self.cb_return,
                    )
                    assert isinstance(image_data, bytes)
                    if not success:
                        self.cb.put(
                            I("Warning: Cannot compress file {}, skip this file...").format(
                                src.name
                            )
                        )
                        continue
                    file_suffix = expected_name.suffix
                else:
                    with open(src, "rb") as f:
                        image_data = f.read()
                    file_suffix = src.suffix.lower()

                base_file_name = sanitize_filename(src.stem) or f"emoji_{str(num).zfill(3)}"
                file_name = sanitize_filename(base_file_name + file_suffix)
                while file_name in file_names_seen:
                    file_name = sanitize_filename(
                        f"{base_file_name}_{str(num).zfill(3)}{file_suffix}"
                    )
                file_names_seen.add(file_name)

                emoji_name = self._get_name(src.stem, category, num, names_seen)
                meta["emojis"].append(
                    {
                        "downloaded": True,
                        "fileName": file_name,
                        "emoji": {
                            "name": emoji_name,
                            "category": category,
                            "aliases": [],
                        },
                    }
                )
                zipf.writestr(file_name, image_data)
                stickers_ok += 1

            zipf.writestr(
                "meta.json",
                json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8"),
            )

        self.cb.put(out_f)
        urls.append(out_f)

        return stickers_ok, stickers_total, urls

    @staticmethod
    def start(
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int, List[str]]:
        exporter = CompressMisskey(opt_output, opt_comp, opt_cred, cb, cb_return)
        return exporter.compress_misskey()
