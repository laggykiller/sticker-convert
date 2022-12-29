import os
import shutil
from utils.run_bin import RunBin
# On Linux, old ImageMagick do not have magick command. In such case, use wand library
if RunBin.get_bin('magick', silent=True) == None:
    from wand.image import Image
import ffmpeg
import tempfile
from utils.lottie_convert import lottie_convert
from utils.codec_info import CodecInfo
import traceback
import gzip
import json

lottie_in_ext_support = ('.lottie', '.sif', '.svg', '.tnz', '.dotlottie', '.kra', '.bmp', '.py', '.tgs', '.png', '.apng', '.gif', '.tiff')
lottie_out_ext_support = ('.lottie', '.tgs', '.html', '.sif', '.svg', '.png', '.pdf', '.ps', '.gif', '.webp', '.tiff', '.dotlottie', '.video', '.webm', '.mp4')

class StickerConvert:
    @staticmethod
    def convert(in_f, out_f, res=512, quality=90, fps=30, color=90):
        '''
        Convert format with given res, quality, fps
        '''
        convert_method = StickerConvert.get_convert_method(in_f, out_f)

        convert_method(in_f, out_f, res=res, quality=quality, fps=fps, color=color)

    @staticmethod
    def convert_and_compress_to_size(in_f, out_f, vid_size_max=None, img_size_max=None, res_min=512, res_max=512, quality_max=90, quality_min=0, fps_max=30, fps_min=3, color_min=60, color_max=90, steps=20):
        '''
        Convert format with given res, quality, fps
        Try to reduce file size to below thresholds (vid_size_max and img_size_max) by adjusting res, quality, fps
        '''
        convert_method = StickerConvert.get_convert_method(in_f, out_f)
        
        return StickerConvert.compress_to_size(convert_method, in_f, out_f, vid_size_max=vid_size_max, img_size_max=img_size_max, res_min=res_min, res_max=res_max, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, color_min=color_min, color_max=color_max, steps=steps)

    @staticmethod
    def get_convert_method(in_f, out_f):
        in_f_ext = CodecInfo.get_file_ext(in_f)
        out_f_ext = CodecInfo.get_file_ext(out_f)

        if in_f_ext == '.tgs' or out_f_ext == '.tgs':
            return StickerConvert.convert_tgs

        else:
            if in_f_ext == '.webp':
                return StickerConvert.convert_from_webp_anim

            # webm should be handled by ffmpeg using vp9 codec
            # ImageMagick will remove transparency
            if CodecInfo.is_anim(in_f) or in_f_ext == '.webm':
                if out_f_ext == '.png' or out_f_ext == '.apng':
                    return StickerConvert.convert_to_apng_anim
                else:
                    return StickerConvert.convert_generic_anim
            else:
                return StickerConvert.convert_generic_image
    
    @staticmethod
    def compress_to_size(convert_method, in_f, out_f, vid_size_max=None, img_size_max=None, res_max=512, res_min=512, quality_max=90, quality_min=0, fps_max=30, fps_min=3, color_min=60, color_max=90, steps=20):
        def get_step_value(max, min, step, steps):
            return round((max - min) * step / steps + min)

        try:
            steps_list = []
            for step in range(steps, -1, -1):
                steps_list.append((
                    get_step_value(res_max, res_min, step, steps),
                    get_step_value(quality_max, quality_min, step, steps),
                    get_step_value(fps_max, fps_min, step, steps),
                    get_step_value(color_max, color_min, step, steps)
                ))

            with tempfile.TemporaryDirectory() as tempdir:
                step_lower = 0
                step_upper = steps
                step_current = round((step_lower + step_upper) / 2)
                while True:
                    param = steps_list[step_current]

                    tmp_f = os.path.join(tempdir, str(step_current) + CodecInfo.get_file_ext(out_f))
                    print(f'Compressing {in_f} -> {out_f} res={param[0]}, quality={param[1]}, fps={param[2]}, color={param[3]}')
                    convert_method(in_f, tmp_f, res=param[0], quality=param[1], fps=param[2], color=param[3])

                    if vid_size_max == None and img_size_max == None:
                        print('vid_size_max and/or img_size_max should be specified')
                        return True
                    
                    size = os.path.getsize(tmp_f)
                    if CodecInfo.is_anim(in_f):
                        size_max = vid_size_max
                    else:
                        size_max = img_size_max

                    if size < size_max:
                        if step_upper - step_lower > 1:
                            step_upper = step_current
                            step_current = int((step_lower + step_upper) / 2)
                            print(f'Compressed {in_f} -> {out_f} but size {size} is smaller than limit {size_max}, recompressing with higher quality (step {step_lower}-{step_current}-{step_upper})')
                        else:
                            shutil.move(os.path.join(tempdir, str(step_current) + CodecInfo.get_file_ext(out_f)), out_f)
                            print(f'Compressed {in_f} -> {out_f} successfully (step {step_current})')
                            return True
                    else:
                        if step_upper - step_lower > 1:
                            step_lower = step_current
                            step_current = round((step_lower + step_upper) / 2)
                            print(f'Compressed {in_f} -> {out_f} but size {size} is larger than limit {size_max}, recompressing with lower quality (step {step_lower}-{step_current}-{step_upper})')
                        else:
                            if step_current < steps:
                                shutil.move(os.path.join(tempdir, str(step_current + 1) + CodecInfo.get_file_ext(out_f)), out_f)
                                print(f'Compressed {in_f} -> {out_f} successfully (step {step_current})')
                                return True
                            else:
                                print(f'Compressing {in_f} -> {out_f} failed as size cannot get below limit {size_max} with lowest quality under current settings')
                                return False

        except Exception as e:
            tb = traceback.format_exc()
            print(e, tb)

    # @staticmethod
    # def compress_to_size(convert_method, in_f, out_f, vid_size_max=None, img_size_max=None, res_max=512, res_min=512, quality_max=90, quality_min=0, fps_max=30, fps_min=3, color_min=60, color_max=90, steps=20):
    #     def get_step_value(max, min, step, steps):
    #         return round((max - min) * step / steps + min)

    #     try:
    #         steps_list = []
    #         for step in range(steps, -1, -1):
    #             steps_list.append((
    #                 get_step_value(res_max, res_min, step, steps),
    #                 get_step_value(quality_max, quality_min, step, steps),
    #                 get_step_value(fps_max, fps_min, step, steps),
    #                 get_step_value(color_max, color_min, step, steps)
    #             ))
            
    #         for param in steps_list:
    #             with tempfile.TemporaryDirectory() as tempdir:
    #                 tmp_f = os.path.join(tempdir, 'temp' + CodecInfo.get_file_ext(out_f))
    #                 print(f'Compressing {in_f} -> {out_f} res={param[0]}, quality={param[1]}, fps={param[2]}, color={param[3]}')
    #                 convert_method(in_f, tmp_f, res=param[0], quality=param[1], fps=param[2], color=param[3])

    #                 if vid_size_max == None and img_size_max == None:
    #                     return True
                    
    #                 size = os.path.getsize(tmp_f)
    #                 if CodecInfo.is_anim(tmp_f):
    #                     size_max = vid_size_max
    #                 else:
    #                     size_max = img_size_max

    #                 if size < size_max:
    #                     shutil.move(tmp_f, out_f)
    #                     print(f'Compressed {in_f} -> {out_f} successfully with size {size} res={param[0]}, quality={param[1]}, fps={param[2]}, color={param[3]}')
    #                     return True
    #                 else:
    #                     print(f'Compressed {in_f} -> {out_f} but size {size} is larger than limit {size_max}, recompressing with lower quality')

    #         print(f'Compressing {in_f} -> {out_f} failed as size cannot get below limit {size_max} with lowest quality under current settings')
    #         return False
                    

    #     except Exception as e:
    #         tb = traceback.format_exc()
    #         print(e, tb)

    @staticmethod
    def magick_crop(in_f, out_f, res):
        # https://stackoverflow.com/a/28503615
        # out_f: tiles_{0}.jpg
        if RunBin.get_bin('magick', silent=True) == None:
            with Image(filename=in_f) as img:
                i = 0
                for h in range(0, img.height, res):
                    for w in range(0, img.width, res):
                        w_end = w + res
                        h_end = h + res
                        with img[w:w_end, h:h_end] as chunk:
                            chunk.save(filename=out_f.format(str(i).zfill(3)))
                        i += 1
        else:
            out_f = out_f.replace('{0}', '%03d')
            RunBin.run_cmd(['magick', in_f, '-crop', f'{res}x{res}', out_f])

    @staticmethod
    def convert_generic_image(in_f, out_f, res=None, quality=90, **kwargs):
        # https://www.imagemagick.org/script/command-line-options.php#quality
        # For png, lower quality actually means less compression and larger file size (zlib compression level = quality / 10)
        # For png, filter_type = quality % 10
        if CodecInfo.get_file_ext(out_f) == '.png':
            quality = 95

        if RunBin.get_bin('magick', silent=True) == None:
            with Image(filename=in_f) as img:
                if res != None:
                    img.resize(width=res, height=res)
                    img.background_color = 'none'
                    img.gravity = 'center'
                    img.extent(width=res, height=res)
                img.compression_quality = quality
                img.save(filename=out_f)
        else:
            if res != None:
                RunBin.run_cmd(['magick', in_f, '-resize', f'{res}x{res}', '-background', 'none', '-gravity', 'center', '-extent', f'{res}x{res}', '-quality', str(quality), out_f])
            else:
                RunBin.run_cmd(['magick', in_f, '-quality', str(quality), out_f])

    @staticmethod
    def convert_generic_anim(in_f, out_f, res=512, quality=90, fps=30, fps_in=None, **kwargs):
        if shutil.which('ffmpeg'):
            # Faster
            StickerConvert.convert_generic_anim_pymodule(in_f, out_f, res=res, quality=quality, fps=fps, fps_in=fps_in)
        else:
            # Slower (a bit) but at least it works
            # e.g. MacOS compiled version in system without ffmpeg
            StickerConvert.convert_generic_anim_subprocess(in_f, out_f, res=res, quality=quality, fps=fps, fps_in=fps_in)

    @staticmethod
    def convert_generic_anim_pymodule(in_f, out_f, res=512, quality=90, fps=30, fps_in=None, **kwargs):
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
        if res:
            width, height = CodecInfo.get_file_res(in_f)

            # Resolution must be even number, or else error occur
            # res = res + res % 2
            # https://trac.ffmpeg.org/wiki/Scaling says can use -2 instead
            if width > height:
                stream = ffmpeg.filter(stream, 'scale', res, -2, flags='neighbor', sws_dither='none')
            else:
                stream = ffmpeg.filter(stream, 'scale', -2, res, flags='neighbor', sws_dither='none')
            stream = ffmpeg.filter(stream, 'pad', res, res, '(ow-iw)/2', '(ow-ih)/2', color='black@0')
            stream = ffmpeg.filter(stream, 'setsar', 1)
        if out_f_ext == '.apng' or out_f_ext == '.png':
            stream = ffmpeg.output(stream, out_f, vcodec='apng', pix_fmt='rgba', quality=95, plays=0)
        elif out_f_ext == '.webp':
            stream = ffmpeg.output(stream, out_f, vcodec='webp', pix_fmt='yuva420p', quality=quality, lossless=0, loop=0)
        else:
            stream = ffmpeg.output(stream, out_f, pix_fmt='yuva420p', quality=quality, lossless=0)
        ffmpeg.run(stream, overwrite_output=True, quiet=True)

    @staticmethod
    def convert_generic_anim_subprocess(in_f, out_f, res=512, quality=90, fps=30, fps_in=None, **kwargs):
        in_f_ext = CodecInfo.get_file_ext(in_f)
        out_f_ext = CodecInfo.get_file_ext(out_f)

        # cmd_list = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error']
        cmd_list = ['ffmpeg', '-y', '-hide_banner']

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
        if res:
            width, height = CodecInfo.get_file_res(in_f)

            # Resolution must be even number, or else error occur
            # res = res + res % 2
            # https://trac.ffmpeg.org/wiki/Scaling says can use -2 instead
            if width > height:
                cmd_list += ['-vf', f'scale={res}:-2:flags=neighbor:sws_dither=none']
            else:
                cmd_list += ['-vf', f'scale=-2:{res}:flags=neighbor:sws_dither=none']

            cmd_list += ['-vf', f'pad={res}:{res}:(ow-iw)/2:(oh-ih)/2:color=black@0']
            cmd_list += ['-vf', f'setsar=1']

        if out_f_ext == '.apng' or out_f_ext == '.png':
            cmd_list += ['-vcodec', 'apng', '-pix_fmt', 'rgba', '-quality', '95', '-plays', '0', out_f]
        elif out_f_ext == '.webp':
            cmd_list += ['-vcodec', 'webp', '-pix_fmt', 'yuva420p', '-quality', str(quality), '-lossless', '0', '-loop', '0', out_f]
        else:
            cmd_list += ['-pix_fmt', 'yuva420p', '-quality', str(quality), '-lossless', '0', out_f]
        # RunBin.run_cmd(cmd_list)
        RunBin.run_cmd(cmd_list, silence=False)

    @staticmethod
    def convert_from_webp_anim(in_f, out_f, res=512, quality=90, fps=30, color=90, **kwargs):
        in_f_ext = CodecInfo.get_file_ext(in_f)
        out_f_ext = CodecInfo.get_file_ext(out_f)

        with tempfile.TemporaryDirectory() as tempdir:
            if CodecInfo.is_anim(in_f):
                # ffmpeg do not support webp decoding (yet)
                # Converting animated .webp to image of the frames or .webp directly can result in broken frames
                # .mp4 does not like odd number of width / height
                # Converting to .webm first is safe way of handling .webp

                tmp_f = os.path.join(tempdir, 'tmp.webm')
                StickerConvert.convert_generic_image(in_f, tmp_f, quality=quality)
                StickerConvert.convert(tmp_f, out_f, res=res, quality=quality, fps=fps)
            else:
                tmp_f = os.path.join(tempdir, f'tmp{out_f_ext}')
                StickerConvert.convert_generic_image(in_f, tmp_f, res=res, quality=quality)
                # Need more compression for .png
                if CodecInfo.get_file_ext(out_f) == '.png':
                    tmp1_f = os.path.join(tempdir, 'tmp.1.png')
                    RunBin.run_cmd(['pngnq-s9', '-L', '-Qn', '-T15', '-n', str(color), '-e', '.1.png', tmp_f])

                    tmp2_f = os.path.join(tempdir, 'tmp.1.2.png')
                    RunBin.run_cmd(['pngquant', '--nofs', '--quality', f'0-{quality}', '--strip', '--ext', '.2.png', tmp1_f])
                    
                    shutil.move(tmp2_f, out_f)
                else:
                    shutil.move(tmp_f, out_f)

    @staticmethod
    def convert_tgs(in_f, out_f, res=512, quality=90, fps=30, **kwargs):
        in_f_ext = CodecInfo.get_file_ext(in_f)
        out_f_ext = CodecInfo.get_file_ext(out_f)

        with tempfile.TemporaryDirectory() as tempdir1, tempfile.TemporaryDirectory() as tempdir2:
            if in_f_ext not in lottie_in_ext_support:
                tmp1_f = os.path.join(tempdir1, 'tmp1.webp')
                StickerConvert.convert_generic_anim(in_f, tmp1_f, res=res, quality=quality, fps=fps)
            else:
                tmp1_f = in_f

            # webm encoding with vp8 by lottie_convert not working, cause loss of transparency (tested on Windows)
            # webp fps is incorrect
            # Safest way is to convert to png files
            if out_f_ext not in lottie_out_ext_support:
                with gzip.open(in_f) as f:
                    file_json = json.loads(f.read().decode(encoding='utf-8'))
                fps_in = file_json['fr']
                frames_start = file_json['ip']
                frames_end = file_json['op']

                j = 1
                for i in range(frames_start, frames_end):
                    # https://stackoverflow.com/questions/41190107/using-ffmpeg-with-python3-subprocess-to-convert-multiple-pngs-to-a-video
                    tmp2_f_frame = os.path.join(tempdir2, f'tmp2-{str(j).zfill(3)}.png')
                    lottie_convert(tmp1_f, tmp2_f_frame, o_options={'frame': i})
                    j += 1
                
                tmp2_f = os.path.join(tempdir2, 'tmp2-{0}.png')

                StickerConvert.convert_generic_anim(tmp2_f, out_f, res=res, quality=quality, fps=fps, fps_in=fps_in)
            else:
                lottie_convert(tmp1_f, out_f, fps=fps)
    
    @staticmethod
    def convert_to_apng_anim(in_f, out_f, res=512, quality=90, fps=30, color=90):
        # Heavily based on https://github.com/teynav/signalApngSticker/blob/main/scripts_linux/script_v3/core-hybrid

        # ffmpeg: Changing apng quality does not affect final size
        # magick: Will output single frame png

        with tempfile.TemporaryDirectory() as tempdir1, tempfile.TemporaryDirectory() as tempdir2:
            delay = round(1000 / fps)

            # Convert to uncompressed apng
            # https://stackoverflow.com/a/29378555
            tmp1_f = os.path.join(tempdir1, 'tmp1.apng')
            StickerConvert.convert_generic_anim(in_f, tmp1_f, res=res, quality=100, fps=fps)

            # apngdis convert to png strip
            tmp2_f = os.path.join(tempdir1, 'tmp1_strip.png')
            RunBin.run_cmd(['apngdis', tmp1_f, '-S'])

            # pngnq-s9 optimization
            tmp3_f = os.path.join(tempdir1, 'tmp1_strip.1.png')
            RunBin.run_cmd(['pngnq-s9', '-L', '-Qn', '-T15', '-n', str(color), '-e', '.1.png', tmp2_f])

            # pngquant optimization
            tmp4_f = os.path.join(tempdir1, 'tmp1_strip.1.2.png')
            RunBin.run_cmd(['pngquant', '--nofs', '--quality', f'0-{quality}', '--strip', '--ext', '.2.png', tmp3_f])

            # magick convert single png strip to png files
            # tmp5_f = os.path.join(tempdir2, 'tmp2-{0}.png')
            tmp5_f = os.path.join(tempdir2, 'tmp2-{0}.png')
            StickerConvert.magick_crop(tmp4_f, tmp5_f, res)
            
            # optipng and magick convert optimize png files
            for i in os.listdir(tempdir2):
                j = os.path.join(tempdir2, i)
                RunBin.run_cmd(['optipng', '-o4', j], silence=True)
                # https://www.imagemagick.org/script/command-line-options.php#quality
                # For png, lower quality actually means less compression and larger file size (zlib compression level = quality / 10)
                # For png, filter_type = quality % 10
                StickerConvert.convert_generic_image(j, j, res=res, quality=95)
            
            # apngasm create optimized apng
            RunBin.run_cmd(['apngasm', '-F', '-d', str(delay), '-o', out_f, f'{tempdir2}/*'])