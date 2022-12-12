from telegram import Bot
import os
from contextlib import contextmanager
from utils.metadata_handler import MetadataHandler
from utils.exceptions import NoTokenException

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
        for i in sticker_set.stickers:
            with cwd(out_dir):
                f_name = i.get_file().download()
            emoji_dict[os.path.splitext(f_name)[0]] = i.emoji
            print('Downloaded', f_name)
        
        MetadataHandler.set_metadata(out_dir, title=title, emoji_dict=emoji_dict)

        return title