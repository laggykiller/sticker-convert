import os
import anyio
from signalstickers_client import StickersClient
from utils.metadata_handler import MetadataHandler

class DownloadSignal:
    @staticmethod
    async def download_stickers_signal_async(url, out_dir):
        async def save_sticker(sticker):
            async with await anyio.open_file(os.path.join(out_dir, f'{sticker.id.zfill(3)}.webp'), "wb",) as f:
                await f.write(sticker.image_data)

        pack_id = url.split('#pack_id=')[1].split('&pack_key=')[0]
        pack_key = url.split('&pack_key=')[1]
        emoji_dict = {}

        async with StickersClient() as client:
            pack = await client.get_pack(pack_id, pack_key)

        async with anyio.create_task_group() as tg:
            for sticker in pack.stickers:
                await tg.spawn(save_sticker, sticker)
                emoji_dict[sticker.id] = sticker.emoji
                print('Downloaded', f'{sticker.id.zfill(3)}.webp')
        
        MetadataHandler.set_metadata(out_dir, title=pack.title, author=pack.author, emoji_dict=emoji_dict)

    @staticmethod
    def download_stickers_signal(url, out_dir):
        anyio.run(DownloadSignal.download_stickers_signal_async, url, out_dir)