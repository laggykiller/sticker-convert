#!/usr/bin/env python3
import shutil
import os
import copy

from .upload_base import UploadBase
from utils.converter import StickerConvert
from utils.format_verify import FormatVerify
from utils.metadata_handler import MetadataHandler
from utils.codec_info import CodecInfo
from utils.run_bin import RunBin
from utils.cache_store import CacheStore

from mergedeep import merge

class CompressWastickers(UploadBase):
    def __init__(self, *args, **kwargs):
        super(CompressWastickers, self).__init__(*args, **kwargs)
        base_spec = {
            'size_max': {
                "img": 100000,
                "vid": 500000
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
            'duration': {
                'min': 8,
                'max': 10000
            },
            'format': '.webp',
            'square': True
        }

        self.spec_cover = {
            "size_max": {
                "img": 50000,
                "vid": 50000
            },
            "res": {
                "w": {
                    "min": 96,
                    "max": 96
                },
                "h": {
                    "min": 96,
                    "max": 96
                }
            }
        }

        self.webp_spec = copy.deepcopy(base_spec)
        self.webp_spec['format'] = '.webp'
        self.webp_spec['animated'] = None if self.fake_vid else True

        self.png_spec = copy.deepcopy(base_spec)
        self.png_spec['format'] = '.png'
        self.png_spec['animated'] = False

        self.opt_comp_merged = merge({}, self.opt_comp, base_spec)

    def compress_wastickers(self):
        urls = []
        title, author, emoji_dict = MetadataHandler.get_metadata(self.in_dir, title=self.opt_output.get('title'), author=self.opt_output.get('author'))
        packs = MetadataHandler.split_sticker_packs(self.in_dir, title=title, file_per_pack=30, separate_image_anim=not self.fake_vid)

        for pack_title, stickers in packs.items():
            num = 0 # Originally the Sticker Maker application name the files with int(time.time())
            with CacheStore.get_cache_store(path=self.opt_comp.get('cache_dir')) as tempdir:
                for src in stickers:
                    self.cb_msg(f'Verifying {src} for compressing into .wastickers')

                    if self.fake_vid or CodecInfo.is_anim(src):
                        ext = '.webp'
                    else:
                        ext = '.png'

                    dst = os.path.join(tempdir, str(num) + ext)
                    num += 1

                    if FormatVerify.check_file(src, spec=self.webp_spec) or FormatVerify.check_file(src, spec=self.png_spec):
                        shutil.copy(src, dst)
                    else:
                        StickerConvert.convert_and_compress_to_size(src, dst, self.opt_comp_merged, self.cb_msg)

                out_f = os.path.join(self.out_dir, FormatVerify.sanitize_filename(pack_title + '.wastickers'))

                self.add_metadata(tempdir, pack_title, author)
                RunBin.run_cmd(cmd_list=['zip', '-jr', out_f, tempdir], silence=True)

            self.cb_msg(out_f)
            urls.append(out_f)
        
        return urls

    def add_metadata(self, pack_dir, title, author):
        opt_comp_merged = merge({}, self.opt_comp, self.spec_cover)

        cover_path = os.path.join(pack_dir, '100.png')
        if 'cover.png' in os.listdir(self.in_dir):
            if FormatVerify.check_file(cover_path, spec=self.spec_cover):
                shutil.copy(os.path.join(self.in_dir, 'cover.png'), cover_path)
            else:
                StickerConvert.convert_and_compress_to_size(os.path.join(self.in_dir, 'cover.png'), cover_path, opt_comp_merged, self.cb_msg)
        else:
            # First image in the directory, extracting first frame
            first_image = [i for i in sorted(os.listdir(self.in_dir)) if os.path.isfile(os.path.join(self.in_dir, i)) and not i.endswith(('.txt', '.m4a', '.wastickers'))][0]
            StickerConvert.compress_to_size(StickerConvert.convert_generic_image, os.path.join(self.in_dir, f'{first_image}[0]'), cover_path, opt_comp_merged, self.cb_msg)
        
        MetadataHandler.set_metadata(pack_dir, author=author, title=title)
    
    @staticmethod
    def start(opt_output, opt_comp, opt_cred, cb_msg=print, cb_msg_block=input, cb_bar=None, out_dir=None, **kwargs):
        exporter = CompressWastickers(opt_output, opt_comp, opt_cred, cb_msg, cb_msg_block, cb_bar, out_dir)
        return exporter.compress_wastickers()