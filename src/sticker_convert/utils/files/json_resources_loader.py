#!/usr/bin/env python3
from typing import Any, Dict, cast

from mergedeep import merge  # type: ignore

from sticker_convert.definitions import CONFIG_DIR, ROOT_DIR, RUNTIME_STATE
from sticker_convert.utils.files.json_manager import JsonManager


def load_resource_json(json_name: str) -> Dict[Any, Any]:
    if RUNTIME_STATE.get(f"{json_name}_json") is not None:
        return cast(Dict[Any, Any], RUNTIME_STATE[f"{json_name}_json"])
    else:
        loaded_json = JsonManager.load_json(ROOT_DIR / f"resources/{json_name}.json")

        json_to_merge = None
        lang = RUNTIME_STATE["LANG"]
        if lang != "en_US":
            # Translated json
            json_to_merge = ROOT_DIR / f"resources/{json_name}.{lang}.json"
        if json_name == "compression":
            # Custom preset json
            json_to_merge = CONFIG_DIR / "custom_preset.json"

        if json_to_merge and json_to_merge.exists():
            custom_preset_json = JsonManager.load_json(json_to_merge)
            loaded_json: Dict[Any, Any] = merge(  # type: ignore
                loaded_json,  # type: ignore
                custom_preset_json,
            )
        RUNTIME_STATE[f"{json_name}_json"] = loaded_json
        return loaded_json
