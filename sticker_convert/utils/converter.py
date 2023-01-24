#!/usr/bin/env python3
import os
import shutil
import math
import tempfile

from .run_bin import RunBin
from .codec_info import CodecInfo
from .lottie_convert import lottie_convert

# On Linux, old ImageMagick do not have magick command. In such case, use wand library
if RunBin.get_bin('magick', silent=True) == None:
    from wand.image import Image
import ffmpeg
from rlottie_python import LottieAnimation

lottie_in_ext_support = ('.lottie', '.sif', '.svg', '.tnz', '.dotlottie', '.kra', '.bmp', '.py', '.tgs', '.png', '.apng', '.gif', '.tiff')
lottie_out_ext_support = ('.lottie', '.tgs', '.html', '.sif', '.svg', '.png', '.pdf', '.ps', '.gif', '.webp', '.tiff', '.dotlottie', '.video', '.webm', '.mp4', '.webm')

vector_formats = ('.lottie', '.sif', '.svg', '.tnz', '.dotlottie', '.kra', '.bmp', '.py', '.tgs')

class StickerConvert:
    @staticmethod
    def convert(in_f, out_f, res_w=None, res_h=None, quality=None, fps=None, color=None, duration_min=None, duration_max=None, fake_vid=False):
        '''
        Convert format with given res, quality, fps
        '''
        convert_method = StickerConvert.get_convert_method(in_f, out_f, fake_vid)

        convert_method(in_f, out_f, res_w=res_w, res_h=res_h, quality=quality, fps=fps, color=color, duration_min=duration_min, duration_max=duration_max, fake_vid=fake_vid)

    @staticmethod
    def convert_and_compress_to_size(in_f, out_f, opt_comp, cb_msg=print):
        '''
        Convert format with given res, quality, fps
        Try to reduce file size to below thresholds (vid_size_max and img_size_max) by adjusting res, quality, fps
        '''
        convert_method = StickerConvert.get_convert_method(in_f, out_f, opt_comp['fake_vid'])
        
        return StickerConvert.compress_to_size(convert_method, in_f, out_f, opt_comp, cb_msg)

    @staticmethod
    def get_convert_method(in_f, out_f, fake_vid):
        in_f_ext = CodecInfo.get_file_ext(in_f)
        out_f_ext = CodecInfo.get_file_ext(out_f)

        lottie_formats = ('.tgs', '.lottie', '.json')
        if in_f_ext in lottie_formats or out_f_ext in lottie_formats:
            return StickerConvert.convert_lottie

        else:
            if in_f_ext == '.webp':
                return StickerConvert.convert_from_webp_anim

            # webm should be handled by ffmpeg using vp9 codec
            # ImageMagick will remove transparency
            if fake_vid or CodecInfo.is_anim(in_f) or in_f_ext == '.webm':
                if out_f_ext == '.png' or out_f_ext == '.apng':
                    return StickerConvert.convert_to_apng_anim
                else:
                    return StickerConvert.convert_generic_anim
            else:
                return StickerConvert.convert_generic_image
    
    @staticmethod
    def compress_to_size(convert_method, in_f, out_f, opt_comp, cb_msg=print):
        def get_step_value(max, min, step, steps):
            if max and min:
                return round((max - min) * step / steps + min)
            else:
                return
        
        in_f_name = os.path.split(in_f)[1]
        out_f_name = os.path.split(out_f)[1]

        cb_msg(f'[I] Start compressing {in_f_name} -> {out_f_name}')

        duration_min = opt_comp.get('duration', {}).get('min')
        duration_max = opt_comp.get('duration', {}).get('max')
        fake_vid = opt_comp.get('fake_vid')

        steps_list = []
        for step in range(opt_comp['steps'], -1, -1):
            steps_list.append((
                get_step_value(opt_comp['res']['w']['max'], opt_comp['res']['w']['min'], step, opt_comp['steps']),
                get_step_value(opt_comp['res']['w']['max'], opt_comp['res']['w']['min'], step, opt_comp['steps']),
                get_step_value(opt_comp['quality']['max'], opt_comp['quality']['min'], step, opt_comp['steps']),
                get_step_value(opt_comp['fps']['max'], opt_comp['fps']['min'], step, opt_comp['steps']),
                get_step_value(opt_comp['color']['max'], opt_comp['color']['min'], step, opt_comp['steps'])
            ))

        with tempfile.TemporaryDirectory() as tempdir:
            step_lower = 0
            step_upper = opt_comp['steps']

            if opt_comp['size_max']['vid'] == None and opt_comp['size_max']['img'] == None:
                # No limit to size, create the best quality result
                step_current = 0
            else:
                step_current = round((step_lower + step_upper) / 2)

            while True:
                param = steps_list[step_current]

                tmp_f = os.path.join(tempdir, str(step_current) + CodecInfo.get_file_ext(out_f))
                cb_msg(f'[C] Compressing {in_f_name} -> {out_f_name} res={param[0]}x{param[1]}, quality={param[2]}, fps={param[3]}, color={param[4]} (step {step_lower}-{step_current}-{step_upper})')
                convert_method(
                    in_f, tmp_f, res_w=param[0], res_h=param[1], quality=param[2], fps=param[3], color=param[4], 
                    duration_min=duration_min, duration_max=duration_max, fake_vid=fake_vid)
                
                size = os.path.getsize(tmp_f)
                if CodecInfo.is_anim(in_f):
                    size_max = opt_comp['size_max']['vid']
                else:
                    size_max = opt_comp['size_max']['img']
                
                if not size_max:
                    shutil.move(os.path.join(tempdir, str(step_current) + CodecInfo.get_file_ext(out_f)), out_f)
                    cb_msg(f'[S] Successful compression {in_f_name} -> {out_f_name} (step {step_current})')
                    return True

                if size < size_max:
                    if step_upper - step_lower > 1:
                        step_upper = step_current
                        step_current = int((step_lower + step_upper) / 2)
                        cb_msg(f'[<] Compressed {in_f_name} -> {out_f_name} but size {size} < limit {size_max}, recompressing')
                    else:
                        shutil.move(os.path.join(tempdir, str(step_current) + CodecInfo.get_file_ext(out_f)), out_f)
                        cb_msg(f'[S] Successful compression {in_f_name} -> {out_f_name} (step {step_current})')
                        return True
                else:
                    if step_upper - step_lower > 1:
                        step_lower = step_current
                        step_current = round((step_lower + step_upper) / 2)
                        cb_msg(f'[>] Compressed {in_f_name} -> {out_f_name} but size {size} > limit {size_max}, recompressing')
                    else:
                        if step_current < opt_comp['steps']:
                            shutil.move(os.path.join(tempdir, str(step_current + 1) + CodecInfo.get_file_ext(out_f)), out_f)
                            cb_msg(f'[S] Successful compression {in_f_name} -> {out_f_name} (step {step_current})')
                            return True
                        else:
                            cb_msg(f'[F] Failed Compression {in_f_name} -> {out_f_name}, cannot get below limit {size_max} with lowest quality under current settings')
                            return False

    @staticmethod
    def magick_crop(in_f, out_f, res_w, res_h):
        # https://stackoverflow.com/a/28503615
        # out_f: tiles_{0}.jpg
        if RunBin.get_bin('magick', silent=True) == None:
            with Image(filename=in_f) as img:
                i = 0
                for h in range(0, img.height, res_h):
                    for w in range(0, img.width, res_w):
                        w_end = w + res_w
                        h_end = h + res_h
                        with img[w:w_end, h:h_end] as chunk:
                            chunk.save(filename=out_f.format(str(i).zfill(3)))
                        i += 1
        else:
            out_f = out_f.replace('{0}', '%03d')
            RunBin.run_cmd(['magick', in_f, '-crop', f'{res_w}x{res_h}', out_f])

    @staticmethod
    def convert_generic_image(in_f, out_f, res_w=None, res_h=None, quality=None, color=None, **kwargs):
        if not quality:
            quality = 95

        if RunBin.get_bin('magick', silent=True) == None:
            StickerConvert.convert_generic_image_pymodule(in_f, out_f, res_w=res_w, res_h=res_h, quality=quality)
        else:
            StickerConvert.convert_generic_image_subprocess(in_f, out_f, res_w=res_w, res_h=res_h, quality=quality)
        
        if CodecInfo.get_file_ext(out_f) == '.png':
            StickerConvert.png_optimize(out_f, out_f, quality=quality, color=color)
    
    @staticmethod
    def convert_generic_image_pymodule(in_f, out_f, res_w=None, res_h=None, quality=None, **kwargs):
        # https://www.imagemagick.org/script/command-line-options.php#quality
        # For png, lower quality actually means less compression and larger file size (zlib compression step = quality / 10)
        # For png, filter_type = quality % 10
        if CodecInfo.get_file_ext(out_f) == '.png' or not quality:
            quality = 95
        
        with Image(filename=in_f) as img:
            if res_w and res_h:
                img.resize(width=res_w, height=res_h)
                img.background_color = 'none'
                img.gravity = 'center'
                img.extent(width=res_w, height=res_h)
            img.compression_quality = quality
            img.save(filename=out_f)
    
    @staticmethod
    def convert_generic_image_subprocess(in_f, out_f, res_w=None, res_h=None, quality=None, **kwargs):
        # https://www.imagemagick.org/script/command-line-options.php#quality
        # For png, lower quality actually means less compression and larger file size (zlib compression step = quality / 10)
        # For png, filter_type = quality % 10
        if CodecInfo.get_file_ext(out_f) == '.png' or not quality:
            quality = 95
        
        if res_w and res_h:
            RunBin.run_cmd(['magick', in_f, '-resize', f'{res_w}x{res_h}', '-background', 'none', '-gravity', 'center', '-extent', f'{res_w}x{res_h}', '-quality', str(quality), out_f])
        else:
            RunBin.run_cmd(['magick', in_f, '-quality', str(quality), out_f])

    @staticmethod
    def png_optimize(in_f, out_f, quality=None, color=None, **kwargs):
        with tempfile.TemporaryDirectory() as tempdir:
            tmp0_f = os.path.join(tempdir, 'tmp.png')
            shutil.copy(in_f, tmp0_f)

            tmp1_f = os.path.join(tempdir, 'tmp.1.png')
            if color and color <= 256:
                RunBin.run_cmd(['pngnq-s9', '-L', '-Qn', '-T15', '-n', str(color), '-e', '.1.png', tmp0_f])
            else:
                shutil.move(tmp0_f, tmp1_f)

            tmp2_f = os.path.join(tempdir, 'tmp.1.2.png')
            if quality and quality < 100:
                RunBin.run_cmd(['pngquant', '--nofs', '--quality', f'0-{quality}', '--strip', '--ext', '.2.png', tmp1_f])
            else:
                shutil.move(tmp1_f, tmp2_f)

            RunBin.run_cmd(['optipng', '-o4', tmp2_f], silence=True)

            shutil.move(tmp2_f, out_f)

    @staticmethod
    def convert_generic_anim(in_f, out_f, res_w=None, res_h=None, quality=None, fps=None, fps_in=None, duration_min=None, duration_max=None, **kwargs):
        # fps should not exceed original
        if fps:
            fps = min(fps, CodecInfo.get_file_fps(in_f))

        # For reducing duration of animation
        extraction_fps = None
        if (duration_min or duration_max) and not ('{0}' in in_f or '%d' in in_f or '%03d' in in_f):
            duration_orig = CodecInfo.get_file_duration(in_f)
            
            if duration_min and duration_min > 0 and duration_orig < duration_min:
                extraction_fps = duration_min / duration_orig * fps
            elif duration_max and duration_max > 0 and duration_orig > duration_max:
                extraction_fps = duration_max / duration_orig * fps
        
        if extraction_fps:
            if extraction_fps < 1:
                extraction_fps = f'1/{math.ceil(1 / extraction_fps)}'
            else:
                extraction_fps = math.ceil(extraction_fps)

            with tempfile.TemporaryDirectory() as tempdir:
                tmp_f = os.path.join(tempdir, 'tmp-{0}.png')
                StickerConvert.convert_generic_anim(in_f, tmp_f, fps=extraction_fps)
                StickerConvert.convert_generic_anim(tmp_f, out_f, res_w=res_w, res_h=res_h, quality=quality, fps_in=fps)

        elif shutil.which('ffmpeg'):
            # Faster
            StickerConvert.convert_generic_anim_pymodule(in_f, out_f, res_w=res_w, res_h=res_h, quality=quality, fps=fps, fps_in=fps_in)
        
        else:
            # Slower (a bit) but at least it works
            # e.g. MacOS compiled version in system without ffmpeg
            StickerConvert.convert_generic_anim_subprocess(in_f, out_f, res_w=res_w, res_h=res_h, quality=quality, fps=fps, fps_in=fps_in)

    @staticmethod
    def convert_generic_anim_pymodule(in_f, out_f, res_w=None, res_h=None, quality=None, fps=None, fps_in=None, **kwargs):
        if not quality:
            quality = 95

        in_f_ext = CodecInfo.get_file_ext(in_f)
        out_f_ext = CodecInfo.get_file_ext(out_f)

        if fps_in:
            # For converting multiple images into animation
            # fps_in is fps of the input sequence of images
            # Example in_f: path/to/dir/image-%03d.png
            stream = ffmpeg.input(in_f.replace('{0}', '%03d'), framerate=fps_in)
        elif in_f_ext == '.webm':
            codec = CodecInfo.get_file_codec(in_f)
            if codec == 'vp8':
                stream = ffmpeg.input(in_f, vcodec='vp8')
            else:
                stream = ffmpeg.input(in_f, vcodec='libvpx-vp9')
        else:
            stream = ffmpeg.input(in_f)

        if fps:
            stream = ffmpeg.filter(stream, 'fps', fps=fps, round='up')
        
        if res_w and res_h:
            width, height = CodecInfo.get_file_res(in_f)

            # Resolution must be even number, or else error occur
            res_w = res_w + res_w % 2
            res_h = res_h + res_h % 2

            if width > height:
                stream = ffmpeg.filter(stream, 'scale', res_w, -1, flags='neighbor', sws_dither='none')
            else:
                stream = ffmpeg.filter(stream, 'scale', -1, res_h, flags='neighbor', sws_dither='none')
            stream = ffmpeg.filter(stream, 'pad', res_w, res_h, '(ow-iw)/2', '(ow-ih)/2', color='black@0')
            stream = ffmpeg.filter(stream, 'setsar', 1)

        if (out_f_ext == '.apng' or out_f_ext == '.png') and not ('{0}' in out_f or '%d' in out_f or '%03d' in out_f):
            stream = ffmpeg.output(stream, out_f, vcodec='apng', pix_fmt='rgba', quality=95, plays=0)
        elif out_f_ext == '.webp':
            stream = ffmpeg.output(stream, out_f.replace('{0}', '%03d'), vcodec='webp', pix_fmt='yuva420p', quality=quality, lossless=0, loop=0)
        else:
            stream = ffmpeg.output(stream, out_f.replace('{0}', '%03d'), pix_fmt='yuva420p', quality=quality, lossless=0)
        ffmpeg.run(stream, overwrite_output=True, quiet=True)

    @staticmethod
    def convert_generic_anim_subprocess(in_f, out_f, res_w=None, res_h=None, quality=None, fps=None, fps_in=None, **kwargs):
        if not quality:
            quality = 95

        in_f_ext = CodecInfo.get_file_ext(in_f)
        out_f_ext = CodecInfo.get_file_ext(out_f)

        cmd_list = ['ffmpeg', '-y', '-hide_banner', '-logstep', 'error']
        # cmd_list = ['ffmpeg', '-y', '-hide_banner']

        if fps_in:
            # For converting multiple images into animation
            # fps_in is fps of the input sequence of images
            # Example in_f: path/to/dir/image-%03d.png
            cmd_list += ['-r', str(fps_in)]
            in_f = in_f.replace('{0}', '%03d')
        elif in_f_ext == '.webm':
            codec = CodecInfo.get_file_codec(in_f)
            if codec == 'vp8':
                cmd_list += ['-vcodec', 'vp8']
            else:
                cmd_list += ['-vcodec', 'libvpx-vp9']
        
        cmd_list += ['-i', in_f]

        if fps:
            cmd_list += ['-r', str(fps)]

        if res_w and res_h:
            width, height = CodecInfo.get_file_res(in_f)

            # Resolution must be even number, or else error occur
            res_w = res_w + res_w % 2
            res_h = res_h + res_h % 2

            if width > height:
                cmd_list += ['-vf', f'scale={res_w}:-1:flags=neighbor:sws_dither=none']
            else:
                cmd_list += ['-vf', f'scale=-1:{res_h}:flags=neighbor:sws_dither=none']

            cmd_list += ['-vf', f'pad={res_w}:{res_h}:(ow-iw)/2:(oh-ih)/2:color=black@0']
            cmd_list += ['-vf', f'setsar=1']

        if (out_f_ext == '.apng' or out_f_ext == '.png') and not ('{0}' in out_f or '%d' in out_f or '%03d' in out_f):
            cmd_list += ['-vcodec', 'apng', '-pix_fmt', 'rgba', '-quality', '95', '-plays', '0', out_f]
        elif out_f_ext == '.webp':
            cmd_list += ['-vcodec', 'webp', '-pix_fmt', 'yuva420p', '-quality', str(quality), '-lossless', '0', '-loop', '0', out_f.replace('{0}', '%03d')]
        else:
            cmd_list += ['-pix_fmt', 'yuva420p', '-quality', str(quality), '-lossless', '0', out_f.replace('{0}', '%03d')]

        # RunBin.run_cmd(cmd_list)
        RunBin.run_cmd(cmd_list, silence=False)

    @staticmethod
    def convert_from_webp_anim(in_f, out_f, res_w=None, res_h=None, quality=None, fps=None, color=None, duration_min=None, duration_max=None, fake_vid=False, **kwargs):
        with tempfile.TemporaryDirectory() as tempdir:
            # ffmpeg do not support webp decoding (yet)
            # Converting animated .webp to image of the frames or .webp directly can result in broken frames
            # .mp4 does not like odd number of width / height
            # Converting to .webm first is safe way of handling .webp

            tmp_f = os.path.join(tempdir, 'tmp.webm')
            StickerConvert.convert_generic_image(in_f, tmp_f, quality=quality)
            StickerConvert.convert(tmp_f, out_f, res_w=res_w, res_h=res_h, quality=quality, fps=fps, color=color, duration_min=duration_min, duration_max=duration_max, fake_vid=fake_vid)

    @staticmethod
    def convert_lottie(in_f, out_f, res_w=None, res_h=None, quality=None, fps=None, duration_min=None, duration_max=None, i_options={}, o_options={}, **kwargs):
        with tempfile.TemporaryDirectory() as tempdir:
            in_f_ext = CodecInfo.get_file_ext(in_f)
            out_f_ext = CodecInfo.get_file_ext(out_f)

            if out_f_ext in ('.tgs', '.lottie', '.json'):
                if in_f_ext not in vector_formats:
                    # o_options['bmp-mode'] = 'trace' # TODO: Use potrace?
                    o_options['bmp-mode'] = 'pixel'

                if in_f_ext not in lottie_in_ext_support:
                    tmp_f = os.path.join(tempdir, 'tmp.webp')
                    StickerConvert.convert_generic_anim(in_f, tmp_f)
                else:
                    tmp_f = in_f

                lottie_convert(tmp_f, out_f, width=res_w, height=res_h, fps=fps, i_options=i_options, o_options=o_options)
            else:
                if in_f_ext == '.tgs':
                    anim = LottieAnimation.from_tgs(in_f)
                else:
                    anim = LottieAnimation.from_file(in_f)

                tmp_f = os.path.join(tempdir, 'tmp.apng')
                anim.save_animation(tmp_f)

                StickerConvert.convert(tmp_f, out_f, res_w=res_w, res_h=res_h, quality=quality, fps=fps, duration_min=duration_min, duration_max=duration_max)
    
    @staticmethod
    def convert_to_apng_anim(in_f, out_f, res_w=None, res_h=None, quality=None, fps=None, color=None, duration_min=None, duration_max=None, **kwargs):
        # Heavily based on https://github.com/teynav/signalApngSticker/blob/main/scripts_linux/script_v3/core-hybrid

        # ffmpeg: Changing apng quality does not affect final size
        # magick: Will output single frame png

        with tempfile.TemporaryDirectory() as tempdir1, tempfile.TemporaryDirectory() as tempdir2:
            # Convert to uncompressed apng
            # https://stackoverflow.com/a/29378555
            tmp1_f = os.path.join(tempdir1, 'tmp1.apng')
            StickerConvert.convert_generic_anim(in_f, tmp1_f, res_w=res_w, res_h=res_h, quality=quality, fps=fps, duration_min=duration_min, duration_max=duration_max)

            # There is a possibility of fps being changed when animation is too long
            # Delay need to be recalculated, cannot rely on fps supplied
            delay = round(1000 / CodecInfo.get_file_fps(tmp1_f))

            # Get res_w and res_h if not supplied
            if not res_w:
                res_w, _ = CodecInfo.get_file_res(tmp1_f)
            if not res_h:
                _, res_h = CodecInfo.get_file_res(tmp1_f)

            # apngdis convert to png strip
            tmp2_f = os.path.join(tempdir1, 'tmp1_strip.png')
            RunBin.run_cmd(['apngdis', tmp1_f, '-S'])

            # pngnq-s9 optimization
            tmp3_f = os.path.join(tempdir1, 'tmp1_strip.1.png')
            if color and color <= 256:
                RunBin.run_cmd(['pngnq-s9', '-L', '-Qn', '-T15', '-n', str(color), '-e', '.1.png', tmp2_f])
            else:
                shutil.move(tmp2_f, tmp3_f)

            # pngquant optimization
            tmp4_f = os.path.join(tempdir1, 'tmp1_strip.1.2.png')
            if quality and quality < 100:
                RunBin.run_cmd(['pngquant', '--nofs', '--quality', f'0-{quality}', '--strip', '--ext', '.2.png', tmp3_f])
            else:
                shutil.move(tmp3_f, tmp4_f)

            # magick convert single png strip to png files
            # tmp5_f = os.path.join(tempdir2, 'tmp2-{0}.png')
            tmp5_f = os.path.join(tempdir2, 'tmp2-{0}.png')
            StickerConvert.magick_crop(tmp4_f, tmp5_f, res_w, res_h)
            
            # optipng and magick convert optimize png files
            for i in os.listdir(tempdir2):
                j = os.path.join(tempdir2, i)
                RunBin.run_cmd(['optipng', '-o4', j], silence=True)
                # https://www.imagemagick.org/script/command-line-options.php#quality
                # For png, lower quality actually means less compression and larger file size (zlib compression step = quality / 10)
                # For png, filter_type = quality % 10
                StickerConvert.convert_generic_image(j, j, res_w=res_w, res_h=res_h, quality=95)
            
            # apngasm create optimized apng
            RunBin.run_cmd(['apngasm', '-F', '-d', str(delay), '-o', out_f, f'{tempdir2}/*'])