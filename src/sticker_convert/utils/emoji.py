#!/usr/bin/env python3
from typing import List, cast

from pyuegc import EGC  # type: ignore

from sticker_convert.definitions import RUNTIME_STATE
from sticker_convert.utils.files.json_resources_loader import load_resource_json


def get_emoji_list() -> List[str]:
    if RUNTIME_STATE.get("EMOJI_LIST") is not None:
        return cast(List[str], RUNTIME_STATE["EMOJI_LIST"])
    else:
        emoji_list = [i["emoji"] for i in load_resource_json("emoji")]
        RUNTIME_STATE["EMOJI_LIST"] = emoji_list
        return emoji_list


EMOJI_LIST = get_emoji_list()


# https://stackoverflow.com/a/43146653
def extract_emojis(s: str) -> str:
    emojis: List[str] = []
    for c in cast(List[str], EGC(s)):
        if c in EMOJI_LIST and c not in emojis:
            emojis.append(c)

    return "".join(emojis)
