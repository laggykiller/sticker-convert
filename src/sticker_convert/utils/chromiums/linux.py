#!/usr/bin/env python3
import configparser
import os
import re
from typing import Optional

# Adopted from https://github.com/roniemartinez/browsers/blob/master/browsers/linux.py

LINUX_DESKTOP_ENTRY_LIST = (
    ("chrome", ("google-chrome",)),
    ("chromium", ("chromium", "chromium_chromium")),
    ("brave", ("brave-browser", "brave_brave")),
    ("brave-beta", ("brave-browser-beta",)),
    ("brave-nightly", ("brave-browser-nightly",)),
    ("msedge", ("microsoft-edge",)),
    ("opera", ("opera_opera",)),
    ("opera-beta", ("opera-beta_opera-beta",)),
    ("opera-developer", ("opera-developer_opera-developer",)),
    ("vivaldi", ("vivaldi_vivaldi-stable",)),
)

# $XDG_DATA_HOME and $XDG_DATA_DIRS are not always set
XDG_DATA_LOCATIONS = (
    "~/.local/share/applications",
    "/usr/share/applications",
    "/var/lib/snapd/desktop/applications",
)

VERSION_PATTERN = re.compile(
    r"\b(\S+\.\S+)\b"
)  # simple pattern assuming all version strings have a dot on them


def get_chromium_path() -> Optional[str]:
    for _, desktop_entries in LINUX_DESKTOP_ENTRY_LIST:
        for application_dir in XDG_DATA_LOCATIONS:
            for desktop_entry in desktop_entries:
                path = os.path.join(application_dir, f"{desktop_entry}.desktop")

                if not os.path.isfile(path):
                    continue

                config = configparser.ConfigParser(interpolation=None)
                config.read(path, encoding="utf-8")
                executable_path = config.get("Desktop Entry", "Exec")

                if executable_path.lower().endswith(" %u"):
                    executable_path = executable_path[:-3].strip()

                return executable_path

    return None
