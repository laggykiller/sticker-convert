#!/usr/bin/env python3
'''
References:
https://github.com/blluv/KakaoTalkEmoticonDownloader
https://github.com/star-39/moe-sticker-bot
'''

import requests
from bs4 import BeautifulSoup
import json
import os
import zipfile
import io
from urllib.parse import urlparse

from .download_base import DownloadBase
from ..utils.metadata_handler import MetadataHandler

class DecryptKakao:
    @staticmethod
    def generate_lfsr(key):
        d = list(key*2)
        seq=[0,0,0]

        seq[0] = 301989938
        seq[1] = 623357073
        seq[2] = -2004086252

        i = 0

        for i in range(0, 4):
            seq[0] = ord(d[i]) | (seq[0] << 8)
            seq[1] = ord(d[4+i]) | (seq[1] << 8)
            seq[2] = ord(d[8+i]) | (seq[2] << 8)

        seq[0] = seq[0] & 0xffffffff
        seq[1] = seq[1] & 0xffffffff
        seq[2] = seq[2] & 0xffffffff

        return seq

    @staticmethod
    def xor_byte(b, seq):
        flag1=1
        flag2=0
        result=0
        for _ in range(0, 8):
            v10 = (seq[0] >> 1)
            if (seq[0] << 31) & 0xffffffff:
                seq[0] = (v10 ^ 0xC0000031)
                v12 = (seq[1] >> 1)
                if (seq[1] << 31) & 0xffffffff:
                    seq[1] = ((v12 | 0xC0000000) ^ 0x20000010)
                    flag1 = 1
                else:
                    seq[1] = (v12 & 0x3FFFFFFF)
                    flag1 = 0
            else:
                seq[0] = v10
                v11 = (seq[2] >> 1)
                if (seq[2] << 31) & 0xffffffff:
                    seq[2] = ((v11 | 0xF0000000) ^ 0x8000001)
                    flag2 = 1
                else:
                    seq[2] = (v11 & 0xFFFFFFF)
                    flag2 = 0

            result = (flag1 ^ flag2 | 2 * result)
        return (result ^ b)

    @staticmethod
    def xor_data(data):
        dat = list(data)
        s = DecryptKakao.generate_lfsr("a271730728cbe141e47fd9d677e9006d")
        for i in range(0,128):
            dat[i] = DecryptKakao.xor_byte(dat[i], s)
        return bytes(dat)

class MetadataKakao:
    @staticmethod
    def get_info_from_share_link(url):
        headers = {
            'User-Agent': 'Android'
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        pack_title = soup.find('title').string

        data_url = soup.find('a', id='app_scheme_link')['data-url']
        item_code = data_url.replace('kakaotalk://store/emoticon/', '').split('?')[0]

        return pack_title, item_code

    @staticmethod
    def get_info_from_pack_title(pack_title):
        pack_meta_r = requests.get(f'https://e.kakao.com/api/v1/items/t/{pack_title}')

        if pack_meta_r.status_code == 200:
            pack_meta = json.loads(pack_meta_r.text)
        else:
            return False

        author = pack_meta['result']['artist']
        title_ko = pack_meta['result']['title']
        thumbnail_urls = pack_meta['result']['thumbnailUrls']

        return author, title_ko, thumbnail_urls

    @staticmethod
    def get_item_code(title_ko, auth_token):
        headers = {
            'Authorization': auth_token,
        }

        data = {
            'query': title_ko
        }

        response = requests.post('https://talk-pilsner.kakao.com/emoticon/item_store/instant_search', headers=headers, data=data)
        
        if response.status_code != 200:
            return

        response_json = json.loads(response.text)
        item_code = response_json['emoticons'][0]['item_code']

        return item_code

    @staticmethod
    def get_title_from_id(item_code, auth_token):
        headers = {
            'Authorization': auth_token,
        }

        response = requests.post(f'https://talk-pilsner.kakao.com/emoticon/api/store/v3/items/{item_code}', headers=headers)

        if response.status_code != 200:
            return
        
        response_json = json.loads(response.text)
        title = response_json['itemUnitInfo'][0]['title']
        # play_path_format = response_json['itemUnitInfo'][0]['playPathFormat']
        # stickers_count = len(response_json['itemUnitInfo'][0]['sizes'])

        return title

class DownloadKakao(DownloadBase):
    def __init__(self, *args, **kwargs):
        super(DownloadKakao, self).__init__(*args, **kwargs)
        self.pack_title = None
        self.author = None

    def download_stickers_kakao(self):
        if urlparse(self.url).netloc == 'emoticon.kakao.com':
            self.pack_title, item_code = MetadataKakao.get_info_from_share_link(self.url)

            return self.download_animated(item_code)

        elif self.url.isnumeric() or self.url.startswith('kakaotalk://store/emoticon/'):
            item_code = self.url.replace('kakaotalk://store/emoticon/', '')

            self.pack_title = None
            if self.opt_cred['kakao']['auth_token']:
                self.pack_title = MetadataKakao.get_title_from_id(item_code, self.opt_cred['kakao']['auth_token'])
                if not self.pack_title:
                    self.cb_msg('Warning: Cannot get pack_title with auth_token.')
                    self.cb_msg('Is auth_token invalid / expired? Try to regenerate it.')
                    self.cb_msg('Continuing without getting pack_title')

            return self.download_animated(item_code)

        elif urlparse(self.url).netloc == 'e.kakao.com':
            self.pack_title = self.url.replace('https://e.kakao.com/t/', '')
            self.author, title_ko, thumbnail_urls = MetadataKakao.get_info_from_pack_title(self.pack_title)

            if self.opt_cred['kakao']['auth_token']:
                item_code = MetadataKakao.get_item_code(title_ko, self.opt_cred['kakao']['auth_token'])
                if item_code:
                    return self.download_animated(item_code)
                else:
                    self.cb_msg('Warning: Cannot get item code.')
                    self.cb_msg('Is auth_token invalid / expired? Try to regenerate it.')
                    self.cb_msg('Downloading static stickers instead')

            return self.download_static(thumbnail_urls)

        else:
            self.cb_msg('Download failed: Unrecognized URL')
            return False

    def download_static(self, thumbnail_urls):
        MetadataHandler.set_metadata(self.out_dir, title=self.pack_title, author=self.author)

        targets = []

        num = 0
        for url in thumbnail_urls:
            dest = os.path.join(self.out_dir, str(num).zfill(3) + '.png')
            targets.append((url, dest))
            num += 1

        self.download_multiple_files(targets)
        
        return True
    
    def download_animated(self, item_code):
        MetadataHandler.set_metadata(self.out_dir, title=self.pack_title, author=self.author)

        pack_url = f"http://item.kakaocdn.net/dw/{item_code}.file_pack.zip"

        zip_file = self.download_file(pack_url)
        if zip_file:
            self.cb_msg(f'Downloaded {pack_url}')
        else:
            self.cb_msg(f'Cannot download {pack_url}')
            return False
                
        num = 0
        with zipfile.ZipFile(io.BytesIO(zip_file)) as zf:
            self.cb_msg(f'Unzipping...')
            if self.cb_bar:
                self.cb_bar(set_progress_mode='determinate', steps=len(zf.namelist()))

            for f_path in sorted(zf.namelist()):
                _, ext = os.path.splitext(f_path)

                if ext in ('.gif', '.webp'):
                    data = DecryptKakao.xor_data(zf.read(f_path))
                    self.cb_msg(f'Decrypted {f_path}')
                else:
                    data = zf.read(f_path)
                    self.cb_msg(f'Read {f_path}')
                
                out_path = os.path.join(self.out_dir, str(num).zfill(3) + ext)
                with open(out_path, 'wb') as f:
                    f.write(data)
                
                if self.cb_bar:
                    self.cb_bar(update_bar=True)

                num += 1

        self.cb_msg(f'Finished getting {pack_url}')
        
        return True

    @staticmethod
    def start(url, out_dir, opt_cred, cb_msg=print, cb_msg_block=input, cb_bar=None):
        downloader = DownloadKakao(url, out_dir, opt_cred, cb_msg, cb_msg_block, cb_bar)
        return downloader.download_stickers_kakao()