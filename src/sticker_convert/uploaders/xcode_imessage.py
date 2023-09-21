#!/usr/bin/env python3
import shutil
import os
import copy
import json
import plistlib

from .upload_base import UploadBase
from ..utils.converter import StickerConvert
from ..utils.format_verify import FormatVerify
from ..utils.metadata_handler import MetadataHandler
from ..utils.codec_info import CodecInfo

from mergedeep import merge

class XcodeImessageIconset:
    def __init__(self):
        self.iconset = {}

        with open('ios-message-stickers-template/stickers StickerPackExtension/Stickers.xcstickers/iMessage App Icon.stickersiconset/Contents.json') as f:
            dict = json.load(f)
        
        for i in dict['images']:
            filename = i['filename']
            size = i['size']
            size_w = int(size.split('x')[0])
            size_h = int(size.split('x')[1])
            scale = int(i['scale'].replace('x', ''))
            size_w_scaled = size_w * scale
            size_h_scaled = size_h * scale

            self.iconset[filename] = (size_w_scaled, size_h_scaled)
        
        # self.iconset = {
        #     'App-Store-1024x1024pt.png': (1024, 1024),
        #     'iPad-Settings-29pt@2x.png': (58, 58),
        #     'iPhone-settings-29pt@2x.png': (58, 58),
        #     'iPhone-settings-29pt@3x.png': (87, 87),
        #     'Messages27x20pt@2x.png': (54, 40),
        #     'Messages27x20pt@3x.png': (81, 60),
        #     'Messages32x24pt@2x.png': (64, 48),
        #     'Messages32x24pt@3x.png': (96, 72),
        #     'Messages-App-Store-1024x768pt.png': (1024, 768),
        #     'Messages-iPad-67x50pt@2x.png': (134, 100),
        #     'Messages-iPad-Pro-74x55pt@2x.png': (148, 110),
        #     'Messages-iPhone-60x45pt@2x.png': (120, 90),
        #     'Messages-iPhone-60x45pt@3x.png': (180, 135)



class XcodeImessage(UploadBase):
    def __init__(self, *args, **kwargs):
        super(XcodeImessage, self).__init__(*args, **kwargs)
        self.iconset = XcodeImessageIconset().iconset

        base_spec = {
            "size_max": {
                "img": 500000,
                "vid": 500000
            },
            'res': {
                'w': {
                    'min': 300,
                    'max': 300
                },
                'h': {
                    'min': 300,
                    'max': 300
                }
            },
            'format': ('.png', '.apng', '.gif', '.jpeg', 'jpg'),
            'square': True
        }

        self.small_spec = copy.deepcopy(base_spec)

        self.medium_spec = copy.deepcopy(base_spec)
        self.medium_spec['res']['w']['min'] = 408
        self.medium_spec['res']['w']['max'] = 408
        self.medium_spec['res']['h']['min'] = 408
        self.medium_spec['res']['h']['max'] = 408

        self.large_spec = copy.deepcopy(base_spec)
        self.large_spec['res']['w']['min'] = 618
        self.large_spec['res']['w']['max'] = 618
        self.large_spec['res']['h']['min'] = 618
        self.large_spec['res']['h']['max'] = 618
    
    def create_imessage_xcode(self):
        urls = []
        title, author, emoji_dict = MetadataHandler.get_metadata(self.in_dir, title=self.opt_output.get('title'), author=self.opt_output.get('author'))
        packs = MetadataHandler.split_sticker_packs(self.in_dir, title=title, file_per_pack=100, separate_image_anim=False)

        res_choice = None

        for pack_title, stickers in packs.items():
            pack_title = FormatVerify.sanitize_filename(pack_title)

            for src in stickers:
                self.cb_msg(f'Verifying {src} for creating Xcode iMessage sticker pack')

                src_path = os.path.join(self.in_dir, src)
                dst_path = os.path.join(self.out_dir, src)

                if res_choice == None:
                    res_choice, _ = CodecInfo.get_file_res(src_path)
                    res_choice = res_choice if res_choice != None else 300
                    
                    if res_choice == 618:
                        spec_choice = self.large_spec
                    elif res_choice == 408:
                        spec_choice = self.medium_spec
                    else:
                        # res_choice == 300
                        spec_choice = self.small_spec
                    
                    opt_comp_merged = merge({}, self.opt_comp, spec_choice)

                if FormatVerify.check_file(src, spec=spec_choice):
                    if src_path != dst_path:
                        shutil.copy(src_path, dst_path)
                else:
                    StickerConvert(src_path, dst_path, opt_comp_merged, self.cb_msg).convert()

            self.add_metadata(author, pack_title)
            self.create_xcode_proj(author, pack_title)

            result = os.path.join(self.out_dir, pack_title)
            self.cb_msg(result)
            urls.append(result)
        
        return urls

    def add_metadata(self, author, title):
        first_image_path = os.path.join(self.in_dir, [i for i in sorted(os.listdir(self.in_dir)) if os.path.isfile(os.path.join(self.in_dir, i)) and i.endswith('.png')][0])
        cover_path = os.path.join(self.in_dir, 'cover.png')
        cover_path_new = os.path.join(self.out_dir, 'cover.png')
        if os.path.isfile(cover_path) and cover_path_new != cover_path:
            shutil.copy(cover_path, cover_path_new)

        if os.path.isfile(cover_path):
            icon_source = cover_path
        else:
            icon_source = first_image_path

        for icon, res in self.iconset.items():
            spec_cover = {
                "res": {
                    "w": {
                        "min": res[0],
                        "max": res[0]
                    },
                    "h": {
                        "min": res[1],
                        "max": res[1]
                    }
                }
            }

            icon_old_path = os.path.join(self.in_dir, icon)
            icon_new_path = os.path.join(self.out_dir, icon)
            if icon in os.listdir(self.in_dir) and not FormatVerify.check_file(icon_old_path, spec=spec_cover):
                StickerConvert(icon_old_path, icon_new_path, spec_cover, self.cb_msg).convert()
            else:
                StickerConvert(icon_source, icon_new_path, spec_cover, self.cb_msg).convert()
                
        MetadataHandler.set_metadata(self.out_dir, author=author, title=title)

    def create_xcode_proj(self, author, title):
        pack_path = os.path.join(self.out_dir, title)
        shutil.copytree('ios-message-stickers-template', pack_path)

        os.remove(os.path.join(pack_path, 'README.md'))
        shutil.rmtree(os.path.join(pack_path, 'stickers.xcodeproj/project.xcworkspace'), ignore_errors=True)
        shutil.rmtree(os.path.join(pack_path, 'stickers.xcodeproj/xcuserdata'), ignore_errors=True)

        with open(os.path.join(pack_path, 'stickers.xcodeproj/project.pbxproj'), encoding='utf-8') as f:
            pbxproj_data = f.read()
        
        pbxproj_data = pbxproj_data.replace('stickers StickerPackExtension', f'{title} StickerPackExtension')
        pbxproj_data = pbxproj_data.replace('stickers.app', f'{title}.app')
        pbxproj_data = pbxproj_data.replace('/* stickers */', f'/* {title} */')
        pbxproj_data = pbxproj_data.replace('name = stickers', f'name = {title}')
        pbxproj_data = pbxproj_data.replace('productName = stickers', f'productName = {title}')
        pbxproj_data = pbxproj_data.replace('/* Build configuration list for PBXProject "stickers" */', f'/* Build configuration list for PBXProject "{title}" */')
        pbxproj_data = pbxproj_data.replace('/* Build configuration list for PBXNativeTarget "stickers StickerPackExtension" */', f'/* Build configuration list for PBXNativeTarget "{title} StickerPackExtension" */')
        pbxproj_data = pbxproj_data.replace('/* Build configuration list for PBXNativeTarget "stickers" */', f'/* Build configuration list for PBXNativeTarget "{title}" */')
        pbxproj_data = pbxproj_data.replace('com.niklaspeterson', f'{title}.{author}')
        pbxproj_data = pbxproj_data.replace('stickers/Info.plist', f'{title}/Info.plist')

        with open(os.path.join(pack_path, 'stickers.xcodeproj/project.pbxproj'), 'w+', encoding='utf-8') as f:
            f.write(pbxproj_data)
        
        # packname StickerPackExtension/Stickers.xcstickers/Sticker Pack.stickerpack
        stickers_path = os.path.join(pack_path, 'stickers StickerPackExtension/Stickers.xcstickers/Sticker Pack.stickerpack')
        
        for i in os.listdir(stickers_path):
            if i.endswith('.sticker'):
                shutil.rmtree(os.path.join(stickers_path, i))
        
        stickers_lst = []
        for i in sorted(os.listdir(self.in_dir)):
            if CodecInfo.get_file_ext(i) == '.png' and i != 'cover.png' and i not in self.iconset:
                sticker_dir = f'{os.path.splitext(i)[0]}.sticker' # 0.sticker
                stickers_lst.append(sticker_dir)
                # packname StickerPackExtension/Stickers.xcstickers/Sticker Pack.stickerpack/0.sticker
                sticker_path = os.path.join(stickers_path, sticker_dir)
                os.mkdir(sticker_path)
                # packname StickerPackExtension/Stickers.xcstickers/Sticker Pack.stickerpack/0.sticker/0.png
                shutil.copy(os.path.join(self.in_dir, i), os.path.join(sticker_path, i))

                dict = {
                    'info': {
                        'author': 'xcode',
                        'version': 1,
                    },
                    'properties': {
                        'filename': i
                    }
                }

                # packname StickerPackExtension/Stickers.xcstickers/Sticker Pack.stickerpack/0.sticker/Contents.json
                with open(os.path.join(sticker_path, 'Contents.json'), 'w+') as f:
                    json.dump(dict, f, indent=2)
        
        # packname StickerPackExtension/Stickers.xcstickers/Sticker Pack.stickerpack/Contents.json
        with open(os.path.join(stickers_path, 'Contents.json')) as f:
            dict = json.load(f)
        
        dict['stickers'] = []
        for i in stickers_lst:
            dict['stickers'].append({'filename': i})
        
        with open(os.path.join(stickers_path, 'Contents.json'), 'w+') as f:
            json.dump(dict, f, indent=2)

        # packname StickerPackExtension/Stickers.xcstickers/iMessage App Icon.stickersiconset
        iconset_path = os.path.join(pack_path, 'stickers StickerPackExtension/Stickers.xcstickers/iMessage App Icon.stickersiconset')

        for i in os.listdir(iconset_path):
            if os.path.splitext(i) == '.png':
                os.remove(os.path.join(iconset_path, i))

        icons_lst = []
        for i in self.iconset:
            shutil.copy(os.path.join(self.in_dir, i), os.path.join(iconset_path, i))
            icons_lst.append(i)
        
        # packname/Info.plist
        plist_path = os.path.join(pack_path, 'stickers/Info.plist')
        with open(plist_path, 'rb') as f:
            plist_dict = plistlib.load(f)
        plist_dict['CFBundleDisplayName'] = title

        with open(plist_path, 'wb+') as f:
            plistlib.dump(plist_dict, f)

        os.rename(os.path.join(pack_path, 'stickers'), os.path.join(pack_path, f'{title}'))
        os.rename(os.path.join(pack_path, 'stickers StickerPackExtension'), os.path.join(pack_path, f'{title} StickerPackExtension'))
        os.rename(os.path.join(pack_path, 'stickers.xcodeproj'), os.path.join(pack_path, f'{title}.xcodeproj'))
    
    @staticmethod
    def start(opt_output, opt_comp, opt_cred, cb_msg=print, cb_msg_block=input, cb_bar=None, out_dir=None, **kwargs):
        exporter = XcodeImessage(opt_output, opt_comp, opt_cred, cb_msg, cb_msg_block, cb_bar, out_dir)
        return exporter.create_imessage_xcode()
