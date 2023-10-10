#!/usr/bin/env python3
import os
import unicodedata
import re
from typing import Optional, Union

from .codec_info import CodecInfo  # type: ignore
from ...job_option import CompOption # type: ignore


class FormatVerify:
    @staticmethod
    def check_file(file: str, spec: CompOption) -> bool:
        return (
            FormatVerify.check_presence(file)
            and FormatVerify.check_file_res(file, res=spec.res, square=spec.square)
            and FormatVerify.check_file_fps(file, fps=spec.fps)
            and FormatVerify.check_file_size(file, size=spec.size_max)
            and FormatVerify.check_animated(file, animated=spec.animated)
            and FormatVerify.check_format(file, fmt=spec.format)
            and FormatVerify.check_duration(file, duration=spec.duration)
        )

    @staticmethod
    def check_presence(file: str) -> bool:
        return os.path.isfile(file)

    @staticmethod
    def check_file_res(
        file: str,
        res: Optional[list[list[int]]] = None,
        square: Optional[bool] = None
    ) -> bool:
        file_width, file_height = CodecInfo.get_file_res(file)

        if res:
            if res[0][0] and file_width < res[0][0]:
                return False
            if res[0][1] and file_width > res[0][1]:
                return False
            if res[1][0] and file_height < res[1][0]:
                return False
            if res[1][1] and file_height > res[1][1]:
                return False
        if square and file_height != file_width:
            return False

        return True

    @staticmethod
    def check_file_fps(file: str, fps: Optional[list[int]]) -> bool:
        file_fps = CodecInfo.get_file_fps(file)

        if fps and fps[0] and file_fps < fps[0]:
            return False
        if fps and fps[1] and file_fps > fps[1]:
            return False

        return True

    @staticmethod
    def check_file_size(file: str, size: Optional[list[int]] = None) -> bool:
        file_size = os.path.getsize(file)
        file_animated = CodecInfo.is_anim(file)

        if (
            file_animated == True
            and size
            and size[1] != None
            and file_size > size[1]
        ):
            return False
        if (
            file_animated == False
            and size
            and size[0] != None
            and file_size > size[0]
        ):
            return False

        return True

    @staticmethod
    def check_animated(file: str, animated: Optional[bool] = None) -> bool:
        if animated != None and CodecInfo.is_anim(file) != animated:
            return False

        return True

    @staticmethod
    def check_format(
        file: str,
        fmt: list[Union[list[str], str, None]] = None
    ):
        compat_ext = {
            ".jpg": ".jpeg",
            ".jpeg": ".jpg",
            ".png": ".apng",
            ".apng": ".png",
        }

        formats: list[str] = []

        if fmt == [None, None]:
            return True
        
        if FormatVerify.check_animated(file):
            if isinstance(fmt[1], list):
                formats = fmt[1].copy()
            else:
                formats.append(fmt[1])
        else:
            if isinstance(fmt[0], list):
                formats = fmt[0].copy()
            else:
                formats.append(fmt[0])

        for f in formats.copy():
            if f in compat_ext:
                formats.append(compat_ext.get(f))  # type: ignore[arg-type]

        if CodecInfo.get_file_ext(file) not in formats:
            return False

        return True

    @staticmethod
    def check_duration(file: str, duration: Optional[list[str]] = None) -> bool:
        file_duration = CodecInfo.get_file_duration(file)
        if duration and duration[0] and file_duration < duration[0]:
            return False
        if duration and duration[1] and file_duration > duration[1]:
            return False

        return True

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        # Based on https://gitlab.com/jplusplus/sanitize-filename/-/blob/master/sanitize_filename/sanitize_filename.py
        # Replace illegal character with '_'
        """Return a fairly safe version of the filename.

        We don't limit ourselves to ascii, because we want to keep municipality
        names, etc, but we do want to get rid of anything potentially harmful,
        and make sure we do not exceed Windows filename length limits.
        Hence a less safe blacklist, rather than a whitelist.
        """
        blacklist = ["\\", "/", ":", "*", "?", '"', "<", ">", "|", "\0"]
        reserved = [
            "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
            "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
            "LPT6", "LPT7", "LPT8", "LPT9",
        ]  # Reserved words on Windows
        filename = "".join(c if c not in blacklist else "_" for c in filename)
        # Remove all charcters below code point 32
        filename = "".join(c if 31 < ord(c) else "_" for c in filename)
        filename = unicodedata.normalize("NFKD", filename)
        filename = filename.rstrip(". ")  # Windows does not allow these at end
        filename = filename.strip()
        if all([x == "." for x in filename]):
            filename = "__" + filename
        if filename in reserved:
            filename = "__" + filename
        if len(filename) == 0:
            filename = "__"
        if len(filename) > 255:
            parts = re.split(r"/|\\", filename)[-1].split(".")
            if len(parts) > 1:
                ext = "." + parts.pop()
                filename = filename[: -len(ext)]
            else:
                ext = ""
            if filename == "":
                filename = "__"
            if len(ext) > 254:
                ext = ext[254:]
            maxl = 255 - len(ext)
            filename = filename[:maxl]
            filename = filename + ext
            # Re-check last character (if there was no extension)
            filename = filename.rstrip(". ")
            if len(filename) == 0:
                filename = "__"
        return filename
