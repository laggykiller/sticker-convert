#!/usr/bin/env python3
import os
import sys
import platform
from typing import Optional


class DirUtils:
    @staticmethod
    def _get_curr_dir_if_writable() -> Optional[str]:
        appimage_path = os.getenv("APPIMAGE")
        curr_dir = os.getcwd()

        if (
            curr_dir.startswith("/usr/bin/")
            or curr_dir.startswith("/bin")
            or curr_dir.startswith("/usr/local/bin")
            or curr_dir.startswith("C:\\Program Files")
            or "site-packages" in __file__
        ):
            return None

        if (
            platform.system() == "Darwin"
            and getattr(sys, "frozen", False)
            and ".app/Contents/MacOS" in curr_dir
        ):
            if curr_dir.startswith("/Applications/"):
                return None
            else:
                curr_dir = os.path.abspath("../../../")

        if appimage_path:
            curr_dir = os.path.split(appimage_path)[0]

        if not os.access(curr_dir, os.W_OK):
            return None

        return curr_dir

    @staticmethod
    def get_curr_dir() -> str:
        home_dir = os.path.expanduser("~")
        if os.path.isdir(os.path.join(home_dir, "Desktop")):
            fallback_dir = os.path.join(home_dir, "Desktop")
        else:
            fallback_dir = home_dir

        if (curr_dir := DirUtils._get_curr_dir_if_writable()) != None:
            return curr_dir
        else:
            return fallback_dir

    @staticmethod
    def get_config_dir() -> str:
        if platform.system() == "Windows":
            fallback_dir = os.path.expandvars("%APPDATA%\\sticker-convert")
        else:
            fallback_dir = os.path.expanduser("~/.config/sticker-convert")

        if (config_dir := DirUtils._get_curr_dir_if_writable()) != None:
            return config_dir
        else:
            return fallback_dir
