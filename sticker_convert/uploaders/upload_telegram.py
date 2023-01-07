import os
import re
import tempfile

from utils.converter import StickerConvert
from utils.metadata_handler import MetadataHandler
from utils.format_verify import FormatVerify
from utils.codec_info import CodecInfo
from utils.exceptions import NoTokenException

from telegram import Bot
from telegram.error import TelegramError

class UploadTelegram:
    @staticmethod
    def upload_stickers_telegram(token, user_id, in_dir, title=None, emoji_dict=None, quality_max=90, quality_min=0, color_min=0, color_max=90, fake_vid=True, steps=20, default_emoji='😀', **kwargs):
        if token == None:
            raise NoTokenException('Token required for uploading to telegram')

        urls = []
        title, author, emoji_dict = MetadataHandler.get_metadata(in_dir, title=title, emoji_dict=emoji_dict)
        packs = MetadataHandler.split_sticker_packs(in_dir, title=title, file_per_anim_pack=50, file_per_image_pack=120, separate_image_anim=not fake_vid)

        if title == None:
            raise TypeError('title cannot be', title)
        if emoji_dict == None:
            print('emoji.txt is required for uploading telegram stickers')
            print(f'emoji.txt generated for you in {in_dir}')
            print(f'Default emoji is set to {default_emoji}.')
            print(f'If you just want to use this emoji on all stickers in this pack, run script again with --no-compress or tick the "No compression" box.')
            MetadataHandler.generate_emoji_file(dir=in_dir, default_emoji=default_emoji)
            return ['emoji.txt is required for uploading telegram stickers', f'emoji.txt generated for you in {in_dir}', f'Default emoji is set to {default_emoji}.', 'If you just want to use this emoji on all stickers in this pack, run script again with --no-compress or tick the "No compression" box.']

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

                    if FormatVerify.check_file(src, res_w_min=512, res_w_max=512, res_h_min=512, res_h_max=512, square=True, size_max=512000, animated=False if not fake_vid else None, format='.png'):
                        png_sticker = src
                    elif FormatVerify.check_file(src, res_w_min=512, res_w_max=512, res_h_min=512, res_h_max=512, fps_min=60, fps_max=60, square=True, size_max=64000, duration_max=3000, format='.tgs'):
                        tgs_sticker = src
                    elif FormatVerify.check_file(src, res_w_min=512, res_w_max=512, res_h_min=512, res_h_max=512, fps_max=30, square=True, size_max=256000, animated=True if not fake_vid else None, duration_max=3000, format='.webm'):
                        webm_sticker = src
                    else:
                        if fake_vid or CodecInfo.is_anim(src):
                            webm_sticker = os.path.join(tempdir, src_name + '.webm')
                            StickerConvert.convert_and_compress_to_size(src, webm_sticker, vid_size_max=256000, img_size_max=512000, res_w_min=512, res_w_max=512, res_h_min=512, res_h_max=512, quality_max=quality_max, quality_min=quality_min, fps_max=30, fps_min=0, color_min=color_min, color_max=color_max, duration_max=3000, steps=steps)
                        else:
                            png_sticker = os.path.join(tempdir, src_name + '.png')
                            StickerConvert.convert_and_compress_to_size(src, png_sticker, vid_size_max=256000, img_size_max=512000, res_w_min=512, res_w_max=512, res_h_min=512, res_h_max=512, quality_max=quality_max, quality_min=quality_min, color_min=color_min, color_max=color_max, steps=steps)
                    
                    try:
                        emoji = emoji_dict[src_name]
                    except KeyError:
                        print(f'Warning: Cannot find emoji for file {src_full_name}, skip uploading this file...')
                        continue
                    
                    try:
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
                    except TelegramError as e:
                        print(f'Cannot upload {name} due to {e}')

                    print('Uploaded', src)

            print(f'https://t.me/addstickers/{name}')
            urls.append(f'https://t.me/addstickers/{name}')

        return urls