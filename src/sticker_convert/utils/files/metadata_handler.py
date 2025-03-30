#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sticker_convert.utils.files.json_resources_loader import INPUT_JSON, OUTPUT_JSON
from sticker_convert.utils.media.codec_info import CodecInfo

RELATED_EXTENSIONS = (
    ".png",
    ".apng",
    ".jpg",
    ".jpeg",
    ".gif",
    ".tgs",
    ".lottie",
    ".json",
    ".svg",
    ".mp4",
    ".mkv",
    ".mov",
    ".webm",
    ".webp",
    ".avi",
    ".m4a",
    ".mp3",
    ".wastickers",
)
RELATED_NAME = (
    "title.txt",
    "author.txt",
    "emoji.txt",
    "export-result.txt",
    ".DS_Store",
    "._.DS_Store",
)

BLACKLIST_PREFIX = ("cover",)
BLACKLIST_SUFFIX = (".txt", ".m4a", ".wastickers", ".zip", ".DS_Store", "._.DS_Store")

XCODE_IMESSAGE_ICONSET = {
    "App-Store-1024x1024pt.png": (1024, 1024),
    "iPad-Settings-29pt@2x.png": (58, 58),
    "iPhone-settings-29pt@2x.png": (58, 58),
    "iPhone-settings-29pt@3x.png": (87, 87),
    "Messages27x20pt@2x.png": (54, 40),
    "Messages27x20pt@3x.png": (81, 60),
    "Messages32x24pt@2x.png": (64, 48),
    "Messages32x24pt@3x.png": (96, 72),
    "Messages-App-Store-1024x768pt.png": (1024, 768),
    "Messages-iPad-67x50pt@2x.png": (134, 100),
    "Messages-iPad-Pro-74x55pt@2x.png": (148, 110),
    "Messages-iPhone-60x45pt@2x.png": (120, 90),
    "Messages-iPhone-60x45pt@3x.png": (180, 135),
}


def check_if_xcodeproj(path: Path) -> bool:
    if not path.is_dir():
        return False
    for i in path.iterdir():
        if i.suffix == ".xcodeproj":
            return True
    return False


class MetadataHandler:
    @staticmethod
    def get_files_related_to_sticker_convert(
        directory: Path, include_archive: bool = True
    ) -> List[Path]:
        files = [
            i
            for i in sorted(directory.iterdir())
            if i.stem in RELATED_NAME
            or i.name in XCODE_IMESSAGE_ICONSET
            or i.suffix in RELATED_EXTENSIONS
            or (include_archive and i.name.startswith("archive_"))
            or check_if_xcodeproj(i)
        ]

        return files

    @staticmethod
    def get_stickers_present(directory: Path) -> List[Path]:
        stickers_present = [
            i
            for i in sorted(directory.iterdir())
            if Path(directory, i.name).is_file()
            and not i.name.startswith(BLACKLIST_PREFIX)
            and i.suffix not in BLACKLIST_SUFFIX
            and i.name not in XCODE_IMESSAGE_ICONSET
        ]

        return stickers_present

    @staticmethod
    def get_cover(directory: Path) -> Optional[Path]:
        stickers_present = sorted(directory.iterdir())
        for i in stickers_present:
            if Path(i).stem == "cover":
                return Path(directory, i.name)

        return None

    @staticmethod
    def get_metadata(
        directory: Path,
        title: Optional[str] = None,
        author: Optional[str] = None,
        emoji_dict: Optional[Dict[str, str]] = None,
    ) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, str]]]:
        title_path = Path(directory, "title.txt")
        if not title and title_path.is_file():
            with open(title_path, encoding="utf-8") as f:
                title = f.read().strip()

        author_path = Path(directory, "author.txt")
        if not author and author_path.is_file():
            with open(author_path, encoding="utf-8") as f:
                author = f.read().strip()

        emoji_path = Path(directory, "emoji.txt")
        if not emoji_dict and emoji_path.is_file():
            with open(emoji_path, "r", encoding="utf-8") as f:
                emoji_dict = json.load(f)

        return title, author, emoji_dict

    @staticmethod
    def set_metadata(
        directory: Path,
        title: Optional[str] = None,
        author: Optional[str] = None,
        emoji_dict: Optional[Dict[str, str]] = None,
        newline: bool = False,
    ) -> None:
        title_path = Path(directory, "title.txt")
        if title is not None:
            with open(title_path, "w+", encoding="utf-8") as f:
                f.write(title)
                if newline:
                    f.write("\n")

        author_path = Path(directory, "author.txt")
        if author is not None:
            with open(author_path, "w+", encoding="utf-8") as f:
                f.write(author)
                if newline:
                    f.write("\n")

        emoji_path = Path(directory, "emoji.txt")
        if emoji_dict is not None:
            with open(emoji_path, "w+", encoding="utf-8") as f:
                json.dump(emoji_dict, f, indent=4, ensure_ascii=False)

    @staticmethod
    def check_metadata_provided(
        input_dir: Path, input_option: str, metadata: str
    ) -> bool:
        """
        Check if metadata provided via .txt file (if from local)
        or will be provided by input source (if not from local)
        Does not check if metadata provided via user input in GUI or flag options
        metadata = 'title' or 'author'
        """
        input_presets = INPUT_JSON
        assert input_presets

        if input_option == "local":
            metadata_file_path = Path(input_dir, f"{metadata}.txt")
            metadata_provided = metadata_file_path.is_file()
            if metadata_provided:
                with open(metadata_file_path, encoding="utf-8") as f:
                    metadata_provided = bool(f.read())
        else:
            metadata_provided = input_presets[input_option]["metadata_provides"][
                metadata
            ]

        return metadata_provided

    @staticmethod
    def check_metadata_required(output_option: str, metadata: str) -> bool:
        # metadata = 'title' or 'author'
        output_presets = OUTPUT_JSON
        assert output_presets
        return output_presets[output_option]["metadata_requirements"][metadata]

    @staticmethod
    def generate_emoji_file(directory: Path, default_emoji: str = "") -> None:
        emoji_path = Path(directory, "emoji.txt")
        emoji_dict = None
        if emoji_path.is_file():
            with open(emoji_path, "r", encoding="utf-8") as f:
                emoji_dict = json.load(f)

        emoji_dict_new = {}
        for file in sorted(directory.iterdir()):
            if not Path(directory, file).is_file() and CodecInfo.get_file_ext(file) in (
                ".txt",
                ".m4a",
            ):
                continue
            file_name = Path(file).stem
            if emoji_dict and file_name in emoji_dict:
                emoji_dict_new[file_name] = emoji_dict[file_name]
            else:
                emoji_dict_new[file_name] = default_emoji

        with open(emoji_path, "w+", encoding="utf-8") as f:
            json.dump(emoji_dict_new, f, indent=4, ensure_ascii=False)

    @staticmethod
    def split_sticker_packs(
        directory: Path,
        title: str,
        file_per_pack: Optional[int] = None,
        file_per_anim_pack: Optional[int] = None,
        file_per_image_pack: Optional[int] = None,
        separate_image_anim: bool = True,
    ) -> Dict[str, List[Path]]:
        # {pack_1: [sticker1_path, sticker2_path]}
        packs: Dict[str, List[Path]] = {}

        if file_per_pack is None:
            file_per_pack = (
                file_per_anim_pack
                if file_per_anim_pack is not None
                else file_per_image_pack
            )
        else:
            file_per_anim_pack = file_per_pack
            file_per_image_pack = file_per_pack

        stickers_present = MetadataHandler.get_stickers_present(directory)

        processed = 0

        if separate_image_anim is True:
            image_stickers: List[Path] = []
            anim_stickers: List[Path] = []

            image_pack_count = 0
            anim_pack_count = 0

            anim_present = False
            image_present = False

            for processed, file in enumerate(stickers_present):
                file_path = directory / file

                if CodecInfo.is_anim(file_path):
                    anim_stickers.append(file_path)
                else:
                    image_stickers.append(file_path)

                anim_present = anim_present or len(anim_stickers) > 0
                image_present = image_present or len(image_stickers) > 0

                finished_all = processed == len(stickers_present) - 1

                if len(anim_stickers) == file_per_anim_pack or (
                    finished_all and len(anim_stickers) > 0
                ):
                    suffix = f"{'-anim' if image_present else ''}{'-' + str(anim_pack_count) if anim_pack_count > 0 else ''}"
                    title_current = str(title) + suffix
                    packs[title_current] = anim_stickers.copy()
                    anim_stickers = []
                    anim_pack_count += 1
                if len(image_stickers) == file_per_image_pack or (
                    finished_all and len(image_stickers) > 0
                ):
                    suffix = f"{'-image' if anim_present else ''}{'-' + str(image_pack_count) if image_pack_count > 0 else ''}"
                    title_current = str(title) + suffix
                    packs[title_current] = image_stickers.copy()
                    image_stickers = []
                    image_pack_count += 1

        else:
            stickers: List[Path] = []
            pack_count = 0

            for processed, file in enumerate(stickers_present):
                file_path = Path(directory, file)

                stickers.append(file_path)

                finished_all = processed == len(stickers_present) - 1

                if len(stickers) == file_per_pack or (
                    finished_all and len(stickers) > 0
                ):
                    suffix = f"{'-' + str(pack_count) if pack_count > 0 else ''}"
                    title_current = str(title) + suffix
                    packs[title_current] = stickers.copy()
                    stickers = []
                    pack_count += 1

        return packs
