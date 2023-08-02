#!/usr/bin/env python3
'''Reference: https://github.com/doubleplusc/Line-sticker-downloader/blob/master/sticker_dl.py'''

import requests
import json
import os
import io
import zipfile
import string
from urllib import parse
from PIL import Image
from bs4 import BeautifulSoup

from utils.metadata_handler import MetadataHandler

class DownloadLine:
    @staticmethod
    def download_stickers_line(url, out_dir, opt_cred=None, cb_msg=print, cb_msg_block=input, cb_bar=None):
        headers = {
                'referer': 'https://store.line.me',
                'user-agent': 'Android',
            }
        
        region = ''
        is_emoji = False
        if url.startswith('line://shop/detail/'):
            pack_id = url.replace('line://shop/detail/', '')
            if len(url) == 24 and all(c in string.hexdigits for c in url):
                is_emoji = True
        elif url.startswith('https://store.line.me/stickershop/product/'):
            pack_id = url.replace('https://store.line.me/stickershop/product/', '').split('/')[0]
            region = url.replace('https://store.line.me/stickershop/product/', '').split('/')[1]
        elif url.startswith('https://line.me/S/sticker'):
            url_parsed = parse.urlparse(url)
            pack_id = url.replace('https://line.me/S/sticker/', '').split('/')[0]
            region = parse.parse_qs(url_parsed.query)['lang']
        elif url.startswith('https://store.line.me/emojishop/product/'):
            pack_id = url.replace('https://store.line.me/emojishop/product/', '').split('/')[0]
            region = url.replace('https://store.line.me/emojishop/product/', '').split('/')[1]
            is_emoji = True
        elif url.startswith('https://line.me/S/emoji'):
            url_parsed = parse.urlparse(url)
            pack_id = parse.parse_qs(url_parsed.query)['id']
            region = parse.parse_qs(url_parsed.query)['lang']
            is_emoji = True
        elif len(url) == 24 and all(c in string.hexdigits for c in url):
            pack_id = url
            is_emoji = True
        elif url.isnumeric():
            pack_id = url
        else:
            cb_msg('Download failed: Unsupported URL format')
            return False

        if is_emoji:
            pack_meta_r = requests.get(f"https://stickershop.line-scdn.net/sticonshop/v1/{pack_id}/sticon/iphone/meta.json")

            if pack_meta_r.status_code == 200:
                pack_meta = json.loads(pack_meta_r.text)
            else:
                return False
            
            if region == '':
                region = 'en'

            pack_store_page = requests.get(f"https://store.line.me/emojishop/product/{pack_id}/{region}")

            if pack_store_page.status_code != 200:
                return False

            pack_store_page_soup = BeautifulSoup(pack_store_page.text, 'html.parser')
            title = pack_store_page_soup.find(class_='mdCMN38Item01Txt').text
            author = pack_store_page_soup.find(class_='mdCMN38Item01Author').text
        else:
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
        sticker_text_dict = {}

        # Reference: https://sora.vercel.app/line-sticker-download
        if is_emoji:
            if pack_meta.get('sticonResourceType') == 'ANIMATION':
                pack_url = f'https://stickershop.line-scdn.net/sticonshop/v1/{pack_id}/sticon/iphone/package_animation.zip'
            else:
                pack_url = f'https://stickershop.line-scdn.net/sticonshop/v1/{pack_id}/sticon/iphone/package.zip'
        else:
            if pack_meta.get('stickerResourceType') in ('ANIMATION', 'ANIMATION_SOUND', 'POPUP') or pack_meta.get('hasSound') == True:
                pack_url = f'https://stickershop.line-scdn.net/stickershop/v1/product/{pack_id}/iphone/stickerpack@2x.zip'
            
            elif pack_meta.get('stickerResourceType') == 'PER_STICKER_TEXT':
                pack_url = f'https://stickershop.line-scdn.net/stickershop/v1/product/{pack_id}/iphone/sticker_custom_plus_base@2x.zip'

            elif pack_meta.get('stickerResourceType') == 'NAME_TEXT':
                pack_url = f'https://stickershop.line-scdn.net/stickershop/v1/product/{pack_id}/iphone/sticker_name_base@2x.zip'
                # Customizing the text requires Line account

            else:
                pack_url = f'https://stickershop.line-scdn.net/stickershop/v1/product/{pack_id}/iphone/stickers@2x.zip'

        response = requests.get(pack_url, stream=True)
        total_length = int(response.headers.get('content-length'))
        zip_file = b''
        chunk_size = 102400

        if response.status_code != 200:
            cb_msg(f'Download failed: Cannot download {pack_url}')
            return False
        else:
            cb_msg(f'Downloading {pack_url}')

        if cb_bar:
            cb_bar(set_progress_mode='determinate', steps=(total_length/chunk_size) + 1)

        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                zip_file += chunk
                if cb_bar:
                    cb_bar(update_bar=True)
        
        num = 0
        with zipfile.ZipFile(io.BytesIO(zip_file)) as zf:
            cb_msg(f'Unzipping...')
            if is_emoji:
                cb_bar(set_progress_mode='determinate', steps=len(pack_meta['orders']))
                for sticker in pack_meta['orders']:
                    if pack_meta.get('sticonResourceType') == 'ANIMATION':
                        f_path = str(sticker) + '_animation.png'
                    else:
                        f_path = str(sticker) + '.png'
                    data = zf.read(f_path)
                    cb_msg(f'Read {f_path}')
                    
                    out_path = os.path.join(out_dir, str(num).zfill(3) + '.png')
                    with open(out_path, 'wb') as f:
                        f.write(data)
                    
                    if cb_bar:
                        cb_bar(update_bar=True)

                    num += 1
            
            else:
                cb_bar(set_progress_mode='determinate', steps=len(pack_meta['stickers']))
                for sticker in pack_meta['stickers']:
                    if pack_meta.get('stickerResourceType') in ('ANIMATION', 'ANIMATION_SOUND'):
                        f_path = 'animation@2x/' + str(sticker['id']) + '@2x.png'
                    elif pack_meta.get('stickerResourceType') == 'POPUP':
                        f_path = 'popup/' + str(sticker['id']) + '.png'
                    else:
                        f_path = str(sticker['id']) + '@2x.png'
                    data = zf.read(f_path)
                    cb_msg(f'Read {f_path}')
                    
                    out_path = os.path.join(out_dir, str(num).zfill(3) + '.png')
                    with open(out_path, 'wb') as f:
                        f.write(data)
                    
                    if pack_meta.get('stickerResourceType') == 'PER_STICKER_TEXT':
                        sticker_text_dict[num] = {
                            'sticker_id': sticker['id'],
                            'sticker_text': sticker['customPlus']['defaultText']
                            }
                    
                    if pack_meta.get('hasSound'):
                        f_path = 'sound/' + str(sticker['id']) + '.m4a'
                        data = zf.read(f_path)
                        cb_msg(f'Read {f_path}')
                        
                        out_path = os.path.join(out_dir, str(num).zfill(3) + '.m4a')
                        with open(out_path, 'wb') as f:
                            f.write(data)
                    
                    if cb_bar:
                        cb_bar(update_bar=True)

                    num += 1
        
        dl_targets = []
        if sticker_text_dict != {}:
            line_sticker_text_path = os.path.join(out_dir, 'line-sticker-text.txt')

            if not os.path.isfile(line_sticker_text_path):
                with open(line_sticker_text_path, 'w+', encoding='utf-8') as f:
                    json.dump(sticker_text_dict, f, indent=4, ensure_ascii=False)

                msg_block = 'The Line sticker pack you are downloading can have customized text.\n'
                msg_block += 'line-sticker-text.txt has been created in input directory.\n'
                msg_block += 'Please edit line-sticker-text.txt, then continue.'
                cb_msg_block(msg_block)

            with open(line_sticker_text_path , "r", encoding='utf-8') as f:
                sticker_text_dict = json.load(f)
            
            for num, data in sticker_text_dict.items():
                out_path = os.path.join(out_dir, str(num).zfill(3))
                sticker_id = data['sticker_id']
                sticker_text = data['sticker_text']
                dl_targets.append((f'https://store.line.me/overlay/sticker/{pack_id}/{sticker_id}/iPhone/sticker.png?text={parse.quote(sticker_text)}', out_path + '-text.png'))
        
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
            if i.endswith('-text.png'):
                base_path = os.path.join(out_dir, i.replace('-text.png', '.png'))
                text_path = os.path.join(out_dir, i)

                base_img = Image.open(base_path).convert('RGBA')
                text_img = Image.open(text_path).convert('RGBA')

                Image.alpha_composite(base_img, text_img).save(base_path)

                os.remove(text_path)

                cb_msg(f"Combined {i.replace('-text.png', '.png')}")
        
        return True