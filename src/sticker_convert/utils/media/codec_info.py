#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import mmap
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP

from PIL import Image, UnidentifiedImageError

class CodecInfo:
    def __init__(self, file: Path):
        self.file_ext = CodecInfo.get_file_ext(file)
        self.fps, self.frames, self.duration = CodecInfo.get_file_fps_frames_duration(file)
        self.codec = CodecInfo.get_file_codec(file)
        self.res = CodecInfo.get_file_res(file)
        self.is_animated = True if self.fps > 1 else False

    @staticmethod
    def get_file_fps_frames_duration(file: Path) -> tuple[float, int, int]:
        file_ext = CodecInfo.get_file_ext(file)

        if file_ext == ".tgs":
            fps, frames = CodecInfo._get_file_fps_frames_tgs(file)
            if fps > 0:
                duration = int(frames / fps * 1000)
            else:
                duration = 0
        else:
            if file_ext == ".webp":
                frames, duration = CodecInfo._get_file_frames_duration_webp(file)
            elif file_ext in (".gif", ".apng", ".png"):
                frames, duration = CodecInfo._get_file_frames_duration_pillow(file)
            else:
                frames, duration = CodecInfo._get_file_frames_duration_av(file)

            if duration > 0:
                fps = frames / duration * 1000
            else:
                fps = 0
        
        return fps, frames, duration

    @staticmethod
    def get_file_fps(file: Path) -> float:
        file_ext = CodecInfo.get_file_ext(file)

        if file_ext == ".tgs":
            return CodecInfo._get_file_fps_tgs(file)
        elif file_ext == ".webp":
            frames, duration = CodecInfo._get_file_frames_duration_webp(file)
        elif file_ext in (".gif", ".apng", ".png"):
            frames, duration = CodecInfo._get_file_frames_duration_pillow(file)
        else:
            frames, duration = CodecInfo._get_file_frames_duration_av(file, frames_to_iterate=10)
        
        if duration > 0:
            return frames / duration * 1000
        else:
            return 0
    
    @staticmethod
    def get_file_frames(file: Path, check_anim: bool = False) -> int:
        # If check_anim is True, return value > 1 means the file is animated
        file_ext = CodecInfo.get_file_ext(file)

        if file_ext == ".tgs":
            return CodecInfo._get_file_frames_tgs(file)
        elif file_ext in (".gif", ".webp", ".png", ".apng"):
            frames, _ = CodecInfo._get_file_frames_duration_pillow(file, frames_only=True)
        else:
            if check_anim == True:
                frames_to_iterate = 2
            else:
                frames_to_iterate = None
            frames, _ = CodecInfo._get_file_frames_duration_av(file, frames_only=True, frames_to_iterate=frames_to_iterate)

        return frames

    @staticmethod
    def get_file_duration(file: Path) -> int:
        # Return duration in miliseconds
        file_ext = CodecInfo.get_file_ext(file)

        if file_ext == ".tgs":
            fps, frames = CodecInfo._get_file_fps_frames_tgs(file)
            if fps > 0:
                duration = int(frames / fps * 1000)
            else:
                duration = 0
        elif file_ext == ".webp":
            _, duration = CodecInfo._get_file_frames_duration_webp(file)
        elif file_ext in (".gif", ".png", ".apng"):
            _, duration = CodecInfo._get_file_frames_duration_pillow(file)
        else:
            _, duration = CodecInfo._get_file_frames_duration_av(file)
        
        return duration
    
    @staticmethod
    def _get_file_fps_tgs(file: Path) -> int:
        from rlottie_python import LottieAnimation  # type: ignore

        if isinstance(file, Path):
            file = file.as_posix()

        with LottieAnimation.from_tgs(file) as anim:
            return anim.lottie_animation_get_framerate()

    @staticmethod    
    def _get_file_frames_tgs(file: Path) -> int:
        from rlottie_python import LottieAnimation  # type: ignore

        if isinstance(file, Path):
            file = file.as_posix()

        with LottieAnimation.from_tgs(file) as anim:
            return anim.lottie_animation_get_totalframe()
    
    @staticmethod
    def _get_file_fps_frames_tgs(file: Path) -> tuple[int, int]:
        from rlottie_python import LottieAnimation  # type: ignore

        if isinstance(file, Path):
            file = file.as_posix()

        with LottieAnimation.from_tgs(file) as anim:
            fps = anim.lottie_animation_get_framerate()
            frames = anim.lottie_animation_get_totalframe()

        return fps, frames
    
    @staticmethod
    def _get_file_frames_duration_pillow(file: Path, frames_only: bool = False) -> tuple[int, int]:
        total_duration = 0

        with Image.open(file) as im:
            if "n_frames" in im.__dir__():
                frames = im.n_frames
                if frames_only == True:
                    return frames, 1
                for i in range(im.n_frames):
                    im.seek(i)
                    total_duration += im.info.get("duration", 1000)
                return frames, total_duration
            else:
                return 1, 0
        
    @staticmethod
    def _get_file_frames_duration_webp(file: Path) -> tuple[int, int]:
        total_duration = 0
        frames = 0
        
        with open(file, "r+b") as f:
            with mmap.mmap(f.fileno(), 0) as mm:
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
            return 1, 0
        else:
            return frames, total_duration
    
    @staticmethod
    def _get_file_frames_duration_av(file: Path, frames_to_iterate: Optional[int] = None, frames_only: bool = False) -> tuple[int, int]:
        import av # type: ignore

        # Getting fps and frame count from metadata is not reliable
        # Example: https://github.com/laggykiller/sticker-convert/issues/114

        if isinstance(file, Path):
            file = file.as_posix()

        with av.open(file) as container:
            stream = container.streams.video[0]
            duration_metadata = int(Decimal(container.duration / 1000).quantize(0, ROUND_HALF_UP))

            if frames_only == True and stream.frames > 1:
                return stream.frames, duration_metadata

            last_frame = None
            for frame_count, frame in enumerate(container.decode(stream)):
                if frames_to_iterate != None and frame_count == frames_to_iterate:
                    break
                last_frame = frame
            
            time_base_ms = last_frame.time_base.numerator / last_frame.time_base.denominator * 1000
            if frame_count <= 1 or duration_metadata != 0:
                return frame_count, duration_metadata
            else:
                duration_n_minus_one = last_frame.pts * time_base_ms
                ms_per_frame = duration_n_minus_one / (frame_count - 1)
                duration = frame_count * ms_per_frame
                return frame_count, int(Decimal(duration).quantize(0, ROUND_HALF_UP))

    @staticmethod
    def get_file_codec(file: Path) -> Optional[str]:
        codec = None

        file_ext = CodecInfo.get_file_ext(file)
        if file_ext in (".tgs", ".lottie", ".json"):
            return file_ext.replace(".", "")
        try:
            with Image.open(file) as im:
                codec = im.format
                if 'is_animated' in im.__dir__():
                    animated = im.is_animated
                else:
                    animated = False
        except UnidentifiedImageError:
            pass

        if codec == "PNG":
            # Unable to distinguish apng and png
            if animated:
                return "apng"
            else:
                return "png"
        elif codec != None:
            return codec.lower()
        
        import av # type: ignore
        from av.error import InvalidDataError

        if isinstance(file, Path):
            file = file.as_posix()
        
        try:
            with av.open(file) as container:
                codec = container.streams.video[0].codec_context.name
        except InvalidDataError:
            return ""
        if codec == None:
            raise ""
        return codec.lower()

    @staticmethod
    def get_file_res(file: Path) -> tuple[int, int]:
        file_ext = CodecInfo.get_file_ext(file)

        if file_ext == ".tgs":
            from rlottie_python import LottieAnimation  # type: ignore

            with LottieAnimation.from_tgs(file) as anim:
                width, height = anim.lottie_animation_get_size()
        elif file_ext in (".webp", ".png", ".apng"):
            with Image.open(file) as im:
                width = im.width
                height = im.height
        else:
            import av # type: ignore

            if isinstance(file, Path):
                file = file.as_posix()

            with av.open(file) as container:
                stream = container.streams.video[0]
                width = stream.width
                height = stream.height

        return width, height

    @staticmethod
    def get_file_ext(file: Path) -> str:
        return Path(file).suffix.lower()

    @staticmethod
    def is_anim(file: Path) -> bool:
        if CodecInfo.get_file_frames(file, check_anim=True) > 1:
            return True
        else:
            return False
