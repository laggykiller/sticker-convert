#!/usr/bin/env python3
import os
import copy
import re

from utils.converter import StickerConvert
from utils.metadata_handler import MetadataHandler
from utils.format_verify import FormatVerify
from utils.codec_info import CodecInfo
from utils.cache_store import CacheStore

from telegram import Bot
from telegram.error import TelegramError
from mergedeep import merge

class UploadTelegram:
    @staticmethod
    def upload_stickers_telegram(opt_output, opt_comp, opt_cred, cb_msg=print, cb_bar=None, out_dir=None, **kwargs):
        if not opt_cred.get('telegram', {}).get('token'):
            msg = 'Token required for uploading to telegram'
            return [msg]
        
        fake_vid = opt_comp.get('fake_vid', False)
        in_dir = opt_output['dir']
        if not out_dir:
            out_dir = opt_output['dir']
        
        base_spec = {
            "size_max": {
                "img": 512000,
                "vid": 256000
            },
            'res': {
                'w': {
                    'min': 512,
                    'max': 512
                },
                'h': {
                    'min': 512,
                    'max': 512
                }
            },
            'square': True,
            'duration': {
                'max': 3000
            },
            'fps': {}
        }

        png_spec = copy.deepcopy(base_spec)
        png_spec['format'] = '.png'
        png_spec['animated'] = False if not fake_vid else None

        tgs_spec = copy.deepcopy(base_spec)
        tgs_spec['format'] = '.tgs'
        tgs_spec['fps']['min'] = 60
        tgs_spec['fps']['max'] = 60
        tgs_spec['size_max']['vid'] = 64000

        webm_spec = copy.deepcopy(base_spec)
        webm_spec['format'] = '.webm'
        webm_spec['fps']['max'] = 30
        webm_spec['animated'] = True if not fake_vid else None

        opt_comp_merged = merge({}, opt_comp, base_spec)

        urls = []
        title, author, emoji_dict = MetadataHandler.get_metadata(in_dir, title=opt_output.get('title'), author=opt_output.get('author'))
        if title == None:
            raise TypeError('title cannot be', title)
        if emoji_dict == None:
            msg = 'emoji.txt is required for uploading signal stickers\n'
            msg += f'emoji.txt generated for you in {in_dir}\n'
            msg += f'Default emoji is set to {opt_comp.get("default_emoji")}.\n'
            msg += f'If you just want to use this emoji on all stickers in this pack,\n'
            msg += f'run script again with --no-compress or tick the "No compression" box.'
            MetadataHandler.generate_emoji_file(dir=in_dir, default_emoji=opt_comp.get("default_emoji"))
            return [msg]

        bot = Bot(opt_cred['telegram']['token'])
        userid = opt_cred['telegram']['userid']

        packs = MetadataHandler.split_sticker_packs(in_dir, title=title, file_per_anim_pack=50, file_per_image_pack=120, separate_image_anim=not fake_vid)
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

            with CacheStore.get_cache_store(path=opt_comp.get('cache_dir')) as tempdir:
                for src in stickers:
                    cb_msg(f'Verifying {src} for uploading to telegram')

                    src_full_name = os.path.split(src)[-1]
                    src_name = os.path.splitext(src_full_name)[0]

                    png_sticker = None
                    tgs_sticker = None
                    webm_sticker = None

                    if FormatVerify.check_file(src, spec=png_spec):
                        png_sticker = src
                    elif FormatVerify.check_file(src, spec=tgs_spec):
                        tgs_sticker = src
                    elif FormatVerify.check_file(src, spec=webm_spec):
                        webm_sticker = src
                    else:
                        if fake_vid or CodecInfo.is_anim(src):
                            webm_sticker = os.path.join(tempdir, src_name + '.webm')
                            StickerConvert.convert_and_compress_to_size(src, webm_sticker, opt_comp_merged, cb_msg)
                        else:
                            png_sticker = os.path.join(tempdir, src_name + '.png')
                            StickerConvert.convert_and_compress_to_size(src, png_sticker, opt_comp_merged, cb_msg)
                    
                    try:
                        emoji = emoji_dict[src_name]
                    except KeyError:
                        cb_msg(f'Warning: Cannot find emoji for file {src_full_name}, skip uploading this file...')
                        continue
                    
                    try:
                        if pack_exists == False:
                            bot.create_new_sticker_set(
                                userid, name, pack_title, emoji,
                                png_sticker=open(png_sticker, 'rb') if png_sticker else None,
                                tgs_sticker=open(tgs_sticker, 'rb') if tgs_sticker else None,
                                webm_sticker=open(webm_sticker, 'rb') if webm_sticker else None)
                            pack_exists = True
                        else:
                            bot.add_sticker_to_set(
                                userid, name, emoji,
                                png_sticker=open(png_sticker, 'rb') if png_sticker else None,
                                tgs_sticker=open(tgs_sticker, 'rb') if tgs_sticker else None,
                                webm_sticker=open(webm_sticker, 'rb') if webm_sticker else None)
                    except TelegramError as e:
                        cb_msg(f'Cannot upload {name} due to {e}')

                    cb_msg(f'Uploaded {src}')

            result = f'https://t.me/addstickers/{name}'
            cb_msg(result)
            urls.append(result)

        return urls