#!/usr/bin/env python3
import os
import io
from multiprocessing.queues import Queue as QueueType
from typing import Optional, Union

import numpy as np
from PIL import Image

from .utils.media.codec_info import CodecInfo # type: ignore
from .utils.files.cache_store import CacheStore # type: ignore
from .utils.media.format_verify import FormatVerify # type: ignore
from .utils.fake_cb_msg import FakeCbMsg # type: ignore
from .job_option import CompOption

def get_step_value(
        max: Optional[int], min: Optional[int],
        step: int, steps: int,
        power: int = 1,
        even: bool = False
    ) -> Optional[int]:
    # Power should be between -1 and positive infinity
    # Smaller power = More 'importance' of the parameter
    # Power of 1 is linear relationship
    # e.g. fps has lower power -> Try not to reduce it early on

    if step > 0:
        factor = pow(step / steps, power)
    else:
        factor = 0
    
    if max != None and min != None:
        v = round((max - min) * step / steps * factor + min)
        if even == True and v % 2 == 1:
            return v + 1
        else:
            return v
    else:
        return None

def useful_array(plane, bytes_per_pixel=1, dtype='uint8'):
    total_line_size = abs(plane.line_size)
    useful_line_size = plane.width * bytes_per_pixel
    arr = np.frombuffer(plane, np.uint8)
    if total_line_size != useful_line_size:
        arr = arr.reshape(-1, total_line_size)[:, 0:useful_line_size].reshape(-1)
    return arr.view(np.dtype(dtype))

class StickerConvert:
    MSG_START_COMP = '[I] Start compressing {} -> {}'
    MSG_SKIP_COMP = '[S] Compatible file found, skip compress and just copy {} -> {}'
    MSG_COMP = ('[C] Compressing {} -> {} res={}x{}, '
        'quality={}, fps={}, color={} (step {}-{}-{})')
    MSG_REDO_COMP = '[{}] Compressed {} -> {} but size {} {} limit {}, recompressing'
    MSG_DONE_COMP = '[S] Successful compression {} -> {} size {} (step {})'
    MSG_FAIL_COMP = ('[F] Failed Compression {} -> {}, '
        'cannot get below limit {} with lowest quality under current settings')

    def __init__(self,
                 in_f: Union[str, list[str, io.BytesIO]],
                 out_f: str,
                 opt_comp: CompOption,
                 cb_msg: Union[FakeCbMsg, bool] = True):
        
        if not isinstance(cb_msg, QueueType):
            if cb_msg == False:
                silent = True
            else:
                silent = False
            cb_msg = FakeCbMsg(print, silent=silent)

        if isinstance(in_f, str):
            self.in_f = in_f
            self.in_f_name = os.path.split(self.in_f)[1]
            self.in_f_ext = CodecInfo.get_file_ext(self.in_f)
        else:
            self.in_f = in_f[1]
            self.in_f_name = os.path.split(in_f[0])[1]
            self.in_f_ext = CodecInfo.get_file_ext(in_f[0])

        self.out_f = out_f
        self.out_f_name = os.path.split(self.out_f)[1]
        self.out_f_ext = os.path.splitext(out_f)[1]

        self.cb_msg = cb_msg
        self.frames_raw: list[np.ndarray] = []
        self.frames_processed: list[np.ndarray] = []
        self.opt_comp = opt_comp
        if not self.opt_comp.steps:
            self.opt_comp.steps = 1

        self.size = 0
        self.size_max = None
        self.res_w = None
        self.res_h = None
        self.quality = None
        self.fps = None
        self.color = None

        self.codec_info_orig = CodecInfo(self.in_f)

        self.tmp_f = None
        self.result = None
        self.result_size = 0
        self.result_step = None

        self.apngasm = None

    def convert(self) -> tuple[bool, str, Union[None, bytes, str], int]:
        if (FormatVerify.check_format(self.in_f, fmt=self.out_f_ext, file_info=self.codec_info_orig) and
            FormatVerify.check_file_res(self.in_f, res=self.opt_comp.res, file_info=self.codec_info_orig) and
            FormatVerify.check_file_fps(self.in_f, fps=self.opt_comp.fps, file_info=self.codec_info_orig) and
            FormatVerify.check_file_size(self.in_f, size=self.opt_comp.size_max, file_info=self.codec_info_orig) and
            FormatVerify.check_file_duration(self.in_f, duration=self.opt_comp.duration, file_info=self.codec_info_orig)):
            self.cb_msg.put(self.MSG_SKIP_COMP.format(self.in_f_name, self.out_f_name))

            with open(self.in_f, 'rb') as f:
                self.result = f.read()
            self.result_size = os.path.getsize(self.in_f)
            
            return self.compress_done(self.result)

        self.cb_msg.put(self.MSG_START_COMP.format(self.in_f_name, self.out_f_name))

        steps_list = []
        for step in range(self.opt_comp.steps, -1, -1):
            steps_list.append((
                get_step_value(self.opt_comp.res_w_max, self.opt_comp.res_w_min, step, self.opt_comp.steps, self.opt_comp.res_power, True),
                get_step_value(self.opt_comp.res_h_max, self.opt_comp.res_h_min, step, self.opt_comp.steps, self.opt_comp.res_power, True),
                get_step_value(self.opt_comp.quality_max, self.opt_comp.quality_min, step, self.opt_comp.steps, self.opt_comp.quality_power),
                get_step_value(self.opt_comp.fps_max, self.opt_comp.fps_min, step, self.opt_comp.steps, self.opt_comp.fps_power),
                get_step_value(self.opt_comp.color_max, self.opt_comp.color_min, step, self.opt_comp.steps, self.opt_comp.color_power)
            ))

        step_lower = 0
        step_upper = self.opt_comp.steps

        if self.opt_comp.size_max == [None, None]:
            # No limit to size, create the best quality result
            step_current = 0
        else:
            step_current = round((step_lower + step_upper) / 2)

        self.frames_import()
        while True:
            param = steps_list[step_current]
            self.res_w = param[0]
            self.res_h = param[1]
            self.quality = param[2]
            self.fps = min(param[3], self.codec_info_orig.fps)
            self.color = param[4]

            self.tmp_f = io.BytesIO()
            msg = self.MSG_COMP.format(
                    self.in_f_name, self.out_f_name,
                    self.res_w, self.res_h,
                    self.quality, int(self.fps), self.color, 
                    step_lower, step_current, step_upper
                )
            self.cb_msg.put(msg)
            
            self.frames_processed = self.frames_drop(self.frames_raw)
            self.frames_processed = self.frames_resize(self.frames_processed)
            self.frames_export()

            self.tmp_f.seek(0)
            self.size = self.tmp_f.getbuffer().nbytes
            if self.codec_info_orig.is_animated == True:
                self.size_max = self.opt_comp.size_max_vid
            else:
                self.size_max = self.opt_comp.size_max_img

            if (not self.size_max or
                (self.size <= self.size_max and self.size >= self.result_size)):
                self.result = self.tmp_f.read()
                self.result_size = self.size
                self.result_step = step_current
        
            if step_upper - step_lower > 1:
                if self.size <= self.size_max:
                    sign = '<'
                    step_upper = step_current
                else:
                    sign = '>'
                    step_lower = step_current
                step_current = int((step_lower + step_upper) / 2)
                self.recompress(sign)
            elif self.result or not self.size_max:
                return self.compress_done(self.result, self.result_step)
            else:
                return self.compress_fail()
    
    def recompress(self, sign: str):
        msg = self.MSG_REDO_COMP.format(
                sign, self.in_f_name, self.out_f_name, self.size, sign, self.size_max
            )
        self.cb_msg.put(msg)

    def compress_fail(self) -> tuple[bool, str, Union[None, bytes, str], int]:
        msg = self.MSG_FAIL_COMP.format(
            self.in_f_name, self.out_f_name, self.size_max
        )
        self.cb_msg.put(msg)

        return False, self.in_f, self.out_f, self.size

    def compress_done(self,
                  data: bytes,
                  result_step: Optional[int] = None
                  ) -> tuple[bool, str, Union[None, bytes, str], int]:
        
        if os.path.splitext(self.out_f_name)[0] == 'none':
            self.out_f = None
        elif os.path.splitext(self.out_f_name)[0] == 'bytes':
            self.out_f = data
        else:
            with open(self.out_f, 'wb+') as f:
                f.write(data)

        if result_step:            
            msg = self.MSG_DONE_COMP.format(
                self.in_f_name, self.out_f_name, self.result_size, result_step
            )
            self.cb_msg.put(msg)
        
        return True, self.in_f, self.out_f, self.result_size

    def frames_import(self):
        if self.in_f_ext in ('.tgs', '.lottie', '.json'):
            self._frames_import_lottie()
        elif self.in_f_ext in ('.webp', '.apng', 'png'):
            # ffmpeg do not support webp decoding (yet)
            # ffmpeg could fail to decode apng if file is buggy
            self._frames_import_pillow()
        else:
            self._frames_import_pyav()

    def _frames_import_pillow(self):
        with Image.open(self.in_f) as im:
            im = im.convert("RGBA")
            if 'n_frames'in im.__dir__():
                for i in range(im.n_frames):
                    im.seek(i)
                    self.frames_raw.append(np.asarray(im))
            else:
                self.frames_raw.append(np.asarray(im))
    
    def _frames_import_pyav(self):
        import av # type: ignore
        from av.codec.context import CodecContext # type: ignore

        # Crashes when handling some webm in yuv420p and convert to rgba
        # https://github.com/PyAV-Org/PyAV/issues/1166
        with av.open(self.in_f) as container:
            context = container.streams.video[0].codec_context
            if context.name == 'vp8':
                context = CodecContext.create('libvpx', 'r')
            elif context.name == 'vp9':
                context = CodecContext.create('libvpx-vp9', 'r')

            for packet in container.demux(container.streams.video):
                for frame in context.decode(packet):
                    if frame.width % 2 != 0:
                        width = frame.width - 1
                    else:
                        width = frame.width
                    if frame.height % 2 != 0:
                        height = frame.height - 1
                    else:
                        height = frame.height
                    if frame.format.name == 'yuv420p':
                        rgb_array = frame.to_ndarray(format='rgb24')
                        rgba_array = np.dstack(
                            (rgb_array, np.zeros(rgb_array.shape[:2], dtype=np.uint8) + 255)
                        )
                    else:
                        # yuva420p may cause crash
                        # https://github.com/laggykiller/sticker-convert/issues/114
                        frame = frame.reformat(width=width, height=height, format='yuva420p', dst_colorspace=1)

                        # https://stackoverflow.com/questions/72308308/converting-yuv-to-rgb-in-python-coefficients-work-with-array-dont-work-with-n
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
                        yuv_array[:, :, 0] = yuv_array[:, :, 0].clip(16, 235).astype(yuv_array.dtype) - 16
                        yuv_array[:, :, 1:] = yuv_array[:, :, 1:].clip(16, 240).astype(yuv_array.dtype) - 128

                        convert = np.array([
                            [1.164,  0.000,  1.793],
                            [1.164, -0.213, -0.533],
                            [1.164,  2.112,  0.000]
                        ])
                        rgb_array = np.matmul(yuv_array, convert.T).clip(0,255).astype('uint8')
                        rgba_array = np.concatenate((rgb_array, a), axis=2)

                    self.frames_raw.append(rgba_array)

    def _frames_import_lottie(self):
        from rlottie_python import LottieAnimation # type: ignore
        
        if self.in_f_ext == '.tgs':
            anim = LottieAnimation.from_tgs(self.in_f)
        else:
            if isinstance(self.in_f, str):
                anim = LottieAnimation.from_file(self.in_f)
            else:
                anim = LottieAnimation.from_data(self.in_f.read().decode('utf-8'))

        for i in range(anim.lottie_animation_get_totalframe()):
            frame = np.asarray(anim.render_pillow_frame(frame_num=i))
            self.frames_raw.append(frame)
        
        anim.lottie_animation_destroy()

    def frames_resize(self, frames_in: list[np.ndarray]) -> list[np.ndarray]:
        frames_out = []

        if self.opt_comp.scale_filter == 'nearest':
            resample = Image.NEAREST
        elif self.opt_comp.scale_filter == 'bilinear':
            resample = Image.BILINEAR
        elif self.opt_comp.scale_filter == 'bicubic':
            resample = Image.BICUBIC
        elif self.opt_comp.scale_filter == 'lanczos':
            resample = Image.LANCZOS
        else:
            resample = Image.LANCZOS

        for frame in frames_in:
            with Image.fromarray(frame, 'RGBA') as im:
                width, height = im.size

                if self.res_w == None:
                    self.res_w = width
                if self.res_h == None:
                    self.res_h = height

                if width > height:
                    width_new = self.res_w
                    height_new = height * self.res_w // width
                else:
                    height_new = self.res_h
                    width_new = width * self.res_h // height

                with (im.resize((width_new, height_new), resample=resample) as im_resized,
                      Image.new('RGBA', (self.res_w, self.res_h), (0, 0, 0, 0)) as im_new):
                    
                    im_new.paste(
                        im_resized, ((self.res_w - width_new) // 2, (self.res_h - height_new) // 2)
                    )
                    frames_out.append(np.asarray(im_new))
        
        return frames_out
    
    def frames_drop(self, frames_in: list[np.ndarray]) -> list[np.ndarray]:
        if not self.codec_info_orig.is_animated or not self.fps:
            return [frames_in[0]]

        frames_out = []

        # fps_ratio: 1 frame in new anim equal to how many frame in old anim
        # speed_ratio: How much to speed up / slow down
        fps_ratio = self.codec_info_orig.fps / self.fps
        if (self.opt_comp.duration_min != None and
            self.codec_info_orig.duration < self.opt_comp.duration_min):

            speed_ratio = self.codec_info_orig.duration / self.opt_comp.duration_min
        elif (self.opt_comp.duration_max != None and
              self.codec_info_orig.duration > self.opt_comp.duration_max):
            
            speed_ratio = self.codec_info_orig.duration / self.opt_comp.duration_max
        else:
            speed_ratio = 1

        frame_current = 0
        frame_current_float = 0
        while frame_current < len(frames_in):
            frames_out.append(frames_in[frame_current])
            frame_current_float += fps_ratio * speed_ratio
            frame_current = round(frame_current_float)

        return frames_out

    def frames_export(self):
        if self.out_f_ext in ('.apng', '.png') and self.fps:
            self._frames_export_apng()
        elif self.out_f_ext == '.png':
            self._frames_export_png()
        elif self.out_f_ext == '.webp' and self.fps:
            self._frames_export_webp()
        elif self.fps:
            self._frames_export_pyav()
        else:
            self._frames_export_pil()
    
    def _frames_export_pil(self):
        with Image.fromarray(self.frames_processed[0]) as im:
            im.save(
                self.tmp_f,
                format=self.out_f_ext.replace('.', ''),
                quality=self.quality
            )

    def _frames_export_pyav(self):
        import av # type: ignore

        options = {}
        
        if isinstance(self.quality, int):
            # Seems not actually working
            options['quality'] = str(self.quality)
            options['lossless'] = '0'

        if self.out_f_ext == '.gif':
            codec = 'gif'
            pixel_format = 'rgb8'
            options['loop'] = '0'
        elif self.out_f_ext in ('.apng', '.png'):
            codec = 'apng'
            pixel_format = 'rgba'
            options['plays'] = '0'
        elif self.out_f_ext in ('.webp', '.webm', '.mkv'):
            codec = 'libvpx-vp9'
            pixel_format = 'yuva420p'
            options['loop'] = '0'
        else:
            codec = 'libx264'
            pixel_format = 'yuv420p'
            options['loop'] = '0'
        
        with av.open(self.tmp_f, 'w', format=self.out_f_ext.replace('.', '')) as output:
            out_stream = output.add_stream(codec, rate=int(self.fps), options=options)
            out_stream.width = self.res_w
            out_stream.height = self.res_h
            out_stream.pix_fmt = pixel_format
            
            for frame in self.frames_processed:
                av_frame = av.VideoFrame.from_ndarray(frame, format='rgba')
                for packet in out_stream.encode(av_frame):
                    output.mux(packet)
            
            for packet in out_stream.encode():
                output.mux(packet)
    
    def _frames_export_webp(self):
        import webp # type: ignore

        config = webp.WebPConfig.new(quality=self.quality)
        enc = webp.WebPAnimEncoder.new(self.res_w, self.res_h)
        timestamp_ms = 0
        for frame in self.frames_processed:
            pic = webp.WebPPicture.from_numpy(frame)
            enc.encode_frame(pic, timestamp_ms, config=config)
            timestamp_ms += int(1 / self.fps * 1000)
        anim_data = enc.assemble(timestamp_ms)
        self.tmp_f.write(anim_data.buffer())
    
    def _frames_export_png(self):
        with Image.fromarray(self.frames_processed[0], 'RGBA') as image:
            if self.color and self.color <= 256:
                image_quant = self.quantize(image)
            else:
                image_quant = image.copy()

        with io.BytesIO() as f:
            image_quant.save(f, format='png')
            f.seek(0)
            frame_optimized = self.optimize_png(f.read())
            self.tmp_f.write(frame_optimized)

    def _frames_export_apng(self):
        from apngasm_python._apngasm_python import APNGAsm, create_frame_from_rgba

        frames_concat = np.concatenate(self.frames_processed)
        with Image.fromarray(frames_concat, 'RGBA') as image_concat:
            if self.color and self.color <= 256:
                image_quant = self.quantize(image_concat)
            else:
                image_quant = image_concat.copy()

        if self.apngasm == None:
            self.apngasm = APNGAsm()

        for i in range(0, image_quant.height, self.res_h):
            with io.BytesIO() as f:
                crop_dimension = (0, i, image_quant.width, i+self.res_h)
                image_cropped = image_quant.crop(crop_dimension)
                image_cropped.save(f, format='png')
                f.seek(0)
                frame_optimized = self.optimize_png(f.read())
            with Image.open(io.BytesIO(frame_optimized)) as im:
                image_final = im.convert('RGBA')
            frame_final = create_frame_from_rgba(
                np.array(image_final),
                image_final.width,
                image_final.height
            )
            frame_final.delay_num = int(1000 / self.fps)
            frame_final.delay_den = 1000
            self.apngasm.add_frame(frame_final)

        with CacheStore.get_cache_store(path=self.opt_comp.cache_dir) as tempdir:
            self.apngasm.assemble(os.path.join(tempdir, f'out{self.out_f_ext}'))

            with open(os.path.join(tempdir, f'out{self.out_f_ext}'), 'rb') as f:
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
            strip=oxipng.StripChunks.safe()
        )

    def quantize(self, image: Image.Image) -> Image.Image:
        if self.opt_comp.quantize_method == 'imagequant':
            return self._quantize_by_imagequant(image)
        elif self.opt_comp.quantize_method == 'fastoctree':
            return self._quantize_by_fastoctree(image)
        else:
            return image

    def _quantize_by_imagequant(self, image: Image.Image) -> Image.Image:
        import imagequant

        dither = 1 - (self.quality - self.opt_comp.quality_min) / (self.opt_comp.quality_max - self.opt_comp.quality_min)
        image_quant = None
        for i in range(self.quality, 101, 5):
            try:
                image_quant = imagequant.quantize_pil_image(
                    image,
                    dithering_level=dither,
                    max_colors=self.color,
                    min_quality=self.opt_comp.quality_min,
                    max_quality=i
                )
                return image_quant
            except RuntimeError:
                pass
        
        return image

    def _quantize_by_fastoctree(self, image: Image.Image) -> Image.Image:
        return image.quantize(colors=self.color, method=2)
