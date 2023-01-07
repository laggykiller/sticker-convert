import os
from rlottie_python import LottieAnimation
import shutil
import mimetypes
import ffmpeg
from utils.run_bin import RunBin
# On Linux, old ImageMagick do not have magick command. In such case, use wand library
if RunBin.get_bin('magick', silent=True) == None:
    from wand.image import Image

class CodecInfo:
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
    def get_file_fps(file):
        file = CodecInfo.resolve_wildcard(file)
        if CodecInfo.get_file_ext(file) == '.tgs':
            with LottieAnimation.from_tgs(file) as anim:
                fps = anim.lottie_animation_get_framerate()

        elif shutil.which('ffmpeg'):
            tmp0_f_ffprobe = ffmpeg.probe(file)
            fps_str = tmp0_f_ffprobe['streams'][0]['r_frame_rate']
            fps_nom = int(fps_str.split('/')[0])
            fps_denom = int(fps_str.split('/')[1])
            fps = fps_nom / fps_denom
        else:
            int(RunBin.run_cmd(['ffprobe', '-v', '0', '-of', 'csv=p=0', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', file])).strip()

        return fps
    
    @staticmethod
    def get_file_codec(file):
        file = CodecInfo.resolve_wildcard(file)
        if shutil.which('ffmpeg'):
            probe_info = ffmpeg.probe(file)
            codec = probe_info['streams'][0]['codec_name']
        else:
            codec = RunBin.run_cmd(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=codec_name', '-of', 'default=noprint_wrappers=1:nokey=1', file]).strip()

        return codec
    
    @staticmethod
    def get_file_res(file):
        file = CodecInfo.resolve_wildcard(file)
        if CodecInfo.get_file_ext(file) == '.tgs':
            with LottieAnimation.from_tgs(file) as anim:
                width, height = anim.lottie_animation_get_size()
            return width, height

        try:
            if shutil.which('ffmpeg'):
                probe_info = ffmpeg.probe(file)
                width_ffprobe = probe_info['streams'][0]['width']
                height_ffprobe = probe_info['streams'][0]['height']
            else:
                res = RunBin.run_cmd(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=width,height', '-of', 'csv=p=0:s=x', file]).strip()
                width_ffprobe = int(res.split('x')[0])
                height_ffprobe = int(res.split('x')[1])
        except:
            width_ffprobe = 0
            height_ffprobe = 0

        try:
            file = str(file) + '[0]'
            if RunBin.get_bin('magick', silent=True) == None:
                with Image(filename=file) as img:
                    width_magick = img.width
                    height_magick = img.height
            else:
                res = RunBin.run_cmd(['magick', 'identify', '-ping', '-format', '%wx%h', file], silence=False)
                width_magick = int(res.split('x')[0])
                height_magick = int(res.split('x')[1])
        except:
            width_magick = 0
            height_magick = 0
        
        return max(width_ffprobe, width_magick), max(height_ffprobe, height_magick)
    
    @staticmethod
    def get_file_frames(file):
        file = CodecInfo.resolve_wildcard(file)
        file_ext = CodecInfo.get_file_ext(file)

        if file_ext == '.tgs':
            with LottieAnimation.from_tgs(file) as anim:
                frames = anim.lottie_animation_get_totalframe()
            return frames
        
        if RunBin.get_bin('ffprobe', silent=True):
            frames_ffprobe = RunBin.run_cmd(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames', '-show_entries', 'stream=nb_read_frames', '-print_format', 'default=nokey=1:noprint_wrappers=1', file], silence=False).strip()
            if frames_ffprobe.isnumeric():
                frames_ffprobe = int(frames_ffprobe)
            else:
                frames_ffprobe = 1
        else:
            frames_ffprobe = 1

        if RunBin.get_bin('magick', silent=True):
            frames_magick = RunBin.run_cmd(['magick', 'identify', file], silence=False).count('\n')
        else:
            with Image(filename=file) as img:
                frames_magick = img.iterator_length()
        
        return max(frames_ffprobe, frames_magick)
    
    @staticmethod
    def get_file_duration(file):
        # Return duration in miliseconds
        return CodecInfo.get_file_frames(file) / CodecInfo.get_file_fps(file) * 1000
    
    @staticmethod
    def get_file_ext(file):
        return os.path.splitext(file)[-1].lower()

    @staticmethod
    def is_anim(file):
        if CodecInfo.get_file_frames(file) > 1:
            return True
        else:
            return False
    
    @staticmethod
    def resolve_wildcard(file):
        if '{0}' in file or '%d' in file or '%03d' in file:
            dir = os.path.split(file)[0]
            file = os.path.join(dir, '000' + os.path.splitext(file)[-1])
            if not os.path.isfile(file):
                file = os.path.join(dir, '001' + os.path.splitext(file)[-1])
            if not os.path.isfile(file):
                file = os.path.join(dir, os.listdir(dir)[0])
        return file