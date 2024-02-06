#!/usr/bin/env python3
import copy
import re
from pathlib import Path
from queue import Queue
from typing import Union, Any, Optional

import anyio
from telegram import Bot, InputSticker, Sticker
from telegram.error import TelegramError

from sticker_convert.converter import StickerConvert
from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.uploaders.upload_base import UploadBase
from sticker_convert.utils.callback import Callback, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.media.format_verify import FormatVerify


class UploadTelegram(UploadBase):
    def __init__(self, *args: Any, **kwargs: Any):
        super(UploadTelegram, self).__init__(*args, **kwargs)

        base_spec = CompOption(
            size_max_img=512000, size_max_vid=256000, square=True, duration_max=3000
        )
        base_spec.res = 512

        self.png_spec = copy.deepcopy(base_spec)
        self.png_spec.format = [".png"]
        self.png_spec.animated = False

        self.tgs_spec = copy.deepcopy(base_spec)
        self.tgs_spec.format = [".tgs"]
        self.tgs_spec.fps_min = 60
        self.tgs_spec.fps_max = 60
        self.tgs_spec.size_max_img = 64000
        self.tgs_spec.size_max_vid = 64000

        self.webm_spec = copy.deepcopy(base_spec)
        self.webm_spec.format = [".webm"]
        self.webm_spec.fps_max = 30
        self.webm_spec.animated = None if self.opt_comp.fake_vid else True

        self.opt_comp_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_merged.merge(base_spec)

        base_cover_spec = CompOption(
            size_max_img=128000, size_max_vid=32000, square=True, duration_max=3000
        )
        base_cover_spec.res = 100

        self.png_cover_spec = copy.deepcopy(base_cover_spec)
        self.png_cover_spec.format = [".png"]
        self.png_cover_spec.animated = False

        self.tgs_cover_spec = copy.deepcopy(base_cover_spec)
        self.tgs_cover_spec.format = [".tgs"]
        self.tgs_cover_spec.fps_min = 60
        self.tgs_cover_spec.fps_max = 60

        self.webm_cover_spec = copy.deepcopy(base_cover_spec)
        self.webm_cover_spec.format = [".webm"]
        self.webm_cover_spec.fps_max = 30
        self.webm_cover_spec.animated = True

        self.opt_comp_cover_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_cover_merged.merge(base_spec)

    async def upload_pack(
        self, pack_title: str, stickers: list[Path], emoji_dict: dict[str, str]
    ) -> str:
        assert self.opt_cred.telegram_token
        bot = Bot(self.opt_cred.telegram_token.strip())

        async with bot:
            pack_short_name = (
                pack_title.replace(" ", "_") + "_by_" + bot.name.replace("@", "")
            )
            pack_short_name = re.sub(
                "[^0-9a-zA-Z]+", "_", pack_short_name
            )  # name used in url, only alphanum and underscore only

            try:
                sticker_set = await bot.get_sticker_set(
                    pack_short_name,  # type: ignore
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30,
                    pool_timeout=30,
                )
                await bot.get_sticker_set(pack_short_name)  # type: ignore
                pack_exists = True
            except TelegramError:
                pack_exists = False

            if pack_exists is True:
                self.cb.put(
                    (
                        "ask_bool",
                        (
                            f"Warning: Pack {pack_short_name} already exists.\nDelete all stickers in pack?",
                        ),
                        None,
                    )
                )
                if self.cb_return:
                    response = self.cb_return.get_response()
                else:
                    response = False
                if response is True:
                    self.cb.put(f"Deleting all stickers from pack {pack_short_name}")
                    try:
                        for i in sticker_set.stickers:  # type: ignore
                            await bot.delete_sticker_from_set(i.file_id)
                    except TelegramError as e:
                        self.cb.put(
                            f"Cannot delete sticker {i.file_id} from {pack_short_name} due to {e}"  # type: ignore
                        )
                else:
                    self.cb.put(f"Not deleting existing pack {pack_short_name}")

            for src in stickers:
                self.cb.put(f"Verifying {src} for uploading to telegram")

                emoji = emoji_dict.get(Path(src).stem, None)
                if emoji:
                    if len(emoji) > 20:
                        self.cb.put(
                            f"Warning: {len(emoji)} emoji for file {Path(src).name}, exceeding limit of 20, keep first 20 only..."
                        )
                    emoji_list = [*emoji][:20]
                else:
                    self.cb.put(
                        f"Warning: Cannot find emoji for file {Path(src).name}, skip uploading this file..."
                    )
                    continue

                ext = Path(src).suffix
                if ext == ".tgs":
                    spec_choice = self.tgs_spec
                    cover_spec_choice = self.tgs_cover_spec
                    sticker_format = "animated"
                elif ext == ".webm":
                    spec_choice = self.webm_spec
                    cover_spec_choice = self.webm_cover_spec
                    sticker_format = "video"
                else:
                    ext = ".png"
                    spec_choice = self.png_spec
                    cover_spec_choice = self.png_cover_spec
                    sticker_format = "static"

                if self.opt_output.option == "telegram_emoji":
                    sticker_type = Sticker.CUSTOM_EMOJI
                    spec_choice.res = 100
                else:
                    sticker_type = Sticker.REGULAR

                if FormatVerify.check_file(src, spec=spec_choice):
                    with open(src, "rb") as f:
                        sticker_bytes = f.read()
                else:
                    _, _, sticker_bytes, _ = StickerConvert.convert(
                        Path(src),
                        Path(f"bytes{ext}"),
                        self.opt_comp_merged,
                        self.cb,
                        self.cb_return,
                    )

                sticker = InputSticker(sticker=sticker_bytes, emoji_list=emoji_list)  # type: ignore

                try:
                    if pack_exists is False:
                        await bot.create_new_sticker_set(
                            user_id=self.opt_cred.telegram_userid,
                            name=pack_short_name,
                            title=pack_title,
                            stickers=[sticker],
                            sticker_format=sticker_format,
                            sticker_type=sticker_type,
                        )  # type: ignore
                        pack_exists = True
                    else:
                        await bot.add_sticker_to_set(
                            user_id=self.opt_cred.telegram_userid,
                            name=pack_short_name,
                            sticker=sticker,
                        )  # type: ignore
                except TelegramError as e:
                    self.cb.put(
                        f"Cannot upload sticker {src} in {pack_short_name} due to {e}"
                    )
                    continue

                self.cb.put(f"Uploaded {src}")

            cover_path = MetadataHandler.get_cover(self.opt_output.dir)
            if cover_path:
                if FormatVerify.check_file(cover_path, spec=cover_spec_choice):  # type: ignore
                    with open(cover_path, "rb") as f:
                        thumbnail_bytes = f.read()
                else:
                    _, _, thumbnail_bytes, _ = StickerConvert.convert(  # type: ignore
                        cover_path,
                        Path(f"bytes{ext}"),  # type: ignore
                        self.opt_comp_cover_merged,
                        self.cb,
                    )

                try:
                    await bot.set_sticker_set_thumbnail(
                        name=pack_short_name,
                        user_id=self.opt_cred.telegram_userid,
                        thumbnail=thumbnail_bytes,
                    )  # type: ignore
                except TelegramError as e:
                    self.cb.put(
                        f"Cannot upload cover (thumbnail) for {pack_short_name} due to {e}"
                    )

        if self.opt_output.option == "telegram_emoji":
            result = f"https://t.me/addemoji/{pack_short_name}"
        else:
            result = f"https://t.me/addstickers/{pack_short_name}"
        return result

    def upload_stickers_telegram(self) -> list[str]:
        urls: list[str] = []

        if not (self.opt_cred.telegram_token and self.opt_cred.telegram_userid):
            self.cb.put("Token and userid required for uploading to telegram")
            return urls

        title, _, emoji_dict = MetadataHandler.get_metadata(
            self.opt_output.dir,
            title=self.opt_output.title,
            author=self.opt_output.author,
        )
        if title is None:
            raise TypeError("title cannot be", title)
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

            title, _, emoji_dict = MetadataHandler.get_metadata(
                self.opt_output.dir,
                title=self.opt_output.title,
                author=self.opt_output.author,
            )

        packs = MetadataHandler.split_sticker_packs(
            self.opt_output.dir,
            title=title,  # type: ignore
            file_per_anim_pack=50,
            file_per_image_pack=120,
            separate_image_anim=not self.opt_comp.fake_vid,
        )

        for pack_title, stickers in packs.items():
            self.cb.put(f"Uploading pack {pack_title}")
            result = anyio.run(self.upload_pack, pack_title, stickers, emoji_dict)
            self.cb.put((result))
            urls.append(result)

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
        exporter = UploadTelegram(
            opt_output,
            opt_comp,
            opt_cred,
            cb,
            cb_return,
        )
        return exporter.upload_stickers_telegram()
