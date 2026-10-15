#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from math import ceil
from multiprocessing import cpu_count
from pathlib import Path
from typing import Any


def to_int(i: float | str | None) -> int | None:
    return int(i) if i is not None else None


@dataclass
class BaseOption:
    def merge(self, config: BaseOption) -> None:
        for k, v in vars(config).items():
            if v is not None:
                setattr(self, k, v)

    def __repr__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self) -> dict[str, str]:
        return {}


@dataclass
class InputOption(BaseOption):
    option: str = "local"
    url: str = ""
    dir: Path = Path()

    def to_dict(self) -> dict[Any, Any]:
        return {"option": self.option, "url": self.url, "dir": self.dir.as_posix()}


@dataclass
class CompOption(BaseOption):
    preset: str = "auto"
    size_max_img: int | None = None
    size_max_vid: int | None = None

    format_img: tuple[str, ...] = ()
    format_vid: tuple[str, ...] = ()

    fps_min: int | None = None
    fps_max: int | None = None
    fps_power: float = -0.5

    res_w_min: int | None = None
    res_w_max: int | None = None
    res_h_min: int | None = None
    res_h_max: int | None = None
    res_power: float = 3.0
    res_snap_pow2: bool = False

    quality_min: int | None = None
    quality_max: int | None = None
    quality_power: float = 5.0

    color_min: int | None = None
    color_max: int | None = None
    color_power: float = 3.0

    duration_min: int | None = None
    duration_max: int | None = None
    duration_spoof: bool = False

    bg_color: str | None = None

    padding_percent: int = 0

    steps: int = 1
    fake_vid: bool | None = None
    quantize_method: str | None = None
    scale_filter: str | None = None
    chromium_path: str | None = None
    cache_dir: str | None = None
    default_emoji: str = "😀"
    no_compress: bool | None = None
    processes: int = ceil(cpu_count() / 2)
    animated: bool | None = None

    def to_dict(self) -> dict[Any, Any]:
        return {
            "preset": self.preset,
            "size_max": {"img": self.size_max_img, "vid": self.size_max_vid},
            "format": {"img": self.format_img, "vid": self.format_vid},
            "fps": {"min": self.fps_min, "max": self.fps_max, "power": self.fps_power},
            "res": {
                "w": {"min": self.res_w_min, "max": self.res_w_max},
                "h": {"min": self.res_h_min, "max": self.res_h_max},
                "power": self.res_power,
                "snap_pow2": self.res_snap_pow2,
            },
            "quality": {
                "min": self.quality_min,
                "max": self.quality_max,
                "power": self.quality_power,
            },
            "color": {
                "min": self.color_min,
                "max": self.color_max,
                "power": self.color_power,
            },
            "duration": {
                "min": self.duration_min,
                "max": self.duration_max,
                "spoof": self.duration_spoof,
            },
            "steps": self.steps,
            "bg_color": self.bg_color,
            "padding_percent": self.padding_percent,
            "fake_vid": self.fake_vid,
            "quantize_method": self.quantize_method,
            "scale_filter": self.scale_filter,
            "chromium_path": self.chromium_path,
            "cache_dir": self.cache_dir,
            "default_emoji": self.default_emoji,
            "no_compress": self.no_compress,
            "processes": self.processes,
            "animated": self.animated,
        }

    def get_size_max(self) -> tuple[int | None, int | None]:
        return (self.size_max_img, self.size_max_vid)

    def set_size_max(self, value: int | None) -> None:
        self.size_max_img, self.size_max_vid = to_int(value), to_int(value)

    def get_format(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (self.format_img, self.format_vid)

    def set_format(self, value: tuple[str, ...]) -> None:
        self.format_img, self.format_vid = value, value

    def get_fps(self) -> tuple[int | None, int | None]:
        return (self.fps_min, self.fps_max)

    def set_fps(self, value: int | None) -> None:
        self.fps_min, self.fps_max = to_int(value), to_int(value)

    def get_res(
        self,
    ) -> tuple[tuple[int | None, int | None], tuple[int | None, int | None]]:
        return (self.get_res_w(), self.get_res_h())

    def set_res(self, value: int | None) -> None:
        self.res_w_min = to_int(value)
        self.res_w_max = to_int(value)
        self.res_h_min = to_int(value)
        self.res_h_max = to_int(value)

    def get_res_max(self) -> tuple[int | None, int | None]:
        return (self.res_w_max, self.res_h_max)

    def set_res_max(self, value: int | None) -> None:
        self.res_w_max = to_int(value)
        self.res_h_max = to_int(value)

    def get_res_min(self) -> tuple[int | None, int | None]:
        return (self.res_w_min, self.res_h_min)

    def set_res_min(self, value: int | None) -> None:
        self.res_w_min = to_int(value)
        self.res_h_min = to_int(value)

    def get_res_w(self) -> tuple[int | None, int | None]:
        return (self.res_w_min, self.res_w_max)

    def set_res_w(self, value: int | None) -> None:
        self.res_w_min, self.res_w_max = to_int(value), to_int(value)

    def get_res_h(self) -> tuple[int | None, int | None]:
        return (self.res_h_min, self.res_h_max)

    def set_res_h(self, value: int | None) -> None:
        self.res_h_min, self.res_h_max = to_int(value), to_int(value)

    def get_quality(self) -> tuple[int | None, int | None]:
        return (self.quality_min, self.quality_max)

    def set_quality(self, value: int | None) -> None:
        self.quality_min, self.quality_max = to_int(value), to_int(value)

    def get_color(self) -> tuple[int | None, int | None]:
        return (self.color_min, self.color_max)

    def set_color(self, value: int | None) -> None:
        self.color_min, self.color_max = to_int(value), to_int(value)

    def get_duration(self) -> tuple[int | None, int | None]:
        return (self.duration_min, self.duration_max)

    def set_duration(self, value: int | None) -> None:
        self.duration_min, self.duration_max = to_int(value), to_int(value)

    def get_duration_spoof(self) -> bool:
        return self.duration_spoof

    def set_duration_spoof(self, value: bool):
        self.duration_spoof = value


@dataclass
class OutputOption(BaseOption):
    option: str = "local"
    dir: Path = Path()
    title: str = ""
    author: str = ""

    def to_dict(self) -> dict[Any, Any]:
        return {
            "option": self.option,
            "dir": self.dir.as_posix(),
            "title": self.title,
            "author": self.author,
        }


@dataclass
class CredOption(BaseOption):
    signal_uuid: str = ""
    signal_password: str = ""
    telegram_token: str = ""
    telegram_userid: str = ""
    telethon_api_id: int = 0
    telethon_api_hash: str = ""
    whatsapp_phone_number: str = ""
    line_cookies: str = ""
    viber_auth: str = ""
    discord_token: str = ""
    mastodon_cookies: str = ""
    mastodon_url: str = ""
    misskey_token: str = ""
    misskey_url: str = ""

    def to_dict(self) -> dict[Any, Any]:
        return {
            "signal": {"uuid": self.signal_uuid, "password": self.signal_password},
            "telegram": {"token": self.telegram_token, "userid": self.telegram_userid},
            "telethon": {
                "api_id": self.telethon_api_id,
                "api_hash": self.telethon_api_hash,
            },
            "line": {"cookies": self.line_cookies},
            "viber": {"auth": self.viber_auth},
            "discord": {"token": self.discord_token},
            "mastodon": {"url": self.mastodon_url, "cookies": self.mastodon_cookies},
            "misskey": {"url": self.misskey_url, "token": self.misskey_token},
        }
