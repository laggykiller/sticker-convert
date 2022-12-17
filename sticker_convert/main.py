#!/usr/bin/env python3
import multiprocessing
import sys
import os
import shutil

script_path = os.path.split(__file__)[0]
os.chdir(os.path.abspath(script_path))

if sys.platform == 'win32' and shutil.which('magick') == None:
    os.environ['MAGICK_HOME'] = os.path.abspath('./ImageMagick')
    os.environ["MAGICK_CODER_MODULE_PATH"] = os.path.abspath('./ImageMagick/coders')
    os.environ["PATH"] += os.pathsep + os.path.abspath('./ImageMagick')
elif sys.platform == 'darwin':
    if "DYLD_LIBRARY_PATH" in os.environ:
        os.environ["DYLD_LIBRARY_PATH"] += os.pathsep + os.path.abspath("./lib")
    else:
        os.environ["DYLD_LIBRARY_PATH"] = os.path.abspath("./lib")

    if shutil.which('magick') == None:
        os.environ['MAGICK_HOME'] = os.path.abspath('./ImageMagick')
        os.environ["PATH"] += os.pathsep + os.path.abspath("./ImageMagick/bin")
        os.environ["MAGICK_CODER_MODULE_PATH"] = os.path.abspath('./ImageMagick/lib/ImageMagick/modules-Q16HDRI/coders')
        os.environ["MAGICK_CONFIGURE_PATH"] = os.path.abspath('./ImageMagick/etc/ImageMagick-7')
        os.environ["DYLD_LIBRARY_PATH"] += os.pathsep + os.path.abspath("./ImageMagick/lib")

os.environ["PATH"] += os.pathsep + os.path.abspath('./bin') + os.sep

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