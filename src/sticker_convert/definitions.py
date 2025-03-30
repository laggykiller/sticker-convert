#!/usr/bin/env python3
import os
import platform
import sys
from pathlib import Path


def get_root_dir() -> Path:
    i = 0
    file_path = Path(__file__).resolve()
    while True:
        root_dir = file_path.parents[i]
        if root_dir.is_dir():
            return root_dir
        i += 1


# Directory that can read program resources
ROOT_DIR = get_root_dir()


def get_root_dir_exe() -> Path:
    if appimage_path := os.getenv("APPIMAGE"):
        return Path(appimage_path).parent

    if (
        platform.system() == "Darwin"
        and getattr(sys, "frozen", False)
        and ".app/Contents/MacOS" in ROOT_DIR.as_posix()
    ):
        return (ROOT_DIR / "../../../").resolve()

    return ROOT_DIR


# Directory that contains .exe/.app/.appimage
ROOT_DIR_EXE = get_root_dir_exe()


def check_root_dir_exe_writable() -> bool:
    if (
        not os.access(ROOT_DIR_EXE.parent, os.W_OK)
        or Path("/usr/bin/") in ROOT_DIR_EXE.parents
        or Path("/bin") in ROOT_DIR_EXE.parents
        or Path("/usr/local/bin") in ROOT_DIR_EXE.parents
        or Path("C:/Program Files") in ROOT_DIR_EXE.parents
        or Path("/Applications/") in ROOT_DIR_EXE.parents
        or "site-packages" in ROOT_DIR_EXE.as_posix()
    ):
        return False
    return True


ROOT_DIR_EXE_WRITABLE = check_root_dir_exe_writable()


def get_default_dir() -> Path:
    if ROOT_DIR_EXE_WRITABLE:
        return ROOT_DIR_EXE
    home_dir = Path.home()
    desktop_dir = home_dir / "Desktop"
    if desktop_dir.is_dir():
        return desktop_dir
    return home_dir


# Default directory for stickers_input and stickers_output
DEFAULT_DIR = get_default_dir()


def get_config_dir() -> Path:
    if platform.system() == "Windows":
        fallback_dir = Path(os.path.expandvars("%APPDATA%\\sticker-convert"))
    else:
        fallback_dir = Path.home() / ".config/sticker-convert"

    if ROOT_DIR_EXE_WRITABLE:
        return ROOT_DIR_EXE
    os.makedirs(fallback_dir, exist_ok=True)
    return fallback_dir


# Directory for saving configs
CONFIG_DIR = get_config_dir()

# When importing SVG, import at this fps
SVG_SAMPLE_FPS = 30

# If width and height not set in SVG tag, import at this dimension
SVG_DEFAULT_WIDTH = 1024
SVG_DEFAULT_HEIGHT = 1024
