#!/usr/bin/env python3
import os
import anyio
from signalstickers_client import StickersClient

from utils.metadata_handler import MetadataHandler
from utils.codec_info import CodecInfo

class DownloadSignal:
    @staticmethod
    async def download_stickers_signal_async(url, out_dir, opt_cred=None, cb_msg=print, cb_bar=None):
        pack_id = url.split('#pack_id=')[1].split('&pack_key=')[0]
        pack_key = url.split('&pack_key=')[1]
        emoji_dict = {}

        async with StickersClient() as client:
            pack = await client.get_pack(pack_id, pack_key)

        if cb_bar:
            cb_bar(set_progress_mode='determinate', steps=len(pack.stickers))

        for sticker in pack.stickers:
            f_id = str(sticker.id).zfill(3)
            f_path = os.path.join(out_dir, f'{f_id}')
            with open(f_path, "wb",) as f:
                f.write(sticker.image_data)

            emoji_dict[f_id] = sticker.emoji

            codec = CodecInfo.get_file_codec(f_path)
            if 'apng' in codec:
                f_path_new = f_path + '.apng'
            elif 'png' in codec:
                f_path_new = f_path + '.png'
            elif 'webp' in codec:
                f_path_new = f_path + '.webp'
            else:
                cb_msg(f'Unknown codec {codec}, defaulting to webp')
                codec = 'webp'
                f_path_new = f_path + '.webp'
            
            os.rename(f_path, f_path_new)
            
            cb_msg(f'Downloaded {f_id}.{codec}')
            if cb_bar:
                cb_bar(update_bar=True)
        
        MetadataHandler.set_metadata(out_dir, title=pack.title, author=pack.author, emoji_dict=emoji_dict)

        return True
    
    @staticmethod
    def download_stickers_signal(url, out_dir, opt_cred=None, cb_msg=print, cb_bar=None):
        anyio.run(DownloadSignal.download_stickers_signal_async, url, out_dir, opt_cred, cb_msg, cb_bar)