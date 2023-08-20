#!/usr/bin/env python3
'''sticker-convert'''
__version__ = '2.0.0'

def main():
    import multiprocessing
    import sys
    import os

    multiprocessing.freeze_support()
    script_path = os.path.split(__file__)[0]
    os.chdir(os.path.abspath(script_path))
    if len(sys.argv) == 1:
        print('Launching GUI...')
        from .gui import GUI
        GUI().root.mainloop()
    else:
        from .cli import CLI
        CLI().cli()