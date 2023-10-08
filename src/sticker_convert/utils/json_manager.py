#!/usr/bin/env python3
import os
import json
from typing import Optional


class JsonManager:
    @staticmethod
    def load_json(path: str) -> Optional[dict]:
        if not os.path.isfile(path):
            return None
        else:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data

    @staticmethod
    def save_json(path: str, data: dict):
        with open(path, "w+", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
