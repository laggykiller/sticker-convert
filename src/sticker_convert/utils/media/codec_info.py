#!/usr/bin/env python3
from __future__ import annotations
import os
import mimetypes
from typing import Optional

import imageio.v3 as iio
from rlottie_python import LottieAnimation  # type: ignore
from PIL import Image, UnidentifiedImageError
import mmap


class CodecInfo:
    def __init__(self):
        mimetypes.init()
        vid_ext = []
        for ext in mimetypes.types_map:
            if mimetypes.types_map[ext].split("/")[0] == "video":
                vid_ext.append(ext)
        vid_ext.append(".webm")
        vid_ext.append(".webp")
        self.vid_ext = tuple(vid_ext)

    @staticmethod
    def get_file_fps(file: str) -> float:
        file_ext = CodecInfo.get_file_ext(file)

        if file_ext in ".tgs":
            with LottieAnimation.from_tgs(file) as anim:
                fps = anim.lottie_animation_get_framerate()
        else:
            if file_ext == ".webp":
                total_duration = 0
                frames = 0
                
                with open(file, "r+b") as f:
                    mm = mmap.mmap(f.fileno(), 0)
                    while True:
                        anmf_pos = mm.find(b"ANMF")
                        if anmf_pos == -1:
                            break
                        mm.seek(anmf_pos + 20)
                        frame_duration_32 = mm.read(4)
                        frame_duration = frame_duration_32[:-1] + bytes(
                            int(frame_duration_32[-1]) & 0b11111100
                        )
                        total_duration += int.from_bytes(frame_duration, "little")
                        frames += 1
                
                if frames == 0:
                    fps = 1
                else:
                    fps = frames / total_duration * 1000
            elif file_ext in (".gif", ".apng", ".png"):
                total_duration = 0
                frames = len([* iio.imiter(file, plugin="pillow")])

                for frame in range(frames):
                    metadata = iio.immeta(
                        file, index=frame, plugin="pillow", exclude_applied=False
                    )
                    total_duration += metadata.get("duration", 1000)
                
                if frames == 0 or total_duration == 0:
                    fps = 1
                else:
                    fps = frames / total_duration * 1000
            else:
                metadata = iio.immeta(file, plugin="pyav", exclude_applied=False)
                fps = metadata.get("fps", 1)

        return fps

    @staticmethod
    def get_file_codec(file: str) -> Optional[str]:
        codec = None
        try:
            codec = Image.open(file).format
        except UnidentifiedImageError:
            pass
        
        # Unable to distinguish apng and png
        if codec not in (None, 'PNG'):
            return codec.lower()
        else:
            metadata = iio.immeta(file, plugin="pyav", exclude_applied=False)
            codec = metadata.get("codec", None)
            return codec

    @staticmethod
    def get_file_res(file: str) -> tuple[int, int]:
        file_ext = CodecInfo.get_file_ext(file)

        if file_ext == ".tgs":
            with LottieAnimation.from_tgs(file) as anim:
                width, height = anim.lottie_animation_get_size()
        else:
            if file_ext == ".webp":
                plugin = "pillow"
            else:
                plugin = "pyav"
            frame = iio.imread(file, plugin=plugin, index=0)
            width, height, _ = frame.shape

        return width, height

    @staticmethod
    def get_file_frames(file: str) -> int:
        file_ext = CodecInfo.get_file_ext(file)

        frames = None

        if file_ext == ".tgs":
            with LottieAnimation.from_tgs(file) as anim:
                frames = anim.lottie_animation_get_totalframe()
        else:
            if file_ext == ".webp":
                frames = Image.open(file).n_frames
            else:
                frames = frames = len([* iio.imiter(file, plugin="pyav")])

        return frames

    @staticmethod
    def get_file_duration(file: str) -> float:
        # Return duration in miliseconds
        return CodecInfo.get_file_frames(file) / CodecInfo.get_file_fps(file) * 1000

    @staticmethod
    def get_file_ext(file: str) -> str:
        return os.path.splitext(file)[-1].lower()

    @staticmethod
    def is_anim(file: str) -> bool:
        if CodecInfo.get_file_frames(file) > 1:
            return True
        else:
            return False
