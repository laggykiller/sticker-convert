#!/usr/bin/env python3
from pathlib import Path
from typing import Dict, Optional, Union
from urllib.parse import urlparse

import anyio
from telegram import PhotoSize, Sticker, StickerSet
from telegram.error import TelegramError
from telegram.ext import AIORateLimiter, ApplicationBuilder

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler


class DownloadTelegram(DownloadBase):
    # def __init__(self, *args: Any, **kwargs: Any) -> None:
    #     super().__init__(*args, **kwargs)

    def download_stickers_telegram(self) -> bool:
        self.token = ""

        if self.opt_cred:
            self.token = self.opt_cred.telegram_token.strip()
        if not self.token:
            self.cb.put("Download failed: Token required for downloading from telegram")
            return False

        if not ("telegram.me" in self.url or "t.me" in self.url):
            self.cb.put("Download failed: Unrecognized URL format")
            return False

        self.title = Path(urlparse(self.url).path).name

        self.emoji_dict: Dict[str, str] = {}

        return anyio.run(self.save_stickers)

    async def save_stickers(self) -> bool:
        timeout = 30
        application = (  # type: ignore
            ApplicationBuilder()
            .token(self.token)
            .rate_limiter(AIORateLimiter(max_retries=3))
            .connect_timeout(timeout)
            .pool_timeout(timeout)
            .read_timeout(timeout)
            .write_timeout(timeout)
            .connection_pool_size(20)
            .build()
        )

        async with application:
            bot = application.bot
            try:
                sticker_set: StickerSet = await bot.get_sticker_set(
                    self.title,
                    read_timeout=timeout,
                    write_timeout=timeout,
                    connect_timeout=timeout,
                    pool_timeout=timeout,
                )
            except TelegramError as e:
                self.cb.put(
                    f"Failed to download telegram sticker set {self.title} due to: {e}"
                )
                return False

            self.cb.put(
                (
                    "bar",
                    None,
                    {
                        "set_progress_mode": "determinate",
                        "steps": len(sticker_set.stickers),
                    },
                )
            )

            async def download_sticker(
                sticker: Union[PhotoSize, Sticker], f_id: str
            ) -> None:
                sticker_file = await sticker.get_file(
                    read_timeout=timeout,
                    write_timeout=timeout,
                    connect_timeout=timeout,
                    pool_timeout=timeout,
                )
                fpath = sticker_file.file_path
                assert fpath is not None
                ext = Path(fpath).suffix
                f_name = f_id + ext
                f_path = Path(self.out_dir, f_name)
                await sticker_file.download_to_drive(
                    custom_path=f_path,
                    read_timeout=timeout,
                    write_timeout=timeout,
                    connect_timeout=timeout,
                    pool_timeout=timeout,
                )
                if isinstance(sticker, Sticker) and sticker.emoji is not None:
                    self.emoji_dict[f_id] = sticker.emoji
                self.cb.put(f"Downloaded {f_name}")
                if f_id != "cover":
                    self.cb.put("update_bar")

            async with anyio.create_task_group() as tg:
                for num, sticker in enumerate(sticker_set.stickers):
                    f_id = str(num).zfill(3)
                    tg.start_soon(download_sticker, sticker, f_id)

                if sticker_set.thumbnail is not None:
                    tg.start_soon(download_sticker, sticker_set.thumbnail, "cover")

        MetadataHandler.set_metadata(
            self.out_dir, title=self.title, emoji_dict=self.emoji_dict
        )
        return True

    @staticmethod
    def start(
        url: str,
        out_dir: Path,
        opt_cred: Optional[CredOption],
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> bool:
        downloader = DownloadTelegram(url, out_dir, opt_cred, cb, cb_return)
        return downloader.download_stickers_telegram()
