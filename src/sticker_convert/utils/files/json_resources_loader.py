from typing import Dict

from sticker_convert.definitions import ROOT_DIR
from sticker_convert.utils.files.json_manager import JsonManager

HELP_JSON: Dict[str, Dict[str, str]] = JsonManager.load_json(
    ROOT_DIR / "resources/help.json"
)
INPUT_JSON = JsonManager.load_json(ROOT_DIR / "resources/input.json")
COMPRESSION_JSON = JsonManager.load_json(ROOT_DIR / "resources/compression.json")
OUTPUT_JSON = JsonManager.load_json(ROOT_DIR / "resources/output.json")
EMOJI_JSON = JsonManager.load_json(ROOT_DIR / "resources/emoji.json")
