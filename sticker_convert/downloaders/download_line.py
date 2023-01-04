'''Reference: https://github.com/doubleplusc/Line-sticker-downloader/blob/master/sticker_dl.py'''

import requests
import json
import os
from utils.metadata_handler import MetadataHandler

class DownloadLine:
    @staticmethod
    def download_stickers_line(url, out_dir):
        pack_ext = ""

        region = ''
        if url.isnumeric():
            pack_id = url
        elif url.startswith('line://shop/detail/'):
            pack_id = url.replace('line://shop/detail/', '')
        elif url.startswith('https://store.line.me/stickershop/product/'):
            pack_id = url.replace('https://store.line.me/stickershop/product/', '').split('/')[0]
            region = url.replace('https://store.line.me/stickershop/product/', '').split('/')[1]
        else:
            print('Unsupported URL format')
            return False

        pack_meta_r = requests.get(f"http://dl.stickershop.line.naver.jp/products/0/0/1/{pack_id}/android/productInfo.meta")

        if pack_meta_r.status_code == 200:
            pack_meta = json.loads(pack_meta_r.text)
        else:
            return False

        if region == '':
            if 'en' in pack_meta['title']:
                # Prefer en release
                region = 'en'
            else:
                # If no en release, use whatever comes first
                region = pack_meta['title'].keys()[0]

        title = pack_meta['title'][region]
        author = pack_meta['author'][region]

        MetadataHandler.set_metadata(out_dir, title=title, author=author)

        if pack_meta['hasAnimation'] == True:
            pack_ext = '.apng'
        else:
            pack_ext = '.png'

        for sticker in pack_meta['stickers']:
            sticker_id = sticker['id']
            out_path = os.path.join(out_dir, str(sticker_id).zfill(3) + pack_ext)

            if pack_ext == '.apng':
                url = f'https://sdl-stickershop.line.naver.jp/products/0/0/1/{pack_id}/iphone/animation/{sticker_id}@2x.png'
            else:
                url = f'http://dl.stickershop.line.naver.jp/stickershop/v1/sticker/{sticker_id}/iphone/sticker@2x.png'
            
            for i in range(3):
                try:
                    image = requests.get(url, stream=True)
                    with open(out_path, 'wb') as f:
                        for chunk in image.iter_content(chunk_size=10240):
                            if chunk:
                                f.write(chunk)
                    print('Downloaded', url)
                    break
                except requests.exceptions.RequestException:
                    print('Cannot download', url, 'try', i)