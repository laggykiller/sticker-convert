import os
import sys

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    if sys.platform == 'win32':
        magick_home = os.path.abspath('./magick')
        os.environ['MAGICK_HOME'] = magick_home
        os.environ["MAGICK_CODER_MODULE_PATH"] = magick_home + os.sep + "coders"
        os.environ["PATH"] += os.pathsep + magick_home + os.sep
    elif sys.platform == 'darwin':
        script_path = os.path.join(os.path.split(__file__)[0], '../')
        os.chdir(os.path.abspath(script_path))
        for i in os.listdir():
            if i.startswith('ImageMagick') and os.path.isdir(i):
                magick_home = os.path.abspath(i)
                break

        os.environ['MAGICK_HOME'] = magick_home
        os.environ["PATH"] += os.pathsep + magick_home + os.sep + "bin"
        os.environ["DYLD_LIBRARY_PATH"] = magick_home + os.sep + "lib"

from wand.image import Image
import ffmpeg
import subprocess
import tempfile
import shutil
from utils.lottie_convert import lottie_convert
from utils.format_verify import FormatVerify
import traceback

lottie_in_ext_support = ('.lottie', '.sif', '.svg', '.tnz', '.dotlottie', '.kra', '.bmp', '.py', '.tgs', '.png', '.apng', '.gif', '.tiff')
lottie_out_ext_support = ('.lottie', '.tgs', '.html', '.sif', '.svg', '.png', '.pdf', '.ps', '.gif', '.webp', '.tiff', '.dotlottie', '.video', '.webm', '.mp4', '.webm')

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
        in_f_ext = os.path.splitext(in_f)[-1].lower()
        out_f_ext = os.path.splitext(out_f)[-1].lower()

        if in_f_ext == '.tgs' or out_f_ext == '.tgs':
            return StickerConvert.convert_tgs

        else:
            if FormatVerify.is_anim(in_f):
                if in_f_ext == '.webp':
                    return StickerConvert.convert_from_webp_anim
                elif out_f_ext == '.png' or out_f_ext == '.apng':
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

                    tmp_f = os.path.join(tempdir, str(step_current) + os.path.splitext(out_f)[-1])
                    print(f'Compressing {in_f} -> {out_f} res={param[0]}, quality={param[1]}, fps={param[2]}, color={param[3]}')
                    convert_method(in_f, tmp_f, res=param[0], quality=param[1], fps=param[2], color=param[3])

                    if vid_size_max == None and img_size_max == None:
                        print('vid_size_max and/or img_size_max should be specified')
                        return True
                    
                    size = os.path.getsize(tmp_f)
                    if FormatVerify.is_anim(tmp_f):
                        size_max = vid_size_max
                    else:
                        size_max = img_size_max

                    if size < size_max:
                        if step_upper - step_lower > 1:
                            step_upper = step_current
                            step_current = int((step_lower + step_upper) / 2)
                            print(f'Compressed {in_f} -> {out_f} but size {size} is smaller than limit {size_max}, recompressing with higher quality (step {step_lower}-{step_current}-{step_upper})')
                        else:
                            shutil.move(os.path.join(tempdir, str(step_current) + os.path.splitext(out_f)[-1]), out_f)
                            print(f'Compressed {in_f} -> {out_f} successfully (step {step_current})')
                            return True
                    else:
                        if step_upper - step_lower > 1:
                            step_lower = step_current
                            step_current = round((step_lower + step_upper) / 2)
                            print(f'Compressed {in_f} -> {out_f} but size {size} is larger than limit {size_max}, recompressing with lower quality (step {step_lower}-{step_current}-{step_upper})')
                        else:
                            if step_current < steps:
                                shutil.move(os.path.join(tempdir, str(step_current + 1) + os.path.splitext(out_f)[-1]), out_f)
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
    #                 tmp_f = os.path.join(tempdir, 'temp' + os.path.splitext(out_f)[-1])
    #                 print(f'Compressing {in_f} -> {out_f} res={param[0]}, quality={param[1]}, fps={param[2]}, color={param[3]}')
    #                 convert_method(in_f, tmp_f, res=param[0], quality=param[1], fps=param[2], color=param[3])

    #                 if vid_size_max == None and img_size_max == None:
    #                     return True
                    
    #                 size = os.path.getsize(tmp_f)
    #                 if FormatVerify.is_anim(tmp_f):
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

        with Image(filename=in_f) as img:
            i = 0
            for h in range(0, img.height, res):
                for w in range(0, img.width, res):
                    w_end = w + res
                    h_end = h + res
                    with img[w:w_end, h:h_end] as chunk:
                        chunk.save(filename=out_f.format(str(i).zfill(3)))
                    i += 1

    @staticmethod
    def convert_generic_image(in_f, out_f, res=512, quality=90, **kwargs):
        with Image(filename=in_f) as img:
            if res != None:
                img.resize(width=res, height=res)
                img.background_color = 'none'
                img.gravity = 'center'
                img.extent(width=res, height=res)
            img.compression_quality = quality
            img.save(filename=out_f)

    @staticmethod
    def convert_generic_anim(in_f, out_f, res=512, quality=90, fps=30, fps_in=None, **kwargs):
        in_f_ext = os.path.splitext(in_f)[-1].lower()
        out_f_ext = os.path.splitext(out_f)[-1].lower()

        if fps_in:
            # For converting multiple images into animation
            # fps_in is fps of the input sequence of images
            # Example in_f: path/to/dir/image-%03d.png
            stream = ffmpeg.input(in_f, framerate=fps_in)
        elif in_f_ext == '.webm':
            stream = ffmpeg.input(in_f, vcodec='libvpx-vp9')
        else:
            stream = ffmpeg.input(in_f)
        if fps:
            stream = ffmpeg.filter(stream, 'fps', fps=fps, round='up')
        if res:
            # Resolution must be even number, or else error occur
            res = res + res % 2
            stream = ffmpeg.filter(stream, 'scale', res, -1, flags='neighbor', sws_dither='none')
            stream = ffmpeg.filter(stream, 'pad', res, res, '(ow-iw)/2', '(ow-ih)/2', color='black@0')
            stream = ffmpeg.filter(stream, 'setsar', 1)
        if out_f_ext == '.apng' or out_f_ext == '.png':
            stream = ffmpeg.output(stream, out_f, vcodec='apng', pix_fmt='rgba', quality=quality, plays=0)
        elif out_f_ext == '.webp':
            stream = ffmpeg.output(stream, out_f, vcodec='webp', pix_fmt='yuva420p', quality=quality, lossless=0, loop=0)
        else:
            stream = ffmpeg.output(stream, out_f, pix_fmt='yuva420p', quality=quality, lossless=0)
        ffmpeg.run(stream, overwrite_output=True, quiet=True)

        # os.system(f'ffmpeg -y -i {in_f} -r {fps} -vf "scale={res}:-1:flags=neighbor:sws_dither=none,pad={res}:{res}:(ow-iw)/2:(oh-ih)/2:color=black@0,setsar=1" -pix_fmt yuva420p -quality {quality} -lossless 0 -loop 0 {out_f}')

        # subprocess.Popen([os.path.abspath(shutil.which('ffmpeg')), '-y', '-i', in_f, '-r', str(fps), '-vf', f'scale={res}:-1:flags=neighbor:sws_dither=none,pad={res}:{res}:(ow-iw)/2:(oh-ih)/2:color=black@0,setsar=1', '-pix_fmt', 'yuva420p', '-quality', str(quality), '-lossless', '0', str(out_f)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    @staticmethod
    def convert_from_webp_anim(in_f, out_f, res=512, quality=90, fps=30, **kwargs):
        # ffmpeg do not support webp decoding (yet)
        # Converting animated .webp to image of the frames or .webp directly can result in broken frames
        # Converting to .mp4 first is safe way of handling .webp

        with tempfile.TemporaryDirectory() as tempdir:
            tmp_f = os.path.join(tempdir, 'temp.mp4')
        
            with Image(filename=in_f) as img:
                img.save(filename=tmp_f)
            
            StickerConvert.convert_generic_anim(tmp_f, out_f, res=res, quality=quality, fps=fps)

    @staticmethod
    def convert_tgs(in_f, out_f, res=512, quality=90, fps=30, **kwargs):
        in_f_ext = os.path.splitext(in_f)[-1].lower()
        out_f_ext = os.path.splitext(out_f)[-1].lower()

        with tempfile.TemporaryDirectory() as tempdir:
            if in_f_ext not in lottie_in_ext_support:
                tmp1_f = os.path.join(tempdir, 'tmp1.webp')
                StickerConvert.convert_generic_anim(in_f, tmp1_f, res=res, quality=quality, fps=fps)
            else:
                tmp1_f = in_f

            if out_f_ext not in lottie_out_ext_support:
                tmp2_f = os.path.join(tempdir, 'tmp2.mp4')
                lottie_convert(tmp1_f, tmp2_f)
                StickerConvert.convert(tmp2_f, out_f, res=res, quality=quality, fps=fps)
            else:
                lottie_convert(tmp1_f, out_f)
    
    @staticmethod
    def convert_to_apng_anim(in_f, out_f, res=512, quality=90, fps=30, color=90):
        # Heavily based on https://github.com/teynav/signalApngSticker/blob/main/scripts_linux/script_v3/core-hybrid

        # ffmpeg: Changing apng quality does not affect final size
        # magick: Will output single frame png

        with tempfile.TemporaryDirectory() as tempdir1, tempfile.TemporaryDirectory() as tempdir2:
            if os.path.splitext(in_f)[-1] == '.webp':
                tmp0_f = os.path.join(tempdir1, 'tmp0.mp4')
                StickerConvert.convert_from_webp_anim(in_f, tmp0_f, res=res, quality=quality, fps=fps)
            else:
                tmp0_f = in_f

            delay = round(1000 / fps)

            # Convert to uncompressed apng
            # https://stackoverflow.com/a/29378555
            tmp1_f = os.path.join(tempdir1, 'tmp1.apng')
            StickerConvert.convert_generic_anim(tmp0_f, tmp1_f, res=res, quality=100, fps=fps)

            # apngdis convert to png strip
            tmp2_f = os.path.join(tempdir1, 'tmp1_strip.png')
            subprocess.call([get_bin('apngdis'), tmp1_f, '-S'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

            # pngnq-s9 optimization
            tmp3_f = os.path.join(tempdir1, 'tmp1_strip.1.png')
            number_of_colors = color # 1-256 number of colors
            subprocess.call([get_bin('pngnq-s9'), '-L', '-Qn', '-T15', '-n', str(number_of_colors), '-e', '.1.png', tmp2_f], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

            # pngquant optimization
            tmp4_f = os.path.join(tempdir1, 'tmp1_strip.1.2.png')
            subprocess.call([get_bin('pngquant'), '--nofs', '--quality', f'0-{quality}', '--strip', '--ext', '.2.png', tmp3_f], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

            # magick convert single png strip to png files
            tmp5_f = os.path.join(tempdir2, 'tmp2-{0}.png')
            StickerConvert.magick_crop(tmp4_f, tmp5_f, res)
            
            # optipng and magick convert optimize png files
            for i in os.listdir(tempdir2):
                j = os.path.join(tempdir2, i)
                subprocess.call([os.path.abspath(shutil.which(('optipng'))), '-o4', j], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                # https://www.imagemagick.org/script/command-line-options.php#quality
                # For png, lower quality actually means less compression and larger file size (zlib compression level = quality / 10)
                # For png, filter_type = quality % 10
                StickerConvert.convert_generic_image(j, j, res=res, quality=95)
            
            # apngasm create optimized apng
            subprocess.call([get_bin('apngasm'), '-F', '-d', str(delay), '-o', out_f, f'{tempdir2}/*'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def get_bin(bin):
    if sys.platform == 'darwin' and getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        script_path = os.path.join(os.path.split(__file__)[0], '../')
        os.chdir(os.path.abspath(script_path))

    which_result = shutil.which(bin)
    if which_result != None:
        return os.path.abspath(which_result)
    elif bin in os.listdir():
        return os.path.abspath(f'./{bin}')
    elif bin in os.listdir('./bin'):
        return os.path.abspath(f'./bin/{bin}')
    else:
        print(f'Warning: Cannot find binary file {bin}')