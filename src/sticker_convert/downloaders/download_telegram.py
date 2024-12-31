#!/usr/bin/env python3
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import anyio

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption, InputOption
from sticker_convert.utils.auth.telegram_api import BotAPI, TelegramAPI, TelethonAPI
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler


class DownloadTelegram(DownloadBase):
    # def __init__(self, *args: Any, **kwargs: Any) -> None:
    #     super().__init__(*args, **kwargs)

    def download_stickers_telegram(self) -> Tuple[int, int]:
        if not ("telegram.me" in self.url or "t.me" in self.url):
            self.cb.put("Download failed: Unrecognized URL format")
            return 0, 0

        return anyio.run(self.save_stickers)

    async def save_stickers(self) -> Tuple[int, int]:
        tg_api: TelegramAPI
        if self.input_option.endswith("telethon"):
            tg_api = TelethonAPI()
        else:
            tg_api = BotAPI()

        if self.opt_cred is None:
            self.cb.put("Download failed: No credentials")
            return 0, 0

        success = await tg_api.setup(self.opt_cred, False, self.cb, self.cb_return)
        if success is False:
            self.cb.put("Download failed: Invalid credentials")
            return 0, 0

        title = Path(urlparse(self.url).path).name
        results, emoji_dict = await tg_api.pack_dl(title, self.out_dir)
        MetadataHandler.set_metadata(self.out_dir, title=title, emoji_dict=emoji_dict)
        return sum(results.values()), len(results)

    @staticmethod
    def start(
        opt_input: InputOption,
        opt_cred: Optional[CredOption],
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int]:
        downloader = DownloadTelegram(opt_input, opt_cred, cb, cb_return)
        return downloader.download_stickers_telegram()
