#!/usr/bin/env python3
'''Reference: https://github.com/blluv/KakaoTalkEmoticonDownloader'''

import requests
import json
import os
import zipfile
import io

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

class DownloadKakaoAnimated:
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

        return title

    @staticmethod
    def download_stickers_kakao_animated(url, out_dir, opt_cred, cb_msg=print, cb_bar=None):
        auth_token = opt_cred['kakao']['auth_token']

        pack_title = None
        author = None
        item_code = None

        if url.isnumeric():
            item_code = url
        elif url.startswith('kakaotalk://store/emoticon/'):
            item_code = url.replace('kakaotalk://store/emoticon/', '')
        elif url.startswith('https://e.kakao.com/t/'):
            pack_title = url.replace('https://e.kakao.com/t/', '')
        else:
            pack_title = url

        if pack_title:
            pack_meta_r = requests.get(f'https://e.kakao.com/api/v1/items/t/{pack_title}')

            if pack_meta_r.status_code == 200:
                pack_meta = json.loads(pack_meta_r.text)
            else:
                return False

            author = pack_meta['result']['artist']
            title_ko = pack_meta['result']['title']

            if auth_token:
                item_code = DownloadKakaoAnimated.get_item_code(title_ko, auth_token)

        else:
            pack_title = DownloadKakaoAnimated.get_title_from_id(item_code, auth_token)
        
        if not item_code:
            cb_msg('Download failed: Cannot get item code. Is auth_token invalid / expired? Try to regenerate it.')
            return False

        MetadataHandler.set_metadata(out_dir, title=pack_title, author=author)

        pack_url = f"http://item.kakaocdn.net/dw/{item_code}.file_pack.zip"
        response = requests.get(pack_url)

        if response.status_code != 200:
            cb_msg(f'Download failed: Cannot download {pack_url}')
            return False
        else:
            cb_msg(f'Downloaded {pack_url}')
        
        num = 0
        with zipfile.ZipFile(io.BytesIO(response.content), "r") as zf:
            for f_path in sorted(zf.namelist()):
                _, ext = os.path.splitext(f_path)

                if ext in ('.gif', '.webp'):
                    data = xor_data(zf.read(f_path))
                    cb_msg(f'Decrypted {f_path}')
                else:
                    data = zf.read(f_path)
                    cb_msg(f'Read {f_path}')
                
                out_path = os.path.join(out_dir, str(num).zfill(3) + ext)
                with open(out_path, 'wb') as f:
                    f.write(data)

                num += 1
        
        return True