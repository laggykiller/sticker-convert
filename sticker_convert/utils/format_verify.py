import os
from utils.run_bin import RunBin
# On Linux, old ImageMagick do not have magick command. In such case, use wand library
if RunBin.get_bin('magick', silent=True) == None:
    from wand.image import Image
import ffmpeg
import mimetypes
from lottie.exporters.tgs_validator import TgsValidator, Severity

class FormatVerify:
    def __init__(self):
        mimetypes.init()
        vid_ext = []
        for ext in mimetypes.types_map:
            if mimetypes.types_map[ext].split('/')[0] == 'video':
                vid_ext.append(ext)
        vid_ext.append('.webm')
        vid_ext.append('.webp')
        self.vid_ext = tuple(vid_ext)

    @staticmethod
    def check_file(file, res_min=None, res_max=None, square=None, fps_min=None, fps_max=None, size_min=None, size_max=None, animated=None, format=None):
        if os.path.splitext(file)[-1].lower() == '.tgs':
            validator = TgsValidator(Severity.Error)
            validator.check_file(file)
            return (not validator.errors and FormatVerify.check_file_size(file, size_min=size_min, size_max=size_max))
        else:
            return (
                FormatVerify.check_presence(file) and
                FormatVerify.check_file_res(file, res_min=res_min, res_max=res_max, square=square) and 
                FormatVerify.check_file_fps(file, fps_min=fps_min, fps_max=fps_max) and
                FormatVerify.check_file_size(file, size_min=size_min, size_max=size_max) and
                FormatVerify.check_animated(file, animated=animated) and
                FormatVerify.check_format(file, format=format)
                )

    @staticmethod
    def check_presence(file):
        return os.path.isfile(file)

    @staticmethod
    def check_file_res(file, res_min=None, res_max=None, square=None):
        file = str(file) + '[0]'
        
        if RunBin.get_bin('magick', silent=True) == None:
            with Image(filename=file) as img:
                if res_min != None and (img.height < res_min or img.width < res_min):
                    return False
                if res_max != None and (img.height > res_max or img.width > res_max):
                    return False
                if square != None and img.height != img.width:
                    return False
        else:
            dimension = RunBin.run_cmd(['magick', 'identify', '-ping', '-format', '%wx%h', file], silence=False)
            width = int(dimension.split('x')[0])
            height = int(dimension.split('x')[1])

            if res_min != None and (height < res_min or width < res_min):
                return False
            if res_max != None and (height > res_max or width > res_max):
                return False
            if square != None and height != width:
                return False

        return True

    @staticmethod
    def check_file_fps(file, fps_min=None, fps_max=None):
        tmp0_f_ffprobe = ffmpeg.probe(file)
        fps_str = tmp0_f_ffprobe['streams'][0]['r_frame_rate']
        fps_nom = int(fps_str.split('/')[0])
        fps_denom = int(fps_str.split('/')[1])
        fps = fps_nom / fps_denom

        if fps_min != None and fps < fps_min:
            return False
        if fps_max != None and fps > fps_max:
            return False

        return True
    
    @staticmethod
    def check_file_size(file, size_min=None, size_max=None):
        size = os.path.getsize(file)

        if size_min != None and size < size_min:
            return False
        if size_max != None and size > size_max:
            return False
        
        return True
    
    @staticmethod
    def check_animated(file, animated=None):
        if animated != None and FormatVerify.is_anim(file) != animated:
            return False
        
        return True
    
    @staticmethod
    def check_format(file, format=None):
        if format != None and os.path.splitext(file)[-1].lower() != format:
            return False
        
        return True
    
    @staticmethod
    def is_anim(file):
        file_ext = os.path.splitext(file)[-1].lower()

        if file_ext == '.tgs':
            return True

        else:
            if os.path.isfile(file):
                if file_ext in ('.apng', '.png'):
                    file_f_ffprobe = ffmpeg.probe(file)
                    video_info = next(s for s in file_f_ffprobe['streams'] if s['codec_type'] == 'video')
                    if video_info['codec_name'] == 'apng':
                        return True
                    else:
                        return False
                if file_ext not in  ('.webp', '.webm'):
                    try:
                        file_f_ffprobe = ffmpeg.probe(file)
                        codec_type = file_f_ffprobe['streams'][0]['codec_type']
                        if codec_type == 'video':
                            return True
                    except ffmpeg.Error:
                        pass
                
                if RunBin.get_bin('magick', silent=True) == None:
                    with Image(filename=file) as img:
                        frames = img.iterator_length()
                else:
                    frames = RunBin.run_cmd(['magick', 'identify', file], silence=False).count('\n')
                
                if frames > 1:
                    return True

            else:
                if file_ext in FormatVerify().vid_ext:
                    return True

            return False