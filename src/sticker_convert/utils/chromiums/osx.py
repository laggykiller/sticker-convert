#!/usr/bin/env python3
import glob
import os
import plistlib
import subprocess
from typing import Optional

# Adopted from https://github.com/roniemartinez/browsers/blob/master/browsers/osx.py

OSX_CHROMIUMS_BUNDLE_LIST = (
    # browser name, bundle ID, version string
    ("chrome", "com.google.Chrome", "CFBundleShortVersionString"),
    ("chrome-beta", "com.google.Chrome.beta", "CFBundleShortVersionString"),
    ("chrome-canary", "com.google.Chrome.canary", "CFBundleShortVersionString"),
    ("chrome-dev", "com.google.Chrome.dev", "CFBundleShortVersionString"),
    ("chrome-test", "com.google.chrome.for.testing", "CFBundleShortVersionString"),
    ("chromium", "org.chromium.Chromium", "CFBundleShortVersionString"),
    ("msedge", "com.microsoft.edgemac", "CFBundleShortVersionString"),
    ("msedge-beta", "com.microsoft.edgemac.Beta", "CFBundleShortVersionString"),
    ("msedge-dev", "com.microsoft.edgemac.Dev", "CFBundleShortVersionString"),
    ("msedge-canary", "com.microsoft.edgemac.Canary", "CFBundleShortVersionString"),
    ("brave", "com.brave.Browser", "CFBundleVersion"),
    ("brave-beta", "com.brave.Browser.beta", "CFBundleVersion"),
    ("brave-dev", "com.brave.Browser.dev", "CFBundleVersion"),
    ("brave-nightly", "com.brave.Browser.nightly", "CFBundleVersion"),
    ("opera", "com.operasoftware.Opera", "CFBundleVersion"),
    ("opera-beta", "com.operasoftware.OperaNext", "CFBundleVersion"),
    ("opera-developer", "com.operasoftware.OperaDeveloper", "CFBundleVersion"),
    ("opera-gx", "com.operasoftware.OperaGX", "CFBundleVersion"),
    ("opera-neon", "com.opera.Neon", "CFBundleShortVersionString"),
    ("duckduckgo", "com.duckduckgo.macos.browser", "CFBundleShortVersionString"),
    ("epic", "com.hiddenreflex.Epic", "CFBundleShortVersionString"),
    ("vivaldi", "com.vivaldi.Vivaldi", "CFBundleShortVersionString"),
    ("yandex", "ru.yandex.desktop.yandex-browser", "CFBundleShortVersionString"),
)

OSX_CHROMIUMS_BUNDLE_DICT = {item[1]: item for item in OSX_CHROMIUMS_BUNDLE_LIST}


def get_chromium_path() -> Optional[str]:
    for _, bundle_id, _ in OSX_CHROMIUMS_BUNDLE_LIST:
        app_dirs = subprocess.getoutput(
            f'mdfind "kMDItemCFBundleIdentifier == {bundle_id}"'
        ).splitlines()
        for app_dir in app_dirs:
            plist_path = os.path.join(app_dir, "Contents/Info.plist")

            with open(plist_path, "rb") as f:
                plist = plistlib.load(f)
                executable_name = plist["CFBundleExecutable"]
                executable = os.path.join(app_dir, "Contents/MacOS", executable_name)
                return executable

    # Naively iterate /Applications folder in case the above check fails
    for plist_path in glob.glob("/Applications/*.app/Contents/Info.plist"):
        with open(plist_path, "rb") as f:
            plist = plistlib.load(f)
            bundle_id = plist.get("CFBundleIdentifier")
            if bundle_id not in OSX_CHROMIUMS_BUNDLE_DICT:
                continue

            app_dir = os.path.dirname(os.path.dirname(plist_path))
            executable_name = plist["CFBundleExecutable"]
            executable = os.path.join(app_dir, "Contents/MacOS", executable_name)

            return executable

    return None
