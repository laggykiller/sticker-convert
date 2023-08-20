#!/usr/bin/env python3
def main():
    import multiprocessing
    import sys
    import os

    multiprocessing.freeze_support()
    script_path = os.path.split(__file__)[0]
    os.chdir(os.path.abspath(script_path))
    if len(sys.argv) == 1:
        print('Launching GUI...')
        from sticker_convert.gui import GUI
        GUI().root.mainloop()
    else:
        from sticker_convert.cli import CLI
        CLI().cli()

if __name__ == '__main__':
    main()