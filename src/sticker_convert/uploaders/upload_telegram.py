#!/usr/bin/env python3
import os
import copy
import re

from .upload_base import UploadBase
from ..utils.converter import StickerConvert
from ..utils.metadata_handler import MetadataHandler
from ..utils.format_verify import FormatVerify
from ..utils.codec_info import CodecInfo
from ..utils.cache_store import CacheStore

import anyio
from telegram import Bot
from telegram.error import TelegramError
from mergedeep import merge

class UploadTelegram(UploadBase):
    def __init__(self, *args, **kwargs):
        super(UploadTelegram, self).__init__(*args, **kwargs)

        if not self.opt_cred.get('telegram', {}).get('token'):
            self.cb_msg('Token required for uploading to telegram')
            return False
        
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

        self.png_spec = copy.deepcopy(base_spec)
        self.png_spec['format'] = '.png'
        self.png_spec['animated'] = False

        self.tgs_spec = copy.deepcopy(base_spec)
        self.tgs_spec['format'] = '.tgs'
        self.tgs_spec['fps']['min'] = 60
        self.tgs_spec['fps']['max'] = 60
        self.tgs_spec['size_max']['vid'] = 64000

        self.webm_spec = copy.deepcopy(base_spec)
        self.webm_spec['format'] = '.webm'
        self.webm_spec['fps']['max'] = 30
        self.webm_spec['animated'] = None if self.fake_vid else True

        self.opt_comp_merged = merge({}, self.opt_comp, base_spec)
    
    async def upload_pack(self, pack_title, stickers, emoji_dict):        
        bot = Bot(self.opt_cred['telegram']['token'])

        async with bot:
            pack_short_name = pack_title.replace(' ', '_') + '_by_' + bot.name.replace('@', '')
            pack_short_name = re.sub('[^0-9a-zA-Z]+', '_', pack_short_name) # name used in url, only alphanum and underscore only

            try:
                pack_exists = True if await bot.get_sticker_set(pack_short_name) else False
            except TelegramError:
                pack_exists = False

            with CacheStore.get_cache_store(path=self.opt_comp.get('cache_dir')) as tempdir:
                for src in stickers:
                    self.cb_msg(f'Verifying {src} for uploading to telegram')

                    src_full_name = os.path.split(src)[-1]
                    src_name = os.path.splitext(src_full_name)[0]
                    ext = os.path.splitext(src_full_name)[-1]

                    emoji = emoji_dict.get(src_name, None)
                    if not emoji:
                        self.cb_msg(f'Warning: Cannot find emoji for file {src_full_name}, skip uploading this file...')
                        continue

                    if ext == '.tgs':
                        spec_choice = self.tgs_spec
                    elif ext == '.webm':
                        spec_choice = self.webm_spec
                    else:
                        spec_choice = self.png_spec

                    if FormatVerify.check_file(src, spec=spec_choice):
                        dst = src
                    else:
                        if self.fake_vid or CodecInfo.is_anim(src):
                            dst = os.path.join(tempdir, src_name + '.webm')
                            ext = '.webm'
                            StickerConvert(src, src, self.opt_comp_merged, self.cb_msg).convert()
                        else:
                            dst = os.path.join(tempdir, src_name + '.png')
                            ext = '.png'
                            StickerConvert(src, src, self.opt_comp_merged, self.cb_msg).convert()
                    
                    try:
                        if pack_exists == False:
                            await bot.create_new_sticker_set(
                                self.opt_cred['telegram']['userid'], pack_short_name, pack_title, emoji,
                                png_sticker=open(dst, 'rb') if ext in ('.png', '.apng') else None,
                                tgs_sticker=open(dst, 'rb') if ext == '.tgs' else None,
                                webm_sticker=open(dst, 'rb') if ext == '.webm' else None)
                            pack_exists = True
                        else:
                            await bot.add_sticker_to_set(
                                self.opt_cred['telegram']['userid'], pack_short_name, emoji,
                                png_sticker=open(dst, 'rb') if ext in ('.png', '.apng') else None,
                                tgs_sticker=open(dst, 'rb') if ext == '.tgs' else None,
                                webm_sticker=open(dst, 'rb') if ext == '.webm' else None)
                    except TelegramError as e:
                        self.cb_msg(f'Cannot upload sticker {dst} in {pack_short_name} due to {e}')
                        continue

                    self.cb_msg(f'Uploaded {src}')
        
        result = f'https://t.me/addstickers/{pack_short_name}'
        return result

    def upload_stickers_telegram(self):
        urls = []
        title, author, emoji_dict = MetadataHandler.get_metadata(self.in_dir, title=self.opt_output.get('title'), author=self.opt_output.get('author'))
        if title == None:
            raise TypeError('title cannot be', title)
        if emoji_dict == None:
            msg_block = 'emoji.txt is required for uploading signal stickers\n'
            msg_block += f'emoji.txt generated for you in {self.in_dir}\n'
            msg_block += f'Default emoji is set to {self.opt_comp.get("default_emoji")}.\n'
            msg_block += f'Please edit emoji.txt now, then continue'
            MetadataHandler.generate_emoji_file(dir=self.in_dir, default_emoji=self.opt_comp.get("default_emoji"))

            self.cb_msg_block(msg_block)

            title, author, emoji_dict = MetadataHandler.get_metadata(self.in_dir, title=self.opt_output.get('title'), author=self.opt_output.get('author'))

        packs = MetadataHandler.split_sticker_packs(self.in_dir, title=title, file_per_anim_pack=50, file_per_image_pack=120, separate_image_anim=not self.fake_vid)
        for pack_title, stickers in packs.items():
            result = anyio.run(self.upload_pack, pack_title, stickers, emoji_dict)
            self.cb_msg(result)
            urls.append(result)

        return urls
    
    @staticmethod
    def start(opt_output, opt_comp, opt_cred, cb_msg=print, cb_msg_block=input, cb_bar=None, out_dir=None, **kwargs):
        exporter = UploadTelegram(opt_output, opt_comp, opt_cred, cb_msg, cb_msg_block, cb_bar, out_dir)
        return exporter.upload_stickers_telegram()