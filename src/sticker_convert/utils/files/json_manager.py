#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sticker_convert.utils.translate import get_translator

I = get_translator()


class JsonManager:
    @staticmethod
    def load_json(path: Path) -> dict[Any, Any]:
        if not path.is_file():
            raise RuntimeError(I("{} cannot be found").format(path))
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data

    @staticmethod
    def save_json(path: Path, data: dict[Any, Any]) -> None:
        with open(path, "w+", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
