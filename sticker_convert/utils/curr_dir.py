#!/usr/bin/env python3
import subprocess
import os
import shutil
import sys
import tempfile

class CurrDir:
    @staticmethod
    def get_curr_dir():
        appimage_path = os.getenv('APPIMAGE')
        
        if appimage_path:
            return os.path.split(appimage_path)[0]
        elif sys.platform == 'darwin' and getattr(sys, 'frozen', False) and '.app/Contents/MacOS' in os.path.abspath(''):
            return os.path.abspath('../../../')
        else:
            return os.path.abspath('')
    
    @staticmethod
    def get_creds_dir():
        appimage_path = os.getenv('APPIMAGE')
        
        if appimage_path:
            return os.path.split(appimage_path)[0]
        else:
            return os.path.abspath('')