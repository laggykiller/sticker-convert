#!/usr/bin/env python3
import shutil
import os
import tempfile
import copy

from utils.converter import StickerConvert
from utils.format_verify import FormatVerify
from utils.metadata_handler import MetadataHandler
from utils.codec_info import CodecInfo
from utils.run_bin import RunBin

from mergedeep import merge

def clean_dir(dir):
    for i in os.listdir(dir):
        shutil.rmtree(os.path.join(dir, i))

class CompressWastickers:
    @staticmethod
    def compress_wastickers(opt_output={}, opt_comp={}, cb_msg=print, cb_bar=None, out_dir=None, **kwargs):
        fake_vid = opt_comp.get('fake_vid', False)
        in_dir = opt_output['dir']
        if not out_dir:
            out_dir = opt_output['dir']

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
                'max': 500000
            },
            'format': '.webp',
            'square': True
        }

        webp_spec = copy.deepcopy(base_spec)
        webp_spec['format'] = '.webp'
        webp_spec['animated'] = True if not fake_vid else None

        png_spec = copy.deepcopy(base_spec)
        png_spec['format'] = '.png'
        png_spec['animated'] = False if not fake_vid else None

        opt_comp_merged = merge({}, opt_comp, base_spec)
        
        urls = []
        title, author, emoji_dict = MetadataHandler.get_metadata(in_dir, title=opt_output.get('title'), author=opt_output.get('author'))
        packs = MetadataHandler.split_sticker_packs(in_dir, title=title, file_per_pack=30, separate_image_anim=not fake_vid)

        for pack_title, stickers in packs.items():
            num = 0 # Originally the Sticker Maker application name the files with int(time.time())
            with tempfile.TemporaryDirectory() as tempdir:
                for src in stickers:
                    cb_msg(f'Verifying {src} for compressing into .wastickers')

                    if fake_vid or CodecInfo.is_anim(src):
                        extension = '.webp'
                    else:
                        extension = '.png'

                    dst = os.path.join(tempdir, str(num) + extension)
                    num += 1

                    if FormatVerify.check_file(src, spec=webp_spec) or FormatVerify.check_file(src, spec=png_spec):
                        shutil.copy(src, dst)
                    else:
                        StickerConvert.convert_and_compress_to_size(src, dst, opt_comp_merged, cb_msg)

                out_f = os.path.join(out_dir, FormatVerify.sanitize_filename(pack_title + '.wastickers'))

                CompressWastickers.add_metadata(in_dir, tempdir, author, title, opt_comp, cb_msg, cb_bar)
                CompressWastickers.compress(out_f, tempdir)

            cb_msg(out_f)
            urls.append(out_f)
        
        return urls

    @staticmethod
    def add_metadata(in_dir, tmp_dir, author, title, opt_comp, cb_msg=print, cb_bar=None):
        spec_cover = {
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

        opt_comp_merged = merge({}, opt_comp, spec_cover)

        cover_path = os.path.join(tmp_dir, '100.png')
        if 'cover.png' in os.listdir(in_dir):
            if FormatVerify.check_file(cover_path, spec=spec_cover):
                shutil.copy(os.path.join(in_dir, 'cover.png'), cover_path)
            else:
                StickerConvert.convert_and_compress_to_size(os.path.join(in_dir, f'cover.png'), cover_path, opt_comp_merged, cb_msg)
        else:
            # First image in the directory, extracting first frame
            first_image = [i for i in os.listdir(in_dir) if not i.endswith('.txt') and not i.endswith('.wastickers')][0]
            StickerConvert.compress_to_size(StickerConvert.convert_generic_image, os.path.join(in_dir, f'{first_image}[0]'), cover_path, opt_comp_merged, cb_msg)
        
        MetadataHandler.set_metadata(tmp_dir, author=author, title=title)
    
    @staticmethod
    def compress(out_f, in_dir):
        RunBin.run_cmd(cmd_list=['zip', '-jr', out_f, in_dir], silence=True)