#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Any


class JsonManager:
    @staticmethod
    def load_json(path: Path) -> dict[Any, Any]:
        if not path.is_file():
            raise RuntimeError(f"{path} cannot be found")
        else:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data

    @staticmethod
    def save_json(path: Path, data: dict[Any, Any]):
        with open(path, "w+", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
