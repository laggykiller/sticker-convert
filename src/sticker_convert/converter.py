#!/usr/bin/env python3
import json
import os
from fractions import Fraction
from io import BytesIO
from math import ceil, floor
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple, Union, cast

import numpy as np
from bs4 import BeautifulSoup
from PIL import Image
from PIL import __version__ as PillowVersion
from PIL import features

from sticker_convert.job_option import CompOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.chrome_remotedebug import CRD
from sticker_convert.utils.files.cache_store import CacheStore
from sticker_convert.utils.media.codec_info import CodecInfo, rounding
from sticker_convert.utils.media.format_verify import FormatVerify
from sticker_convert.utils.singletons import singletons

if TYPE_CHECKING:
    from av.video.frame import VideoFrame
    from av.video.plane import VideoPlane

MSG_START_COMP = "[I] Start compressing {} -> {}"
MSG_SKIP_COMP = "[S] Compatible file found, skip compress and just copy {} -> {}"
MSG_COMP = (
    "[C] Compressing {} -> {} res={}x{}, quality={}, fps={}, color={} (step {}-{}-{})"
)
MSG_REDO_COMP = "[{}] Compressed {} -> {} but size {} {} limit {}, recompressing"
MSG_DONE_COMP = "[S] Successful compression {} -> {} size {} (step {})"
MSG_FAIL_COMP = (
    "[F] Failed Compression {} -> {}, "
    "cannot get below limit {} with lowest quality under current settings (Best size: {})"
)

YUV_RGB_MATRIX = np.array(
    [
        [1.164, 0.000, 1.793],
        [1.164, -0.213, -0.533],
        [1.164, 2.112, 0.000],
    ]
)

# Whether animated WebP is supported
# See https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#saving-sequences
PIL_WEBP_ANIM = cast(bool, features.check("webp_anim"))  # type: ignore


def get_step_value(
    max_step: Optional[int],
    min_step: Optional[int],
    step: int,
    steps: int,
    power: float = 1.0,
    even: bool = False,
) -> Optional[int]:
    # Power should be between -1 and positive infinity
    # Smaller power = More 'importance' of the parameter
    # Power of 1 is linear relationship
    # e.g. fps has lower power -> Try not to reduce it early on

    if step > 0:
        factor = pow(step / steps, power)
    else:
        factor = 0

    if max_step is not None and min_step is not None:
        v = round((max_step - min_step) * step / steps * factor + min_step)
        if even is True and v % 2 == 1:
            return v + 1
        return v
    return None


def useful_array(
    plane: "VideoPlane", bytes_per_pixel: int = 1, dtype: str = "uint8"
) -> "np.ndarray[Any, Any]":
    total_line_size = abs(plane.line_size)
    useful_line_size = plane.width * bytes_per_pixel
    arr: "np.ndarray[Any, Any]" = np.frombuffer(cast(bytes, plane), np.uint8)
    if total_line_size != useful_line_size:
        arr = arr.reshape(-1, total_line_size)[:, 0:useful_line_size].reshape(-1)
    return arr.view(np.dtype(dtype))


def yuva_to_rgba(frame: "VideoFrame") -> "np.ndarray[Any, Any]":
    # https://stackoverflow.com/questions/72308308/converting-yuv-to-rgb-in-python-coefficients-work-with-array-dont-work-with-n

    width = frame.width
    height = frame.height

    y = useful_array(frame.planes[0]).reshape(height, width)
    u = useful_array(frame.planes[1]).reshape(height // 2, width // 2)
    v = useful_array(frame.planes[2]).reshape(height // 2, width // 2)
    a = useful_array(frame.planes[3]).reshape(height, width)

    u = u.repeat(2, axis=0).repeat(2, axis=1)
    v = v.repeat(2, axis=0).repeat(2, axis=1)

    y = y.reshape((y.shape[0], y.shape[1], 1))
    u = u.reshape((u.shape[0], u.shape[1], 1))
    v = v.reshape((v.shape[0], v.shape[1], 1))
    a = a.reshape((a.shape[0], a.shape[1], 1))

    yuv_array = np.concatenate((y, u, v), axis=2)

    yuv_array = yuv_array.astype(np.float32)
    yuv_array[:, :, 0] = (
        yuv_array[:, :, 0].clip(16, 235).astype(yuv_array.dtype) - 16  # type: ignore
    )
    yuv_array[:, :, 1:] = (
        yuv_array[:, :, 1:].clip(16, 240).astype(yuv_array.dtype) - 128  # type: ignore
    )

    rgb_array = np.matmul(yuv_array, YUV_RGB_MATRIX.T).clip(0, 255).astype("uint8")

    return np.concatenate((rgb_array, a), axis=2)


class StickerConvert:
    def __init__(
        self,
        in_f: Union[Path, Tuple[Path, bytes]],
        out_f: Path,
        opt_comp: CompOption,
        cb: CallbackProtocol,
        #  cb_return: CallbackReturn
    ) -> None:
        self.in_f: Union[bytes, Path]
        if isinstance(in_f, Path):
            self.in_f = in_f
            self.in_f_name = self.in_f.name
            self.in_f_path = in_f
            self.codec_info_orig = CodecInfo(self.in_f)
        else:
            self.in_f = in_f[1]
            self.in_f_name = Path(in_f[0]).name
            self.in_f_path = in_f[0]
            self.codec_info_orig = CodecInfo(in_f[1], Path(in_f[0]).suffix)

        valid_formats: List[str] = []
        for i in opt_comp.get_format():
            valid_formats.extend(i)

        valid_ext = False
        self.out_f = Path()
        if len(valid_formats) == 0 or Path(out_f).suffix in valid_formats:
            self.out_f = Path(out_f)
            valid_ext = True

        if not valid_ext:
            if self.codec_info_orig.is_animated or opt_comp.fake_vid:
                ext = opt_comp.format_vid[0]
            else:
                ext = opt_comp.format_img[0]
            self.out_f = out_f.with_suffix(ext)

        self.out_f_name: str = self.out_f.name

        self.cb = cb
        self.frames_raw: "List[np.ndarray[Any, Any]]" = []
        self.frames_processed: "List[np.ndarray[Any, Any]]" = []
        self.opt_comp: CompOption = opt_comp
        if not self.opt_comp.steps:
            self.opt_comp.steps = 1

        self.size: int = 0
        self.size_max: Optional[int] = None
        self.res_w: Optional[int] = None
        self.res_h: Optional[int] = None
        self.quality: Optional[int] = None
        self.fps: Optional[Fraction] = None
        self.color: Optional[int] = None

        self.bg_color: Optional[Tuple[int, int, int, int]] = None
        if self.opt_comp.bg_color:
            r, g, b, a = bytes.fromhex(self.opt_comp.bg_color)
            self.bg_color = (r, g, b, a)

        self.tmp_f: BytesIO = BytesIO()
        self.result: Optional[bytes] = None
        self.result_size: int = 0
        self.result_step: Optional[int] = None

        self.apngasm = None

    @staticmethod
    def convert(
        in_f: Union[Path, Tuple[Path, bytes]],
        out_f: Path,
        opt_comp: CompOption,
        cb: CallbackProtocol,
        _cb_return: CallbackReturn,
    ) -> Tuple[bool, Path, Union[None, bytes, Path], int]:
        sticker = StickerConvert(in_f, out_f, opt_comp, cb)
        result = sticker._convert()
        cb.put("update_bar")
        return result

    def _convert(self) -> Tuple[bool, Path, Union[None, bytes, Path], int]:
        result = self.check_if_compatible()
        if result:
            return self.compress_done(result)

        self.cb.put((MSG_START_COMP.format(self.in_f_name, self.out_f_name)))

        steps_list = self.generate_steps_list()

        step_lower = 0
        step_upper = self.opt_comp.steps

        if self.codec_info_orig.is_animated is True:
            self.size_max = self.opt_comp.size_max_vid
        else:
            self.size_max = self.opt_comp.size_max_img

        if self.size_max in (None, 0):
            # No limit to size, create the best quality result
            step_current = 0
        else:
            step_current = int(rounding((step_lower + step_upper) / 2))

        self.frames_import()
        while True:
            param = steps_list[step_current]
            self.res_w = param[0]
            self.res_h = param[1]
            self.quality = param[2]
            if param[3] and self.codec_info_orig.fps:
                fps_tmp = min(param[3], self.codec_info_orig.fps)
                self.fps = self.fix_fps(fps_tmp)
            else:
                self.fps = Fraction(0)
            self.color = param[4]

            self.tmp_f = BytesIO()
            msg = MSG_COMP.format(
                self.in_f_name,
                self.out_f_name,
                self.res_w,
                self.res_h,
                self.quality,
                int(self.fps),
                self.color,
                step_lower,
                step_current,
                step_upper,
            )
            self.cb.put(msg)

            self.frames_processed = self.frames_drop(self.frames_raw)
            self.frames_processed = self.frames_resize(self.frames_processed)
            self.frames_export()

            self.tmp_f.seek(0)
            self.size = self.tmp_f.getbuffer().nbytes

            if not self.size_max or (
                self.size <= self.size_max and self.size >= self.result_size
            ):
                self.result = self.tmp_f.read()
                self.result_size = self.size
                self.result_step = step_current

            if (
                step_upper - step_lower > 0
                and step_current != step_lower
                and self.size_max
            ):
                if self.size <= self.size_max:
                    sign = "<"
                    step_upper = step_current
                else:
                    sign = ">"
                    step_lower = step_current
                if step_current == step_lower + 1:
                    step_current = step_lower
                else:
                    step_current = int(rounding((step_lower + step_upper) / 2))
                self.recompress(sign)
            elif self.result:
                return self.compress_done(self.result, self.result_step)
            else:
                return self.compress_fail()

    def check_if_compatible(self) -> Optional[bytes]:
        f_fmt = self.opt_comp.get_format()
        if (
            # Issue #260: Some webp file not accepted by Whatsapp
            ".webp" not in f_fmt[0]
            and ".webp" not in f_fmt[1]
            and FormatVerify.check_format(
                self.in_f,
                fmt=f_fmt,
                file_info=self.codec_info_orig,
            )
            and FormatVerify.check_file_res(
                self.in_f, res=self.opt_comp.get_res(), file_info=self.codec_info_orig
            )
            and FormatVerify.check_file_fps(
                self.in_f, fps=self.opt_comp.get_fps(), file_info=self.codec_info_orig
            )
            and FormatVerify.check_file_size(
                self.in_f,
                size=self.opt_comp.get_size_max(),
                file_info=self.codec_info_orig,
            )
            and FormatVerify.check_file_duration(
                self.in_f,
                duration=self.opt_comp.get_duration(),
                file_info=self.codec_info_orig,
            )
        ):
            self.cb.put((MSG_SKIP_COMP.format(self.in_f_name, self.out_f_name)))

            if isinstance(self.in_f, Path):
                with open(self.in_f, "rb") as f:
                    result = f.read()
                self.result_size = os.path.getsize(self.in_f)
            else:
                result = self.in_f
                self.result_size = len(self.in_f)

            return result

        return None

    def generate_steps_list(self) -> List[Tuple[Optional[int], ...]]:
        steps_list: List[Tuple[Optional[int], ...]] = []
        need_even = self.out_f.suffix in (".webm", ".mp4", ".mkv", ".webp")
        for step in range(self.opt_comp.steps, -1, -1):
            steps_list.append(
                (
                    get_step_value(
                        self.opt_comp.res_w_max,
                        self.opt_comp.res_w_min,
                        step,
                        self.opt_comp.steps,
                        self.opt_comp.res_power,
                        need_even,
                    ),
                    get_step_value(
                        self.opt_comp.res_h_max,
                        self.opt_comp.res_h_min,
                        step,
                        self.opt_comp.steps,
                        self.opt_comp.res_power,
                        need_even,
                    ),
                    get_step_value(
                        self.opt_comp.quality_max,
                        self.opt_comp.quality_min,
                        step,
                        self.opt_comp.steps,
                        self.opt_comp.quality_power,
                    ),
                    get_step_value(
                        self.opt_comp.fps_max,
                        self.opt_comp.fps_min,
                        step,
                        self.opt_comp.steps,
                        self.opt_comp.fps_power,
                    ),
                    get_step_value(
                        self.opt_comp.color_max,
                        self.opt_comp.color_min,
                        step,
                        self.opt_comp.steps,
                        self.opt_comp.color_power,
                    ),
                )
            )

        return steps_list

    def recompress(self, sign: str) -> None:
        msg = MSG_REDO_COMP.format(
            sign, self.in_f_name, self.out_f_name, self.size, sign, self.size_max
        )
        self.cb.put(msg)

    def compress_fail(
        self,
    ) -> Tuple[bool, Path, Union[None, bytes, Path], int]:
        msg = MSG_FAIL_COMP.format(
            self.in_f_name, self.out_f_name, self.size_max, self.size
        )
        self.cb.put(msg)

        return False, self.in_f_path, self.out_f, self.size

    def compress_done(
        self, data: bytes, result_step: Optional[int] = None
    ) -> Tuple[bool, Path, Union[None, bytes, Path], int]:
        out_f: Union[None, bytes, Path]

        if self.out_f.stem == "none":
            out_f = None
        elif self.out_f.stem == "bytes":
            out_f = data
        else:
            out_f = self.out_f
            with open(self.out_f, "wb+") as f:
                f.write(data)

        if result_step is not None:
            msg = MSG_DONE_COMP.format(
                self.in_f_name, self.out_f_name, self.result_size, result_step
            )
            self.cb.put(msg)

        return True, self.in_f_path, out_f, self.result_size

    def frames_import(self) -> None:
        if isinstance(self.in_f, Path):
            suffix = self.in_f.suffix
        else:
            suffix = Path(self.in_f_name).suffix

        if suffix in (".tgs", ".lottie", ".json"):
            self._frames_import_lottie()
        elif suffix in (".webp", ".apng", ".png", ".gif"):
            # ffmpeg do not support webp decoding (yet)
            # ffmpeg could fail to decode apng if file is buggy
            self._frames_import_pillow()
        elif suffix == ".svg":
            self._frames_import_svg()
        else:
            self._frames_import_pyav()

    def _frames_import_svg(self) -> None:
        width = self.codec_info_orig.res[0]
        height = self.codec_info_orig.res[1]

        if singletons.objs.get("crd") is None:
            chrome_path: Optional[str]
            if self.opt_comp.chromium_path:
                chrome_path = self.opt_comp.chromium_path
            else:
                chrome_path = CRD.get_chromium_path()
            args = [
                "--headless",
                "--kiosk",
                "--disable-extensions",
                "--disable-infobars",
                "--disable-gpu",
                "--disable-gpu-rasterization",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                "about:blank",
            ]
            if chrome_path is None:
                raise RuntimeError("[F] Chrome/Chromium required for importing svg")
            self.cb.put("[W] Importing SVG takes long time")
            singletons.objs["crd"] = CRD(chrome_path, args=args)
            singletons.objs["crd"].connect(-1)  # type: ignore

        crd = cast(CRD, singletons.objs["crd"])
        if isinstance(self.in_f, bytes):
            svg = self.in_f.decode()
        else:
            with open(self.in_f) as f:
                svg = f.read()
        soup = BeautifulSoup(svg, "html.parser")
        svg_tag = soup.find_all("svg")[0]

        if svg_tag.get("width") is None:
            svg_tag["width"] = width
        if svg_tag.get("height") is None:
            svg_tag["height"] = height
        svg = str(soup)

        crd.open_html_str(svg)
        crd.set_transparent_bg()
        init_js = 'svg = document.getElementsByTagName("svg")[0];'
        if self.codec_info_orig.fps > 0:
            init_js += "svg.pauseAnimations();"
        init_js += "JSON.stringify(svg.getBoundingClientRect());"
        bound = json.loads(
            json.loads(crd.exec_js(init_js))["result"]["result"]["value"]
        )
        clip = {
            "x": bound["x"],
            "y": bound["y"],
            "width": width,
            "height": height,
            "scale": 1,
        }

        if self.codec_info_orig.fps > 0:
            for i in range(self.codec_info_orig.frames):
                curr_time = (
                    i
                    / self.codec_info_orig.frames
                    * self.codec_info_orig.duration
                    / 1000
                )
                crd.exec_js(f"svg.setCurrentTime({curr_time})")
                self.frames_raw.append(np.asarray(crd.screenshot(clip)))
        else:
            self.frames_raw.append(np.asarray(crd.screenshot(clip)))

    def _frames_import_pillow(self) -> None:
        with Image.open(self.in_f) as im:
            # Note: im.convert("RGBA") would return rgba image of current frame only
            if (
                "n_frames" in dir(im)
                and im.n_frames != 0
                and self.codec_info_orig.fps != 0.0
            ):
                # Pillow is not reliable for getting webp frame durations
                durations: Optional[List[int]]
                if im.format == "WEBP":
                    _, _, _, durations = CodecInfo._get_file_fps_frames_duration_webp(  # type: ignore
                        self.in_f
                    )
                else:
                    durations = None

                duration_ptr = 0.0
                duration_inc = 1 / self.codec_info_orig.fps * 1000
                frame = 0
                if durations is None:
                    next_frame_start_duration = cast(int, im.info.get("duration", 1000))
                else:
                    next_frame_start_duration = durations[0]
                while True:
                    self.frames_raw.append(np.asarray(im.convert("RGBA")))
                    duration_ptr += duration_inc
                    if duration_ptr >= next_frame_start_duration:
                        frame += 1
                        if frame == im.n_frames:
                            break
                        im.seek(frame)

                        if durations is None:
                            next_frame_start_duration += cast(
                                int, im.info.get("duration", 1000)
                            )
                        else:
                            next_frame_start_duration += durations[frame]
            else:
                self.frames_raw.append(np.asarray(im.convert("RGBA")))

    def _frames_import_pyav(self) -> None:
        import av
        from av.codec.context import CodecContext
        from av.container.input import InputContainer
        from av.video.codeccontext import VideoCodecContext
        from av.video.frame import VideoFrame

        # Crashes when handling some webm in yuv420p and convert to rgba
        # https://github.com/PyAV-Org/PyAV/issues/1166
        file: Union[BytesIO, str]
        if isinstance(self.in_f, Path):
            file = self.in_f.as_posix()
        else:
            file = BytesIO(self.in_f)
        with av.open(file) as container:
            container = cast(InputContainer, container)
            context = container.streams.video[0].codec_context
            if context.name == "vp8":
                context = CodecContext.create("libvpx", "r")
            elif context.name == "vp9":
                context = cast(
                    VideoCodecContext, CodecContext.create("libvpx-vp9", "r")
                )

            for packet in container.demux(container.streams.video):
                for frame in context.decode(packet):
                    width_orig = frame.width
                    height_orig = frame.height

                    # Need to pad frame to even dimension first
                    if width_orig % 2 == 1 or height_orig % 2 == 1:
                        from av.filter import Graph

                        width_new = width_orig + width_orig % 2
                        height_new = height_orig + height_orig % 2

                        graph = Graph()
                        in_src = graph.add_buffer(template=container.streams.video[0])
                        pad = graph.add(
                            "pad", f"{width_new}:{height_new}:0:0:color=#00000000"
                        )
                        in_src.link_to(pad)
                        sink = graph.add("buffersink")
                        pad.link_to(sink)
                        graph.configure()

                        graph.push(frame)
                        frame_resized = cast(VideoFrame, graph.pull())
                    else:
                        frame_resized = frame

                    # yuva420p may cause crash
                    # Not safe to directly call frame.to_ndarray(format="rgba")
                    # https://github.com/PyAV-Org/PyAV/discussions/1510
                    # if int(av.__version__.split(".")[0]) >= 14:
                    #     rgba_array = frame_resized.to_ndarray(format="rgba")
                    if frame_resized.format.name == "yuv420p":
                        rgb_array = frame_resized.to_ndarray(format="rgb24")
                        rgba_array = np.dstack(
                            (
                                rgb_array,
                                cast(
                                    np.ndarray[Any, np.dtype[np.uint8]],
                                    np.zeros(rgb_array.shape[:2], dtype=np.uint8) + 255,
                                ),
                            )
                        )
                    else:
                        frame_resized = frame_resized.reformat(
                            format="yuva420p",
                            dst_colorspace=1,
                        )
                        rgba_array = yuva_to_rgba(frame_resized)

                    # Remove pixels that was added to make dimensions even
                    rgba_array = rgba_array[0:height_orig, 0:width_orig]
                    self.frames_raw.append(rgba_array)

    def _frames_import_lottie(self) -> None:
        from rlottie_python.rlottie_wrapper import LottieAnimation

        if isinstance(self.in_f, Path):
            suffix = self.in_f.suffix
        else:
            suffix = Path(self.in_f_name).suffix

        if suffix == ".tgs":
            if isinstance(self.in_f, Path):
                anim = LottieAnimation.from_tgs(self.in_f.as_posix())
            else:
                import gzip

                with gzip.open(BytesIO(self.in_f)) as f:
                    data = f.read().decode(encoding="utf-8")
                anim = LottieAnimation.from_data(data)
        else:
            if isinstance(self.in_f, Path):
                anim = LottieAnimation.from_file(self.in_f.as_posix())
            else:
                anim = LottieAnimation.from_data(self.in_f.decode("utf-8"))

        for i in range(anim.lottie_animation_get_totalframe()):
            frame = np.asarray(anim.render_pillow_frame(frame_num=i))
            self.frames_raw.append(frame)

        anim.lottie_animation_destroy()

    def determine_bg_color(self) -> Tuple[int, int, int, int]:
        mean_total = 0.0
        # Calculate average color of all frames for selecting background color
        for frame in self.frames_raw:
            s = frame.shape
            colors = frame.reshape((-1, s[2]))  # type: ignore
            # Do not count in alpha=0
            # If alpha > 0, use alpha as weight
            colors = colors[colors[:, 3] != 0]
            if colors.shape[0] != 0:
                alphas = colors[:, 3] / 255
                r_mean = cast(float, np.mean(colors[:, 0] * alphas))
                g_mean = cast(float, np.mean(colors[:, 1] * alphas))
                b_mean = cast(float, np.mean(colors[:, 2] * alphas))
                mean_total += (r_mean + g_mean + b_mean) / 3

        if mean_total / len(self.frames_raw) < 128:
            return (255, 255, 255, 0)
        else:
            return (0, 0, 0, 0)

    def frames_resize(
        self, frames_in: "List[np.ndarray[Any, Any]]"
    ) -> "List[np.ndarray[Any, Any]]":
        frames_out: "List[np.ndarray[Any, Any]]" = []

        resample: Literal[0, 1, 2, 3, 4, 5]
        if self.opt_comp.scale_filter == "nearest":
            resample = Image.NEAREST
        elif self.opt_comp.scale_filter == "box":
            resample = Image.BOX
        elif self.opt_comp.scale_filter == "bilinear":
            resample = Image.BILINEAR
        elif self.opt_comp.scale_filter == "hamming":
            resample = Image.HAMMING
        elif self.opt_comp.scale_filter == "bicubic":
            resample = Image.BICUBIC
        elif self.opt_comp.scale_filter == "lanczos":
            resample = Image.LANCZOS
        else:
            resample = Image.BICUBIC

        if self.bg_color is None:
            self.bg_color = self.determine_bg_color()

        for frame in frames_in:
            with Image.fromarray(frame, "RGBA") as im:  # type: ignore
                width, height = im.size

            if self.res_w is None:
                self.res_w = width
            if self.res_h is None:
                self.res_h = height

            scaling = 1 - (self.opt_comp.padding_percent / 100)
            if width / self.res_w > height / self.res_h:
                width_new = int(self.res_w * scaling)
                height_new = int(height * self.res_w / width * scaling)
            else:
                height_new = int(self.res_h * scaling)
                width_new = int(width * self.res_h / height * scaling)

            with im.resize((width_new, height_new), resample=resample) as im_resized:
                with Image.new(
                    "RGBA", (self.res_w, self.res_h), self.bg_color
                ) as im_new:
                    im_new.alpha_composite(
                        im_resized,
                        ((self.res_w - width_new) // 2, (self.res_h - height_new) // 2),
                    )
                    frames_out.append(np.asarray(im_new))

        return frames_out

    def frames_drop(
        self, frames_in: "List[np.ndarray[Any, Any]]"
    ) -> "List[np.ndarray[Any, Any]]":
        if (
            not self.codec_info_orig.is_animated
            or not self.fps
            or len(self.frames_processed) == 1
        ):
            return [frames_in[0]]

        frames_out: "List[np.ndarray[Any, Any]]" = []

        # fps_ratio: 1 frame in new anim equal to how many frame in old anim
        # speed_ratio: How much to speed up / slow down
        fps_ratio = self.codec_info_orig.fps / self.fps
        if (
            self.opt_comp.duration_min
            and self.codec_info_orig.duration < self.opt_comp.duration_min
        ):
            speed_ratio = self.codec_info_orig.duration / self.opt_comp.duration_min
        elif (
            self.opt_comp.duration_max
            and self.codec_info_orig.duration > self.opt_comp.duration_max
        ):
            speed_ratio = self.codec_info_orig.duration / self.opt_comp.duration_max
        else:
            speed_ratio = 1

        # How many frames to advance in original video for each frame of output video
        frame_increment = fps_ratio * speed_ratio

        frames_out_min = None
        frames_out_max = None
        if self.opt_comp.duration_min:
            frames_out_min = ceil(self.fps * self.opt_comp.duration_min / 1000)
        if self.opt_comp.duration_max:
            frames_out_max = floor(self.fps * self.opt_comp.duration_max / 1000)

        frame_current = 0
        frame_current_float = 0.0
        while True:
            if frame_current <= len(frames_in) - 1 and not (
                frames_out_max and len(frames_out) == frames_out_max
            ):
                frames_out.append(frames_in[frame_current])
            else:
                while len(frames_out) == 0 or (
                    frames_out_min and len(frames_out) < frames_out_min
                ):
                    frames_out.append(frames_in[-1])
                return frames_out
            frame_current_float += frame_increment
            frame_current = int(rounding(frame_current_float))

    def frames_export(self) -> None:
        is_animated = len(self.frames_processed) > 1 and self.fps
        if self.out_f.suffix in (".apng", ".png"):
            if is_animated:
                self._frames_export_apng()
            else:
                self._frames_export_png()
        elif self.out_f.suffix in (".gif", ".webp"):
            self._frames_export_pil_anim()
        elif self.out_f.suffix in (".webm", ".mp4", ".mkv") or is_animated:
            self._frames_export_pyav()
        else:
            self._frames_export_pil()

    def _check_dup(self) -> bool:
        if len(self.frames_processed) == 1:
            return False

        prev_frame = self.frames_processed[0]
        for frame in self.frames_processed[1:]:
            if np.array_equal(frame, prev_frame):
                return True
            prev_frame = frame

        return False

    def _frames_export_pil(self) -> None:
        with Image.fromarray(self.frames_processed[0]) as im:  # type: ignore
            im.save(
                self.tmp_f,
                format=self.out_f.suffix.replace(".", ""),
                quality=self.quality,
            )

    def _frames_export_pyav(self) -> None:
        import av
        from av.video.stream import VideoStream

        options_container: Dict[str, str] = {}
        options_stream: Dict[str, str] = {}

        if isinstance(self.quality, int):
            # Seems not actually working
            options_stream["quality"] = str(self.quality)
            options_stream["lossless"] = "0"

        if self.out_f.suffix in (".apng", ".png"):
            codec = "apng"
            pixel_format = "rgba"
            options_stream["plays"] = "0"
        elif self.out_f.suffix in (".webm", ".mkv"):
            codec = "libvpx-vp9"
            pixel_format = "yuva420p"
            options_stream["loop"] = "0"
        elif self.out_f.suffix == ".webp":
            codec = "webp"
            pixel_format = "yuva420p"
            options_container["loop"] = "0"
        else:
            codec = "libvpx-vp9"
            pixel_format = "yuv420p"
            options_stream["loop"] = "0"

        with av.open(
            self.tmp_f,
            "w",
            format=self.out_f.suffix.replace(".", ""),
            options=options_container,
        ) as output:
            out_stream = output.add_stream(codec, rate=self.fps, options=options_stream)  # type: ignore
            out_stream = cast(VideoStream, out_stream)
            assert isinstance(self.res_w, int) and isinstance(self.res_h, int)
            out_stream.width = self.res_w
            out_stream.height = self.res_h
            out_stream.pix_fmt = pixel_format

            for frame in self.frames_processed:
                av_frame = av.VideoFrame.from_ndarray(frame, format="rgba")
                output.mux(out_stream.encode(av_frame))
            output.mux(out_stream.encode())

    def _frames_export_pil_anim(self) -> None:
        extra_kwargs: Dict[str, Any] = {}

        # disposal=2 on gif cause flicker in image with transparency
        # Occurs in Pillow == 10.2.0
        # https://github.com/python-pillow/Pillow/issues/7787
        if PillowVersion == "10.2.0":
            extra_kwargs["optimize"] = False
        else:
            extra_kwargs["optimize"] = True

        if self.out_f.suffix == ".gif":
            # GIF can only have one alpha color
            # Change lowest alpha to alpha=0
            # Only keep alpha=0 and alpha=255, nothing in between
            extra_kwargs["format"] = "GIF"
            frames_processed = np.array(self.frames_processed)
            alpha = frames_processed[:, :, :, 3]
            alpha_min = np.min(alpha)  # type: ignore
            if alpha_min < 255:
                alpha[alpha > alpha_min] = 255
                alpha[alpha == alpha_min] = 0

            if 0 in alpha:
                extra_kwargs["transparency"] = 0
                extra_kwargs["disposal"] = 2
                im_out = [self.quantize(Image.fromarray(i)) for i in frames_processed]  # type: ignore
            else:
                im_out = [
                    self.quantize(Image.fromarray(i).convert("RGB")).convert("RGB")  # type: ignore
                    for i in frames_processed
                ]
        elif self.out_f.suffix == ".webp":
            im_out = [Image.fromarray(i) for i in self.frames_processed]  # type: ignore
            extra_kwargs["format"] = "WebP"
            extra_kwargs["allow_mixed"] = True
            extra_kwargs["kmax"] = (
                1  # Keyframe every frame, otherwise black lines artifact can appear
            )
            if self.quality:
                if self.quality < 20:
                    extra_kwargs["minimize_size"] = True
                extra_kwargs["method"] = 4 + int(2 * (100 - self.quality) / 100)
                extra_kwargs["alpha_quality"] = self.quality
        else:
            raise RuntimeError(f"Invalid format {self.out_f.suffix}")

        if self.fps:
            extra_kwargs["save_all"] = True
            extra_kwargs["append_images"] = im_out[1:]
            extra_kwargs["duration"] = int(1000 / self.fps)
            extra_kwargs["loop"] = 0

        im_out[0].save(
            self.tmp_f,
            quality=self.quality,
            **extra_kwargs,
        )

    def _frames_export_png(self) -> None:
        with Image.fromarray(self.frames_processed[0], "RGBA") as image:  # type: ignore
            image_quant = self.quantize(image)

        with BytesIO() as f:
            image_quant.save(f, format="png")
            f.seek(0)
            frame_optimized = self.optimize_png(f.read())
            self.tmp_f.write(frame_optimized)

    def _frames_export_apng(self) -> None:
        from apngasm_python._apngasm_python import APNGAsm, create_frame_from_rgba  # type: ignore

        assert self.fps
        assert self.res_h

        frames_concat = np.concatenate(self.frames_processed)
        with Image.fromarray(frames_concat, "RGBA") as image_concat:  # type: ignore
            image_quant = self.quantize(image_concat)

        if self.apngasm is None:
            self.apngasm = APNGAsm()  # type: ignore
        assert isinstance(self.apngasm, APNGAsm)

        delay_num = int(1000 / self.fps)
        for i in range(0, image_quant.height, self.res_h):
            with BytesIO() as f:
                crop_dimension = (0, i, image_quant.width, i + self.res_h)
                image_cropped = image_quant.crop(crop_dimension)
                image_cropped.save(f, format="png")
                f.seek(0)
                frame_optimized = self.optimize_png(f.read())
            with Image.open(BytesIO(frame_optimized)) as im:
                image_final = im.convert("RGBA")
            frame_final = create_frame_from_rgba(
                np.array(image_final),
                width=image_final.width,
                height=image_final.height,
                delay_num=delay_num,
                delay_den=1000,
            )
            self.apngasm.add_frame(frame_final)

        with CacheStore.get_cache_store(path=self.opt_comp.cache_dir) as tempdir:
            tmp_apng = Path(tempdir, f"out{self.out_f.suffix}")
            self.apngasm.assemble(tmp_apng.as_posix())

            with open(tmp_apng, "rb") as f:
                self.tmp_f.write(f.read())

        self.apngasm.reset()

    def optimize_png(self, image_bytes: bytes) -> bytes:
        import oxipng

        return oxipng.optimize_from_memory(
            image_bytes,
            level=4,
            fix_errors=True,
            filter=[oxipng.RowFilter.Brute],
            optimize_alpha=True,
            strip=oxipng.StripChunks.safe(),
        )

    def quantize(self, image: Image.Image) -> Image.Image:
        if not (self.color and self.color <= 256):
            return image.copy()
        if self.opt_comp.quantize_method == "imagequant":
            return self._quantize_by_imagequant(image)
        if self.opt_comp.quantize_method == "fastoctree":
            return self._quantize_by_fastoctree(image)

        return image

    def _quantize_by_imagequant(self, image: Image.Image) -> Image.Image:
        import imagequant  # type: ignore

        assert isinstance(self.quality, int)
        assert isinstance(self.opt_comp.quality_min, int)
        assert isinstance(self.opt_comp.quality_max, int)
        assert isinstance(self.color, int)

        dither = 1 - (self.quality - self.opt_comp.quality_min) / (
            self.opt_comp.quality_max - self.opt_comp.quality_min
        )
        image_quant = None
        for i in range(self.quality, 101, 5):
            try:
                image_quant = imagequant.quantize_pil_image(  # type: ignore
                    image,
                    dithering_level=dither,
                    max_colors=self.color,
                    min_quality=self.opt_comp.quality_min,
                    max_quality=i,
                )
                return image_quant
            except RuntimeError:
                pass

        return image

    def _quantize_by_fastoctree(self, image: Image.Image) -> Image.Image:
        assert self.color

        return image.quantize(colors=self.color, method=2)

    def fix_fps(self, fps: float) -> Fraction:
        # After rounding fps/duration during export,
        # Video duration may exceed limit.
        # Hence we need to 'fix' the fps
        if self.out_f.suffix == ".gif":
            # Quote from https://www.w3.org/Graphics/GIF/spec-gif89a.txt
            # vii) Delay Time - If not 0, this field specifies
            # the number of hundredths (1/100) of a second
            #
            # For GIF, we need to adjust fps such that delay is matching to hundreths of second
            return self._fix_fps_duration(fps, 100)
        if self.out_f.suffix in (".webp", ".apng", ".png"):
            return self._fix_fps_duration(fps, 1000)

        return self._fix_fps_pyav(fps)

    def _fix_fps_duration(self, fps: float, denominator: int) -> Fraction:
        delay = int(rounding(denominator / fps))
        fps_fraction = Fraction(denominator, delay)
        if self.opt_comp.fps_max and fps_fraction > self.opt_comp.fps_max:
            return Fraction(denominator, (delay + 1))
        if self.opt_comp.fps_min and fps_fraction < self.opt_comp.fps_min:
            return Fraction(denominator, (delay - 1))
        return fps_fraction

    def _fix_fps_pyav(self, fps: float) -> Fraction:
        return Fraction(rounding(fps))
