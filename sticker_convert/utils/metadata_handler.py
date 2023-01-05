import os
import json
from utils.codec_info import CodecInfo

class MetadataHandler:
    @staticmethod
    def get_stickers_present(dir):
        from uploaders.xcode_imessage import XcodeImessage

        stickers_present = os.listdir(dir)
        if 'cover.png' in stickers_present:
            stickers_present.remove('cover.png')
        for icon in XcodeImessage().iconset:
            if icon in stickers_present:
                stickers_present.remove(icon)
        if '.DS_Store' in stickers_present:
            stickers_present.remove('.DS_Store')
        if '._.DS_Store' in stickers_present:
            stickers_present.remove('._.DS_Store')
        stickers_present = [i for i in stickers_present if not i.endswith('.txt')]

        return stickers_present
    
    @staticmethod
    def get_metadata(dir, title=None, author=None, emoji_dict=None):
        title_path = os.path.join(dir, 'title.txt')
        if title == None and os.path.isfile(title_path):
            with open(title_path, encoding='utf-8') as f:
                title = f.read().strip()

        author_path = os.path.join(dir, 'author.txt')
        if author == None and os.path.isfile(author_path):
            with open(author_path, encoding='utf-8') as f:
                author = f.read().strip()
        
        emoji_path = os.path.join(dir, 'emoji.txt')
        if emoji_dict == None and os.path.isfile(emoji_path):
            with open(emoji_path , "r", encoding='utf-8') as f:
                emoji_dict = json.load(f)
        
        return title, author, emoji_dict
    
    @staticmethod
    def set_metadata(dir, title=None, author=None, emoji_dict=None):
        title_path = os.path.join(dir, 'title.txt')
        if title != None:
            with open(title_path, 'w+', encoding='utf-8') as f:
                f.write(title)
        
        author_path = os.path.join(dir, 'author.txt')
        if author != None:
            with open(author_path, 'w+', encoding='utf-8') as f:
                f.write(author)
        
        emoji_path = os.path.join(dir, 'emoji.txt')
        if emoji_dict != None:
            with open(emoji_path, 'w+', encoding='utf-8') as f:
                json.dump(emoji_dict, f, indent=4, ensure_ascii=False)
    
    @staticmethod
    def generate_emoji_file(dir, default_emoji=''):
        emoji_path = os.path.join(dir, 'emoji.txt')
        emoji_dict = None
        if os.path.isfile(emoji_path):
            with open(emoji_path , "r", encoding='utf-8') as f:
                emoji_dict = json.load(f)

        emoji_dict_new = {}
        for file in os.listdir(dir):
            if CodecInfo.get_file_ext(file) == '.txt':
                continue
            file_name = os.path.splitext(file)[0]
            if emoji_dict and file_name in emoji_dict:
                emoji_dict_new[file_name] = emoji_dict[file_name]
            else:
                emoji_dict_new[file_name] = default_emoji
        
        with open(emoji_path, 'w+', encoding='utf-8') as f:
            json.dump(emoji_dict_new, f, indent=4, ensure_ascii=False)
    
    def split_sticker_packs(dir, title, file_per_pack=None, file_per_anim_pack=None, file_per_image_pack=None, separate_image_anim=True):
        # {pack_1: [sticker1_path, sticker2_path]}
        packs = {}

        if file_per_pack == None:
            file_per_pack = file_per_anim_pack if file_per_anim_pack != None else file_per_image_pack
        else:
            file_per_anim_pack = file_per_pack
            file_per_image_pack = file_per_pack

        stickers_present = MetadataHandler.get_stickers_present(dir)

        processed = 0

        if separate_image_anim == True:
            image_stickers = []
            anim_stickers = []

            image_pack_count = 0
            anim_pack_count = 0

            anim_present = False
            image_present = False

            for file in stickers_present:
                file_path = os.path.join(dir, file)

                if CodecInfo.is_anim(file_path):
                    anim_stickers.append(file_path)
                else:
                    image_stickers.append(file_path)
                    
                anim_present = anim_present or len(anim_stickers) > 0
                image_present = image_present or len(image_stickers) > 0
                
                processed += 1
                finished_all = True if processed == len(stickers_present) else False

                if len(anim_stickers) == file_per_anim_pack or (finished_all and len(anim_stickers) > 0):
                    suffix = f'{"-anim" if image_present else ""}{"-" + str(anim_pack_count) if anim_pack_count > 0 else ""}'
                    title_current = str(title) + suffix
                    packs[title_current] = anim_stickers.copy()
                    anim_stickers = []
                    anim_pack_count += 1
                if len(image_stickers) == file_per_image_pack or (finished_all and len(image_stickers) > 0):
                    suffix = f'{"-image" if anim_present else ""}{"-" + str(image_pack_count) if image_pack_count > 0 else ""}'
                    title_current = str(title) + suffix
                    packs[title_current] = image_stickers.copy()
                    image_stickers = []
                    image_pack_count += 1

        else:
            stickers = []
            pack_count = 0

            for file in stickers_present:
                file_path = os.path.join(dir, file)

                stickers.append(file_path)
                
                processed += 1
                finished_all = True if processed == len(stickers_present) else False

                if len(stickers) == file_per_pack or (finished_all and len(stickers) > 0):
                    suffix = f'{"-" + str(pack_count) if pack_count > 0 else ""}'
                    title = str(title) + suffix
                    packs[title] = stickers.copy()
                    stickers = []
                    pack_count += 1
        
        return packs
