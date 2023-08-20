#!/usr/bin/env python3
import os
import mimetypes

import imageio.v3 as iio
from rlottie_python import LottieAnimation
from PIL import Image
import mmap

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
        file_ext = CodecInfo.get_file_ext(file)

        if file_ext in '.tgs':
            with LottieAnimation.from_tgs(file) as anim:
                fps = anim.lottie_animation_get_framerate()
        else:
            if file_ext == '.webp':
                with open(file, 'r+b') as f:
                    mm = mmap.mmap(f.fileno(), 0)
                    anmf_pos = mm.find(b'ANMF')
                    if anmf_pos == -1:
                        return 1
                    mm.seek(anmf_pos+20)
                    frame_duration_32 = mm.read(4)
                    frame_duration = frame_duration_32[:-1] + bytes(int(frame_duration_32[-1]) & 0b11111100)
                    fps = 1000 / int.from_bytes(frame_duration, 'little')
            elif file_ext in ('.gif', '.apng', '.png'):
                metadata = iio.immeta(file, index=0, plugin='pillow', exclude_applied=False)
                fps = int(1000 / metadata.get('duration', 1000))
            else:
                metadata = iio.immeta(file, plugin='pyav', exclude_applied=False)
                fps = metadata.get('fps', 1)

        return fps
    
    @staticmethod
    def get_file_codec(file):
        file_ext = CodecInfo.get_file_ext(file)

        if file_ext == '.webp':
            plugin = 'pillow'
        else:
            plugin = 'pyav'
        metadata = iio.immeta(file, plugin=plugin, exclude_applied=False)
        codec = metadata.get('codec', None)

        return codec
    
    @staticmethod
    def get_file_res(file):
        file_ext = CodecInfo.get_file_ext(file)

        if file_ext == '.tgs':
            with LottieAnimation.from_tgs(file) as anim:
                width, height = anim.lottie_animation_get_size()
        else:
            if file_ext == '.webp':
                plugin = 'pillow'
            else:
                plugin = 'pyav'
            frame = iio.imread(file, plugin=plugin, index=0)
            width, height, _ = frame.shape
        
        return width, height
    
    @staticmethod
    def get_file_frames(file):
        file_ext = CodecInfo.get_file_ext(file)

        frames = None

        if file_ext == '.tgs':
            with LottieAnimation.from_tgs(file) as anim:
                frames = anim.lottie_animation_get_totalframe()
        else:
            if file_ext == '.webp':
                frames = Image.open(file).n_frames
            else:
                frames = len(iio.imread(file, plugin='pyav'))
        
        return frames
    
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