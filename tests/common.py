import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

PYTHON_EXE = shutil.which('python3') if shutil.which('python3') else shutil.which('python')
SRC_DIR = Path(__file__).resolve().parent / '../src'
SAMPLE_DIR = Path(__file__).resolve().parent / 'samples'
COMPRESSION_JSON_PATH = SRC_DIR / 'sticker_convert/resources/compression.json'
CREDS_JSON_PATH = SRC_DIR / 'sticker_convert/creds.json'

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
    SIGNAL_UUID = os.environ.get("SIGNAL_UUID")
    SIGNAL_PASSWORD = os.environ.get("SIGNAL_PASSWORD")
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    TELEGRAM_USERID = os.environ.get("TELEGRAM_USERID")
    KAKAO_TOKEN = os.environ.get("KAKAO_TOKEN")
    LINE_COOKIES = os.environ.get("LINE_COOKIES")

def run_cmd(cmd, **kwargs):
    result = subprocess.run(cmd, **kwargs)

    assert result.returncode == 0