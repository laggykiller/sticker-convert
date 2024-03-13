from typing import Dict, Tuple
import json
from pathlib import Path

ROOT_DIR = Path(__file__).parents[1]

def main():
    xcode_imessage_iconset: Dict[str, Tuple[int, int]] = {}

    with open(ROOT_DIR / "src/sticker_convert/ios-message-stickers-template/stickers StickerPackExtension/Stickers.xcstickers/iMessage App Icon.stickersiconset/Contents.json") as f:
        dict = json.load(f)

    for i in dict["images"]:
        filename = i["filename"]
        size = i["size"]
        size_w = int(size.split("x")[0])
        size_h = int(size.split("x")[1])
        scale = int(i["scale"].replace("x", ""))
        size_w_scaled = size_w * scale
        size_h_scaled = size_h * scale

        xcode_imessage_iconset[filename] = (size_w_scaled, size_h_scaled)
    
    print(xcode_imessage_iconset)

if __name__ == "__main__":
    main()