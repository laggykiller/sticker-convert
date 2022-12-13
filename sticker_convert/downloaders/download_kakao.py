'''Reference: https://github.com/star-39/moe-sticker-bot/blob/master/pkg/core/import.go'''

import requests
import json
import os
from utils.metadata_handler import MetadataHandler

class DownloadKakao:
    @staticmethod
    def download_stickers_kakao(url, out_dir):
        pack_ext = ""

        region = ''
        if url.startswith('https://e.kakao.com/t/'):
            pack_id = url.replace('https://e.kakao.com/t/', '')
        else:
            pack_id = url

        pack_meta_r = requests.get(f'https://e.kakao.com/api/v1/items/t/{pack_id}')

        if pack_meta_r.status_code == 200:
            pack_meta = json.loads(pack_meta_r.text)
        else:
            return False

        author = pack_meta['result']['artist']

        MetadataHandler.set_metadata(out_dir, title=pack_id, author=author)

        for url in pack_meta['result']['thumbnailUrls']:
            sticker_id = url.split('/')[-1]
            out_path = os.path.join(out_dir, str(sticker_id) + '.png')
            
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