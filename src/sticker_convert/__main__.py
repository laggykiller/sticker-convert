#!/usr/bin/env python3


def main() -> None:
    import multiprocessing
    import sys

    from sticker_convert.version import __version__

    multiprocessing.freeze_support()
    print(f"sticker-convert {__version__}")
    print("Free and Opensource software by laggykiller")
    print("https://github.com/laggykiller/sticker-convert")
    print()
    if len(sys.argv) == 1:
        print("Launching GUI...")
        from sticker_convert.gui import GUI

        GUI().gui()
    else:
        from sticker_convert.cli import CLI

        CLI().cli()


if __name__ == "__main__":
    main()
