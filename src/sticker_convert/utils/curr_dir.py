#!/usr/bin/env python3
import os
import sys

class CurrDir:
    @staticmethod
    def get_curr_dir():
        appimage_path = os.getenv('APPIMAGE')

        cwd = os.getcwd()
        home_dir = os.path.expanduser('~')
        if os.path.isdir(os.path.join(home_dir, 'Desktop')):
            fallback_dir = os.path.join(home_dir, 'Desktop')
        else:
            fallback_dir = home_dir

        if sys.platform == 'darwin' and getattr(sys, 'frozen', False) and '.app/Contents/MacOS' in cwd:
            if cwd.startswith('/Applications/'):
                curr_dir = fallback_dir
            else:
                curr_dir = os.path.abspath('../../../')
        elif appimage_path:
            curr_dir = os.path.split(appimage_path)[0]
        elif (cwd.startswith('/usr/bin/') 
              or cwd.startswith('/bin') 
              or cwd.startswith('/usr/local/bin')
              or cwd.startswith('C:\\Program Files')
              or 'site-packages' in __file__):
            curr_dir = fallback_dir
        else:
            curr_dir = cwd
        
        if os.access(curr_dir, os.W_OK):
            return curr_dir
        else:
            return fallback_dir
    
    @staticmethod
    def get_creds_dir():
        appimage_path = os.getenv('APPIMAGE')

        cwd = os.getcwd()
        if sys.platform == 'win32':
            fallback_dir = os.path.expandvars('%APPDATA%\\sticker-convert')
        else:
            fallback_dir = os.path.expanduser('~/.config/sticker-convert')

        if sys.platform == 'darwin' and getattr(sys, 'frozen', False) and '.app/Contents/MacOS' in cwd:
            if cwd.startswith('/Applications/'):
                creds_dir = fallback_dir
            else:
                creds_dir = os.path.abspath('../../../')
        elif appimage_path:
            creds_dir = os.path.split(appimage_path)[0]
        elif (cwd.startswith('/usr/bin/') 
              or cwd.startswith('/bin') 
              or cwd.startswith('/usr/local/bin')
              or cwd.startswith('C:\\Program Files')
              or 'site-packages' in __file__):
            creds_dir = fallback_dir
        else:
            creds_dir = cwd
        
        os.makedirs(creds_dir, exist_ok=True)
        if os.access(creds_dir, os.W_OK):
            return creds_dir
        else:
            os.makedirs(fallback_dir, exist_ok=True)
            return fallback_dir