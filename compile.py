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

UNIVERSAL_WHEEL_EXCEPTIONS = ["mini_racer"]


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


def copy_if_universal(wheel_name: Path, in_dir: Path, out_dir: Path) -> bool:
    if wheel_name.name.endswith("universal2.whl") or wheel_name.name.endswith(
        "any.whl"
    ):
        src_path = Path(in_dir, wheel_name.name)
        dst_path = Path(
            out_dir,
            wheel_name.name.replace("x86_64", "universal2").replace(
                "arm64", "universal2"
            ),
        )

        shutil.copy(src_path, dst_path)
        return True
    else:
        return False


def create_universal_wheels(in_dir1: Path, in_dir2: Path, out_dir: Path) -> None:
    for wheel_name_1 in in_dir1.iterdir():
        package = wheel_name_1.name.split("-")[0]
        if package in UNIVERSAL_WHEEL_EXCEPTIONS:
            src_path = Path(in_dir1, wheel_name_1.name)
            dst_path = Path(out_dir, wheel_name_1.name)
            shutil.copy(src_path, dst_path)
            continue
        wheel_name_2 = search_wheel_in_dir(package, in_dir2)
        if copy_if_universal(wheel_name_1, in_dir1, out_dir):
            continue
        if copy_if_universal(wheel_name_2, in_dir2, out_dir):
            continue

        wheel_path_1 = Path(in_dir1, wheel_name_1.name)
        wheel_path_2 = Path(in_dir2, wheel_name_2.name)
        subprocess.run(
            ["delocate-fuse", wheel_path_1, wheel_path_2, "-w", str(out_dir)]
        )
        print(f"Created universal wheel {wheel_path_1} {wheel_path_2}")

    for wheel_path in out_dir.iterdir():
        wheel_name_new = wheel_path.name.replace("x86_64", "universal2").replace(
            "arm64", "universal2"
        )

        src_path = Path(out_dir, wheel_path.name)
        dst_path = Path(out_dir, wheel_name_new)

        src_path.rename(dst_path)
        print(f"Renamed universal wheel {dst_path}")


def osx_install_universal2_dep(arch: str) -> None:
    shutil.rmtree("wheel_arm", ignore_errors=True)
    shutil.rmtree("wheel_x64", ignore_errors=True)
    shutil.rmtree("wheel_universal2", ignore_errors=True)

    Path("wheel_arm").mkdir()
    Path("wheel_x64").mkdir()
    Path("wheel_universal2").mkdir()

    osx_run_in_venv(
        "python -m pip download --require-virtualenv -r requirements.txt --platform macosx_11_0_arm64 --only-binary=:all: -d wheel_arm"
    )
    osx_run_in_venv(
        "python -m pip download --require-virtualenv -r requirements.txt --platform macosx_11_0_x86_64 --only-binary=:all: -d wheel_x64"
    )

    if arch == "arm64":
        w1 = "./wheel_arm"
        w2 = "./wheel_x64"
    else:
        w1 = "./wheel_x64"
        w2 = "./wheel_arm"

    create_universal_wheels(Path(w1), Path(w2), Path("wheel_universal2"))
    osx_run_in_venv("python -m pip install --require-virtualenv ./wheel_universal2/*")


def nuitka(python_bin: str, arch: Optional[str] = None) -> None:
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
    arch = os.getenv("SC_COMPILE_ARCH")
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
        if arch is None:
            osx_run_in_venv(
                "python -m pip install --require-virtualenv -r requirements.txt"
            )
        else:
            osx_install_universal2_dep(arch)

    nuitka(python_bin, arch)

    if platform.system() == "Windows":
        win_patch()
    elif platform.system() == "Darwin":
        osx_patch()


if __name__ == "__main__":
    compile()
