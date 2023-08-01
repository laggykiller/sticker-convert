#!/usr/bin/env python3
'''Reference: https://github.com/doubleplusc/Line-sticker-downloader/blob/master/sticker_dl.py'''

import requests
import json
import os

from utils.metadata_handler import MetadataHandler

class DownloadLine:
    @staticmethod
    def download_stickers_line(url, out_dir, opt_cred=None, cb_msg=print, cb_bar=None):
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
            cb_msg('Download failed: Unsupported URL format')
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
        
        if region == 'zh-Hant':
            region = 'zh_TW'

        title = pack_meta['title'].get(region)
        if title == None:
            title = pack_meta['title']['en']

        author = pack_meta['author'].get(region)
        if author == None:
            author = pack_meta['author']['en']

        MetadataHandler.set_metadata(out_dir, title=title, author=author)

        num = 0
        dl_targets = []
        for sticker in pack_meta['stickers']:
            sticker_id = sticker['id']
            out_path = os.path.join(out_dir, str(num).zfill(3))

            if pack_meta.get('hasSound') == True:
                # Packs with sound does not necessary have 'stickerResourceType' attribute
                if pack_meta.get('stickerResourceType') == 'ANIMATION_SOUND':
                    dl_targets.append((f'https://sdl-stickershop.line.naver.jp/products/0/0/1/{pack_id}/iphone/animation/{sticker_id}@2x.png', out_path + '.apng'))
                elif requests.get(f'https://sdl-stickershop.line.naver.jp/products/0/0/1/{pack_id}/iphone/animation/{sticker_id}@2x.png').ok:
                    dl_targets.append((f'https://sdl-stickershop.line.naver.jp/products/0/0/1/{pack_id}/iphone/animation/{sticker_id}@2x.png', out_path + '.apng'))
                else:
                    dl_targets.append((f'http://dl.stickershop.line.naver.jp/stickershop/v1/sticker/{sticker_id}/iphone/sticker@2x.png', out_path + '.png'))
                dl_targets.append((f'https://stickershop.line-scdn.net/stickershop/v1/sticker/{sticker_id}/android/sticker_sound.m4a', out_path + '.m4a'))

            elif pack_meta.get('stickerResourceType') == 'POPUP':
                dl_targets.append((f'https://stickershop.line-scdn.net/stickershop/v1/sticker/{sticker_id}/android/sticker_popup.png', out_path + '.apng'))

            elif pack_meta.get('stickerResourceType') in ('ANIMATION', 'ANIMATION_SOUND'):
                dl_targets.append((f'https://sdl-stickershop.line.naver.jp/products/0/0/1/{pack_id}/iphone/animation/{sticker_id}@2x.png', out_path + '.apng'))

            else:
                dl_targets.append((f'http://dl.stickershop.line.naver.jp/stickershop/v1/sticker/{sticker_id}/iphone/sticker@2x.png', out_path + '.png'))
            
            num += 1
        
        if cb_bar:
            cb_bar(set_progress_mode='determinate', steps=len(dl_targets))
        
        for i in dl_targets:
            success = False
            for _ in range(3):
                try:
                    image = requests.get(i[0], stream=True, timeout=5)
                    with open(i[1], 'wb') as f:
                        for chunk in image.iter_content(chunk_size=10240):
                            if chunk:
                                f.write(chunk)
                    cb_msg(f'Downloaded {i[0]}')

                    if cb_bar:
                        cb_bar(update_bar=True)
                        
                    success = True
                    break
                except requests.exceptions.RequestException:
                    pass
            
            if not success:
                cb_msg(f'Cannot download {i[0]} (tried 3 times)')
        
        return True