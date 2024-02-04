#!/usr/bin/env python3
from pathlib import Path
import json
from typing import Optional

class JsonManager:
    @staticmethod
    def load_json(path: Path) -> Optional[dict]:
        if not path.is_file():
            return None
        else:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data

    @staticmethod
    def save_json(path: Path, data: dict):
        with open(path, "w+", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
