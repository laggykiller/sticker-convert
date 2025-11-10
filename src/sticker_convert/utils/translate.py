#!/usr/bin/env python3
import gettext
import locale
import platform
import sys
from json import JSONDecodeError
from multiprocessing import current_process
from typing import Any, Callable, Dict, cast

from sticker_convert.definitions import CONFIG_DIR, ROOT_DIR, RUNTIME_STATE
from sticker_convert.utils.files.json_manager import JsonManager

LANG_DICT = {
    "en_US": ("en_US",),
    "ja_JP": ("ja_jp",),
    "zh_CN": ("zh_chs", "zh_cn", "zh_sg"),
    "zh_TW": ("zh_tw", "zh_hk", "zh_mo", "zh_cht"),
}


def get_default_lang() -> str:
    lang = locale.getlocale()[0]
    winlang = ""
    if platform.system() == "Windows":
        import ctypes

        windll = ctypes.windll.kernel32  # type: ignore
        winlang_id = cast(int, windll.GetUserDefaultUILanguage())  # type: ignore
        winlang = cast(str, locale.windows_locale[winlang_id])  # type: ignore

    for k, v in LANG_DICT.items():
        for i in v:
            if (
                lang is not None and lang.lower().startswith(i)
            ) or winlang.lower().startswith(i):
                return k

    return "en_US"


def get_lang() -> str:
    # Priority 1: From --lang CLI flag
    is_lang = False
    lang = None
    for i in sys.argv:
        if is_lang:
            return i
        if i == "--lang":
            is_lang = True

    # Priority 2: From config
    settings_path = CONFIG_DIR / "config.json"
    if settings_path.is_file():
        try:
            settings: Dict[Any, Any] = JsonManager.load_json(settings_path)
            lang = settings.get("lang")
            if lang:
                if lang in LANG_DICT:
                    return lang
                elif lang != "auto":
                    return "en_US"
        except JSONDecodeError:
            pass

    # Priority 3: Default locale
    lang = get_default_lang()
    return lang


LANG = RUNTIME_STATE.get("LANG", get_lang())
RUNTIME_STATE["LANG"] = LANG


def gettext_dummy(x: str) -> str:
    return x


def get_translator() -> Callable[[str], str]:
    if RUNTIME_STATE.get("TRANS") is not None:
        return RUNTIME_STATE["TRANS"]

    try:
        trans: Callable[[str], str] = gettext.translation(
            "base", ROOT_DIR / "locales", languages=[RUNTIME_STATE["LANG"]]
        ).gettext
    except FileNotFoundError:
        if current_process().name == "MainProcess":
            print(f"Warning: Cannot find locales/{LANG}/LC_MESSAGES/base.mo")
            print(
                "Please generate by running scripts/update-locales.sh in root of repo"
            )
            print("Fallback to using English...")
        trans = gettext_dummy
    RUNTIME_STATE["TRANS"] = trans
    return trans


def I(x: str) -> str:  # noqa: E743
    return get_translator()(x)


SUPPORTED_LANG = {
    I("Auto"): "auto",
    "English": "en_US",
    "繁體中文": "zh_TW",
    "简体中文": "zh_CN",
    "日本語": "ja_JP",
}
