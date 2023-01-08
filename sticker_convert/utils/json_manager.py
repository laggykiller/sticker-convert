#!/usr/bin/env python3
import os
import json

class JsonManager:
    @staticmethod
    def load_json(path):
        if not os.path.isfile(path):
            return
        else:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            return data
    
    @staticmethod
    def save_json(path, data):
        with open(path, 'w+', encoding='utf-8') as f:
            json.dump(data, f, indent=4)