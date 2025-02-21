#!/usr/bin/env python3
from pathlib import Path
from typing import Dict, Optional, Tuple

import anyio
from signalstickers_client.errors import SignalException
from signalstickers_client.models import StickerPack
from signalstickers_client.stickersclient import StickersClient

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption, InputOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.media.codec_info import CodecInfo


class DownloadSignal(DownloadBase):
    # def __init__(self, *args: Any, **kwargs: Any) -> None:
    #     super().__init__(*args, **kwargs)

    @staticmethod
    async def get_pack(pack_id: str, pack_key: str) -> StickerPack:
        async with StickersClient() as client:
            pack = await client.get_pack(pack_id, pack_key)

        return pack

    def save_stickers(self, pack: StickerPack) -> None:
        self.cb.put(
            (
                "bar",
                None,
                {
                    "set_progress_mode": "determinate",
                    "steps": len(pack.stickers),
                },
            )
        )

        emoji_dict: Dict[str, str] = {}
        for sticker in pack.stickers:
            f_id = str(sticker.id).zfill(3)
            f_path = Path(self.out_dir, f_id)
            with open(f_path, "wb") as f:
                f.write(sticker.image_data)  # type: ignore

            emoji_dict[f_id] = sticker.emoji  # type: ignore

            codec = CodecInfo.get_file_codec(f_path)
            if codec == "":
                msg = f"Warning: Downloaded {f_path} but cannot get file codec"
                self.cb.put(msg)
            else:
                f_path_new = Path(f"{f_path}.{codec}")
                f_path.rename(f_path_new)
                msg = f"Downloaded {f_id}.{codec}"
                self.cb.put(msg)

            self.cb.put("update_bar")

        if pack.cover is not None and pack.cover.image_data is not None:
            cover_path = Path(self.out_dir, "cover")
            with open(cover_path, "wb") as f:
                f.write(pack.cover.image_data)

            cover_codec = CodecInfo.get_file_codec(cover_path)
            if cover_codec == "":
                cover_codec = "png"
            cover_path_new = Path(self.out_dir, f"cover.{cover_codec}")
            cover_path.rename(cover_path_new)
            self.cb.put(f"Downloaded cover.{cover_codec}")

        MetadataHandler.set_metadata(
            self.out_dir, title=pack.title, author=pack.author, emoji_dict=emoji_dict
        )

    def download_stickers_signal(self) -> Tuple[int, int]:
        if "signal.art" not in self.url and not self.url.startswith(
            "sgnl://addstickers/"
        ):
            self.cb.put("Download failed: Unrecognized URL format")
            return 0, 0

        pack_id = self.url.split("pack_id=")[1].split("&pack_key=")[0]
        pack_key = self.url.split("&pack_key=")[1]

        try:
            pack = anyio.run(DownloadSignal.get_pack, pack_id, pack_key)
        except SignalException as e:
            self.cb.put(f"Failed to download pack due to {repr(e)}")
            return 0, 0

        self.save_stickers(pack)

        return len(pack.stickers), len(pack.stickers)

    @staticmethod
    def start(
        opt_input: InputOption,
        opt_cred: Optional[CredOption],
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int]:
        downloader = DownloadSignal(opt_input, opt_cred, cb, cb_return)
        return downloader.download_stickers_signal()
