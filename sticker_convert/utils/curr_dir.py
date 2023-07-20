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
        
        if appimage_path == None:
            return os.path.abspath('')
        elif sys.platform == 'darwin' and getattr(sys, 'frozen', False):
            return os.path.abspath('../../')
        else:
            return os.path.split(appimage_path)[0]