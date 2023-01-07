import os
from contextlib import contextmanager
import shutil
import tempfile

from utils.metadata_handler import MetadataHandler
from utils.exceptions import NoTokenException

from telegram import Bot

@contextmanager
def cwd(path):
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)

class DownloadTelegram:
    @staticmethod
    def download_stickers_telegram(url, token, out_dir):
        if token == None:
            raise NoTokenException('Token required for downloading from telegram')

        bot= Bot(token)

        title = ""
        try:
            title = url.split("/addstickers/")[1]
        except:
            title = url.split("eu/stickers/")[1]
        
        sticker_set = bot.getStickerSet(title)

        emoji_dict = {}
        num = 0
        with tempfile.TemporaryDirectory() as tempdir:
            for i in sticker_set.stickers:
                with cwd(tempdir):
                    f_name_orig = i.get_file().download()
                f_path_orig = os.path.join(tempdir, f_name_orig)
                f_name = str(num).zfill(3) + os.path.splitext(f_name_orig)[-1]
                f_path = os.path.join(out_dir, f_name)
                shutil.move(f_path_orig, f_path)
                emoji_dict[os.path.splitext(f_name)[0]] = i.emoji
                print('Downloaded', f_name)
                num += 1
        
        MetadataHandler.set_metadata(out_dir, title=title, emoji_dict=emoji_dict)

        return title