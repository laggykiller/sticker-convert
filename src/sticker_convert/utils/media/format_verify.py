#!/usr/bin/env python3
import os
from fractions import Fraction
from pathlib import Path
from typing import Optional, Tuple, Union

from sticker_convert.job_option import CompOption
from sticker_convert.utils.media.codec_info import CodecInfo


class FormatVerify:
    @staticmethod
    def check_file(file: Union[Path, bytes], spec: CompOption) -> bool:
        if FormatVerify.check_presence(file) is False:
            return False

        file_info = CodecInfo(file)

        return (
            FormatVerify.check_file_res(file, res=spec.get_res(), file_info=file_info)
            and FormatVerify.check_file_fps(
                file, fps=spec.get_fps(), file_info=file_info
            )
            and FormatVerify.check_file_duration(
                file, duration=spec.get_duration(), file_info=file_info
            )
            and FormatVerify.check_file_size(
                file, size=spec.get_size_max(), file_info=file_info
            )
            and FormatVerify.check_animated(
                file, animated=spec.animated, file_info=file_info
            )
            and FormatVerify.check_format(
                file, fmt=spec.get_format(), file_info=file_info
            )
        )

    @staticmethod
    def check_presence(file: Union[Path, bytes]) -> bool:
        if isinstance(file, Path):
            return Path(file).is_file()
        return True

    @staticmethod
    def check_file_res(
        file: Union[Path, bytes],
        res: Tuple[
            Tuple[Optional[int], Optional[int]], Tuple[Optional[int], Optional[int]]
        ],
        file_info: Optional[CodecInfo] = None,
    ) -> bool:
        if file_info:
            file_width, file_height = file_info.res
        else:
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

        min_ratio = None
        if res[0][0] and res[1][0]:
            min_ratio = Fraction(res[0][0], res[1][0])

        max_ratio = None
        if res[0][1] and res[1][1]:
            max_ratio = Fraction(res[0][1], res[1][1])

        file_ratio = Fraction(file_width, file_height)

        if min_ratio is not None and max_ratio is not None:
            if min_ratio == max_ratio:
                return True if file_ratio == min_ratio else False
            else:
                return True

        if min_ratio is not None:
            return True if file_ratio == min_ratio else False
        if max_ratio is not None:
            return True if file_ratio == max_ratio else False

        return True

    @staticmethod
    def check_file_fps(
        file: Union[Path, bytes],
        fps: Tuple[Optional[int], Optional[int]],
        file_info: Optional[CodecInfo] = None,
    ) -> bool:
        if file_info:
            file_fps = file_info.fps
        else:
            file_fps = CodecInfo.get_file_fps(file)

        if fps and fps[0] and file_fps < fps[0]:
            return False
        if fps and fps[1] and file_fps > fps[1]:
            return False

        return True

    @staticmethod
    def check_file_duration(
        file: Union[Path, bytes],
        duration: Tuple[Optional[int], Optional[int]],
        file_info: Optional[CodecInfo] = None,
    ) -> bool:
        if file_info:
            file_duration = file_info.duration
        else:
            file_duration = CodecInfo.get_file_duration(file)

        if file_duration == 0:
            return True
        if duration and duration[0] and file_duration < duration[0]:
            return False
        if duration and duration[1] and file_duration > duration[1]:
            return False

        return True

    @staticmethod
    def check_file_size(
        file: Union[Path, bytes],
        size: Tuple[Optional[int], Optional[int]],
        file_info: Optional[CodecInfo] = None,
    ) -> bool:
        if isinstance(file, Path):
            file_size = os.path.getsize(file)
        else:
            file_size = len(file)

        if file_info:
            file_animated = file_info.is_animated
        else:
            file_animated = CodecInfo.is_anim(file)

        if file_animated is True:
            if not size[1]:
                return True
            elif file_size > size[1]:
                return False
        else:
            if not size[0]:
                return True
            elif file_size > size[0]:
                return False

        return True

    @staticmethod
    def check_animated(
        file: Union[Path, bytes],
        animated: Optional[bool] = None,
        file_info: Optional[CodecInfo] = None,
    ) -> bool:
        if file_info:
            file_animated = file_info.is_animated
        else:
            file_animated = CodecInfo.is_anim(file)

        if animated is not None and file_animated != animated:
            return False

        return True

    @staticmethod
    def check_format(
        file: Union[Path, bytes],
        fmt: Tuple[Tuple[str, ...], Tuple[str, ...]],
        file_info: Optional[CodecInfo] = None,
    ) -> bool:
        if file_info:
            file_animated = file_info.is_animated
            file_ext = file_info.file_ext
        else:
            file_animated = CodecInfo.is_anim(file)
            if isinstance(file, Path):
                file_ext = CodecInfo.get_file_ext(file)
            else:
                file_ext = "." + CodecInfo.get_file_codec(file)

        jpg_exts = (".jpg", ".jpeg")
        png_exts = (".png", ".apng")

        if file_animated:
            valid_fmt = fmt[1]
        else:
            valid_fmt = fmt[0]

        if len(valid_fmt) == 0:
            return True
        if file_ext in valid_fmt:
            return True
        if file_ext in jpg_exts and (".jpg" in valid_fmt or ".jpeg" in valid_fmt):
            return True
        if file_ext in png_exts and (".png" in valid_fmt or ".apng" in valid_fmt):
            return True
        return False
