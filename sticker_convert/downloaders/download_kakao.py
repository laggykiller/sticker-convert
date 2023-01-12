#!/usr/bin/env python3
'''Reference: https://github.com/star-39/moe-sticker-bot/blob/master/pkg/core/import.go'''

import requests
import json
import os
import sys

from utils.metadata_handler import MetadataHandler

class DownloadKakao:
    @staticmethod
    def download_stickers_kakao(url, out_dir, opt_cred=None, cb_msg=sys.stdout.write, cb_bar=None):
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

        num = 0

        if cb_bar:
            cb_bar(set_progress_mode='determinate', steps=len(pack_meta['result']['thumbnailUrls']))

        for url in pack_meta['result']['thumbnailUrls']:
            # sticker_id = url.split('/')[-1]
            out_path = os.path.join(out_dir, str(num).zfill(3) + '.png')
            
            for i in range(3):
                try:
                    image = requests.get(url, stream=True)
                    with open(out_path, 'wb') as f:
                        for chunk in image.iter_content(chunk_size=10240):
                            if chunk:
                                f.write(chunk)
                    cb_msg('Downloaded', url)
                    if cb_bar:
                        cb_bar(update_bar=True)
                    break
                except requests.exceptions.RequestException:
                    cb_msg('Cannot download', url, 'try', i)
            
            num += 1
        
        return True