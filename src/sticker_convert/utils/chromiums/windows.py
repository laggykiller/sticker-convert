#!/usr/bin/env python3
import os
from typing import Optional

# Not adopting approach of reading registry like https://github.com/roniemartinez/browsers
# As trigger antivirus

PF32 = os.environ.get("PROGRAMW6432")
PF64 = os.environ.get("PROGRAMFILES")
LAD = os.environ.get("LOCALAPPDATA")

WINDOWS_CHROMIUMS_PATHS = (
    f"{PF64}\\Google\\Chrome\\Application\\chrome.exe",  # chromium
    f"{PF32}\\Google\\Chrome\\Application\\chrome.exe",  # chromium
    f"{LAD}\\Google\\Chrome SxS\\Application\\chrome.exe",  # chromium-canary
    f"{PF64}\\Opera\\opera.exe",  # opera
    f"{PF32}\\Opera\\opera.exe",  # opera
    f"{LAD}\\Programs\\Opera\\opera.exe",  # opera
    f"{LAD}\\Programs\\Opera\\launcher.exe",  # opera
    f"{LAD}\\Programs\\Opera Beta\\opera.exe",  # opera-beta
    f"{LAD}\\Programs\\Opera Beta\\launcher.exe",  # opera-beta
    f"{LAD}\\Programs\\Opera Developer\\opera.exe",  # opera-developer
    f"{LAD}\\Programs\\Opera Developer\\launcher.exe",  # opera-developer
    f"{PF64}\\Microsoft\\Edge\\Application\\msedge.exe",  # msedge
    f"{PF32}\\Microsoft\\Edge\\Application\\msedge.exe",  # msedge
    f"{PF64}\\Microsoft\\Edge Beta\\Application\\msedge.exe",  # msedge-beta
    f"{PF32}\\Microsoft\\Edge Beta\\Application\\msedge.exe",  # msedge-beta
    f"{PF64}\\Microsoft\\Edge Dev\\Application\\msedge.exe",  # msedge-dev
    f"{PF32}\\Microsoft\\Edge Dev\\Application\\msedge.exe",  # msedge-dev
    f"{LAD}\\Microsoft\\Edge SxS\\Application\\msedge.exe",  # msedge-canary
    f"{PF64}\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",  # brave
    f"{PF32}\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",  # brave
    f"{PF64}\\BraveSoftware\\Brave-Browser-Beta\\Application\\brave.exe",  # brave-beta
    f"{PF32}\\BraveSoftware\\Brave-Browser-Beta\\Application\\brave.exe",  # brave-beta
    f"{PF64}\\BraveSoftware\\Brave-Browser-Nightly\\Application\\brave.exe",  # brave-nightly
    f"{PF32}\\BraveSoftware\\Brave-Browser-Nightly\\Application\\brave.exe",  # brave-nightly
)


def get_chromium_path() -> Optional[str]:
    for path in WINDOWS_CHROMIUMS_PATHS:
        if os.path.exists(path):
            return path

    return None
