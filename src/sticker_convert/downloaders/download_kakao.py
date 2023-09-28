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
from typing import Optional

from .download_base import DownloadBase # type: ignore
from ..utils.metadata_handler import MetadataHandler # type: ignore

class DecryptKakao:
    @staticmethod
    def generate_lfsr(key: str) -> list[int]:
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
    def xor_byte(b: int, seq: list) -> int:
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
    def xor_data(data: bytes) -> bytes:
        dat = list(data)
        s = DecryptKakao.generate_lfsr("a271730728cbe141e47fd9d677e9006d")
        for i in range(0,128):
            dat[i] = DecryptKakao.xor_byte(dat[i], s)
        return bytes(dat)

class MetadataKakao:
    @staticmethod
    def get_info_from_share_link(url: str) -> tuple[Optional[str], Optional[str]]:
        headers = {
            'User-Agent': 'Android'
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        pack_title_tag = soup.find('title')
        if not pack_title_tag:
            return None, None
        
        pack_title = pack_title_tag.string # type: ignore[union-attr]

        data_url = soup.find('a', id='app_scheme_link').get('data-url') # type: ignore[union-attr]
        if not data_url:
            return None, None
        
        item_code = data_url.replace('kakaotalk://store/emoticon/', '').split('?')[0] # type: ignore[union-attr]

        return pack_title, item_code

    @staticmethod
    def get_info_from_pack_title(pack_title: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        pack_meta_r = requests.get(f'https://e.kakao.com/api/v1/items/t/{pack_title}')

        if pack_meta_r.status_code == 200:
            pack_meta = json.loads(pack_meta_r.text)
        else:
            return None, None, None

        author = pack_meta['result']['artist']
        title_ko = pack_meta['result']['title']
        thumbnail_urls = pack_meta['result']['thumbnailUrls']

        return author, title_ko, thumbnail_urls

    @staticmethod
    def get_item_code(title_ko: str, auth_token: str) -> Optional[str]:
        headers = {
            'Authorization': auth_token,
        }

        data = {
            'query': title_ko
        }

        response = requests.post('https://talk-pilsner.kakao.com/emoticon/item_store/instant_search', headers=headers, data=data)
        
        if response.status_code != 200:
            return None

        response_json = json.loads(response.text)
        item_code = response_json['emoticons'][0]['item_code']

        return item_code

    @staticmethod
    def get_title_from_id(item_code: str, auth_token: str) -> Optional[str]:
        headers = {
            'Authorization': auth_token,
        }

        response = requests.post(f'https://talk-pilsner.kakao.com/emoticon/api/store/v3/items/{item_code}', headers=headers)

        if response.status_code != 200:
            return None
        
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

    def download_stickers_kakao(self) -> bool:
        if self.opt_cred:
            auth_token = self.opt_cred.get('kakao', {}).get('auth_token')

        if urlparse(self.url).netloc == 'emoticon.kakao.com':
            self.pack_title, item_code = MetadataKakao.get_info_from_share_link(self.url)

            if item_code:
                return self.download_animated(item_code)
            else:
                self.cb_msg('Download failed: Cannot download metadata for sticker pack')
                return False

        elif self.url.isnumeric() or self.url.startswith('kakaotalk://store/emoticon/'):
            item_code = self.url.replace('kakaotalk://store/emoticon/', '')

            self.pack_title = None
            if auth_token:
                self.pack_title = MetadataKakao.get_title_from_id(item_code, auth_token) # type: ignore[arg-type]
                if not self.pack_title:
                    self.cb_msg('Warning: Cannot get pack_title with auth_token.')
                    self.cb_msg('Is auth_token invalid / expired? Try to regenerate it.')
                    self.cb_msg('Continuing without getting pack_title')

            return self.download_animated(item_code) # type: ignore[arg-type]

        elif urlparse(self.url).netloc == 'e.kakao.com':
            self.pack_title = self.url.replace('https://e.kakao.com/t/', '')
            self.author, title_ko, thumbnail_urls = MetadataKakao.get_info_from_pack_title(self.pack_title)

            if not thumbnail_urls:
                self.cb_msg('Download failed: Cannot download metadata for sticker pack')
                return False

            if auth_token:
                item_code = MetadataKakao.get_item_code(title_ko, auth_token) # type: ignore[arg-type]
                if item_code:
                    return self.download_animated(item_code)
                else:
                    msg = 'Warning: Cannot get item code.\n'
                    msg += 'Is auth_token invalid / expired? Try to regenerate it.\n'
                    msg += 'Continue to download static stickers instead?'
                    response = self.cb_msg_block(msg)
                    if response == False:
                        return False

            return self.download_static(thumbnail_urls)

        else:
            self.cb_msg('Download failed: Unrecognized URL')
            return False

    def download_static(self, thumbnail_urls: str) -> bool:
        MetadataHandler.set_metadata(self.out_dir, title=self.pack_title, author=self.author)

        targets = []

        num = 0
        for url in thumbnail_urls:
            dest = os.path.join(self.out_dir, str(num).zfill(3) + '.png')
            targets.append((url, dest))
            num += 1

        self.download_multiple_files(targets)
        
        return True
    
    def download_animated(self, item_code: str) -> bool:
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
    def start(url: str, out_dir: str, opt_cred: Optional[dict] = None, cb_msg=print, cb_msg_block=input, cb_bar=None) -> bool:
        downloader = DownloadKakao(url, out_dir, opt_cred, cb_msg, cb_msg_block, cb_bar)
        return downloader.download_stickers_kakao()