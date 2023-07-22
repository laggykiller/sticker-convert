#!/usr/bin/env python3
import os
import sys

class CurrDir:
    @staticmethod
    def get_curr_dir():
        appimage_path = os.getenv('APPIMAGE')

        curr_dir = ''

        if sys.platform == 'darwin' and getattr(sys, 'frozen', False) and not os.getcwd().startswith('/Applications/') and '.app/Contents/MacOS' in os.getcwd():
            curr_dir = '../../../'
        elif appimage_path:
            curr_dir = os.path.split(appimage_path)[0]
        
        curr_dir = os.path.abspath(curr_dir)
        
        if os.access(curr_dir, os.W_OK):
            return curr_dir
        
        if os.path.isdir(os.path.expanduser('~/Desktop')):
            curr_dir = os.path.expanduser('~/Desktop')
        else:
            curr_dir = os.path.expanduser('~')
        
        return curr_dir
    
    @staticmethod
    def get_creds_dir():
        appimage_path = os.getenv('APPIMAGE')

        creds_dir = ''

        if sys.platform == 'darwin' and getattr(sys, 'frozen', False) and not os.getcwd().startswith('/Applications/') and '.app/Contents/MacOS' in os.getcwd():
            creds_dir = '../../../'
        elif appimage_path:
            creds_dir = os.path.split(appimage_path)[0]
        
        creds_dir = os.path.abspath(creds_dir)

        if os.access(creds_dir, os.W_OK):
            return creds_dir
        
        if sys.platform == 'win32':
            creds_dir = os.path.expandvars('%APPDATA%/sticker-convert')
        else:
            creds_dir = os.path.expanduser('~/.config/sticker-convert')
        
        os.makedirs(creds_dir, exist_ok=True)
        return creds_dir