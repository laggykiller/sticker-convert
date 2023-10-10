#!/usr/bin/env python3
import os
import io
from multiprocessing.queues import Queue as QueueType
from typing import Optional, Union

import imageio.v3 as iio
from rlottie_python import LottieAnimation # type: ignore
from apngasm_python._apngasm_python import APNGAsm, create_frame_from_rgba
import numpy as np
from PIL import Image
import av # type: ignore
from av.codec.context import CodecContext # type: ignore
import webp # type: ignore
import oxipng

from .utils.media.codec_info import CodecInfo # type: ignore
from .utils.files.cache_store import CacheStore # type: ignore
from .utils.media.format_verify import FormatVerify # type: ignore
from .utils.fake_cb_msg import FakeCbMsg # type: ignore
from .job_option import CompOption

def get_step_value(
        max: Optional[int], min: Optional[int],
        step: int, steps: int
        ) -> Optional[int]:
    
    if max and min:
        return round((max - min) * step / steps + min)
    else:
        return None

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

        self.frames_orig = CodecInfo.get_file_frames(self.in_f)
        self.fps_orig = CodecInfo.get_file_fps(self.in_f)
        self.duration_orig = self.frames_orig / self.fps_orig * 1000

        self.tmp_f = None
        self.result = None
        self.result_size = 0
        self.result_step = None

        self.apngasm = APNGAsm() # type: ignore[call-arg]

    def convert(self) -> tuple[bool, str, Union[None, bytes, str], int]:
        if (FormatVerify.check_format(self.in_f, fmt=self.out_f_ext) and
            FormatVerify.check_file_res(self.in_f, res=self.opt_comp.res) and
            FormatVerify.check_file_fps(self.in_f, fps=self.opt_comp.fps) and
            FormatVerify.check_file_size(self.in_f, size=self.opt_comp.size_max) and
            FormatVerify.check_duration(self.in_f, duration=self.opt_comp.duration)):
            self.cb_msg.put(self.MSG_SKIP_COMP.format(self.in_f_name, self.out_f_name))

            with open(self.in_f, 'rb') as f:
                self.result = f.read()
            self.result_size = os.path.getsize(self.in_f)
            
            return self.compress_done(self.result)

        self.cb_msg.put(self.MSG_START_COMP.format(self.in_f_name, self.out_f_name))

        steps_list = []
        for step in range(self.opt_comp.steps, -1, -1):
            steps_list.append((
                get_step_value(self.opt_comp.res_w_max, self.opt_comp.res_w_min, step, self.opt_comp.steps),
                get_step_value(self.opt_comp.res_h_max, self.opt_comp.res_h_min, step, self.opt_comp.steps),
                get_step_value(self.opt_comp.quality_max, self.opt_comp.quality_min, step, self.opt_comp.steps),
                get_step_value(self.opt_comp.fps_max, self.opt_comp.fps_min, step, self.opt_comp.steps),
                get_step_value(self.opt_comp.color_max, self.opt_comp.color_min, step, self.opt_comp.steps)
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
            self.fps = param[3]
            self.color = param[4]

            self.tmp_f = io.BytesIO()
            msg = self.MSG_COMP.format(
                    self.in_f_name, self.out_f_name,
                    self.res_w, self.res_h,
                    self.quality, self.fps, self.color, 
                    step_lower, step_current, step_upper
                )
            self.cb_msg.put(msg)
            
            self.frames_processed = self.frames_drop(self.frames_raw)
            self.frames_processed = self.frames_resize(self.frames_processed)
            self.frames_export()

            self.tmp_f.seek(0)
            self.size = self.tmp_f.getbuffer().nbytes
            if CodecInfo.is_anim(self.in_f):
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
            self.frames_import_lottie()
        else:
            self.frames_import_imageio()

    def frames_import_imageio(self):
        if self.in_f_ext in '.webp':
            # ffmpeg do not support webp decoding (yet)
            for frame in iio.imiter(self.in_f, plugin='pillow', mode='RGBA'):
                self.frames_raw.append(frame)
            return
        
        frame_format = 'rgba'
        # Crashes when handling some webm in yuv420p and convert to rgba
        # https://github.com/PyAV-Org/PyAV/issues/1166
        metadata = iio.immeta(self.in_f, plugin='pyav', exclude_applied=False)
        context = None
        if metadata.get('video_format') == 'yuv420p':
            if metadata.get('alpha_mode') != '1':
                frame_format = 'rgb24'
            if metadata.get('codec') == 'vp8':
                context = CodecContext.create('v8', 'r')
            elif metadata.get('codec') == 'vp9':
                context = CodecContext.create('libvpx-vp9', 'r')
        
        with av.open(self.in_f) as container:
            if not context:
                context = container.streams.video[0].codec_context
            for packet in container.demux(video=0):
                for frame in context.decode(packet):
                    frame = frame.to_ndarray(format=frame_format)
                    if frame_format == 'rgb24':
                        frame = np.dstack(
                            (frame, np.zeros(frame.shape[:2], dtype=np.uint8)+255)
                            )
                    self.frames_raw.append(frame)

    def frames_import_lottie(self):
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

        for frame in frames_in:
            im = Image.fromarray(frame, 'RGBA')
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
            im = im.resize((width_new, height_new), resample=Image.LANCZOS)
            im_new = Image.new('RGBA', (self.res_w, self.res_h), (0, 0, 0, 0))
            im_new.paste(
                im, ((self.res_w - width_new) // 2, (self.res_h - height_new) // 2)
                )
            frames_out.append(np.asarray(im_new))
        
        return frames_out
    
    def frames_drop(self, frames_in: list[np.ndarray]) -> list[np.ndarray]:
        if not self.fps:
            return [frames_in[0]]

        frames_out = []

        # fps_ratio: 1 frame in new anim equal to how many frame in old anim
        # speed_ratio: How much to speed up / slow down
        fps_ratio = self.fps_orig / self.fps
        if (self.opt_comp.duration_min and
            self.duration_orig < self.opt_comp.duration_min):

            speed_ratio = self.duration_orig / self.opt_comp.duration_min
        elif (self.opt_comp.duration_max and
              self.duration_orig > self.opt_comp.duration_max):
            
            speed_ratio = self.duration_orig / self.opt_comp.duration_max
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
            self.frames_export_apng()
        elif self.out_f_ext == '.png':
            self.frames_export_png()
        elif self.out_f_ext == '.webp' and self.fps:
            self.frames_export_webp()
        elif self.fps:
            self.frames_export_pyav()
        else:
            self.frames_export_pil()
    
    def frames_export_pil(self):
        image = Image.fromarray(self.frames_processed[0])
        image.save(
            self.tmp_f,
            format=self.out_f_ext.replace('.', ''),
            quality=self.quality
        )

    def frames_export_pyav(self):
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
        else:
            codec = 'vp9'
            pixel_format = 'yuva420p'
            options['loop'] = '0'
        
        with av.open(self.tmp_f, 'w', format=self.out_f_ext.replace('.', '')) as output:
            out_stream = output.add_stream(codec, rate=self.fps, options=options)
            out_stream.width = self.res_w
            out_stream.height = self.res_h
            out_stream.pix_fmt = pixel_format
            
            for frame in self.frames_processed:
                av_frame = av.VideoFrame.from_ndarray(frame, format='rgba')
                for packet in out_stream.encode(av_frame):
                    output.mux(packet)
            
            for packet in out_stream.encode():
                output.mux(packet)
    
    def frames_export_webp(self):
        config = webp.WebPConfig.new(quality=self.quality)
        enc = webp.WebPAnimEncoder.new(self.res_w, self.res_h)
        timestamp_ms = 0
        for frame in self.frames_processed:
            pic = webp.WebPPicture.from_numpy(frame)
            enc.encode_frame(pic, timestamp_ms, config=config)
            timestamp_ms += int(1 / self.fps * 1000)
        anim_data = enc.assemble(timestamp_ms)
        self.tmp_f.write(anim_data.buffer())

    def frames_export_png(self):
        image = Image.fromarray(self.frames_processed[0], 'RGBA')
        if self.color and self.color <= 256:
            image_quant = image.quantize(colors=self.color, method=2)
        else:
            image_quant = image
        with io.BytesIO() as f:
            image_quant.save(f, format='png')
            f.seek(0)
            frame_optimized = oxipng.optimize_from_memory(f.read(), level=4)
            self.tmp_f.write(frame_optimized)

    def frames_export_apng(self):
        frames_concat = np.concatenate(self.frames_processed)
        image_concat = Image.fromarray(frames_concat, 'RGBA')
        if self.color and self.color <= 256:
            image_quant = image_concat.quantize(colors=self.color, method=2)
        else:
            image_quant = image_concat

        for i in range(0, image_quant.height, self.res_h):
            with io.BytesIO() as f:
                crop_dimension = (0, i, image_quant.width, i+self.res_h)
                image_cropped = image_quant.crop(crop_dimension)
                image_cropped.save(f, format='png')
                f.seek(0)
                frame_optimized = oxipng.optimize_from_memory(f.read(), level=4)
            image_final = Image.open(io.BytesIO(frame_optimized)).convert('RGBA')
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