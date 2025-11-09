#!/usr/bin/env python3


def main() -> None:
    import multiprocessing
    import sys

    from sticker_convert.utils.translate import I

    multiprocessing.freeze_support()

    if len(sys.argv) == 1:
        print(I("Launching GUI..."))
        from sticker_convert.gui import GUI

        GUI().gui()
    else:
        from sticker_convert.cli import CLI

        CLI().cli()


if __name__ == "__main__":
    main()
