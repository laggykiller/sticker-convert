#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Any, Dict


class JsonManager:
    @staticmethod
    def load_json(path: Path) -> Dict[Any, Any]:
        if not path.is_file():
            raise RuntimeError(f"{path} cannot be found")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data

    @staticmethod
    def save_json(path: Path, data: Dict[Any, Any]) -> None:
        with open(path, "w+", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
