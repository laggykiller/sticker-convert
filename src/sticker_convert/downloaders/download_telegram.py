#!/usr/bin/env python3
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import anyio
from telegram import Bot
from telegram.error import TelegramError

from .download_base import DownloadBase  # type: ignore
from ..utils.files.metadata_handler import MetadataHandler  # type: ignore
from ..job_option import CredOption  # type: ignore


class DownloadTelegram(DownloadBase):
    def __init__(self, *args, **kwargs):
        super(DownloadTelegram, self).__init__(*args, **kwargs)

    def download_stickers_telegram(self) -> bool:
        self.token = self.opt_cred.telegram_token
        if self.token == None:
            self.cb_msg("Download failed: Token required for downloading from telegram")
            return False

        if not ("telegram.me" in self.url or "t.me" in self.url):
            self.cb_msg("Download failed: Unrecognized URL format")
            return False
        
        self.title = Path(urlparse(self.url).path).name

        return anyio.run(self.save_stickers)

    async def save_stickers(self) -> bool:
        bot = Bot(self.token)
        async with bot:
            try:
                sticker_set = await bot.get_sticker_set(
                    self.title,
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30,
                    pool_timeout=30,
                )
            except TelegramError as e:
                self.cb_msg(
                    f"Failed to download telegram sticker set {self.title} due to: {e}"
                )
                return False

            if self.cb_bar:
                self.cb_bar(
                    set_progress_mode="determinate", steps=len(sticker_set.stickers)
                )

            emoji_dict = {}
            for num, i in enumerate(sticker_set.stickers):
                sticker = await i.get_file(
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30,
                    pool_timeout=30,
                )
                ext = Path(sticker.file_path).suffix
                f_id = str(num).zfill(3)
                f_name = f_id + ext
                f_path = Path(self.out_dir, f_name)
                await sticker.download_to_drive(
                    custom_path=f_path,
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30,
                    pool_timeout=30,
                )
                emoji_dict[f_id] = i.emoji
                self.cb_msg(f"Downloaded {f_name}")
                if self.cb_bar:
                    self.cb_bar(update_bar=True)

            if sticker_set.thumbnail:
                cover = await sticker_set.thumbnail.get_file(
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30,
                    pool_timeout=30,
                )
                cover_ext = Path(cover.file_path).suffix
                cover_name = "cover" + cover_ext
                cover_path = Path(self.out_dir, cover_name)
                await cover.download_to_drive(
                    custom_path=cover_path,
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30,
                    pool_timeout=30,
                )
                self.cb_msg(f"Downloaded {cover_name}")

        MetadataHandler.set_metadata(
            self.out_dir, title=self.title, emoji_dict=emoji_dict
        )
        return True

    @staticmethod
    def start(
        url: str,
        out_dir: str,
        opt_cred: Optional[CredOption] = None,
        cb_msg=print,
        cb_msg_block=input,
        cb_bar=None,
    ) -> bool:
        downloader = DownloadTelegram(
            url, out_dir, opt_cred, cb_msg, cb_msg_block, cb_bar
        )
        return downloader.download_stickers_telegram()
