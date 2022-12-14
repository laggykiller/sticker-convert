#!/usr/bin/env python3
import multiprocessing
import sys
import os
import shutil

script_path = os.path.split(__file__)[0]
os.chdir(os.path.abspath(script_path))

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS') or shutil.which('magick') == None:
    if sys.platform == 'win32':
        magick_home = os.path.abspath('./ImageMagick')
        os.environ['MAGICK_HOME'] = magick_home
        os.environ["MAGICK_CODER_MODULE_PATH"] = magick_home + os.sep + "coders"
        os.environ["PATH"] += os.pathsep + magick_home + os.sep
    elif sys.platform == 'darwin':
        magick_home = os.path.abspath('./ImageMagick')
        os.environ['MAGICK_HOME'] = magick_home
        os.environ["PATH"] += os.pathsep + magick_home + os.sep + "bin"
        os.environ["DYLD_LIBRARY_PATH"] = magick_home + os.sep + "lib"

from gui import GUI
from cli import CLI

def main():
    if len(sys.argv) == 1:
        print('Launching GUI...')
        with GUI() as w:
            w.root.mainloop()
    else:
        CLI().cli()

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()