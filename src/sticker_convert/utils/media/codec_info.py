#!/usr/bin/env python3
from __future__ import annotations

import json
import mmap
import warnings
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from io import BytesIO
from math import ceil, gcd
from pathlib import Path
from typing import BinaryIO, List, Optional, Tuple, Union, cast

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from PIL import Image, UnidentifiedImageError
from rlottie_python.rlottie_wrapper import LottieAnimation

from sticker_convert.definitions import SVG_DEFAULT_HEIGHT, SVG_DEFAULT_WIDTH, SVG_SAMPLE_FPS

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def lcm(a: int, b: int) -> int:
    return abs(a * b) // gcd(a, b)


def rounding(value: float) -> Decimal:
    return Decimal(value).quantize(0, ROUND_HALF_UP)


def fraction_gcd(x: Fraction, y: Fraction) -> Fraction:
    a = x.numerator
    b = x.denominator
    c = y.numerator
    d = y.denominator
    return Fraction(gcd(a, c), lcm(b, d))


def fractions_gcd(*fractions: Fraction) -> Fraction:
    fractions_list = list(fractions)
    gcd = fractions_list.pop(0)
    for fraction in fractions_list:
        gcd = fraction_gcd(gcd, fraction)

    return gcd


def get_five_dec_place(value: float) -> str:
    return str(value).split(".")[1][:5].ljust(5, "0")


def likely_int(value: float) -> bool:
    if isinstance(value, int):
        return True
    return True if get_five_dec_place(value) in ("99999", "00000") else False


def durations_gcd(*durations: Union[int, float]) -> Union[float, Fraction]:
    if any(i for i in durations if isinstance(i, float)):
        if all(i for i in durations if likely_int(i)):
            return Fraction(gcd(*(int(rounding(i)) for i in durations)), 1)
        # Test for denominators that can produce recurring decimal
        for x in (3, 6, 7, 9, 11, 13):
            if all(likely_int(i * x) for i in durations):
                return Fraction(gcd(*(int(rounding(i * x)) for i in durations)), x)
        else:
            return min(durations)
    else:
        return Fraction(gcd(*durations), 1)  # type: ignore


def open_lottie(file: Union[Path, bytes]) -> LottieAnimation:
    if isinstance(file, Path):
        if file.suffix == ".tgs":
            return LottieAnimation.from_tgs(file.as_posix())
        else:
            return LottieAnimation.from_file(file.as_posix())
    else:
        import gzip

        try:
            with gzip.open(BytesIO(file)) as f:
                data = f.read().decode(encoding="utf-8")
        except gzip.BadGzipFile:
            data = json.loads(file.decode())

        return LottieAnimation.from_data(data)


class CodecInfo:
    def __init__(
        self, file: Union[Path, bytes], file_ext: Optional[str] = None
    ) -> None:
        self.file_ext: Optional[str]
        if file_ext is None and isinstance(file, Path):
            self.file_ext = CodecInfo.get_file_ext(file)
        else:
            self.file_ext = file_ext
        if self.file_ext == ".svg":
            self.fps, self.frames, self.duration, self.res = CodecInfo.get_svg_info(
                file
            )
            self.codec = "svg"
        else:
            self.fps, self.frames, self.duration = (
                CodecInfo.get_file_fps_frames_duration(file)
            )
            self.codec = CodecInfo.get_file_codec(file)
            self.res = CodecInfo.get_file_res(file)
        self.is_animated = self.fps > 1

    @staticmethod
    def get_file_fps_frames_duration(
        file: Union[Path, bytes], file_ext: Optional[str] = None
    ) -> Tuple[float, int, int]:
        fps: float
        duration: int

        if not file_ext and isinstance(file, Path):
            file_ext = CodecInfo.get_file_ext(file)

        if file_ext in (".tgs", ".json", ".lottie"):
            fps, frames = CodecInfo._get_file_fps_frames_lottie(file)
            if fps > 0:
                duration = int(frames / fps * 1000)
            else:
                duration = 0
        elif file_ext == ".webp":
            fps, frames, duration, _ = CodecInfo._get_file_fps_frames_duration_webp(
                file
            )
        elif file_ext in (".gif", ".apng", ".png"):
            fps, frames, duration = CodecInfo._get_file_fps_frames_duration_pillow(file)
        else:
            frames, duration = CodecInfo._get_file_frames_duration_av(file)

            if duration > 0:
                fps = frames / duration * 1000
            else:
                fps = 0

        return fps, frames, duration

    @staticmethod
    def get_file_fps(file: Union[Path, bytes], file_ext: Optional[str] = None) -> float:
        if not file_ext and isinstance(file, Path):
            file_ext = CodecInfo.get_file_ext(file)

        if file_ext in (".tgs", ".json", ".lottie"):
            return CodecInfo._get_file_fps_lottie(file)
        elif file_ext == ".webp":
            fps, _, _, _ = CodecInfo._get_file_fps_frames_duration_webp(file)
            return fps
        elif file_ext in (".gif", ".apng", ".png"):
            fps, _, _ = CodecInfo._get_file_fps_frames_duration_pillow(file)
            return fps

        frames, duration = CodecInfo._get_file_frames_duration_av(
            file, frames_to_iterate=10
        )

        if duration > 0:
            return frames / duration * 1000
        return 0

    @staticmethod
    def get_file_frames(
        file: Union[Path, bytes],
        file_ext: Optional[str] = None,
        check_anim: bool = False,
    ) -> int:
        # If check_anim is True, return value > 1 means the file is animated
        if not file_ext and isinstance(file, Path):
            file_ext = CodecInfo.get_file_ext(file)

        if file_ext in (".tgs", ".json", ".lottie"):
            return CodecInfo._get_file_frames_lottie(file)
        if file_ext in (".gif", ".webp", ".png", ".apng"):
            _, frames, _ = CodecInfo._get_file_fps_frames_duration_pillow(
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
        file: Union[Path, bytes], file_ext: Optional[str] = None
    ) -> int:
        duration: int

        # Return duration in miliseconds
        if not file_ext and isinstance(file, Path):
            file_ext = CodecInfo.get_file_ext(file)

        if file_ext in (".tgs", ".json", ".lottie"):
            fps, frames = CodecInfo._get_file_fps_frames_lottie(file)
            if fps > 0:
                duration = int(frames / fps * 1000)
            else:
                duration = 0
        elif file_ext == ".webp":
            _, _, duration, _ = CodecInfo._get_file_fps_frames_duration_webp(file)
        elif file_ext in (".gif", ".png", ".apng"):
            _, _, duration = CodecInfo._get_file_fps_frames_duration_pillow(file)
        else:
            _, duration = CodecInfo._get_file_frames_duration_av(file)

        return duration

    @staticmethod
    def _get_file_fps_lottie(file: Union[Path, bytes]) -> int:
        anim = open_lottie(file)
        fps = anim.lottie_animation_get_framerate()

        return fps

    @staticmethod
    def _get_file_frames_lottie(file: Union[Path, bytes]) -> int:
        anim = open_lottie(file)
        frames = anim.lottie_animation_get_totalframe()

        return frames

    @staticmethod
    def _get_file_fps_frames_lottie(file: Union[Path, bytes]) -> Tuple[int, int]:
        anim = open_lottie(file)
        fps = anim.lottie_animation_get_framerate()
        frames = anim.lottie_animation_get_totalframe()
        anim.lottie_animation_destroy()

        return fps, frames

    @staticmethod
    def _get_file_fps_frames_duration_pillow(
        file: Union[Path, bytes], frames_only: bool = False
    ) -> Tuple[float, int, int]:
        total_duration = 0
        durations: List[int] = []

        with Image.open(file) as im:
            if "n_frames" in dir(im):
                frames = im.n_frames
                if frames_only is True:
                    return 0.0, frames, 1
                for i in range(im.n_frames):
                    im.seek(i)
                    frame_duration = cast(int, im.info.get("duration", 1000))
                    if frame_duration not in durations and frame_duration != 0:
                        durations.append(frame_duration)
                    total_duration += frame_duration
                if im.n_frames == 0 or total_duration == 0:
                    fps = 0.0
                elif len(durations) == 1:
                    fps = frames / total_duration * 1000
                else:
                    duration_gcd = durations_gcd(*durations)
                    frames_apparent = total_duration / duration_gcd
                    fps = float(frames_apparent / total_duration * 1000)
                return fps, frames, total_duration

        return 0.0, 1, 0

    @staticmethod
    def _get_file_fps_frames_duration_webp(
        file: Union[Path, bytes],
    ) -> Tuple[float, int, int, List[int]]:
        total_duration = 0
        frames = 0
        durations: List[int] = []
        durations_unique: List[int] = []

        def _open_f(file: Union[Path, bytes]) -> BinaryIO:
            if isinstance(file, Path):
                return open(file, "r+b")
            return BytesIO(file)

        with _open_f(file) as f:
            with mmap.mmap(f.fileno(), 0) as mm:
                while True:
                    anmf_pos = mm.find(b"ANMF")
                    if anmf_pos == -1:
                        break
                    mm.seek(anmf_pos + 20)
                    frame_duration_32 = mm.read(4)
                    frame_duration_bytes = frame_duration_32[:-1] + bytes(
                        int(frame_duration_32[-1]) & 0b11111100
                    )
                    frame_duration = int.from_bytes(frame_duration_bytes, "little")
                    if frame_duration not in durations_unique and frame_duration != 0:
                        durations_unique.append(frame_duration)
                    durations.append(frame_duration)
                    total_duration += frame_duration
                    frames += 1

        if frames <= 1:
            return 0.0, 1, 0, durations

        if len(durations_unique) == 1:
            fps = frames / total_duration * 1000
        else:
            duration_gcd = durations_gcd(*durations_unique)
            frames_apparent = total_duration / duration_gcd
            fps = float(frames_apparent / total_duration * 1000)

        return fps, frames, total_duration, durations

    @staticmethod
    def _get_file_frames_duration_av(
        file: Union[Path, bytes],
        frames_to_iterate: Optional[int] = None,
        frames_only: bool = False,
    ) -> Tuple[int, int]:
        import av
        from av.container.input import InputContainer

        # Getting fps and frame count from metadata is not reliable
        # Example: https://github.com/laggykiller/sticker-convert/issues/114

        file_ref: Union[str, BinaryIO]
        if isinstance(file, Path):
            file_ref = file.as_posix()
        else:
            file_ref = BytesIO(file)

        with av.open(file_ref) as container:
            container = cast(InputContainer, container)
            stream = container.streams.video[0]
            if container.duration:
                duration_metadata = int(rounding(container.duration / 1000))
            else:
                duration_metadata = 0

            if frames_only is True and stream.frames > 1:
                return stream.frames, duration_metadata

            frame_count = 0
            last_frame = None
            for frame_count, frame in enumerate(container.decode(stream)):
                if frames_to_iterate is not None and frame_count == frames_to_iterate:
                    break
                last_frame = frame

            if last_frame is None:
                return 0, 0

            time_base_ms = (
                last_frame.time_base.numerator / last_frame.time_base.denominator * 1000
            )
            if frame_count <= 1 or duration_metadata != 0:
                return frame_count, duration_metadata
            duration_n_minus_one = last_frame.pts * time_base_ms
            ms_per_frame = duration_n_minus_one / (frame_count - 1)
            duration = frame_count * ms_per_frame
            return frame_count, int(rounding(duration))

        return 0, 0

    @staticmethod
    def get_file_codec(file: Union[Path, bytes], file_ext: Optional[str] = None) -> str:
        if not file_ext and isinstance(file, Path):
            file_ext = CodecInfo.get_file_ext(file)

        file_ref: Union[str, BinaryIO]
        if isinstance(file, Path):
            file_ref = file.as_posix()
        else:
            file_ref = BytesIO(file)

        codec = None
        animated = False
        if file_ext in (".tgs", ".lottie", ".json"):
            return file_ext.replace(".", "")
        try:
            with Image.open(file) as im:
                codec = im.format
                if "is_animated" in dir(im):
                    animated = im.is_animated
                else:
                    animated = False
        except UnidentifiedImageError:
            pass

        if codec == "PNG":
            # Unable to distinguish apng and png
            if animated:
                return "apng"
            return "png"
        if codec is not None:
            return codec.lower()

        import av
        from av.error import InvalidDataError

        try:
            with av.open(file_ref) as container:
                return container.streams.video[0].codec_context.name.lower()
        except InvalidDataError:
            pass

        return ""

    @staticmethod
    def get_file_res(
        file: Union[Path, bytes], file_ext: Optional[str] = None
    ) -> Tuple[int, int]:
        if not file_ext and isinstance(file, Path):
            file_ext = CodecInfo.get_file_ext(file)

        if file_ext in (".tgs", ".json", ".lottie"):
            anim = open_lottie(file)
            width, height = anim.lottie_animation_get_size()
            anim.lottie_animation_destroy()
        elif file_ext in (".webp", ".png", ".apng"):
            with Image.open(file) as im:
                width = im.width
                height = im.height
        else:
            import av

            file_ref: Union[str, BinaryIO]
            if isinstance(file, Path):
                file_ref = file.as_posix()
            else:
                file_ref = BytesIO(file)

            with av.open(file_ref) as container:
                stream = container.streams.video[0]
                width = stream.width
                height = stream.height

        return width, height

    @staticmethod
    def get_file_ext(file: Path) -> str:
        return Path(file).suffix.lower()

    @staticmethod
    def is_anim(file: Union[Path, bytes]) -> bool:
        if CodecInfo.get_file_frames(file, check_anim=True) > 1:
            return True
        return False

    @staticmethod
    def get_svg_info(
        file: Union[Path, bytes],
    ) -> Tuple[float, int, int, Tuple[int, int]]:
        if isinstance(file, Path):
            with open(file) as f:
                svg = f.read()
        else:
            svg = file.decode()

        soup = BeautifulSoup(svg, "html.parser")
        svg_tag = soup.find_all("svg")[0]
        width = int(svg_tag.get("width", SVG_DEFAULT_WIDTH))
        height = int(svg_tag.get("height", SVG_DEFAULT_HEIGHT))

        animate_elements = [*soup.find_all("animate")] + [
            *soup.find_all("animateTransform")
        ]
        duration = 0
        for element in animate_elements:
            dur = cast(str, element.get("dur"))
            if dur.endswith("s"):
                duration = int(max(duration, float(dur[:-1]) * 1000))
            elif dur.endswith("ms"):
                duration = int(max(duration, float(dur[:-2])))

        if duration != 0:
            fps = SVG_SAMPLE_FPS
            frames = ceil(fps * duration / 1000)
        else:
            fps = 0
            frames = 1

        return fps, frames, duration, (width, height)
