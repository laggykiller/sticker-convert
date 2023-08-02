#!/usr/bin/env python3
import os
from contextlib import contextmanager
import shutil

from utils.metadata_handler import MetadataHandler
from utils.cache_store import CacheStore

import anyio
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
    async def download_stickers_telegram_async(url, out_dir, opt_cred=None, cb_msg=print, cb_msg_block=input, cb_bar=None):
        token = opt_cred.get('telegram', {}).get('token')
        if token == None:
            cb_msg('Download failed: Token required for downloading from telegram')
            return False
    
        if not ('telegram.me' in url or 't.me' in url):
            cb_msg('Download failed: Unrecognized URL format')
            return False

        bot= Bot(token)

        title = ""
        try:
            title = url.split("/addstickers/")[1]
        except IndexError:
            title = url.split("eu/stickers/")[1]
        
        sticker_set = await bot.get_sticker_set(title, read_timeout=30, write_timeout=30, connect_timeout=30, pool_timeout=30)

        if cb_bar:
            cb_bar(set_progress_mode='determinate', steps=len(sticker_set.stickers))

        emoji_dict = {}
        num = 0
        with CacheStore.get_cache_store() as tempdir:
            for i in sticker_set.stickers:
                with cwd(tempdir):
                    f_name_orig = await i.get_file(read_timeout=30, write_timeout=30, connect_timeout=30, pool_timeout=30)
                    await f_name_orig.download_to_drive(read_timeout=30, write_timeout=30, connect_timeout=30, pool_timeout=30)
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

    @staticmethod
    def download_stickers_telegram(url, out_dir, opt_cred=None, cb_msg=print, cb_msg_block=input, cb_bar=None):
        return anyio.run(DownloadTelegram.download_stickers_telegram_async, url, out_dir, opt_cred, cb_msg, cb_msg_block, cb_bar)