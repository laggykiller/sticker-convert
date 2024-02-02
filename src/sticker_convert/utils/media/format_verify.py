#!/usr/bin/env python3
import os
from typing import Optional, Union

from .codec_info import CodecInfo  # type: ignore
from ...job_option import CompOption # type: ignore


class FormatVerify:
    @staticmethod
    def check_file(file: str, spec: CompOption) -> bool:
        if FormatVerify.check_presence(file) == False:
            return False

        file_info = CodecInfo(file)

        return (
            FormatVerify.check_file_res(file, res=spec.res, square=spec.square, file_info=file_info)
            and FormatVerify.check_file_fps(file, fps=spec.fps, file_info=file_info)
            and FormatVerify.check_file_duration(file, duration=spec.duration, file_info=file_info)
            and FormatVerify.check_file_size(file, size=spec.size_max, file_info=file_info)
            and FormatVerify.check_animated(file, animated=spec.animated, file_info=file_info)
            and FormatVerify.check_format(file, fmt=spec.format, file_info=file_info)
        )

    @staticmethod
    def check_presence(file: str) -> bool:
        return os.path.isfile(file)

    @staticmethod
    def check_file_res(
        file: str,
        res: Optional[list[list[int]]] = None,
        square: Optional[bool] = None,
        file_info: Optional[CodecInfo] = None
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
        if square and file_height != file_width:
            return False

        return True

    @staticmethod
    def check_file_fps(
        file: str,fps: Optional[list[int]],
        file_info: Optional[CodecInfo] = None
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
        file: str,
        duration: Optional[list[str]] = None,
        file_info: Optional[CodecInfo] = None
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
        file: str,
        size: Optional[list[int]] = None,
        file_info: Optional[CodecInfo] = None
    ) -> bool:
        
        file_size = os.path.getsize(file)
        if file_info:
            file_animated = file_info.is_animated
        else:
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
    def check_animated(
        file: str,
        animated: Optional[bool] = None,
        file_info: Optional[CodecInfo] = None
    ) -> bool:
        
        if file_info:
            file_animated = file_info.is_animated
        else:
            file_animated = CodecInfo.is_anim(file)

        if animated != None and file_animated != animated:
            return False

        return True

    @staticmethod
    def check_format(
        file: str,
        fmt: list[Union[list[str], str, None]] = None,
        file_info: Optional[CodecInfo] = None
    ):
        
        if file_info:
            file_animated = file_info.is_animated
            file_ext = file_info.file_ext
        else:
            file_animated = CodecInfo.is_anim(file)
            file_ext = CodecInfo.get_file_ext(file)
        
        jpg_exts = (".jpg", ".jpeg")
        png_exts = (".png", ".apng")

        if file_animated:
            valid_fmt = fmt[1]
        else:
            valid_fmt = fmt[0]

        if isinstance(valid_fmt, str):
            if file_ext == valid_fmt:
                return True
            elif file_ext in jpg_exts and valid_fmt in jpg_exts:
                return True
            elif file_ext in png_exts and valid_fmt in png_exts:
                return True
            else:
                return False
            
        elif isinstance(valid_fmt, list):
            if file_ext in valid_fmt:
                return True
            elif file_ext in jpg_exts and (".jpg" in valid_fmt or ".jpeg" in valid_fmt):
                return True
            elif file_ext in png_exts and (".png" in valid_fmt or ".apng" in valid_fmt):
                return True
            else:
                return False
            
        elif valid_fmt == None:
            return False
        else:
            raise TypeError(f"valid_fmt should be either str, list or None. {valid_fmt} was given")