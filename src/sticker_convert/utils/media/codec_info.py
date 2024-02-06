#!/usr/bin/env python3
from __future__ import annotations

import io
import mmap
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Optional, Union

from PIL import Image, UnidentifiedImageError


class CodecInfo:
    def __init__(self, file: Union[Path, io.BytesIO], file_ext: Optional[str] = None):
        if not file_ext and isinstance(file, Path):
            self.file_ext = CodecInfo.get_file_ext(file)
        else:
            self.file_ext = file_ext
        self.fps, self.frames, self.duration = CodecInfo.get_file_fps_frames_duration(
            file
        )
        self.codec = CodecInfo.get_file_codec(file)
        self.res = CodecInfo.get_file_res(file)
        self.is_animated = True if self.fps > 1 else False

    @staticmethod
    def get_file_fps_frames_duration(
        file: Union[Path, io.BytesIO], file_ext: Optional[str] = None
    ) -> tuple[float, int, int]:
        if not file_ext and isinstance(file, Path):
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
    def get_file_fps(
        file: Union[Path, io.BytesIO], file_ext: Optional[str] = None
    ) -> float:
        if not file_ext and isinstance(file, Path):
            file_ext = CodecInfo.get_file_ext(file)

        if file_ext == ".tgs":
            return CodecInfo._get_file_fps_tgs(file)
        elif file_ext == ".webp":
            frames, duration = CodecInfo._get_file_frames_duration_webp(file)
        elif file_ext in (".gif", ".apng", ".png"):
            frames, duration = CodecInfo._get_file_frames_duration_pillow(file)
        else:
            frames, duration = CodecInfo._get_file_frames_duration_av(
                file, frames_to_iterate=10
            )

        if duration > 0:
            return frames / duration * 1000
        else:
            return 0

    @staticmethod
    def get_file_frames(
        file: Union[Path, io.BytesIO],
        file_ext: Optional[str] = None,
        check_anim: bool = False,
    ) -> int:
        # If check_anim is True, return value > 1 means the file is animated
        if not file_ext and isinstance(file, Path):
            file_ext = CodecInfo.get_file_ext(file)

        if file_ext == ".tgs":
            return CodecInfo._get_file_frames_tgs(file)
        elif file_ext in (".gif", ".webp", ".png", ".apng"):
            frames, _ = CodecInfo._get_file_frames_duration_pillow(
                file, frames_only=True
            )
        else:
            if check_anim is True:
                frames_to_iterate = 2
            else:
                frames_to_iterate = None
            frames, _ = CodecInfo._get_file_frames_duration_av(
                file, frames_only=True, frames_to_iterate=frames_to_iterate
            )

        return frames

    @staticmethod
    def get_file_duration(
        file: Union[Path, io.BytesIO], file_ext: Optional[str] = None
    ) -> int:
        # Return duration in miliseconds
        if not file_ext and isinstance(file, Path):
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
    def _get_file_fps_tgs(file: Union[Path, io.BytesIO]) -> int:
        from rlottie_python.rlottie_wrapper import LottieAnimation

        if isinstance(file, Path):
            tgs = file.as_posix()
        else:
            tgs = file

        with LottieAnimation.from_tgs(tgs) as anim:  # type: ignore
            return anim.lottie_animation_get_framerate()  # type: ignore

    @staticmethod
    def _get_file_frames_tgs(file: Union[Path, io.BytesIO]) -> int:
        from rlottie_python.rlottie_wrapper import LottieAnimation

        if isinstance(file, Path):
            tgs = file.as_posix()
        else:
            tgs = file

        with LottieAnimation.from_tgs(tgs) as anim:  # type: ignore
            return anim.lottie_animation_get_totalframe()  # type: ignore

    @staticmethod
    def _get_file_fps_frames_tgs(file: Union[Path, io.BytesIO]) -> tuple[int, int]:
        from rlottie_python.rlottie_wrapper import LottieAnimation

        if isinstance(file, Path):
            tgs = file.as_posix()
        else:
            tgs = file

        with LottieAnimation.from_tgs(tgs) as anim:  # type: ignore
            fps = anim.lottie_animation_get_framerate()  # type: ignore
            frames = anim.lottie_animation_get_totalframe()  # type: ignore

        return fps, frames  # type: ignore

    @staticmethod
    def _get_file_frames_duration_pillow(
        file: Union[Path, io.BytesIO], frames_only: bool = False
    ) -> tuple[int, int]:
        total_duration = 0

        with Image.open(file) as im:
            if "n_frames" in im.__dir__():
                frames = im.n_frames
                if frames_only is True:
                    return frames, 1
                for i in range(im.n_frames):
                    im.seek(i)
                    total_duration += im.info.get("duration", 1000)
                return frames, total_duration
            else:
                return 1, 0

    @staticmethod
    def _get_file_frames_duration_webp(
        file: Union[Path, io.BytesIO],
    ) -> tuple[int, int]:
        total_duration = 0
        frames = 0

        with open(file, "r+b") as f:  # type: ignore
            with mmap.mmap(f.fileno(), 0) as mm:  # type: ignore
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
    def _get_file_frames_duration_av(
        file: Union[Path, io.BytesIO],
        frames_to_iterate: Optional[int] = None,
        frames_only: bool = False,
    ) -> tuple[int, int]:
        import av

        # Getting fps and frame count from metadata is not reliable
        # Example: https://github.com/laggykiller/sticker-convert/issues/114

        if isinstance(file, Path):
            file_ref = file.as_posix()
        else:
            file_ref = file

        with av.open(file_ref) as container:  # type: ignore
            stream = container.streams.video[0]
            if container.duration:
                duration_metadata = int(
                    Decimal(container.duration / 1000).quantize(0, ROUND_HALF_UP)
                )
            else:
                duration_metadata = 0

            if frames_only is True and stream.frames > 1:
                return stream.frames, duration_metadata

            frame_count = 0
            last_frame = None
            for frame_count, frame in enumerate(container.decode(stream)):  # type: ignore
                if frames_to_iterate is not None and frame_count == frames_to_iterate:
                    break
                last_frame = frame  # type: ignore

            time_base_ms = (  # type: ignore
                last_frame.time_base.numerator / last_frame.time_base.denominator * 1000  # type: ignore
            )
            if frame_count <= 1 or duration_metadata != 0:
                return frame_count, duration_metadata
            else:
                duration_n_minus_one = last_frame.pts * time_base_ms  # type: ignore
                ms_per_frame = duration_n_minus_one / (frame_count - 1)  # type: ignore
                duration = frame_count * ms_per_frame  # type: ignore
                return frame_count, int(Decimal(duration).quantize(0, ROUND_HALF_UP))  # type: ignore

    @staticmethod
    def get_file_codec(
        file: Union[Path, io.BytesIO], file_ext: Optional[str] = None
    ) -> str:
        if not file_ext and isinstance(file, Path):
            file_ext = CodecInfo.get_file_ext(file)

        if isinstance(file, Path):
            file_ref = file.as_posix()
        else:
            file_ref = file

        codec = None
        animated = False
        if file_ext in (".tgs", ".lottie", ".json"):
            return file_ext.replace(".", "")
        try:
            with Image.open(file) as im:
                codec = im.format
                if "is_animated" in im.__dir__():
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
        elif codec is not None:
            return codec.lower()

        import av
        from av.error import InvalidDataError

        try:
            with av.open(file_ref) as container:  # type: ignore
                codec = container.streams.video[0].codec_context.name
        except InvalidDataError:
            return ""

        return codec.lower()

    @staticmethod
    def get_file_res(
        file: Union[Path, io.BytesIO], file_ext: Optional[str] = None
    ) -> tuple[int, int]:
        if not file_ext and isinstance(file, Path):
            file_ext = CodecInfo.get_file_ext(file)

        if isinstance(file, Path):
            file_ref = file.as_posix()
        else:
            file_ref = file

        if file_ext == ".tgs":
            from rlottie_python.rlottie_wrapper import LottieAnimation

            with LottieAnimation.from_tgs(file_ref) as anim:  # type: ignore
                width, height = anim.lottie_animation_get_size()  # type: ignore
        elif file_ext in (".webp", ".png", ".apng"):
            with Image.open(file) as im:
                width = im.width
                height = im.height
        else:
            import av

            with av.open(file_ref) as container:  # type: ignore
                stream = container.streams.video[0]
                width = stream.width
                height = stream.height

        return width, height  # type: ignore

    @staticmethod
    def get_file_ext(file: Path) -> str:
        return Path(file).suffix.lower()

    @staticmethod
    def is_anim(file: Union[Path, io.BytesIO]) -> bool:
        if CodecInfo.get_file_frames(file, check_anim=True) > 1:
            return True
        else:
            return False
