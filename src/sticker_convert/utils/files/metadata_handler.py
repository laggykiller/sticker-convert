#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from sticker_convert.definitions import ROOT_DIR
from sticker_convert.utils.files.json_manager import JsonManager
from sticker_convert.utils.media.codec_info import CodecInfo


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
        dir: Path, include_archive: bool = True
    ) -> list[Path]:
        from sticker_convert.uploaders.xcode_imessage import XcodeImessageIconset

        xcode_iconset = XcodeImessageIconset().iconset
        related_extensions = (
            ".png",
            ".apng",
            ".jpg",
            ".jpeg",
            ".gif",
            ".tgs",
            ".lottie",
            ".json",
            ".mp4",
            ".mkv",
            ".mov",
            ".webm",
            ".webp",
            ".avi",
            ".m4a",
            ".wastickers",
        )
        related_name = (
            "title.txt",
            "author.txt",
            "emoji.txt",
            "export-result.txt",
            ".DS_Store",
            "._.DS_Store",
        )

        files = [
            i
            for i in sorted(dir.iterdir())
            if i.stem in related_name
            or i.name in xcode_iconset
            or i.suffix in related_extensions
            or (include_archive and i.name.startswith("archive_"))
            or check_if_xcodeproj(i)
        ]

        return files

    @staticmethod
    def get_stickers_present(dir: Path) -> list[Path]:
        from sticker_convert.uploaders.xcode_imessage import XcodeImessageIconset

        blacklist_prefix = ("cover",)
        blacklist_suffix = (".txt", ".m4a", ".wastickers", ".DS_Store", "._.DS_Store")
        xcode_iconset = XcodeImessageIconset().iconset

        stickers_present = [
            i
            for i in sorted(dir.iterdir())
            if Path(dir, i.name).is_file()
            and not i.name.startswith(blacklist_prefix)
            and i.suffix not in blacklist_suffix
            and i.name not in xcode_iconset
        ]

        return stickers_present

    @staticmethod
    def get_cover(dir: Path) -> Optional[Path]:
        stickers_present = sorted(dir.iterdir())
        for i in stickers_present:
            if Path(i).stem == "cover":
                return Path(dir, i.name)

        return None

    @staticmethod
    def get_metadata(
        dir: Path,
        title: Optional[str] = None,
        author: Optional[str] = None,
        emoji_dict: Optional[dict[str, str]] = None,
    ) -> tuple[Optional[str], Optional[str], Optional[dict[str, str]]]:
        title_path = Path(dir, "title.txt")
        if not title and title_path.is_file():
            with open(title_path, encoding="utf-8") as f:
                title = f.read().strip()

        author_path = Path(dir, "author.txt")
        if not author and author_path.is_file():
            with open(author_path, encoding="utf-8") as f:
                author = f.read().strip()

        emoji_path = Path(dir, "emoji.txt")
        if not emoji_dict and emoji_path.is_file():
            with open(emoji_path, "r", encoding="utf-8") as f:
                emoji_dict = json.load(f)

        return title, author, emoji_dict

    @staticmethod
    def set_metadata(
        dir: Path,
        title: Optional[str] = None,
        author: Optional[str] = None,
        emoji_dict: Optional[dict[str, str]] = None,
    ):
        title_path = Path(dir, "title.txt")
        if title is not None:
            with open(title_path, "w+", encoding="utf-8") as f:
                f.write(title)

        author_path = Path(dir, "author.txt")
        if author is not None:
            with open(author_path, "w+", encoding="utf-8") as f:
                f.write(author)

        emoji_path = Path(dir, "emoji.txt")
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
        input_presets = JsonManager.load_json(ROOT_DIR / "resources/input.json")
        assert input_presets

        if input_option == "local":
            metadata_file_path = Path(input_dir, f"{metadata}.txt")
            metadata_provided = metadata_file_path.is_file()
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
        output_presets = JsonManager.load_json(ROOT_DIR / "resources/output.json")
        assert output_presets
        return output_presets[output_option]["metadata_requirements"][metadata]

    @staticmethod
    def generate_emoji_file(dir: Path, default_emoji: str = ""):
        emoji_path = Path(dir, "emoji.txt")
        emoji_dict = None
        if emoji_path.is_file():
            with open(emoji_path, "r", encoding="utf-8") as f:
                emoji_dict = json.load(f)

        emoji_dict_new = {}
        for file in sorted(dir.iterdir()):
            if not Path(dir, file).is_file() and CodecInfo.get_file_ext(file) in (
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
        dir: Path,
        title: str,
        file_per_pack: Optional[int] = None,
        file_per_anim_pack: Optional[int] = None,
        file_per_image_pack: Optional[int] = None,
        separate_image_anim: bool = True,
    ) -> dict[str, list[Path]]:
        # {pack_1: [sticker1_path, sticker2_path]}
        packs: dict[str, list[Path]] = {}

        if file_per_pack is None:
            file_per_pack = (
                file_per_anim_pack
                if file_per_anim_pack is not None
                else file_per_image_pack
            )
        else:
            file_per_anim_pack = file_per_pack
            file_per_image_pack = file_per_pack

        stickers_present = MetadataHandler.get_stickers_present(dir)

        processed = 0

        if separate_image_anim is True:
            image_stickers: list[Path] = []
            anim_stickers: list[Path] = []

            image_pack_count = 0
            anim_pack_count = 0

            anim_present = False
            image_present = False

            for processed, file in enumerate(stickers_present):
                file_path = dir / file

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
            stickers: list[Path] = []
            pack_count = 0

            for processed, file in enumerate(stickers_present):
                file_path = Path(dir, file)

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
