import subprocess
import shutil
import os
import tempfile
from utils.converter import StickerConvert
from utils.format_verify import FormatVerify
from utils.metadata_handler import MetadataHandler

def clean_dir(dir):
    for i in os.listdir(dir):
        shutil.rmtree(os.path.join(dir, i))

class CompressWastickers:
    @staticmethod
    def compress_wastickers(in_dir, out_dir, author='Me', title='My sticker pack', quality_max=90, quality_min=0, fps_max=30, fps_min=3, steps=20, **kwargs):
        title, author, emoji_dict = MetadataHandler.get_metadata(in_dir, title=title, author=author)
        # packs = MetadataHandler.split_sticker_packs(in_dir, title=title, file_per_pack=30, separate_image_anim=True)
        packs = MetadataHandler.split_sticker_packs(in_dir, title=title, file_per_pack=30, separate_image_anim=False)

        for pack_title, stickers in packs.items():
            num = 0 # Originally the Sticker Maker application name the files with int(time.time())
            with tempfile.TemporaryDirectory() as tempdir:
                for src in stickers:
                    print('Verifying', src, 'for compressing into .wastickers')

                    src_full_name = os.path.split(src)[-1]
                    src_name = os.path.splitext(src_full_name)[0]

                    # WhatsApp does not care about a static image in webp anyway
                    # if FormatVerify.is_anim(src):
                    #     extension = '.webp'
                    # else:
                    #     extension = '.png'
                    
                    extension = '.webp'

                    dst = os.path.join(tempdir, str(num) + extension)
                    num += 1

                    # WhatsApp does not care about a static image in webp anyway
                    # if FormatVerify.check_file(src, res_min=512, res_max=512, square=True, size_max=500000, animated=True, format='.webp') or FormatVerify.check_file(src, res_min=512, res_max=512, square=True, size_max=100000, animated=False, format='.png'):
                    if FormatVerify.check_file(src, res_min=512, res_max=512, square=True, size_max=500000, format='.webp') or FormatVerify.check_file(src, res_min=512, res_max=512, square=True, size_max=100000, format='.png'):
                        shutil.copy(src, dst)
                    else:
                        StickerConvert.convert_and_compress_to_size(src, dst, vid_size_max=500000, img_size_max=100000, res_min=512, res_max=512, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, steps=steps)

                out_f = os.path.join(out_dir, pack_title + '.wastickers')

                CompressWastickers.add_metadata(in_dir, tempdir, author, title)
                CompressWastickers.compress(out_f, tempdir)

    @staticmethod
    def add_metadata(in_dir, tmp_dir, author, title):
        cover_path = os.path.join(tmp_dir, '100.png')
        if 'cover.png' in os.listdir(in_dir):
            if FormatVerify.check_file(cover_path, res=96, size_max=50000):
                shutil.copy(os.path.join(in_dir, 'cover.png'), cover_path)
            else:
                StickerConvert.convert_and_compress_to_size(os.path.join(in_dir, f'cover.png'), cover_path, img_size_max=50000, vid_size_max=50000, res_min=96, res_max=96)
        else:
            # First image in the directory, extracting first frame
            first_image = [i for i in os.listdir(in_dir) if not i.endswith('.txt') and not i.endswith('.wastickers')][0]
            StickerConvert.compress_to_size(StickerConvert.convert_generic_image, os.path.join(in_dir, f'{first_image}[0]'), cover_path, img_size_max=50000, vid_size_max=50000, res_min=96, res_max=96)
        
        MetadataHandler.set_metadata(tmp_dir, author=author, title=title)
    
    @staticmethod
    def compress(out_f, in_dir):
        subprocess.call([os.path.abspath(shutil.which(('zip'))), '-jr', out_f, in_dir], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)