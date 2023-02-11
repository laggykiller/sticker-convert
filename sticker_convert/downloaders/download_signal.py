#!/usr/bin/env python3
import os
import anyio
from signalstickers_client import StickersClient

from utils.metadata_handler import MetadataHandler

class DownloadSignal:
    @staticmethod
    async def download_stickers_signal_async(url, out_dir, opt_cred=None, cb_msg=print, cb_bar=None):
        async def save_sticker(sticker):
            f_id = str(sticker.id).zfill(3)
            async with await anyio.open_file(os.path.join(out_dir, f'{f_id}.webp'), "wb",) as f:
                await f.write(sticker.image_data)

        pack_id = url.split('#pack_id=')[1].split('&pack_key=')[0]
        pack_key = url.split('&pack_key=')[1]
        emoji_dict = {}

        async with StickersClient() as client:
            pack = await client.get_pack(pack_id, pack_key)

        if cb_bar:
            cb_bar(set_progress_mode='determinate', steps=len(pack.stickers))

        async with anyio.create_task_group() as tg:
            for sticker in pack.stickers:
                await tg.spawn(save_sticker, sticker)
                f_id = str(sticker.id).zfill(3)
                emoji_dict[f_id] = sticker.emoji
                
                cb_msg(f'Downloaded {f_id}.webp')
                if cb_bar:
                    cb_bar(update_bar=True)
        
        MetadataHandler.set_metadata(out_dir, title=pack.title, author=pack.author, emoji_dict=emoji_dict)

        return True

    @staticmethod
    def download_stickers_signal(url, out_dir, opt_cred=None, cb_msg=print, cb_bar=None):
        anyio.run(DownloadSignal.download_stickers_signal_async, url, out_dir, opt_cred, cb_msg, cb_bar)