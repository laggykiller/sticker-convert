import os
import re
from telegram import Bot
from telegram.error import TelegramError
from utils.sticker_convert import StickerConvert
from utils.metadata_handler import MetadataHandler
from utils.format_verify import FormatVerify
from utils.exceptions import NoTokenException
import tempfile

class UploadTelegram:
    @staticmethod
    def upload_stickers_telegram(token, user_id, in_dir, title=None, emoji_dict=None, quality_max=90, quality_min=0, steps=20, default_emoji='😀', **kwargs):
        if token == None:
            raise NoTokenException('Token required for uploading to telegram')

        urls = []
        title, author, emoji_dict = MetadataHandler.get_metadata(in_dir, title=title, emoji_dict=emoji_dict)
        packs = MetadataHandler.split_sticker_packs(in_dir, title=title, file_per_anim_pack=50, file_per_image_pack=120, separate_image_anim=True)

        if title == None:
            raise TypeError('title cannot be', title)
        if emoji_dict == None:
            print('emoji.txt is required for uploading telegram stickers')
            print(f'emoji.txt generated for you in {in_dir}')
            print(f'Default emoji is set to {default_emoji}. If you just want to use this emoji on all stickers in this pack, run script again')
            MetadataHandler.generate_emoji_file(dir=in_dir, default_emoji=default_emoji)
            return ['emoji.txt is required for uploading telegram stickers', f'emoji.txt generated for you in {in_dir}', f'Default emoji is set to {default_emoji}. If you just want to use this emoji on all stickers in this pack, run script again']

        bot= Bot(token)

        for pack_title, stickers in packs.items():
            png_sticker = None
            tgs_sticker = None
            webm_sticker = None
            emoji = None

            name = pack_title.replace(' ', '_') + '_by_' + bot.name.replace('@', '')
            name = re.sub('[^0-9a-zA-Z]+', '_', name) # name used in url, only alphanum and underscore only

            try:
                pack_exists = True if bot.getStickerSet(name) else False
            except TelegramError:
                pack_exists = False

            with tempfile.TemporaryDirectory() as tempdir:
                for src in stickers:
                    print('Verifying', src, 'for uploading to telegram')

                    src_full_name = os.path.split(src)[-1]
                    src_name = os.path.splitext(src_full_name)[0]

                    png_sticker = None
                    tgs_sticker = None
                    webm_sticker = None

                    if FormatVerify.check_file(src, res_min=512, res_max=512, square=True, size_max=512000, animated=False, format='.png'):
                        png_sticker = src
                    elif FormatVerify.check_file(src, size_max=64000, format='.tgs'):
                        tgs_sticker = src
                    elif FormatVerify.check_file(src, res_min=512, res_max=512, fps_max=30, square=True, size_max=256000, animated=True, format='.webm'):
                        webm_sticker = src
                    else:
                        if FormatVerify.is_anim(src):
                            webm_sticker = os.path.join(tempdir, src_name + '.webm')
                            StickerConvert.convert_and_compress_to_size(src, webm_sticker, res_min=512, res_max=512, quality_max=quality_max, quality_min=quality_min, fps_max=30, fps_min=0, steps=steps)
                        else:
                            png_sticker = os.path.join(tempdir, src_name + '.png')
                            StickerConvert.convert_and_compress_to_size(src, png_sticker, res_min=512, res_max=512, quality_max=quality_max, quality_min=quality_min, steps=steps)
                    
                    try:
                        emoji = emoji_dict[src_name]
                    except KeyError:
                        print(f'Warning: Cannot find emoji for file {src_full_name}, skip uploading this file...')
                        continue
                    
                    if pack_exists == False:
                        bot.create_new_sticker_set(
                            user_id, name, pack_title, emoji,
                            png_sticker=open(png_sticker, 'rb') if png_sticker else None,
                            tgs_sticker=open(tgs_sticker, 'rb') if tgs_sticker else None,
                            webm_sticker=open(webm_sticker, 'rb') if webm_sticker else None)
                        pack_exists = True
                    else:
                        bot.add_sticker_to_set(
                            user_id, name, emoji,
                            png_sticker=open(png_sticker, 'rb') if png_sticker else None,
                            tgs_sticker=open(tgs_sticker, 'rb') if tgs_sticker else None,
                            webm_sticker=open(webm_sticker, 'rb') if webm_sticker else None)
                    print('Uploaded', src)

            print(f'https://t.me/addstickers/{name}')
            urls.append(f'https://t.me/addstickers/{name}')

        return urls