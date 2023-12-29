#!/usr/bin/env python3
import os
import copy
import re
from typing import Optional

import anyio
from telegram import Bot, InputSticker
from telegram.error import TelegramError

from .upload_base import UploadBase  # type: ignore
from ..converter import StickerConvert  # type: ignore
from ..utils.files.metadata_handler import MetadataHandler  # type: ignore
from ..utils.media.format_verify import FormatVerify  # type: ignore
from ..job_option import CompOption, OutputOption, CredOption # type: ignore


class UploadTelegram(UploadBase):
    def __init__(self, *args, **kwargs):
        super(UploadTelegram, self).__init__(*args, **kwargs)

        base_spec = CompOption({
            "size_max": {"img": 512000, "vid": 256000},
            "res": 512,
            "square": True,
            "duration": {"max": 3000}
        })

        self.png_spec = copy.deepcopy(base_spec)
        self.png_spec.format = ".png"
        self.png_spec.animated = False

        self.tgs_spec = copy.deepcopy(base_spec)
        self.tgs_spec.format = ".tgs"
        self.tgs_spec.fps_min = 60
        self.tgs_spec.fps_max = 60
        self.tgs_spec.size_max_img = 64000
        self.tgs_spec.size_max_vid = 64000

        self.webm_spec = copy.deepcopy(base_spec)
        self.webm_spec.format = ".webm"
        self.webm_spec.fps_max = 30
        self.webm_spec.animated = None if self.fake_vid else True

        self.opt_comp_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_merged.merge(base_spec)

        base_cover_spec = CompOption({
            "size_max": {"img": 128000, "vid": 32000},
            "res": 100,
            "square": True,
            "duration": {"max": 3000}
        })

        self.png_cover_spec = copy.deepcopy(base_cover_spec)
        self.png_cover_spec.format = ".png"
        self.png_cover_spec.animated = False

        self.tgs_cover_spec = copy.deepcopy(base_cover_spec)
        self.tgs_cover_spec.format = ".tgs"
        self.tgs_cover_spec.fps_min = 60
        self.tgs_cover_spec.fps_max = 60

        self.webm_cover_spec = copy.deepcopy(base_cover_spec)
        self.webm_cover_spec.format = ".webm"
        self.webm_cover_spec.fps_max = 30
        self.webm_cover_spec.animated = True

        self.opt_comp_cover_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_cover_merged.merge(base_spec)

    async def upload_pack(
        self, pack_title: str, stickers: list[str], emoji_dict: dict[str, str]
    ) -> str:
        bot = Bot(self.opt_cred.telegram_token)

        async with bot:
            pack_short_name = (
                pack_title.replace(" ", "_") + "_by_" + bot.name.replace("@", "")
            )
            pack_short_name = re.sub(
                "[^0-9a-zA-Z]+", "_", pack_short_name
            )  # name used in url, only alphanum and underscore only

            try:
                sticker_set = await bot.get_sticker_set(
                    pack_short_name,
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30,
                    pool_timeout=30,
                )
                await bot.get_sticker_set(pack_short_name)
                pack_exists = True
            except TelegramError:
                pack_exists = False

            if pack_exists == True:
                response = self.cb_ask_bool(
                    f"Warning: Pack {pack_short_name} already exists.\nDelete all stickers in pack?"
                )
                if response == True:
                    self.cb_msg(f"Deleting all stickers from pack {pack_short_name}")
                    try:
                        for i in sticker_set.stickers:
                            await bot.delete_sticker_from_set(i.file_id)
                    except TelegramError as e:
                        self.cb_msg(
                            f"Cannot delete sticker {i.file_id} from {pack_short_name} due to {e}"
                        )
                else:
                    self.cb_msg(f"Not deleting existing pack {pack_short_name}")

            for src in stickers:
                self.cb_msg(f"Verifying {src} for uploading to telegram")

                src_full_name = os.path.split(src)[-1]
                src_name = os.path.splitext(src_full_name)[0]
                ext = os.path.splitext(src_full_name)[-1]

                emoji = emoji_dict.get(src_name, None)
                if emoji:
                    if len(emoji) > 20:
                        self.cb_msg(
                            f"Warning: {len(emoji)} emoji for file {src_full_name}, exceeding limit of 20, keep first 20 only..."
                        )
                    emoji_list = [*emoji][:20]
                else:
                    self.cb_msg(
                        f"Warning: Cannot find emoji for file {src_full_name}, skip uploading this file..."
                    )
                    continue

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

                if FormatVerify.check_file(src, spec=spec_choice):
                    with open(src, "rb") as f:
                        sticker_bytes = f.read()
                else:
                    _, _, sticker_bytes, _ = StickerConvert(
                        src, f"bytes{ext}", self.opt_comp_merged, self.cb_msg
                    ).convert()

                sticker = InputSticker(sticker=sticker_bytes, emoji_list=emoji_list)

                try:
                    if pack_exists == False:
                        await bot.create_new_sticker_set(
                            user_id=self.opt_cred.telegram_userid,
                            name=pack_short_name,
                            title=pack_title,
                            stickers=[sticker],
                            sticker_format=sticker_format,
                        )
                        pack_exists = True
                    else:
                        await bot.add_sticker_to_set(
                            user_id=self.opt_cred.telegram_userid,
                            name=pack_short_name,
                            sticker=sticker,
                        )
                except TelegramError as e:
                    self.cb_msg(
                        f"Cannot upload sticker {src} in {pack_short_name} due to {e}"
                    )
                    continue

                self.cb_msg(f"Uploaded {src}")

            cover_path = MetadataHandler.get_cover(self.in_dir)
            if cover_path:
                if FormatVerify.check_file(cover_path, spec=cover_spec_choice):
                    with open(cover_path, "rb") as f:
                        thumbnail_bytes = f.read()
                else:
                    _, _, thumbnail_bytes, _ = StickerConvert(
                        cover_path,
                        f"bytes{ext}",
                        self.opt_comp_cover_merged,
                        self.cb_msg,
                    ).convert()

                try:
                    await bot.set_sticker_set_thumbnail(
                        name=pack_short_name,
                        user_id=self.opt_cred.telegram_userid,
                        thumbnail=thumbnail_bytes,
                    )
                except TelegramError as e:
                    self.cb_msg(
                        f"Cannot upload cover (thumbnail) for {pack_short_name} due to {e}"
                    )

        result = f"https://t.me/addstickers/{pack_short_name}"
        return result

    def upload_stickers_telegram(self) -> list[str]:
        urls = []

        if not self.opt_cred.telegram_token:
            self.cb_msg("Token required for uploading to telegram")
            return urls

        title, author, emoji_dict = MetadataHandler.get_metadata(
            self.in_dir,
            title=self.opt_output.title,
            author=self.opt_output.author,
        )
        if title == None:
            raise TypeError("title cannot be", title)
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
            self.in_dir,
            title=title,
            file_per_anim_pack=50,
            file_per_image_pack=120,
            separate_image_anim=not self.fake_vid,
        )

        for pack_title, stickers in packs.items():
            self.cb_msg(f"Uploading pack {pack_title}")
            result = anyio.run(self.upload_pack, pack_title, stickers, emoji_dict)
            self.cb_msg(result)
            urls.append(result)

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
        exporter = UploadTelegram(
            opt_output,
            opt_comp,
            opt_cred,
            cb_msg,
            cb_msg_block,
            cb_ask_bool,
            cb_bar,
            out_dir,
        )
        return exporter.upload_stickers_telegram()
