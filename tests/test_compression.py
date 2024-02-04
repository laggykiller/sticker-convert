import os
import sys
from pathlib import Path

import pytest

from .common import run_cmd, PYTHON_EXE, SRC_DIR, SAMPLE_DIR, COMPRESSION_DICT

os.chdir(Path(__file__).resolve().parent)
sys.path.append('../src')

from sticker_convert.utils.media.codec_info import CodecInfo

SIZE_MAX_IMG = COMPRESSION_DICT.get('custom').get('size_max').get('img')
SIZE_MAX_VID = COMPRESSION_DICT.get('custom').get('size_max').get('vid')

def _run_sticker_convert(fmt: str, tmp_path: Path):
    run_cmd([
        PYTHON_EXE,
        'sticker-convert.py',
        '--input-dir', SAMPLE_DIR,
        '--output-dir', tmp_path,
        '--preset', 'custom',
        '--duration-max', '2',
        '--steps', '6',
        '--img-format', fmt,
        '--vid-format', fmt
    ], cwd=SRC_DIR)

    for i in os.listdir(SAMPLE_DIR):
        preset_dict = COMPRESSION_DICT.get("custom")
        if i.startswith("static_") and preset_dict.get("fake_vid") == False:
            size_max = preset_dict.get("size_max").get("img")
        else:
            size_max = preset_dict.get("size_max").get("vid")
            
        fname = Path(i).stem + fmt
        fpath = tmp_path / fname
        fps, frames, duration = CodecInfo.get_file_fps_frames_duration(fpath)

        print(f"[TEST] Check if {fname} exists")
        assert fpath.is_file()
        assert os.path.getsize(fpath) < size_max

        if i.startswith("animated_"):
            print(f"[TEST] {fname}: {fps=} {frames=} {duration=}")
            duration_min = preset_dict.get("duration").get("min")
            duration_max = preset_dict.get("duration").get("max")
            assert fps <= preset_dict.get("fps").get("max")
            if duration_min:
                assert duration >= duration_min
            if duration_max:
                assert duration <= duration_max

def test_to_static_png(tmp_path):
    _run_sticker_convert('.png', tmp_path)

def test_to_static_webp(tmp_path):
    _run_sticker_convert('.webp', tmp_path)

def test_to_animated_apng(tmp_path):
    _run_sticker_convert('.apng', tmp_path)

def test_to_animated_gif(tmp_path):
    _run_sticker_convert('.gif', tmp_path)

def test_to_animated_webm(tmp_path):
    _run_sticker_convert('.webm', tmp_path)

def test_to_animated_webp(tmp_path):
    _run_sticker_convert('.webp', tmp_path)

def test_to_animated_mp4(tmp_path):
    _run_sticker_convert('.mp4', tmp_path)