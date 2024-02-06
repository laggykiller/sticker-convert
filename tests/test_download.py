import os
from pathlib import Path

import pytest

from tests.common import (
    KAKAO_TOKEN,
    LINE_COOKIES,
    PYTHON_EXE,
    SRC_DIR,
    TELEGRAM_TOKEN,
    run_cmd,
)

TEST_DOWNLOAD = os.environ.get("TEST_DOWNLOAD")


def _run_sticker_convert(
    tmp_path: Path,
    source: str,
    url: str,
    expected_file_count: int,
    expected_file_formats: list[str],
    with_title: bool,
    with_author: bool,
    with_emoji: bool,
):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"

    run_cmd(
        cmd=[
            PYTHON_EXE,
            "sticker-convert.py",
            f"--download-{source}",
            url,
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
            "--no-confirm",
            "--author",
            "sticker-convert-test",
            "--title",
            "sticker-convert-test",
        ],
        cwd=SRC_DIR,
    )

    for i in range(expected_file_count):
        for fmt in expected_file_formats:
            fname = Path(str(i).zfill(3) + fmt)
            assert fname in input_dir.iterdir()

    if with_title:
        assert Path("title.txt") in input_dir.iterdir()
    if with_author:
        assert Path("author.txt") in input_dir.iterdir()
    if with_emoji:
        assert Path("emoji.txt") in input_dir.iterdir()


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_signal_static_png(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="signal",
        url="https://signal.art/addstickers/#pack_id=caf8b92fcadce4b7f33ad949f2d8754b&pack_key=decb0e6cdec7683ee2fe54a291aa1e50db19dbab4a063f0cb1610aeda146698c",
        expected_file_count=3,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=True,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_signal_static_webp(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="signal",
        url="https://signal.art/addstickers/#pack_id=8c865ab7218386ceddbb563681634e22&pack_key=0394dfca57e10a34ea70cad834e343d90831c9f69164b03c813575c34873ef8d",
        expected_file_count=3,
        expected_file_formats=[".webp"],
        with_title=True,
        with_author=True,
        with_emoji=True,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_signal_animated_apng(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="signal",
        url="https://signal.art/addstickers/#pack_id=842af30fbf4dc7a502dbe15385e6ceb6&pack_key=4a5d6a5de108dc4eb873d900bf31a70ac312046751475a6c42195dbf7b729d48",
        expected_file_count=3,
        expected_file_formats=[".apng"],
        with_title=True,
        with_author=True,
        with_emoji=True,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_telegram_static_webp(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="telegram",
        url="https://t.me/addstickers/sticker_convert_test_by_laggykillerstickerbot",
        expected_file_count=3,
        expected_file_formats=[".webp"],
        with_title=True,
        with_author=False,
        with_emoji=True,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
@pytest.mark.skipif(not TELEGRAM_TOKEN, reason="No credentials")
def test_download_telegram_animated_webm(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="telegram",
        url="https://t.me/addstickers/sticker_convert_test_animated_by_laggykillerstickerbot",
        expected_file_count=3,
        expected_file_formats=[".webp"],
        with_title=True,
        with_author=False,
        with_emoji=True,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
@pytest.mark.skipif(not TELEGRAM_TOKEN, reason="No credentials")
def test_download_telegram_animated_tgs(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="telegram",
        url="https://telegram.me/addstickers/ColoredCats",
        expected_file_count=30,
        expected_file_formats=[".tgs"],
        with_title=True,
        with_author=False,
        with_emoji=True,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
@pytest.mark.skipif(not TELEGRAM_TOKEN, reason="No credentials")
def test_download_telegram_emoji(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="telegram",
        url="https://t.me/addemoji/ragemojis",
        expected_file_count=39,
        expected_file_formats=[".webp"],
        with_title=True,
        with_author=False,
        with_emoji=True,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_line_static_png_below_775(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="line",
        url="https://store.line.me/stickershop/product/1/en",
        expected_file_count=88,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_line_static_png_no_region_lock(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="line",
        url="https://store.line.me/stickershop/product/26407/",
        expected_file_count=24,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_line_static_png_with_region_lock(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="line",
        url="https://store.line.me/stickershop/product/12320864/zh-Hant",
        expected_file_count=24,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_line_static_png_officialaccount(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="line",
        url="https://store.line.me/officialaccount/event/sticker/27404/zh-Hant",
        expected_file_count=16,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_line_static_png_officialaccount_special(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="line",
        url="https://store.line.me/officialaccount/event/sticker/27239/ja",
        expected_file_count=16,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_line_animated_apng(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="line",
        url="https://store.line.me/stickershop/product/8831/",
        expected_file_count=24,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_line_animated_apng_sound(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="line",
        url="https://store.line.me/stickershop/product/5440/ja",
        expected_file_count=24,
        expected_file_formats=[".png", ".m4a"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_line_animated_apng_popup(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="line",
        url="https://store.line.me/stickershop/product/22229788/ja",
        expected_file_count=24,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_line_animated_apng_popup_foreground(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="line",
        url="https://store.line.me/stickershop/product/14011294/ja",
        expected_file_count=24,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_line_animated_apng_name_text(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="line",
        url="https://store.line.me/stickershop/product/13780/ja",
        expected_file_count=40,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_line_animated_apng_per_sticker_text_no_cookies(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="line",
        url="https://store.line.me/stickershop/product/12188389/ja",
        expected_file_count=24,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
@pytest.mark.skipif(not LINE_COOKIES, reason="No credentials")
def test_download_line_animated_apng_per_sticker_text_with_cookies(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="line",
        url="https://store.line.me/stickershop/product/12188389/ja",
        expected_file_count=24,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_line_static_png_emoji(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="line",
        url="https://store.line.me/emojishop/product/5f290aa26f7dd32fa145906b/ja",
        expected_file_count=40,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_line_animated_apng_emoji(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="line",
        url="https://store.line.me/emojishop/product/6124aa4ae72c607c18108562/ja",
        expected_file_count=40,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_kakao_static_png(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="kakao",
        url="https://e.kakao.com/t/pretty-all-friends",
        expected_file_count=32,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_kakao_animated_gif_store_link_no_token(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="kakao",
        url="https://e.kakao.com/t/lovey-dovey-healing-bear",
        expected_file_count=24,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
@pytest.mark.skipif(not KAKAO_TOKEN, reason="No credentials")
def test_download_kakao_animated_gif_store_link_with_token(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="kakao",
        url="https://e.kakao.com/t/lovey-dovey-healing-bear",
        expected_file_count=24,
        expected_file_formats=[".webp"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )


@pytest.mark.skipif(not TEST_DOWNLOAD, reason="TEST_DOWNLOAD not set")
def test_download_kakao_animated_gif_share_link(tmp_path):  # type: ignore
    _run_sticker_convert(
        tmp_path=tmp_path,  # type: ignore
        source="kakao",
        url="https://emoticon.kakao.com/items/lV6K2fWmU7CpXlHcP9-ysQJx9rg=?referer=share_link",
        expected_file_count=24,
        expected_file_formats=[".png"],
        with_title=True,
        with_author=True,
        with_emoji=False,
    )
