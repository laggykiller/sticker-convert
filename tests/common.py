import shutil
import subprocess
from pathlib import Path
import json

import pytest

PYTHON_EXE = shutil.which('python3') if shutil.which('python3') else shutil.which('python')
SRC_DIR = Path(__file__).resolve().parent / '../src'
SAMPLE_DIR = Path(__file__).resolve().parent / 'samples'
COMPRESSION_JSON_PATH = SRC_DIR / 'sticker_convert/resources/compression.json'

with open(COMPRESSION_JSON_PATH) as f:
    COMPRESSION_DICT = json.load(f)

def run_cmd(cmd, **kwargs):
    result = subprocess.run(cmd, **kwargs)

    assert result.returncode == 0