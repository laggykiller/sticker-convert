import json
import os
import shutil
import subprocess
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any


def get_python_path() -> str:
    path = shutil.which("python3")
    if not path:
        shutil.which("python")
    if not path:
        raise RuntimeError("Cannot find python executable")
    return path


PYTHON_EXE = get_python_path()
SRC_DIR = Path(__file__).resolve().parent / "../src"
SAMPLE_DIR = Path(__file__).resolve().parent / "samples"
COMPRESSION_JSON_PATH = SRC_DIR / "sticker_convert/resources/compression.json"
CREDS_JSON_PATH = SRC_DIR / "sticker_convert/creds.json"

with open(COMPRESSION_JSON_PATH) as f:
    COMPRESSION_DICT = json.load(f)

if CREDS_JSON_PATH.is_file():
    with open(CREDS_JSON_PATH) as f:
        CREDS_JSON_DICT = json.load(f)

        SIGNAL_UUID = CREDS_JSON_DICT.get("signal", {}).get("uuid")
        SIGNAL_PASSWORD = CREDS_JSON_DICT.get("signal", {}).get("password")
        TELEGRAM_TOKEN = CREDS_JSON_DICT.get("telegram", {}).get("token")
        TELEGRAM_USERID = CREDS_JSON_DICT.get("telegram", {}).get("userid")
        KAKAO_TOKEN = CREDS_JSON_DICT.get("kakao", {}).get("auth_token")
        LINE_COOKIES = CREDS_JSON_DICT.get("line", {}).get("cookies")
else:
    SIGNAL_UUID = os.environ.get("SIGNAL_UUID")  # type: ignore
    SIGNAL_PASSWORD = os.environ.get("SIGNAL_PASSWORD")  # type: ignore
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")  # type: ignore
    TELEGRAM_USERID = os.environ.get("TELEGRAM_USERID")  # type: ignore
    KAKAO_TOKEN = os.environ.get("KAKAO_TOKEN")  # type: ignore
    LINE_COOKIES = os.environ.get("LINE_COOKIES")  # type: ignore


def run_cmd(cmd: list[str], **kwargs: Any):
    result: CompletedProcess[Any] = subprocess.run(cmd, **kwargs)  # type: ignore

    assert result.returncode == 0  # type: ignore
