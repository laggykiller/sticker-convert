import os
import sys
from pathlib import Path

from _pytest._py.path import LocalPath  # type: ignore

from tests.common import COMPRESSION_DICT, PYTHON_EXE, SAMPLE_DIR, SRC_DIR, run_cmd

os.chdir(Path(__file__).resolve().parent)
sys.path.append("../src")

from sticker_convert.utils.media.codec_info import CodecInfo  # type: ignore # noqa: E402

SIZE_MAX_IMG = COMPRESSION_DICT.get("custom").get("size_max").get("img")
SIZE_MAX_VID = COMPRESSION_DICT.get("custom").get("size_max").get("vid")


def _run_sticker_convert(fmt: str, tmp_path: LocalPath) -> None:
    run_cmd(
        [
            PYTHON_EXE,
            "sticker-convert.py",
            "--input-dir",
            str(SAMPLE_DIR),
            "--output-dir",
            str(tmp_path),
            "--preset",
            "custom",
            "--duration-max",
            "2000",
            "--steps",
            "6",
            "--no-confirm",
            "--img-format",
            fmt,
            "--vid-format",
            fmt,
        ],
        cwd=SRC_DIR,
    )

    for i in SAMPLE_DIR.iterdir():
        preset_dict = COMPRESSION_DICT.get("custom")
        if i.name.startswith("static_") and preset_dict.get("fake_vid") is False:
            size_max = preset_dict.get("size_max").get("img")
        else:
            size_max = preset_dict.get("size_max").get("vid")

        fname = Path(i).stem + fmt
        fpath = Path(tmp_path) / fname
        fps, frames, duration = CodecInfo.get_file_fps_frames_duration(fpath)

        print(f"[TEST] Check if {fname} exists")
        assert fpath.is_file()
        assert os.path.getsize(fpath) < size_max

        if i.name.startswith("animated_"):
            print(f"[TEST] {fname}: {fps=} {frames=} {duration=}")
            duration_min = preset_dict.get("duration").get("min")
            duration_max = preset_dict.get("duration").get("max")
            assert fps <= preset_dict.get("fps").get("max")
            if duration_min:
                assert duration >= duration_min
            if duration_max:
                assert duration <= duration_max


def test_to_static_png(tmp_path: LocalPath) -> None:
    _run_sticker_convert(".png", tmp_path)


def test_to_static_webp(tmp_path: LocalPath) -> None:
    _run_sticker_convert(".webp", tmp_path)


def test_to_animated_apng(tmp_path: LocalPath) -> None:
    _run_sticker_convert(".apng", tmp_path)


def test_to_animated_gif(tmp_path: LocalPath) -> None:
    _run_sticker_convert(".gif", tmp_path)


def test_to_animated_webm(tmp_path: LocalPath) -> None:
    _run_sticker_convert(".webm", tmp_path)


def test_to_animated_webp(tmp_path: LocalPath) -> None:
    _run_sticker_convert(".webp", tmp_path)


def test_to_animated_mp4(tmp_path: LocalPath) -> None:
    _run_sticker_convert(".mp4", tmp_path)
