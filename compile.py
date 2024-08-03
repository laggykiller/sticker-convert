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


def osx_run_in_venv(cmd: str, get_stdout: bool = False) -> Optional[str]:
    if Path("/bin/zsh").is_file():
        sh_cmd = ["/bin/zsh", "-c"]
    else:
        sh_cmd = ["/bin/bash", "-c"]
    venv_cmd = "source venv/bin/activate && "

    if get_stdout:
        return subprocess.run(
            sh_cmd + [venv_cmd + cmd], stdout=subprocess.PIPE
        ).stdout.decode()
    else:
        subprocess.run(sh_cmd + [venv_cmd + cmd])

    return None


def search_wheel_in_dir(package: str, dir: Path) -> Path:
    for i in dir.iterdir():
        if i.name.startswith(package):
            return i

    raise RuntimeError(f"Cannot find wheel for {package}")


def nuitka(python_bin: str) -> None:
    cmd_list = [
        python_bin,
        "-m",
        "nuitka",
        "--standalone",
        "--follow-imports",
        "--assume-yes-for-downloads",
        "--include-data-files=src/sticker_convert/ios-message-stickers-template.zip=ios-message-stickers-template.zip",
        "--include-data-dir=src/sticker_convert/resources=resources",
        "--enable-plugin=tk-inter",
        "--enable-plugin=multiprocessing",
        "--include-package-data=signalstickers_client",
        "--noinclude-data-file=tcl/opt0.4",
        "--noinclude-data-file=tcl/http1.0",
        "--user-package-configuration-file=nuitka.config.yml",
    ]

    if platform.system() == "Windows":
        cmd_list.append(
            "--windows-icon-from-ico=src/sticker_convert/resources/appicon.ico"
        )
    elif platform.system() == "Darwin":
        cmd_list.append("--disable-console")
        cmd_list.append("--macos-create-app-bundle")
        cmd_list.append("--macos-app-icon=src/sticker_convert/resources/appicon.icns")
        cmd_list.append(f"--macos-app-version={__version__}")
    else:
        cmd_list.append("--linux-icon=src/sticker_convert/resources/appicon.png")

    cmd_list.append("src/sticker-convert.py")
    if platform.system() == "Darwin":
        osx_run_in_venv(" ".join(cmd_list))
    else:
        subprocess.run(cmd_list, shell=True)


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

    osx_run_in_venv("codesign --force --deep -s - sticker-convert.app")


def compile() -> None:
    python_bin = str(Path(sys.executable).resolve())

    ios_stickers_path = "src/sticker_convert/ios-message-stickers-template"
    ios_stickers_zip = ios_stickers_path + ".zip"
    if Path(ios_stickers_zip).exists():
        os.remove(ios_stickers_zip)
    shutil.make_archive(ios_stickers_path, "zip", ios_stickers_path)

    if platform.system() == "Windows":
        subprocess.run(
            f"{python_bin} -m pip install --upgrade pip".split(" "), shell=True
        )
        subprocess.run(
            f"{python_bin} -m pip install -r requirements-build.txt".split(" "),
            shell=True,
        )
        subprocess.run(
            f"{python_bin} -m pip install -r requirements.txt".split(" "), shell=True
        )
    elif platform.system() == "Darwin":
        shutil.rmtree("venv", ignore_errors=True)
        subprocess.run(f"{python_bin} -m pip install --upgrade pip delocate".split(" "))
        subprocess.run(f"{python_bin} -m venv venv".split(" "))
        python_bin = "python"
        osx_run_in_venv("python -m pip install -r requirements-build.txt")
        osx_run_in_venv(
            "python -m pip install --require-virtualenv -r requirements.txt"
        )

    nuitka(python_bin)

    if platform.system() == "Windows":
        win_patch()
    elif platform.system() == "Darwin":
        osx_patch()


if __name__ == "__main__":
    compile()
