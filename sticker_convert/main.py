#!/usr/bin/env python3
import multiprocessing
import sys
import os
from gui import GUI
from cli import CLI

if sys.platform == 'darwin' and getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    script_path = os.path.join(os.path.split(__file__)[0], '../')
else:
    script_path = os.path.split(__file__)[0]
os.chdir(os.path.abspath(script_path))

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