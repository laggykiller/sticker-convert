#!/usr/bin/env python3
from typing import Callable, List, Sequence, Set

from ugrapheme import graphemes  # type: ignore

from sticker_convert.utils.files.json_resources_loader import load_resource_json

graphemes: Callable[[str], Sequence[str]]  # type: ignore


# https://stackoverflow.com/a/480227
# Return list of unique items of list while preserve order
def uniques(seq: List[str]):
    seen: Set[str] = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def get_emoji_list() -> List[str]:
    return [i["emoji"] for i in load_resource_json("emoji")]


EMOJI_LIST = get_emoji_list()


# https://stackoverflow.com/a/43146653
def extract_emojis(s: str) -> str:
    return "".join(uniques(list(c for c in graphemes(s) if c in EMOJI_LIST)))
