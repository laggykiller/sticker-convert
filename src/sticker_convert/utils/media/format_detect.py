from pathlib import Path
from typing import List, Optional


def is_png(header: bytes, trailer: bytes):
    return header[:8] == b"\x89PNG\r\n\x1a\n"


def is_gif(header: bytes, trailer: bytes):
    return header[:6] in (b"GIF87a", b"GIF89a")


def is_jpeg(header: bytes, trailer: bytes):
    return header[:2] == b"\xff\xd8" and trailer[-2:] == b"\xff\xd9"


def is_webp(header: bytes, trailer: bytes):
    return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP"


def is_webm(header: bytes, trailer: bytes):
    return header[:4] == b"\x1a\x45\xdf\xa3"


FORMATS = {
    ".png": is_png,
    ".gif": is_gif,
    ".jpeg": is_jpeg,
    ".webp": is_webp,
    ".webm": is_webm,
}


def format_detect(path: Path, possible: Optional[List[str]] = None) -> str:
    with open(path, "rb") as f:
        header = f.read(16)
        f.seek(-16, 2)
        trailer = f.read(16)

    if possible is None:
        for k, v in FORMATS.items():
            if v(header, trailer) is True:
                return k
    else:
        for i in possible:
            if i in FORMATS and FORMATS[i](header, trailer):
                return i
    return ".unknown_ext"
