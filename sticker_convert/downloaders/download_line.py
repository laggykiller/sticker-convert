#!/usr/bin/env python3
'''Reference: https://github.com/doubleplusc/Line-sticker-downloader/blob/master/sticker_dl.py'''

import requests
import json
import os
from urllib import parse
from PIL import Image

from utils.metadata_handler import MetadataHandler

class DownloadLine:
    @staticmethod
    def download_stickers_line(url, out_dir, opt_cred=None, cb_msg=print, cb_msg_block=input, cb_bar=None):
        headers = {
                'referer': 'https://store.line.me',
                'user-agent': 'Android',
            }
        
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
        sticker_text_dict = {}
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
            
            elif pack_meta.get('stickerResourceType') == 'PER_STICKER_TEXT':
                dl_targets.append((f'https://stickershop.line-scdn.net/stickershop/v1/sticker/{sticker_id}/iPhone/base/plus/sticker@2x.png', out_path + '-base.png'))
                sticker_text_dict[sticker_id] = sticker['customPlus']['defaultText']

            else:
                dl_targets.append((f'http://dl.stickershop.line.naver.jp/stickershop/v1/sticker/{sticker_id}/iphone/sticker@2x.png', out_path + '.png'))
            
            num += 1
        
        if sticker_text_dict != {}:
            with open(os.path.join(out_dir, 'line-sticker-text.txt'), 'w+', encoding='utf-8') as f:
                json.dump(sticker_text_dict, f, indent=4, ensure_ascii=False)

            msg_block = 'The Line sticker pack you are downloading can have customized text.\n'
            msg_block += 'line-sticker-text.txt has been created in input directory.\n'
            msg_block += 'Please edit line-sticker-text.txt, then continue.'
            cb_msg_block(msg_block)

            with open(os.path.join(out_dir, 'line-sticker-text.txt') , "r", encoding='utf-8') as f:
                sticker_text_dict = json.load(f)
            
            num = 0
            for sticker_id, sticker_text in sticker_text_dict.items():
                out_path = os.path.join(out_dir, str(num).zfill(3))
                dl_targets.append((f'https://store.line.me/overlay/sticker/{pack_id}/{sticker_id}/iPhone/sticker.png?text={parse.quote(sticker_text)}', out_path + '-text.png'))
                
                num += 1
        
        if cb_bar:
            cb_bar(set_progress_mode='determinate', steps=len(dl_targets))
        
        for i in dl_targets:
            success = False
            for _ in range(3):
                try:
                    image = requests.get(i[0], stream=True, timeout=5, headers=headers)
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
        
        for i in os.listdir(out_dir):
            if i.endswith('-base.png'):
                base_path = os.path.join(out_dir, i)
                text_path = os.path.join(out_dir, i.replace('-base.png', '-text.png'))
                combined_path = os.path.join(out_dir, i.replace('-base.png', '.png'))

                base_img = Image.open(base_path).convert('RGBA')
                text_img = Image.open(text_path).convert('RGBA')

                Image.alpha_composite(base_img, text_img).save(combined_path)

                os.remove(base_path)
                os.remove(text_path)

                cb_msg(f"Combined {i.replace('-base.png', '.png')}")
        
        return True