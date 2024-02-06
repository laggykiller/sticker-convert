#!/usr/bin/env python3
from pathlib import Path
from queue import Queue
from typing import Optional, Union, Any
from urllib.parse import urlparse

import anyio
from telegram import Bot
from telegram.error import TelegramError

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption
from sticker_convert.utils.callback import Callback, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler


class DownloadTelegram(DownloadBase):
    def __init__(self, *args: Any, **kwargs: Any):
        super(DownloadTelegram, self).__init__(*args, **kwargs)

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

        return anyio.run(self.save_stickers)

    async def save_stickers(self) -> bool:
        bot = Bot(self.token)
        async with bot:
            try:
                sticker_set = await bot.get_sticker_set(
                    self.title,  # type: ignore
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30,
                    pool_timeout=30,
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
                self.cb.put(f"Downloaded {f_name}")
                self.cb.put("update_bar")

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
                self.cb.put(f"Downloaded {cover_name}")

        MetadataHandler.set_metadata(
            self.out_dir, title=self.title, emoji_dict=emoji_dict
        )
        return True

    @staticmethod
    def start(
        url: str,
        out_dir: Path,
        opt_cred: Optional[CredOption],
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
    ) -> bool:
        downloader = DownloadTelegram(url, out_dir, opt_cred, cb, cb_return)
        return downloader.download_stickers_telegram()
