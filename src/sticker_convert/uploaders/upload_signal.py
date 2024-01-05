#!/usr/bin/env python3
import os
import copy
from typing import Optional

import anyio
from signalstickers_client import StickersClient  # type: ignore
from signalstickers_client.models import LocalStickerPack, Sticker  # type: ignore
from signalstickers_client.errors import SignalException # type: ignore

from .upload_base import UploadBase  # type: ignore
from ..utils.files.metadata_handler import MetadataHandler  # type: ignore
from ..converter import StickerConvert  # type: ignore
from ..utils.media.format_verify import FormatVerify  # type: ignore
from ..utils.media.codec_info import CodecInfo  # type: ignore
from ..job_option import CompOption, OutputOption, CredOption # type: ignore


class UploadSignal(UploadBase):
    def __init__(self, *args, **kwargs):
        super(UploadSignal, self).__init__(*args, **kwargs)

        base_spec = CompOption({
            "size_max": {"img": 300000, "vid": 300000},
            "res": {"max": 512},
            "duration": {"max": 3000},
            "square": True,
        })

        self.png_spec = copy.deepcopy(base_spec)
        self.png_spec.format_vid = '.apng'

        self.webp_spec = copy.deepcopy(base_spec)
        self.webp_spec.format_img = '.webp'
        self.webp_spec.animated = False

        self.opt_comp_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_merged.merge(base_spec)

    @staticmethod
    async def upload_pack(pack: LocalStickerPack, uuid: str, password: str):
        async with StickersClient(uuid, password) as client:
            pack_id, pack_key = await client.upload_pack(pack)

        result = (
            f"https://signal.art/addstickers/#pack_id={pack_id}&pack_key={pack_key}"
        )
        return result

    def add_stickers_to_pack(
        self, pack: LocalStickerPack, stickers: list[str], emoji_dict: dict
    ):
        for src in stickers:
            self.cb_msg(f"Verifying {src} for uploading to signal")

            src_full_name = os.path.split(src)[-1]
            src_name = os.path.splitext(src_full_name)[0]
            ext = os.path.splitext(src_full_name)[-1]

            sticker = Sticker()
            sticker.id = pack.nb_stickers

            emoji = emoji_dict.get(src_name, None)
            if not emoji:
                self.cb_msg(
                    f"Warning: Cannot find emoji for file {src_full_name}, skip uploading this file..."
                )
                continue
            sticker.emoji = emoji[:1]

            if ext == ".webp":
                spec_choice = self.webp_spec
            else:
                spec_choice = self.png_spec

            if not FormatVerify.check_file(src, spec=spec_choice):
                if self.fake_vid or CodecInfo.is_anim(src):
                    dst = "bytes.apng"
                else:
                    dst = "bytes.png"
                _, _, sticker.image_data, _ = StickerConvert(
                    src, dst, self.opt_comp_merged, self.cb_msg
                ).convert()
            else:
                with open(src, "rb") as f:
                    sticker.image_data = f.read()

            pack._addsticker(sticker)

    def upload_stickers_signal(self) -> list[str]:
        urls = []

        if not self.opt_cred.signal_uuid:
            self.cb_msg("uuid required for uploading to Signal")
            return urls
        if not self.opt_cred.signal_password:
            self.cb_msg("password required for uploading to Signal")
            return urls

        title, author, emoji_dict = MetadataHandler.get_metadata(
            self.in_dir,
            title=self.opt_output.title,
            author=self.opt_output.author,
        )
        if title == None:
            raise TypeError(f"title cannot be {title}")
        if author == None:
            raise TypeError(f"author cannot be {author}")
        if emoji_dict == None:
            msg_block = "emoji.txt is required for uploading signal stickers\n"
            msg_block += f"emoji.txt generated for you in {self.in_dir}\n"
            msg_block += (
                f'Default emoji is set to {self.opt_comp.default_emoji}.\n'
            )
            msg_block += "Please edit emoji.txt now, then continue"
            MetadataHandler.generate_emoji_file(
                dir=self.in_dir, default_emoji=self.opt_comp.default_emoji
            )

            self.cb_msg_block(msg_block)

            title, author, emoji_dict = MetadataHandler.get_metadata(
                self.in_dir,
                title=self.opt_output.title,
                author=self.opt_output.author,
            )

        packs = MetadataHandler.split_sticker_packs(
            self.in_dir, title=title, file_per_pack=200, separate_image_anim=False
        )
        for pack_title, stickers in packs.items():
            pack = LocalStickerPack()
            pack.title = pack_title
            pack.author = author

            self.add_stickers_to_pack(pack, stickers, emoji_dict)
            self.cb_msg(f"Uploading pack {pack_title}")
            try:
                result = anyio.run(
                    UploadSignal.upload_pack,
                    pack,
                    self.opt_cred.signal_uuid,
                    self.opt_cred.signal_password,
                )
                self.cb_msg(result)
                urls.append(result)

            except SignalException as e:
                self.cb_msg(f"Failed to upload pack {pack_title} due to {repr(e)}")

        return urls

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
        exporter = UploadSignal(
            opt_output,
            opt_comp,
            opt_cred,
            cb_msg,
            cb_msg_block,
            cb_ask_bool,
            cb_bar,
            out_dir,
        )
        return exporter.upload_stickers_signal()
