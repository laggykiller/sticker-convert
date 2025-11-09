#!/usr/bin/env python3
from typing import List

from sticker_convert.utils.files.json_resources_loader import load_resource_json


def get_emoji_list() -> List[str]:
    return [i["emoji"] for i in load_resource_json("emoji")]


EMOJI_LIST = get_emoji_list()


# https://stackoverflow.com/a/43146653
def extract_emojis(s: str) -> str:
    return "".join(set(c for c in s if c in EMOJI_LIST))
