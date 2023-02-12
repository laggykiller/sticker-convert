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

from utils.metadata_handler import MetadataHandler

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

def xor_data(data):
    dat=list(data)
    s=generate_lfsr("a271730728cbe141e47fd9d677e9006d")
    for i in range(0,128):
        dat[i]=xor_byte(dat[i], s)
    return bytes(dat)

def get_info_from_share_link(url):
    headers = {
        'User-Agent': 'Android'
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    pack_title = soup.find('title').string.split(' | ', 1)[1]

    data_url = soup.find('a', id='app_scheme_link')['data-url']
    item_code = data_url.replace('kakaotalk://store/emoticon/', '').split('?')[0]

    return pack_title, item_code

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

class DownloadKakao:
    def __init__(self, url, out_dir, auth_token=None, cb_msg=print, cb_bar=None):
        self.url = url
        self.out_dir = out_dir
        self.auth_token = auth_token
        self.cb_msg = cb_msg
        self.cb_bar = cb_bar

        self.pack_title = None
        self.author = None
    
    def start(self):
        if 'emoticon.kakao.com' in self.url:
            self.pack_title, item_code = get_info_from_share_link(self.url)

            return self.download_animated(item_code)

        elif self.url.isnumeric() or self.url.startswith('kakaotalk://store/emoticon/'):
            item_code = self.url.replace('kakaotalk://store/emoticon/', '')

            self.pack_title = None
            if self.auth_token:
                self.pack_title = get_title_from_id(item_code, self.auth_token)
                if not self.pack_title:
                    self.cb_msg('Warning: Cannot get pack_title with auth_token.')
                    self.cb_msg('Is auth_token invalid / expired? Try to regenerate it.')
                    self.cb_msg('Continuing without getting pack_title')

            return self.download_animated(item_code)

        elif 'e.kakao.com' in self.url:
            self.pack_title = self.url.replace('https://e.kakao.com/t/', '')
            self.author, title_ko, thumbnail_urls = get_info_from_pack_title(self.pack_title)

            if self.auth_token:
                item_code = get_item_code(title_ko, self.auth_token)
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

        num = 0

        if self.cb_bar:
            self.cb_bar(set_progress_mode='determinate', steps=len(thumbnail_urls))

        for url in thumbnail_urls:
            # sticker_id = url.split('/')[-1]
            out_path = os.path.join(self.out_dir, str(num).zfill(3) + '.png')
            
            for i in range(3):
                try:
                    image = requests.get(url, stream=True, timeout=5)
                    with open(out_path, 'wb') as f:
                        for chunk in image.iter_content(chunk_size=10240):
                            if chunk:
                                f.write(chunk)
                    self.cb_msg(f'Downloaded {url}')
                    if self.cb_bar:
                        self.cb_bar(update_bar=True)
                    break
                except requests.exceptions.RequestException:
                    self.cb_msg(f'Cannot download {url} try {i}')
            
            num += 1
        
        return True
    
    def download_animated(self, item_code):
        MetadataHandler.set_metadata(self.out_dir, title=self.pack_title, author=self.author)

        pack_url = f"http://item.kakaocdn.net/dw/{item_code}.file_pack.zip"

        response = requests.get(pack_url, stream=True)
        total_length = int(response.headers.get('content-length'))
        zip_file = b''
        chunk_size = 102400

        if response.status_code != 200:
            self.cb_msg(f'Download failed: Cannot download {pack_url}')
            return False
        else:
            self.cb_msg(f'Downloading {pack_url}')

        if self.cb_bar:
            self.cb_bar(set_progress_mode='determinate', steps=(total_length/chunk_size) + 1)

        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                zip_file += chunk
                if self.cb_bar:
                    self.cb_bar(update_bar=True)
        
        num = 0
        with zipfile.ZipFile(io.BytesIO(zip_file)) as zf:
            self.cb_msg(f'Unzipping...')
            if self.cb_bar:
                self.cb_bar(set_progress_mode='determinate', steps=len(zf.namelist()))

            for f_path in sorted(zf.namelist()):
                _, ext = os.path.splitext(f_path)

                if ext in ('.gif', '.webp'):
                    data = xor_data(zf.read(f_path))
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
    def download_stickers_kakao(url, out_dir, opt_cred, cb_msg=print, cb_bar=None):
        auth_token = opt_cred['kakao']['auth_token']

        k = DownloadKakao(url, out_dir, auth_token, cb_msg, cb_bar)
        return k.start()