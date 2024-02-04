#!/usr/bin/env python3
from pathlib import Path
import json
from typing import Optional

from .dir_utils import CURR_DIR

class JsonManager:
    @staticmethod
    def load_json(path: str) -> Optional[dict]:
        if Path(path).is_absolute() == False:
            json_path = CURR_DIR / path
        else:
            json_path = Path(path)

        if not json_path.is_file():
            return None
        else:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            return data

    @staticmethod
    def save_json(path: str, data: dict):
        if Path(path).is_absolute() == False:
            json_path = CURR_DIR / path
        else:
            json_path = Path(path)

        with open(json_path, "w+", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
