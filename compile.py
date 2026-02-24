#!/usr/bin/env python3
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

sys.path.append("./src")
from sticker_convert import __version__


def nuitka(python_bin: str, arch: Optional[str] = None) -> None:
    cmd_list = [
        python_bin,
        "-m",
        "nuitka",
        "--standalone",
        "--follow-imports",
        "--assume-yes-for-downloads",
        "--include-package=socksio",
        "--include-data-files=src/sticker_convert/ios-message-stickers-template.zip=ios-message-stickers-template.zip",
        "--include-data-dir=src/sticker_convert/resources=resources",
        "--include-data-dir=src/sticker_convert/locales=locales",
        "--enable-plugin=tk-inter",
        "--include-package-data=signalstickers_client",
        "--noinclude-data-file=tcl/opt0.4",
        "--noinclude-data-file=tcl/http1.0",
        "--product-name=sticker-convert",
        "--company-name=laggykiller",
        f"--product-version={__version__}",
        f"--file-version={__version__}",
        "--copyright=GPL-2.0",
    ]

    if platform.system() == "Windows":
        cmd_list.append(
            "--windows-icon-from-ico=src/sticker_convert/resources/appicon.ico"
        )
        cmd_list.append("--mingw64")
    elif platform.system() == "Darwin":
        cmd_list.append("--disable-console")
        cmd_list.append("--macos-create-app-bundle")
        cmd_list.append("--macos-app-icon=src/sticker_convert/resources/appicon.icns")
        if arch is not None:
            cmd_list.append(f"--macos-target-arch={arch}")
        cmd_list.append(f"--macos-app-version={__version__}")
    else:
        cmd_list.append("--linux-icon=src/sticker_convert/resources/appicon.png")

    cmd_list.append("src/sticker-convert.py")
    subprocess.run(cmd_list)


def win_patch() -> None:
    for i in Path("sticker-convert.dist/av.libs").iterdir():
        file_path = Path("sticker-convert.dist", i.name)
        if file_path.is_file():
            os.remove(file_path)


def osx_patch() -> None:
    # https://github.com/pyinstaller/pyinstaller/issues/5154#issuecomment-1567603461
    sticker_bin = Path("sticker-convert.app/Contents/MacOS/sticker-convert")
    sticker_bin_cli = Path("sticker-convert.app/Contents/MacOS/sticker-convert-cli")
    sticker_bin.rename(sticker_bin_cli)
    with open(sticker_bin, "w+") as f:
        f.write("#!/bin/bash\n")
        f.write('cd "$(dirname "$0")"\n')
        f.write("open ./sticker-convert-cli")
    os.chmod(sticker_bin, 0o744)

    subprocess.run(["codesign", "--force", "--deep", "-s", "-", "sticker-convert.app"])


def compile() -> None:
    arch = os.getenv("SC_COMPILE_ARCH")
    python_bin = str(Path(sys.executable).resolve())

    ios_stickers_path = "src/sticker_convert/ios-message-stickers-template"
    ios_stickers_zip = ios_stickers_path + ".zip"
    if Path(ios_stickers_zip).exists():
        os.remove(ios_stickers_zip)
    shutil.make_archive(ios_stickers_path, "zip", ios_stickers_path)

    shutil.rmtree("venv", ignore_errors=True)
    subprocess.run([python_bin, "-m", "venv", "venv"])
    if platform.system() == "Windows":
        python_bin = os.path.abspath("venv/Scripts/python.exe")
    else:
        python_bin = os.path.abspath("venv/bin/python")

    subprocess.run(
        [python_bin, "-m", "pip", "install", "--prefer-binary", ".[build]"]
    )

    nuitka(python_bin, arch)

    if platform.system() == "Windows":
        win_patch()
    elif platform.system() == "Darwin":
        osx_patch()


if __name__ == "__main__":
    compile()
