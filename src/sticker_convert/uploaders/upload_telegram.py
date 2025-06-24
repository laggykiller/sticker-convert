#!/usr/bin/env python3
import copy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import anyio
from telegram import Sticker

from sticker_convert.converter import StickerConvert
from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.uploaders.upload_base import UploadBase
from sticker_convert.utils.auth.telegram_api import BotAPI, TelegramAPI, TelegramSticker, TelethonAPI
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.emoji import extract_emojis
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.media.codec_info import CodecInfo
from sticker_convert.utils.media.format_verify import FormatVerify


class UploadTelegram(UploadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.base_spec.size_max_img = 512000
        self.base_spec.size_max_vid = 256000
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
            size_max_img=128000, size_max_vid=32000, duration_max=3000
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
    ) -> Tuple[Optional[str], int, int]:
        tg_api: TelegramAPI
        if self.opt_output.option.endswith("telethon"):
            tg_api = TelethonAPI()
        else:
            tg_api = BotAPI()

        is_emoji = False
        if "emoji" in self.opt_output.option:
            is_emoji = True

        success = await tg_api.setup(self.opt_cred, True, self.cb, self.cb_return)
        if success is False:
            self.cb.put("Download failed: Invalid credentials")
            return None, len(stickers), 0

        pack_short_name = await tg_api.set_upload_pack_short_name(pack_title)
        await tg_api.set_upload_pack_type(is_emoji)
        pack_exist = await tg_api.check_pack_exist()
        if pack_exist:
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
                await tg_api.pack_del()
                pack_exist = False
            else:
                self.cb.put(f"Not deleting existing pack {pack_short_name}")

        if self.opt_output.option == "telegram_emoji":
            sticker_type = Sticker.CUSTOM_EMOJI
        else:
            sticker_type = Sticker.REGULAR

        stickers_list: List[TelegramSticker] = []
        sticker_format = None
        for src in stickers:
            self.cb.put(f"Verifying {src} for uploading to telegram")

            emoji = extract_emojis(emoji_dict.get(Path(src).stem, ""))
            if emoji == "":
                self.cb.put(
                    f"Warning: Cannot find emoji for file {Path(src).name}, using default emoji..."
                )
                emoji_list = [self.opt_comp.default_emoji]

            if len(emoji) > 20:
                self.cb.put(
                    f"Warning: {len(emoji)} emoji for file {Path(src).name}, exceeding limit of 20, keep first 20 only..."
                )
            emoji_list = [*emoji][:20]

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

            file_info = CodecInfo(src)
            check_file_result = (
                FormatVerify.check_file_fps(
                    src, fps=spec_choice.get_fps(), file_info=file_info
                )
                and FormatVerify.check_file_duration(
                    src, duration=spec_choice.get_duration(), file_info=file_info
                )
                and FormatVerify.check_file_size(
                    src, size=spec_choice.get_size_max(), file_info=file_info
                )
                and FormatVerify.check_format(
                    src, fmt=spec_choice.get_format(), file_info=file_info
                )
            )
            if self.opt_output.option == "telegram":
                if sticker_format == "animated":
                    check_file_result = (
                        check_file_result
                        and file_info.res[0] == 512
                        and file_info.res[1] == 512
                    )
                else:
                    # For video and static stickers (Not animated)
                    # Allow file with one of the dimension = 512 but another <512
                    # https://core.telegram.org/stickers#video-requirements
                    check_file_result = check_file_result and (
                        file_info.res[0] == 512 or file_info.res[1] == 512
                    )
                    check_file_result = check_file_result and (
                        file_info.res[0] <= 512 and file_info.res[1] <= 512
                    )
            else:
                # telegram_emoji
                check_file_result = (
                    check_file_result
                    and file_info.res[0] == 100
                    and file_info.res[1] == 100
                )

            if sticker_format == "static":
                # It is important to check if webp and png are static only
                check_file_result = check_file_result and FormatVerify.check_animated(
                    src, animated=spec_choice.animated, file_info=file_info
                )

            if check_file_result:
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

            stickers_list.append((src, sticker_bytes, emoji_list, sticker_format))

        if pack_exist is False:
            stickers_total, stickers_ok = await tg_api.pack_new(
                stickers_list, sticker_type
            )
            pack_exist = True
        else:
            stickers_total, stickers_ok = await tg_api.pack_add(
                stickers_list, sticker_type
            )

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
                _, _, thumbnail_bytes, _ = cast(
                    Tuple[Any, Any, bytes, Any],
                    StickerConvert.convert(
                        cover_path,
                        Path(f"bytes{cover_ext}"),
                        self.opt_comp_cover_merged,
                        self.cb,
                        self.cb_return,
                    ),
                )

            await tg_api.pack_thumbnail(
                (cover_path, thumbnail_bytes, [], thumbnail_format)
            )

        self.cb.put(f"Finish uploading {pack_short_name}")
        await tg_api.exit()
        return await tg_api.get_pack_url(), stickers_total, stickers_ok

    def upload_stickers_telegram(self) -> Tuple[int, int, List[str]]:
        urls: List[str] = []

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

        stickers_total = 0
        stickers_ok = 0
        for pack_title, stickers in packs.items():
            self.cb.put(f"Uploading pack {pack_title}")
            result, stickers_total_pack, stickers_ok_pack = anyio.run(
                self.upload_pack, pack_title, stickers, emoji_dict
            )
            if result:
                self.cb.put((result))
                urls.append(result)
            stickers_total += stickers_total_pack
            stickers_ok += stickers_ok_pack

        return stickers_ok, stickers_total, urls

    @staticmethod
    def start(
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int, List[str]]:
        exporter = UploadTelegram(
            opt_output,
            opt_comp,
            opt_cred,
            cb,
            cb_return,
        )
        return exporter.upload_stickers_telegram()
