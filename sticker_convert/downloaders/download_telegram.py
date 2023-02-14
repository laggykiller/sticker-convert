#!/usr/bin/env python3
import os
from contextlib import contextmanager
import shutil
import tempfile

from utils.metadata_handler import MetadataHandler

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
    def download_stickers_telegram(url, out_dir, opt_cred=None, cb_msg=print, cb_bar=None):
        token = opt_cred.get('telegram', {}).get('token')
        if token == None:
            cb_msg('Download failed: Token required for downloading from telegram')
            return False
    
        if 'telegram.me' not in url or 't.me' not in url:
            cb_msg('Download failed: Unrecognized URL format')
            return False

        bot= Bot(token)

        title = ""
        try:
            title = url.split("/addstickers/")[1]
        except IndexError:
            title = url.split("eu/stickers/")[1]
        
        sticker_set = bot.getStickerSet(title)

        if cb_bar:
            cb_bar(set_progress_mode='determinate', steps=len(sticker_set.stickers))

        emoji_dict = {}
        num = 0
        with tempfile.TemporaryDirectory() as tempdir:
            for i in sticker_set.stickers:
                with cwd(tempdir):
                    f_name_orig = i.get_file().download()
                f_path_orig = os.path.join(tempdir, f_name_orig)
                f_id = str(num).zfill(3)
                f_name = f_id + os.path.splitext(f_name_orig)[-1]
                f_path = os.path.join(out_dir, f_name)
                shutil.move(f_path_orig, f_path)
                emoji_dict[f_id] = i.emoji
                cb_msg(f'Downloaded {f_name}')
                if cb_bar:
                    cb_bar(update_bar=True)
                num += 1
        
        MetadataHandler.set_metadata(out_dir, title=title, emoji_dict=emoji_dict)

        return True