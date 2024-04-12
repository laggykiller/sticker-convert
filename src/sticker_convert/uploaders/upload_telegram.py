#!/usr/bin/env python3
import copy
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

import anyio
from telegram import InputSticker, Sticker
from telegram.error import BadRequest, TelegramError
from telegram.ext import AIORateLimiter, ApplicationBuilder

from sticker_convert.converter import StickerConvert
from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.uploaders.upload_base import UploadBase
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.media.format_verify import FormatVerify


class UploadTelegram(UploadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.base_spec.size_max_img = 512000
        self.base_spec.size_max_vid = 256000
        self.base_spec.square = True
        self.base_spec.duration_max = 3000
        self.base_spec.set_res(512)

        self.png_spec = copy.deepcopy(self.base_spec)
        self.png_spec.set_format((".png",))
        self.png_spec.animated = False

        self.tgs_spec = copy.deepcopy(self.base_spec)
        self.tgs_spec.set_format((".tgs",))
        self.tgs_spec.fps_min = 60
        self.tgs_spec.fps_max = 60
        self.tgs_spec.size_max_img = 64000
        self.tgs_spec.size_max_vid = 64000

        self.webm_spec = copy.deepcopy(self.base_spec)
        self.webm_spec.set_format((".webm",))
        self.webm_spec.fps_max = 30
        self.webm_spec.animated = None if self.opt_comp.fake_vid else True

        self.opt_comp_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_merged.merge(self.base_spec)

        base_cover_spec = CompOption(
            size_max_img=128000, size_max_vid=32000, square=True, duration_max=3000
        )
        base_cover_spec.set_res(100)

        self.png_cover_spec = copy.deepcopy(base_cover_spec)
        self.png_cover_spec.set_format((".png",))
        self.png_cover_spec.animated = False

        self.tgs_cover_spec = copy.deepcopy(base_cover_spec)
        self.tgs_cover_spec.set_format((".tgs",))
        self.tgs_cover_spec.fps_min = 60
        self.tgs_cover_spec.fps_max = 60

        self.webm_cover_spec = copy.deepcopy(base_cover_spec)
        self.webm_cover_spec.set_format((".webm",))
        self.webm_cover_spec.fps_max = 30
        self.webm_cover_spec.animated = True

        self.opt_comp_cover_merged = copy.deepcopy(self.opt_comp)
        self.opt_comp_cover_merged.merge(self.base_spec)

    async def upload_pack(
        self, pack_title: str, stickers: List[Path], emoji_dict: Dict[str, str]
    ) -> Optional[str]:
        token = self.opt_cred.telegram_token.strip()
        assert token
        timeout = 10 * len(stickers)

        application = (  # type: ignore
            ApplicationBuilder()
            .token(self.opt_cred.telegram_token.strip())
            .rate_limiter(AIORateLimiter(max_retries=3))
            .connect_timeout(timeout)
            .pool_timeout(timeout)
            .read_timeout(timeout)
            .write_timeout(timeout)
            .connection_pool_size(len(stickers))
            .build()
        )

        async with application:
            bot = application.bot
            pack_short_name = (
                pack_title.replace(" ", "_") + "_by_" + bot.name.replace("@", "")
            )
            pack_short_name = re.sub(
                "[^0-9a-zA-Z]+", "_", pack_short_name
            )  # name used in url, only alphanum and underscore only

            sticker_set: Any = None
            try:
                sticker_set = await bot.get_sticker_set(
                    pack_short_name,
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30,
                    pool_timeout=30,
                )
            except TelegramError:
                pass

            if sticker_set is not None:
                question = f"Warning: Pack {pack_short_name} already exists.\n"
                question += "Delete all stickers in pack?\n"
                question += "Note: After recreating set, please wait for about 3 minutes for the set to reappear."

                self.cb.put(
                    (
                        "ask_bool",
                        (question,),
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
                        await bot.delete_sticker_set(pack_short_name)
                    except BadRequest as e:
                        self.cb.put(
                            f"Cannot delete sticker set {pack_short_name} due to {e}"
                        )
                        if str(e) == "Stickerpack_not_found":
                            self.cb.put(
                                "Hint: You might had deleted and recreated pack too quickly. Wait about 3 minutes and try again."
                            )
                        return None
                    except TelegramError as e:
                        self.cb.put(
                            f"Cannot delete sticker set {pack_short_name} due to {e}"
                        )
                        return None
                    sticker_set = None
                else:
                    self.cb.put(f"Not deleting existing pack {pack_short_name}")

            if self.opt_output.option == "telegram_emoji":
                sticker_type = Sticker.CUSTOM_EMOJI
            else:
                sticker_type = Sticker.REGULAR

            init_input_stickers: List[InputSticker] = []
            sticker_format = None
            sticker_format_prev = None
            for count, src in enumerate(stickers):
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
                    sticker_format = "animated"
                elif ext == ".webm":
                    spec_choice = self.webm_spec
                    sticker_format = "video"
                else:
                    ext = ".png"
                    spec_choice = self.png_spec
                    sticker_format = "static"

                if self.opt_output.option == "telegram_emoji":
                    spec_choice.set_res(100)

                if FormatVerify.check_file(src, spec=spec_choice):
                    with open(src, "rb") as f:
                        sticker_bytes = f.read()
                else:
                    _, _, convert_result, _ = StickerConvert.convert(
                        Path(src),
                        Path(f"bytes{ext}"),
                        self.opt_comp_merged,
                        self.cb,
                        self.cb_return,
                    )
                    sticker_bytes = cast(bytes, convert_result)

                input_sticker = InputSticker(
                    sticker=sticker_bytes,
                    emoji_list=emoji_list,
                    format=sticker_format,
                )

                if sticker_set is None:
                    if count < 50 and (
                        sticker_format_prev is None
                        or sticker_format_prev == sticker_format
                    ):
                        init_input_stickers.append(input_sticker)
                    else:
                        start_msg = f"Creating pack and bulk uploading {count} stickers with same format of {pack_short_name}"
                        finish_msg = f"Created pack and bulk uploaded {count} stickers with same format of {pack_short_name}"
                        error_msg = f"Cannot create pack and bulk upload {count} stickers with same format of {pack_short_name} due to"
                        self.cb.put(start_msg)
                        try:
                            await bot.create_new_sticker_set(
                                user_id=self.telegram_userid,
                                name=pack_short_name,
                                title=pack_title,
                                stickers=init_input_stickers,
                                sticker_type=sticker_type,
                            )
                            sticker_set = True
                            self.cb.put(finish_msg)
                        except TelegramError as e:
                            self.cb.put(f"{error_msg} {e}")
                            return None
                else:
                    try:
                        # We could use tg.start_soon() here
                        # But this would disrupt the order of stickers
                        await bot.add_sticker_to_set(
                            user_id=self.telegram_userid,
                            name=pack_short_name,
                            sticker=input_sticker,
                        )
                        self.cb.put(f"Uploaded sticker {src} of {pack_short_name}")
                    except BadRequest as e:
                        self.cb.put(
                            f"Cannot upload sticker {src} of {pack_short_name} due to {e}"
                        )
                        if str(e) == "Stickerpack_not_found":
                            self.cb.put(
                                "Hint: You might had deleted and recreated pack too quickly. Wait about 3 minutes and try again."
                            )
                    except TelegramError as e:
                        self.cb.put(
                            f"Cannot upload sticker {src} of {pack_short_name} due to {e}"
                        )

                sticker_format_prev = sticker_format

            cover_path = MetadataHandler.get_cover(self.opt_output.dir)
            if cover_path:
                thumbnail_bytes: Union[None, bytes, Path] = None
                cover_ext = Path(cover_path).suffix

                if cover_ext == ".tgs":
                    thumbnail_format = "animated"
                    cover_spec_choice = self.tgs_cover_spec
                elif cover_ext == ".webm":
                    thumbnail_format = "video"
                    cover_spec_choice = self.webm_cover_spec
                else:
                    cover_ext = ".png"
                    thumbnail_format = "static"
                    cover_spec_choice = self.png_cover_spec

                if FormatVerify.check_file(cover_path, spec=cover_spec_choice):
                    with open(cover_path, "rb") as f:
                        thumbnail_bytes = f.read()
                else:
                    _, _, thumbnail_bytes, _ = StickerConvert.convert(
                        cover_path,
                        Path(f"bytes{cover_ext}"),
                        self.opt_comp_cover_merged,
                        self.cb,
                        self.cb_return,
                    )

                try:
                    self.cb.put(
                        f"Uploading cover (thumbnail) of pack {pack_short_name}"
                    )
                    await bot.set_sticker_set_thumbnail(
                        name=pack_short_name,
                        user_id=self.telegram_userid,
                        thumbnail=thumbnail_bytes,
                        format=thumbnail_format,
                    )
                    self.cb.put(f"Uploaded cover (thumbnail) of pack {pack_short_name}")
                except TelegramError as e:
                    self.cb.put(
                        f"Cannot upload cover (thumbnail) of pack {pack_short_name} due to {e}"
                    )

            self.cb.put(f"Finish uploading {pack_short_name}")

        if self.opt_output.option == "telegram_emoji":
            result = f"https://t.me/addemoji/{pack_short_name}"
        else:
            result = f"https://t.me/addstickers/{pack_short_name}"
        return result

    def upload_stickers_telegram(self) -> List[str]:
        urls: List[str] = []

        if not (self.opt_cred.telegram_token and self.opt_cred.telegram_userid):
            self.cb.put("Token and userid required for uploading to telegram")
            return urls

        if self.opt_cred.telegram_userid.isnumeric():
            self.telegram_userid = int(self.opt_cred.telegram_userid)
        else:
            self.cb.put("Invalid userid, should contain numbers only")
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
                directory=self.opt_output.dir, default_emoji=self.opt_comp.default_emoji
            )

            self.cb.put(("msg_block", (msg_block,), None))
            if self.cb_return:
                self.cb_return.get_response()

            title, _, emoji_dict = MetadataHandler.get_metadata(
                self.opt_output.dir,
                title=self.opt_output.title,
                author=self.opt_output.author,
            )

        assert title is not None
        assert emoji_dict is not None

        if self.opt_output.option == "telegram_emoji":
            file_per_pack = 200
        else:
            file_per_pack = 120

        packs = MetadataHandler.split_sticker_packs(
            self.opt_output.dir,
            title=title,
            file_per_anim_pack=file_per_pack,
            file_per_image_pack=file_per_pack,
            separate_image_anim=not self.opt_comp.fake_vid,
        )

        for pack_title, stickers in packs.items():
            self.cb.put(f"Uploading pack {pack_title}")
            result = anyio.run(self.upload_pack, pack_title, stickers, emoji_dict)
            if result:
                self.cb.put((result))
                urls.append(result)

        return urls

    @staticmethod
    def start(
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> List[str]:
        exporter = UploadTelegram(
            opt_output,
            opt_comp,
            opt_cred,
            cb,
            cb_return,
        )
        return exporter.upload_stickers_telegram()
