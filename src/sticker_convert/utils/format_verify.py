#!/usr/bin/env python3
import os
from .codec_info import CodecInfo
from lottie.exporters.tgs_validator import TgsValidator, Severity
import unicodedata
import re

'''
Example of spec
spec = {
    "res": {
        "w": {
            "min": 256,
            "max": 512
        },
        "h": {
            "min": 256,
            "max": 512
        }
    },
    "fps": {
        "min": 1,
        "max": 30
    },
    "size_max": {
        "vid": 500000,
        "img": 300000
    },
    "duration": {
        "min": 0,
        "max": 3
    },
    "animated": True,
    "square": True,
    "format": ".apng"
}
'''

class FormatVerify:
    @staticmethod
    def check_file(file, spec):
        if CodecInfo.get_file_ext(file) == '.tgs':
            validator = TgsValidator(Severity.Error)
            validator.check_file(file)
            return (not validator.errors and FormatVerify.check_file_size(file, size=spec.get('size_max')))
        else:
            return (
                FormatVerify.check_presence(file) and
                FormatVerify.check_file_res(file, res=spec.get('res'), square=spec.get('square')) and 
                FormatVerify.check_file_fps(file, fps=spec.get('fps')) and
                FormatVerify.check_file_size(file, size=spec.get('size_max')) and
                FormatVerify.check_animated(file, animated=spec.get('animated')) and
                FormatVerify.check_format(file, format=spec.get('format')) and 
                FormatVerify.check_duration(file, duration=spec.get('duration'))
                )

    @staticmethod
    def check_presence(file):
        return os.path.isfile(file)

    @staticmethod
    def check_file_res(file, res=None, square=None):
        file_width, file_height = CodecInfo.get_file_res(file)

        if res and (res.get('w', {}).get('min') and res.get('w', {}).get('max')) and (file_width < res['w']['min'] or file_width > res['w']['max']):
            return False
        if res and (res.get('h', {}).get('min') and res.get('h', {}).get('max')) and (file_height < res['h']['min'] or file_height > res['h']['max']):
            return False
        if square != None and file_height != file_width:
            return False

        return True

    @staticmethod
    def check_file_fps(file, fps):
        file_fps = CodecInfo.get_file_fps(file)

        if fps and fps.get('min') != None and file_fps < fps['min']:
            return False
        if fps and fps.get('max') != None and file_fps > fps['max']:
            return False

        return True
        
    @staticmethod
    def check_file_size(file, size=None):
        file_size = os.path.getsize(file)
        file_animated = CodecInfo.is_anim(file)

        if file_animated == True and size and size.get('vid') != None and file_size > size['vid']:
            return False
        if file_animated == False and size and size.get('img') != None and file_size > size['img']:
            return False
        
        return True
    
    @staticmethod
    def check_animated(file, animated=None):
        if animated != None and CodecInfo.is_anim(file) != animated:
            return False
        
        return True
    
    @staticmethod
    def check_format(file, format=None, allow_compat_ext=True):
        compat_ext = {
            '.jpg': '.jpeg',
            '.jpeg': '.jpg',
            '.png': '.apng',
            '.apng': '.png'
        }

        formats = []
        if format != None:
            if type(format) == dict:
                if FormatVerify.check_animated(file):
                    format = format.get('vid')
                else:
                    format = format.get('img')

            if type(format) == str:
                formats.append(format)
            elif (type(format) == tuple or type(format) == list):
                formats.extend(format)
            
            if allow_compat_ext:
                for fmt in formats.copy():
                    if fmt in compat_ext:
                        formats.append(compat_ext.get(fmt))
            if CodecInfo.get_file_ext(file) not in formats:
                return False
            
        return True
    
    @staticmethod
    def check_duration(file, duration=None):
        file_duration = CodecInfo.get_file_duration(file)
        if duration and duration.get('min') != None and file_duration < duration['min']:
            return False
        if duration and duration.get('max') != None and file_duration > duration['max']:
            return False
        
        return True
    
    @staticmethod
    def sanitize_filename(filename):
        # Based on https://gitlab.com/jplusplus/sanitize-filename/-/blob/master/sanitize_filename/sanitize_filename.py
        # Replace illegal character with '_'
        """Return a fairly safe version of the filename.

        We don't limit ourselves to ascii, because we want to keep municipality
        names, etc, but we do want to get rid of anything potentially harmful,
        and make sure we do not exceed Windows filename length limits.
        Hence a less safe blacklist, rather than a whitelist.
        """
        blacklist = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", "\0"]
        reserved = [
            "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
            "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
            "LPT6", "LPT7", "LPT8", "LPT9",
        ]  # Reserved words on Windows
        filename = "".join(c if c not in blacklist else '_' for c in filename)
        # Remove all charcters below code point 32
        filename = "".join(c if 31 < ord(c) else '_' for c in filename)
        filename = unicodedata.normalize("NFKD", filename)
        filename = filename.rstrip(". ")  # Windows does not allow these at end
        filename = filename.strip()
        if all([x == "." for x in filename]):
            filename = "__" + filename
        if filename in reserved:
            filename = "__" + filename
        if len(filename) == 0:
            filename = "__"
        if len(filename) > 255:
            parts = re.split(r"/|\\", filename)[-1].split(".")
            if len(parts) > 1:
                ext = "." + parts.pop()
                filename = filename[:-len(ext)]
            else:
                ext = ""
            if filename == "":
                filename = "__"
            if len(ext) > 254:
                ext = ext[254:]
            maxl = 255 - len(ext)
            filename = filename[:maxl]
            filename = filename + ext
            # Re-check last character (if there was no extension)
            filename = filename.rstrip(". ")
            if len(filename) == 0:
                filename = "__"
        return filename