import os
from utils.run_bin import RunBin
from utils.codec_info import CodecInfo
from lottie.exporters.tgs_validator import TgsValidator, Severity
import unicodedata
import re

class FormatVerify:
    @staticmethod
    def check_file(file, res_min=None, res_max=None, square=None, fps_min=None, fps_max=None, size_min=None, size_max=None, animated=None, format=None):
        if CodecInfo.get_file_ext(file) == '.tgs':
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
        width, height = CodecInfo.get_file_res(file)

        if res_min != None and (height < res_min or width < res_min):
            return False
        if res_max != None and (height > res_max or width > res_max):
            return False
        if square != None and height != width:
            return False

        return True

    @staticmethod
    def check_file_fps(file, fps_min=None, fps_max=None):
        fps = CodecInfo.get_file_fps(file)

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
        if animated != None and CodecInfo.is_anim(file) != animated:
            return False
        
        return True
    
    @staticmethod
    def check_format(file, format=None):
        if format != None and CodecInfo.get_file_ext(file) != format:
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
