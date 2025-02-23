#!/usr/bin/env python3
import copy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import anyio
from signalstickers_client.errors import SignalException
from signalstickers_client.models import LocalStickerPack, Sticker
from signalstickers_client.stickersclient import StickersClient

from sticker_convert.converter import StickerConvert
from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.uploaders.upload_base import UploadBase
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.emoji import extract_emojis
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.media.codec_info import CodecInfo
from sticker_convert.utils.media.format_verify import FormatVerify


class UploadSignal(UploadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.base_spec.set_size_max(300000)
        self.base_spec.set_res_max(512)
        self.base_spec.duration_max = 3000

        self.png_spec = copy.deepcopy(self.base_spec)
        self.png_spec.set_format((".apng",))

        self.webp_spec = copy.deepcopy(self.base_spec)
        self.webp_spec.format_img = (".webp",)
        self.webp_spec.animated = False

        self.opt_comp_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_merged.merge(self.base_spec)

    @staticmethod
    async def upload_pack(pack: LocalStickerPack, uuid: str, password: str) -> str:
        async with StickersClient(uuid, password) as client:
            pack_id, pack_key = await client.upload_pack(pack)

        result = (
            f"https://signal.art/addstickers/#pack_id={pack_id}&pack_key={pack_key}"
        )
        return result

    def create_sticker(
        self, src: Path, emoji_dict: Dict[str, str]
    ) -> Optional[Sticker]:
        self.cb.put(f"Verifying {src} for uploading to signal")

        sticker = Sticker()

        emoji = extract_emojis(emoji_dict.get(Path(src).stem, ""))
        if emoji == "":
            self.cb.put(
                f"Warning: Cannot find emoji for file {Path(src).name}, using default emoji..."
            )
            emoji = self.opt_comp.default_emoji
        sticker.emoji = emoji

        if Path(src).suffix == ".webp":
            spec_choice = self.webp_spec
        else:
            spec_choice = self.png_spec

        if not FormatVerify.check_file(src, spec=spec_choice):
            if self.opt_comp.fake_vid or CodecInfo.is_anim(src):
                dst = "bytes.apng"
            else:
                dst = "bytes.png"
            success, _, image_data, _ = StickerConvert.convert(
                Path(src), Path(dst), self.opt_comp_merged, self.cb, self.cb_return
            )
            if not success:
                self.cb.put(
                    f"Warning: Cannot compress file {Path(src).name}, skip uploading this file..."
                )
                return None

            assert isinstance(image_data, bytes)

            sticker.image_data = image_data
        else:
            with open(src, "rb") as f:
                sticker.image_data = f.read()

        return sticker

    def add_stickers_to_pack(
        self, pack: LocalStickerPack, stickers: List[Path], emoji_dict: Dict[str, str]
    ) -> None:
        cover_file = MetadataHandler.get_cover(self.opt_output.dir)
        cover_file_bytes = None
        if cover_file:
            with open(cover_file, "rb") as f:
                cover_file_bytes = f.read()
        for src in stickers:
            sticker = self.create_sticker(src, emoji_dict)
            if sticker is None:
                continue
            sticker.id = pack.nb_stickers
            pack._addsticker(sticker)  # type: ignore

            if (
                cover_file
                and pack.cover is None
                and sticker.image_data == cover_file_bytes
            ):
                pack.cover = sticker

        if cover_file and pack.cover is None:
            sticker = self.create_sticker(cover_file, emoji_dict)
            if sticker is not None:
                sticker.id = pack.nb_stickers
                pack.cover = sticker

    def upload_stickers_signal(self) -> Tuple[int, int, List[str]]:
        urls: List[str] = []

        if not self.opt_cred.signal_uuid:
            self.cb.put("uuid required for uploading to Signal")
            return 0, 0, urls
        if not self.opt_cred.signal_password:
            self.cb.put("password required for uploading to Signal")
            return 0, 0, urls

        title, author, emoji_dict = MetadataHandler.get_metadata(
            self.opt_output.dir,
            title=self.opt_output.title,
            author=self.opt_output.author,
        )
        if title is None:
            raise TypeError(f"title cannot be {title}")
        if author is None:
            raise TypeError(f"author cannot be {author}")
        if emoji_dict is None:
            msg_block = "emoji.txt is required for uploading signal stickers\n"
            msg_block += f"emoji.txt generated for you in {self.opt_output.dir}\n"
            msg_block += f"Default emoji is set to {self.opt_comp.default_emoji}.\n"
            msg_block += "Please edit emoji.txt now, then continue"
            MetadataHandler.generate_emoji_file(
                directory=self.opt_output.dir, default_emoji=self.opt_comp.default_emoji
            )

            self.cb.put(("msg_block", (msg_block,), None))
            if self.cb_return:
                self.cb_return.get_response()

            title, author, emoji_dict = MetadataHandler.get_metadata(
                self.opt_output.dir,
                title=self.opt_output.title,
                author=self.opt_output.author,
            )
            assert title
            assert author
            assert emoji_dict

        packs = MetadataHandler.split_sticker_packs(
            self.opt_output.dir,
            title=title,
            file_per_pack=200,
            separate_image_anim=False,
        )
        stickers_total = 0
        stickers_ok = 0
        for pack_title, stickers in packs.items():
            stickers_total += len(stickers)
            pack = LocalStickerPack()
            pack.title = pack_title
            pack.author = author

            self.add_stickers_to_pack(pack, stickers, emoji_dict)
            self.cb.put(f"Uploading pack {pack_title}")
            self.cb.put("update_bar")
            try:
                result = anyio.run(
                    UploadSignal.upload_pack,
                    pack,
                    self.opt_cred.signal_uuid,
                    self.opt_cred.signal_password,
                )
                self.cb.put((result))
                urls.append(result)
                stickers_ok += len(stickers)

            except SignalException as e:
                self.cb.put(f"Failed to upload pack {pack_title} due to {repr(e)}")

        return stickers_ok, stickers_total, urls

    @staticmethod
    def start(
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int, List[str]]:
        exporter = UploadSignal(opt_output, opt_comp, opt_cred, cb, cb_return)
        return exporter.upload_stickers_signal()
