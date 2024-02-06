#!/usr/bin/env python3
import copy
from pathlib import Path
from queue import Queue
from typing import Union, Any, Optional

import anyio
from signalstickers_client import StickersClient  # type: ignore
from signalstickers_client.errors import SignalException  # type: ignore
from signalstickers_client.models import LocalStickerPack, Sticker  # type: ignore

from sticker_convert.converter import StickerConvert
from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.uploaders.upload_base import UploadBase
from sticker_convert.utils.callback import Callback, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.media.codec_info import CodecInfo
from sticker_convert.utils.media.format_verify import FormatVerify


class UploadSignal(UploadBase):
    def __init__(self, *args: Any, **kwargs: Any):
        super(UploadSignal, self).__init__(*args, **kwargs)

        base_spec = CompOption()
        base_spec.size_max = 300000
        base_spec.res_max = 512
        base_spec.duration_max = 3000
        base_spec.square = True

        self.png_spec = copy.deepcopy(base_spec)
        self.png_spec.format = [".apng"]

        self.webp_spec = copy.deepcopy(base_spec)
        self.webp_spec.format_img = [".webp"]
        self.webp_spec.animated = False

        self.opt_comp_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_merged.merge(base_spec)

    @staticmethod
    async def upload_pack(pack: LocalStickerPack, uuid: str, password: str):
        async with StickersClient(uuid, password) as client:
            pack_id, pack_key = await client.upload_pack(pack)  # type: ignore

        result = (
            f"https://signal.art/addstickers/#pack_id={pack_id}&pack_key={pack_key}"
        )
        return result

    def add_stickers_to_pack(
        self, pack: LocalStickerPack, stickers: list[Path], emoji_dict: dict[str, str]
    ):
        for src in stickers:
            self.cb.put(f"Verifying {src} for uploading to signal")

            sticker = Sticker()
            sticker.id = pack.nb_stickers  # type: ignore

            emoji = emoji_dict.get(Path(src).stem, None)
            if not emoji:
                self.cb.put(
                    f"Warning: Cannot find emoji for file {Path(src).name}, skip uploading this file..."
                )
                continue
            sticker.emoji = emoji[:1]  # type: ignore

            if Path(src).suffix == ".webp":
                spec_choice = self.webp_spec
            else:
                spec_choice = self.png_spec

            if not FormatVerify.check_file(src, spec=spec_choice):
                if self.opt_comp.fake_vid or CodecInfo.is_anim(src):
                    dst = "bytes.apng"
                else:
                    dst = "bytes.png"
                _, _, image_data, _ = StickerConvert.convert(
                    Path(src), Path(dst), self.opt_comp_merged, self.cb, self.cb_return
                )
                assert image_data

                sticker.image_data = image_data  # type: ignore
            else:
                with open(src, "rb") as f:
                    sticker.image_data = f.read()  # type: ignore

            pack._addsticker(sticker)  # type: ignore

    def upload_stickers_signal(self) -> list[str]:
        urls: list[str] = []

        if not self.opt_cred.signal_uuid:
            self.cb.put("uuid required for uploading to Signal")
            return urls
        if not self.opt_cred.signal_password:
            self.cb.put("password required for uploading to Signal")
            return urls

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
                dir=self.opt_output.dir, default_emoji=self.opt_comp.default_emoji
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
        for pack_title, stickers in packs.items():
            pack = LocalStickerPack()
            pack.title = pack_title  # type: ignore
            pack.author = author  # type: ignore

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

            except SignalException as e:
                self.cb.put(f"Failed to upload pack {pack_title} due to {repr(e)}")

        return urls

    @staticmethod
    def start(
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: Union[
            Queue[
                Union[
                    tuple[str, Optional[tuple[str]], Optional[dict[str, str]]],
                    str,
                    None,
                ]
            ],
            Callback,
        ],
        cb_return: CallbackReturn,
    ) -> list[str]:
        exporter = UploadSignal(opt_output, opt_comp, opt_cred, cb, cb_return)
        return exporter.upload_stickers_signal()
