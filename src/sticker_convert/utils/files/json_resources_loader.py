from typing import Any, Dict

from mergedeep import merge  # type: ignore

from sticker_convert.definitions import CONFIG_DIR, ROOT_DIR
from sticker_convert.utils.files.json_manager import JsonManager


def _load_compression() -> Dict[Any, Any]:
    compression_json = JsonManager.load_json(ROOT_DIR / "resources/compression.json")
    custom_preset_json_path = CONFIG_DIR / "custom_preset.json"
    if custom_preset_json_path.exists():
        custom_preset_json = JsonManager.load_json(custom_preset_json_path)
        compression_json: Dict[Any, Any] = merge(  # type: ignore
            compression_json,  # type: ignore
            custom_preset_json,
        )
    return compression_json


HELP_JSON: Dict[str, Dict[str, str]] = JsonManager.load_json(
    ROOT_DIR / "resources/help.json"
)
INPUT_JSON = JsonManager.load_json(ROOT_DIR / "resources/input.json")
COMPRESSION_JSON = _load_compression()
OUTPUT_JSON = JsonManager.load_json(ROOT_DIR / "resources/output.json")
EMOJI_JSON = JsonManager.load_json(ROOT_DIR / "resources/emoji.json")
