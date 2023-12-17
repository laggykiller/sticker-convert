#!/usr/bin/env python3
from __future__ import annotations
import os
import json
from typing import Optional

from ..media.codec_info import CodecInfo  # type: ignore
from .json_manager import JsonManager  # type: ignore


class MetadataHandler:
    @staticmethod
    def get_stickers_present(dir: str) -> list[str]:
        from ...uploaders.xcode_imessage import XcodeImessageIconset  # type: ignore

        blacklist_prefix = ('cover',)
        blacklist_suffix = (".txt", ".m4a", ".wastickers", ".DS_Store", "._.DS_Store")
        xcode_iconset = XcodeImessageIconset().iconset
        
        stickers_present = [
            i
            for i in sorted(os.listdir(dir))
            if os.path.isfile(os.path.join(dir, i)) and
            not i.startswith(blacklist_prefix) and
            not i.endswith(blacklist_suffix) and
            not i in xcode_iconset
        ]

        return stickers_present

    @staticmethod
    def get_cover(dir: str) -> Optional[str]:
        stickers_present = sorted(os.listdir(dir))
        for i in stickers_present:
            if os.path.splitext(i)[0] == "cover":
                return os.path.join(dir, i)

        return None

    @staticmethod
    def get_metadata(
        dir: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        emoji_dict: Optional[dict[str, str]] = None,
    ) -> tuple[Optional[str], Optional[str], Optional[dict[str, str]]]:
        title_path = os.path.join(dir, "title.txt")
        if not title and os.path.isfile(title_path):
            with open(title_path, encoding="utf-8") as f:
                title = f.read().strip()

        author_path = os.path.join(dir, "author.txt")
        if not author and os.path.isfile(author_path):
            with open(author_path, encoding="utf-8") as f:
                author = f.read().strip()

        emoji_path = os.path.join(dir, "emoji.txt")
        if not emoji_dict and os.path.isfile(emoji_path):
            with open(emoji_path, "r", encoding="utf-8") as f:
                emoji_dict = json.load(f)

        return title, author, emoji_dict

    @staticmethod
    def set_metadata(
        dir: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        emoji_dict: Optional[dict[str, str]] = None,
    ):
        title_path = os.path.join(dir, "title.txt")
        if title != None:
            with open(title_path, "w+", encoding="utf-8") as f:
                f.write(title)  # type: ignore[arg-type]

        author_path = os.path.join(dir, "author.txt")
        if author != None:
            with open(author_path, "w+", encoding="utf-8") as f:
                f.write(author)  # type: ignore[arg-type]

        emoji_path = os.path.join(dir, "emoji.txt")
        if emoji_dict != None:
            with open(emoji_path, "w+", encoding="utf-8") as f:
                json.dump(emoji_dict, f, indent=4, ensure_ascii=False)

    @staticmethod
    def check_metadata_provided(
        input_dir: str, input_option: str, metadata: str
    ) -> bool:
        """
        Check if metadata provided via .txt file (if from local)
        or will be provided by input source (if not from local)
        Does not check if metadata provided via user input in GUI or flag options
        metadata = 'title' or 'author'
        """
        input_presets = JsonManager.load_json("resources/input.json")

        if input_option == "local":
            metadata_file_path = os.path.join(input_dir, f"{metadata}.txt")
            metadata_provided = os.path.isfile(metadata_file_path)
            if metadata_provided:
                with open(metadata_file_path, encoding="utf-8") as f:
                    metadata_provided = True if f.read() else False
        else:
            metadata_provided = input_presets[input_option]["metadata_provides"][
                metadata
            ]

        return metadata_provided

    @staticmethod
    def check_metadata_required(output_option: str, metadata: str) -> bool:
        # metadata = 'title' or 'author'
        output_presets = JsonManager.load_json("resources/output.json")
        return output_presets[output_option]["metadata_requirements"][metadata]

    @staticmethod
    def generate_emoji_file(dir: str, default_emoji: str = ""):
        emoji_path = os.path.join(dir, "emoji.txt")
        emoji_dict = None
        if os.path.isfile(emoji_path):
            with open(emoji_path, "r", encoding="utf-8") as f:
                emoji_dict = json.load(f)

        emoji_dict_new = {}
        for file in sorted(os.listdir(dir)):
            if not os.path.isfile(os.path.join(dir, file)) and CodecInfo.get_file_ext(
                file
            ) in (".txt", ".m4a"):
                continue
            file_name = os.path.splitext(file)[0]
            if emoji_dict and file_name in emoji_dict:
                emoji_dict_new[file_name] = emoji_dict[file_name]
            else:
                emoji_dict_new[file_name] = default_emoji

        with open(emoji_path, "w+", encoding="utf-8") as f:
            json.dump(emoji_dict_new, f, indent=4, ensure_ascii=False)

    @staticmethod
    def split_sticker_packs(
        dir: str,
        title: str,
        file_per_pack: Optional[int] = None,
        file_per_anim_pack: Optional[int] = None,
        file_per_image_pack: Optional[int] = None,
        separate_image_anim: bool = True,
    ) -> dict:
        # {pack_1: [sticker1_path, sticker2_path]}
        packs = {}

        if file_per_pack == None:
            file_per_pack = (
                file_per_anim_pack
                if file_per_anim_pack != None
                else file_per_image_pack
            )
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

            for processed, file in enumerate(stickers_present):
                file_path = os.path.join(dir, file)

                if CodecInfo.is_anim(file_path):
                    anim_stickers.append(file_path)
                else:
                    image_stickers.append(file_path)

                anim_present = anim_present or len(anim_stickers) > 0
                image_present = image_present or len(image_stickers) > 0

                finished_all = True if processed == len(stickers_present) - 1 else False

                if len(anim_stickers) == file_per_anim_pack or (
                    finished_all and len(anim_stickers) > 0
                ):
                    suffix = f'{"-anim" if image_present else ""}{"-" + str(anim_pack_count) if anim_pack_count > 0 else ""}'
                    title_current = str(title) + suffix
                    packs[title_current] = anim_stickers.copy()
                    anim_stickers = []
                    anim_pack_count += 1
                if len(image_stickers) == file_per_image_pack or (
                    finished_all and len(image_stickers) > 0
                ):
                    suffix = f'{"-image" if anim_present else ""}{"-" + str(image_pack_count) if image_pack_count > 0 else ""}'
                    title_current = str(title) + suffix
                    packs[title_current] = image_stickers.copy()
                    image_stickers = []
                    image_pack_count += 1

        else:
            stickers = []
            pack_count = 0

            for processed, file in enumerate(stickers_present):
                file_path = os.path.join(dir, file)

                stickers.append(file_path)

                finished_all = True if processed == len(stickers_present) - 1 else False

                if len(stickers) == file_per_pack or (
                    finished_all and len(stickers) > 0
                ):
                    suffix = f'{"-" + str(pack_count) if pack_count > 0 else ""}'
                    title_current = str(title) + suffix
                    packs[title_current] = stickers.copy()
                    stickers = []
                    pack_count += 1

        return packs
