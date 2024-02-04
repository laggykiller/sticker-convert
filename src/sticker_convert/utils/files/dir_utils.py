#!/usr/bin/env python3
import os
import sys
import platform
from pathlib import Path
from typing import Optional

def _get_curr_dir_if_writable() -> Optional[Path]:
    appimage_path = os.getenv("APPIMAGE")
    try:
        curr_dir = Path(__compiled__.containing_dir)
    except NameError:
        # curr_dir = os.path.dirname(__file__)
        program = Path(sys.argv[0]).resolve()
        if program.name == "sticker-convert.py":
            curr_dir = program.parent / "sticker_convert"
        
        if not curr_dir.is_dir():
            curr_dir = Path(__file__).resolve().parent
            curr_dir = (curr_dir / "../../").resolve()

    if (
        "/usr/bin/" in curr_dir.parents
        or "/bin" in curr_dir.parents
        or "/usr/local/bin" in curr_dir.parents
        or "C:\\Program Files" in curr_dir.parents
        or "site-packages" in __file__
    ):
        return None

    if (
        platform.system() == "Darwin"
        and getattr(sys, "frozen", False)
        and ".app/Contents/MacOS" in curr_dir
    ):
        if "/Applications/" in curr_dir.parents:
            return None
        else:
            curr_dir = (curr_dir / "../../../").resolve()

    if appimage_path:
        curr_dir = Path(appimage_path).parent

    if not os.access(curr_dir, os.W_OK):
        return None

    return curr_dir

def get_curr_dir() -> Path:
    home_dir = Path.home()
    desktop_dir = home_dir / "Desktop"
    if desktop_dir.is_dir():
        fallback_dir = desktop_dir
    else:
        fallback_dir = home_dir

    if (curr_dir := _get_curr_dir_if_writable()) != None:
        return curr_dir
    else:
        return fallback_dir

CURR_DIR = get_curr_dir()

def get_config_dir() -> Path:
    if platform.system() == "Windows":
        fallback_dir = Path(os.path.expandvars("%APPDATA%\\sticker-convert"))
    else:
        fallback_dir = Path.home() / ".config/sticker-convert"

    if (config_dir := _get_curr_dir_if_writable()) != None:
        return config_dir
    else:
        os.makedirs(fallback_dir, exist_ok=True)
        return fallback_dir

CONFIG_DIR = get_config_dir()

def get_resource_dir() -> Path:
    dirs = [
        Path("resources"),
        Path(CURR_DIR / "resources"),
        (Path(sys.argv[0]).parent / "resources"),
        (Path(sys.argv[0]).parent / "sticker_convert/resources"),
        (Path(__file__).resolve().parent / "../../resources"),
    ]

    try:
        dirs.append(Path(__compiled__.containing_dir, "resources"))
    except NameError:
        pass

    for dir in dirs:
        if dir.is_dir():
            return dir

RESOURCE_DIR = get_resource_dir()