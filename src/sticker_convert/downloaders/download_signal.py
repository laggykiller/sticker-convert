#!/usr/bin/env python3
import os
from pathlib import Path
from typing import Optional, Union
from multiprocessing.managers import BaseProxy

import anyio
from signalstickers_client import StickersClient  # type: ignore
from signalstickers_client.errors import SignalException  # type: ignore
from signalstickers_client.models import StickerPack  # type: ignore

from sticker_convert.downloaders.download_base import DownloadBase  # type: ignore
from sticker_convert.utils.callback import Callback, CallbackReturn  # type: ignore
from sticker_convert.job_option import CredOption  # type: ignore
from sticker_convert.utils.files.metadata_handler import MetadataHandler  # type: ignore
from sticker_convert.utils.media.codec_info import CodecInfo  # type: ignore


class DownloadSignal(DownloadBase):
    def __init__(self, *args, **kwargs):
        super(DownloadSignal, self).__init__(*args, **kwargs)

    @staticmethod
    async def get_pack(pack_id: str, pack_key: str) -> StickerPack:
        async with StickersClient() as client:
            pack = await client.get_pack(pack_id, pack_key)

        return pack

    def save_stickers(self, pack: StickerPack):
        self.cb.put(("bar", None, {
            "set_progress_mode": "determinate",
            "steps": len(pack.stickers)
        }))

        emoji_dict = {}
        for sticker in pack.stickers:
            f_id = str(sticker.id).zfill(3)
            f_path = Path(self.out_dir, f_id)
            with open(f_path, "wb") as f:
                f.write(sticker.image_data)

            emoji_dict[f_id] = sticker.emoji

            codec = CodecInfo.get_file_codec(f_path)
            if codec == "":
                msg = f"Warning: Downloaded {f_path} but cannot get file codec"
                self.cb.put(msg)
            else:
                f_path_new = f"{f_path}.{codec}"
                os.rename(f_path, f_path_new)
                msg = f"Downloaded {f_id}.{codec}"
                self.cb.put(msg)

            self.cb.put("update_bar")

        MetadataHandler.set_metadata(
            self.out_dir, title=pack.title, author=pack.author, emoji_dict=emoji_dict
        )

    def download_stickers_signal(self) -> bool:
        if "signal.art" not in self.url:
            self.cb.put("Download failed: Unrecognized URL format")
            return False

        pack_id = self.url.split("#pack_id=")[1].split("&pack_key=")[0]
        pack_key = self.url.split("&pack_key=")[1]

        try:
            pack = anyio.run(DownloadSignal.get_pack, pack_id, pack_key)
        except SignalException as e:
            self.cb.put(f"Failed to download pack due to {repr(e)}")
        self.save_stickers(pack)

        return True

    @staticmethod
    def start(
        url: str,
        out_dir: str,
        opt_cred: Optional[CredOption] = None,
        cb: Union[BaseProxy, Callback, None] = None,
        cb_return: Optional[CallbackReturn] = None,
    ) -> bool:
        downloader = DownloadSignal(
            url, out_dir, opt_cred, cb, cb_return
        )
        return downloader.download_stickers_signal()
