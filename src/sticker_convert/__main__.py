#!/usr/bin/env python3
def main():
    import multiprocessing
    import sys
    import os
    from .__init__ import __version__

    multiprocessing.freeze_support()
    print(f"sticker-convert {__version__}")
    script_path = os.path.dirname(__file__)
    if not os.path.isdir(script_path):
        script_path = os.path.dirname(sys.argv[0])
    os.chdir(script_path)
    if len(sys.argv) == 1:
        print("Launching GUI...")
        from sticker_convert.gui import GUI  # type: ignore

        GUI().gui()
    else:
        from sticker_convert.cli import CLI

        CLI().cli()


if __name__ == "__main__":
    main()
