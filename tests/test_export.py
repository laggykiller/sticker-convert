import os
import sys
from pathlib import Path
from typing import List, Optional

import pytest
from _pytest._py.path import LocalPath  # type: ignore

from tests.common import COMPRESSION_DICT, PYTHON_EXE, SAMPLE_DIR, SIGNAL_PASSWORD, SIGNAL_UUID, SRC_DIR, TELEGRAM_TOKEN, TELEGRAM_USERID, VIBER_AUTH, run_cmd

os.chdir(Path(__file__).resolve().parent)
sys.path.append("../src")

from sticker_convert.utils.media.codec_info import CodecInfo  # type: ignore # noqa: E402

TEST_UPLOAD = os.environ.get("TEST_UPLOAD")


def _run_sticker_convert(
    tmp_path: LocalPath, preset: str, export: Optional[str]
) -> None:
    preset_dict = COMPRESSION_DICT.get(preset)

    cmd: List[str] = [
        PYTHON_EXE,
        "sticker-convert.py",
        "--input-dir",
        str(SAMPLE_DIR),
        "--output-dir",
        str(tmp_path),
        "--preset",
        preset,
        "--no-confirm",
        "--author",
        "sticker-convert-test",
        "--title",
        "sticker-convert-test",
    ]

    if export:
        cmd.append(f"--export-{export}")

    run_cmd(cmd, cwd=SRC_DIR)

    for i in SAMPLE_DIR.iterdir():
        preset_dict.get("size_max").get("img")

        if i.name.startswith("static_") and preset_dict.get("fake_vid") is False:
            size_max = preset_dict.get("size_max").get("img")
            fmt: str = preset_dict.get("format").get("img")
        else:
            size_max = preset_dict.get("size_max").get("vid")
            fmt = preset_dict.get("format").get("vid")

        fname = i.stem + fmt
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


def _xcode_asserts(tmp_path: LocalPath) -> None:
    iconset = {
        "App-Store-1024x1024pt.png": (1024, 1024),
        "iPad-Settings-29pt@2x.png": (58, 58),
        "iPhone-settings-29pt@2x.png": (58, 58),
        "iPhone-Settings-29pt@3x.png": (87, 87),
        "Messages27x20pt@2x.png": (54, 40),
        "Messages27x20pt@3x.png": (81, 60),
        "Messages32x24pt@2x.png": (64, 48),
        "Messages32x24pt@3x.png": (96, 72),
        "Messages-App-Store-1024x768pt.png": (1024, 768),
        "Messages-iPad-67x50pt@2x.png": (134, 100),
        "Messages-iPad-Pro-74x55pt@2x.png": (148, 110),
        "Messages-iPhone-60x45pt@2x.png": (120, 90),
        "Messages-iPhone-60x45pt@3x.png": (180, 135),
    }

    imessage_xcode_dir = Path(tmp_path) / "sticker-convert-test"

    assert Path(imessage_xcode_dir / "sticker-convert-test/Info.plist").is_file()

    assert Path(
        imessage_xcode_dir / "sticker-convert-test StickerPackExtension/Info.plist"
    ).is_file()
    assert Path(
        imessage_xcode_dir
        / "sticker-convert-test StickerPackExtension/Stickers.xcstickers/Contents.json"
    ).is_file()
    for i in iconset:
        assert Path(
            imessage_xcode_dir
            / "sticker-convert-test StickerPackExtension/Stickers.xcstickers/iMessage App Icon.stickersiconset"
            / i
        ).is_file()

    assert Path(
        imessage_xcode_dir / "sticker-convert-test.xcodeproj/project.pbxproj"
    ).is_file()


@pytest.mark.skipif(not TEST_UPLOAD, reason="TEST_UPLOAD not set")
@pytest.mark.skipif(not (SIGNAL_UUID and SIGNAL_PASSWORD), reason="No credentials")
def test_upload_signal_with_upload(tmp_path: LocalPath) -> None:
    _run_sticker_convert(tmp_path, "signal", "signal")


@pytest.mark.skipif(not TEST_UPLOAD, reason="TEST_UPLOAD not set")
@pytest.mark.skipif(not (TELEGRAM_TOKEN and TELEGRAM_USERID), reason="No credentials")
def test_upload_telegram_with_upload(tmp_path: LocalPath) -> None:
    _run_sticker_convert(tmp_path, "telegram", "telegram")


@pytest.mark.skipif(not TEST_UPLOAD, reason="TEST_UPLOAD not set")
@pytest.mark.skipif(not (TELEGRAM_TOKEN and TELEGRAM_USERID), reason="No credentials")
def test_upload_telegram_emoji_with_upload(tmp_path: LocalPath) -> None:
    _run_sticker_convert(tmp_path, "telegram_emoji", None)


@pytest.mark.skipif(not TEST_UPLOAD, reason="TEST_UPLOAD not set")
@pytest.mark.skipif(not VIBER_AUTH, reason="No credentials")
def test_upload_viber_with_upload(tmp_path: LocalPath) -> None:
    _run_sticker_convert(tmp_path, "viber", "viber")


@pytest.mark.skipif(
    TELEGRAM_TOKEN is not None and TELEGRAM_USERID is not None,
    reason="With credentials",
)
def test_upload_signal(tmp_path: LocalPath) -> None:
    _run_sticker_convert(tmp_path, "signal", None)


@pytest.mark.skipif(
    TELEGRAM_TOKEN is not None and TELEGRAM_USERID is not None,
    reason="With credentials",
)
def test_upload_telegram(tmp_path: LocalPath) -> None:
    _run_sticker_convert(tmp_path, "telegram", None)


@pytest.mark.skipif(
    TELEGRAM_TOKEN is not None and TELEGRAM_USERID is not None,
    reason="With credentials",
)
def test_upload_telegram_emoji(tmp_path: LocalPath) -> None:
    _run_sticker_convert(tmp_path, "telegram_emoji", None)


@pytest.mark.skipif(
    VIBER_AUTH is not None,
    reason="With credentials",
)
def test_export_viber(tmp_path: LocalPath) -> None:
    _run_sticker_convert(tmp_path, "viber", None)


def test_export_wastickers(tmp_path: LocalPath) -> None:
    _run_sticker_convert(tmp_path, "whatsapp", "whatsapp")

    wastickers_path = Path(tmp_path, "sticker-convert-test.wastickers")
    assert Path(wastickers_path).is_file()


def test_export_line(tmp_path: LocalPath) -> None:
    _run_sticker_convert(tmp_path, "line", None)


def test_export_kakao(tmp_path: LocalPath) -> None:
    _run_sticker_convert(tmp_path, "kakao", None)


def test_export_xcode_imessage_small(tmp_path: LocalPath) -> None:
    _run_sticker_convert(tmp_path, "imessage_small", "imessage")

    _xcode_asserts(tmp_path)


def test_export_xcode_imessage_medium(tmp_path: LocalPath) -> None:
    _run_sticker_convert(tmp_path, "imessage_medium", "imessage")

    _xcode_asserts(tmp_path)


def test_export_xcode_imessage_large(tmp_path: LocalPath) -> None:
    _run_sticker_convert(tmp_path, "imessage_large", "imessage")

    _xcode_asserts(tmp_path)
