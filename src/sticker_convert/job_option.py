#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union


def to_int(i) -> Optional[int]:
    return int(i) if i != None else None

class BaseOption:
    def merge(self, config: "BaseOption"):
        for k, v in vars(config).items():
            if v != None:
                setattr(self, k, v)

class InputOption(BaseOption):
    def __init__(self, input_config_dict: dict):
        self.option: Optional[str] = input_config_dict.get('option')
        self.url: Optional[str] = input_config_dict.get('url')
        self.dir: Path = Path(input_config_dict.get('dir'))
        
    def to_dict(self) -> dict:
        return {
            'option': self.option,
            'url': self.url,
            'dir': self.dir.as_posix()
        }

class CompOption(BaseOption):
    def __init__(self, comp_config_dict: dict):
        self.preset: Optional[str] = comp_config_dict.get('preset')

        size_max: Union[dict, int, None] = comp_config_dict.get('size_max')
        if isinstance(size_max, dict):
            self.size_max_img: Optional[int] = to_int(size_max.get('img'))
            self.size_max_vid: Optional[int] = to_int(size_max.get('vid'))
        else:
            self.size_max_img: Optional[int] = to_int(size_max)
            self.size_max_vid: Optional[int] = to_int(size_max)
        
        fmt: Union[dict, list, str, None] = comp_config_dict.get('format')
        if isinstance(fmt, dict):
            self.format_img: Optional[str] = fmt.get('img')
            self.format_vid: Optional[str] = fmt.get('vid')
        else:
            self.format_img: Optional[str] = fmt
            self.format_vid: Optional[str] = fmt
        
        fps: Union[dict, int, None] = comp_config_dict.get('fps')
        if isinstance(fps, dict):
            self.fps_min: Optional[int] = to_int(fps.get('min'))
            self.fps_max: Optional[int] = to_int(fps.get('max'))
            self.fps_power: float = fps.get('power') if fps.get('power') else -0.5
        else:
            self.fps_min: Optional[int] = to_int(fps)
            self.fps_max: Optional[int] = to_int(fps)
            self.fps_power: float = -0.5
        
        self.res_w_min: Optional[int] = None
        self.res_w_max: Optional[int] = None
        self.res_h_min: Optional[int] = None
        self.res_h_max: Optional[int] = None
        if isinstance(res := comp_config_dict.get('res'), dict):
            if res_w := res.get('w'):
                if isinstance(res_w, dict):
                    self.res_w_min = to_int(res_w.get('min'))
                    self.res_w_max = to_int(res_w.get('max'))
                else:
                    self.res_w_min = res_w
                    self.res_w_max = res_w
            if res_h := res.get('h'):
                if isinstance(res_h, dict):
                    self.res_h_min = to_int(res_h.get('min', res_h))
                    self.res_h_max = to_int(res_h.get('max', res_h))
                else:
                    self.res_h_min = res_h
                    self.res_h_max = res_h
            if res_min := res.get('min'):
                if isinstance(res_min, dict):
                    self.res_w_min = to_int(res_min.get('w', res_min))
                    self.res_h_min = to_int(res_min.get('h', res_min))
                else:
                    self.res_w_min = res_min
                    self.res_h_min = res_min
            if res_max := res.get('max'):
                if isinstance(res_max, dict):
                    self.res_w_max = to_int(res_max.get('w', res_max))
                    self.res_h_max = to_int(res_max.get('h', res_max))
                else:
                    self.res_w_max = res_max
                    self.res_h_max = res_max
            self.res_power: float = res.get('power') if res.get('power') else 3.0
        else:
            self.res_w_min = to_int(res)
            self.res_w_max = to_int(res)
            self.res_h_min = to_int(res)
            self.res_h_max = to_int(res)
            self.res_power: float = 3.0
        
        quality: Union[dict, int, None] = comp_config_dict.get('quality')
        if isinstance(quality, dict):
            self.quality_min: Optional[int] = to_int(quality.get('min'))
            self.quality_max: Optional[int] = to_int(quality.get('max'))
            self.quality_power: float = quality.get('power') if quality.get('power') else 5.0
        else:
            self.quality_min: Optional[int] = to_int(quality)
            self.quality_max: Optional[int] = to_int(quality)
            self.quality_power: float = 5.0
        
        color: Union[dict, int, None] = comp_config_dict.get('color')
        if isinstance(color, dict):
            self.color_min: Optional[int] = to_int(color.get('min'))
            self.color_max: Optional[int] = to_int(color.get('max'))
            self.color_power: float = color.get('power') if color.get('power') else 3.0
        else:
            self.color_min: Optional[int] = to_int(color)
            self.color_max: Optional[int] = to_int(color)
            self.color_power: float = 3.0
        
        duration: Union[dict, int, None] = comp_config_dict.get('duration')
        if isinstance(duration, dict):
            self.duration_min: Optional[int] = to_int(duration.get('min'))
            self.duration_max: Optional[int] = to_int(duration.get('max'))
        else:
            self.duration_min: Optional[int] = to_int(duration)
            self.duration_max: Optional[int] = to_int(duration)
        
        self.steps: Optional[int] = to_int(comp_config_dict.get('steps'))
        self.fake_vid: Optional[bool] = comp_config_dict.get('fake_vid')
        self.quantize_method: Optional[str] = comp_config_dict.get('quantize_method', 'imagequant')
        self.scale_filter: Optional[str] = comp_config_dict.get('scale_filter', 'lanczos')
        self.cache_dir: Optional[str] = comp_config_dict.get('cache_dir')
        self.default_emoji: Optional[str] = comp_config_dict.get('default_emoji')
        self.no_compress: Optional[bool] = comp_config_dict.get('no_compress')
        self.processes: Optional[int] = to_int(comp_config_dict.get('processes'))

        # Only used for format verification
        self.animated: Optional[bool] = comp_config_dict.get('animated')
        self.square: Optional[bool] = comp_config_dict.get('square')

    def to_dict(self) -> dict:
        return {
            'preset': self.preset,
            'size_max': {
                'img': self.size_max_img,
                'vid': self.size_max_vid
            },
            'format': {
                'img': self.format_img,
                'vid': self.format_vid
            },
            'fps': {
                'min': self.fps_min,
                'max': self.fps_max,
                'power': self.fps_power
            },
            'res': {
                'w': {
                    'min': self.res_w_min,
                    'max': self.res_w_max
                },
                'h': {
                    'min': self.res_h_min,
                    'max': self.res_h_max
                },
                'power': self.res_power
            },
            'quality': {
                'min': self.quality_min,
                'max': self.quality_max,
                'power': self.quality_power
            },
            'color': {
                'min': self.color_min,
                'max': self.color_max,
                'power': self.color_power
            },
            'duration': {
                'min': self.duration_min,
                'max': self.duration_max
            },
            'steps': self.steps,
            'fake_vid': self.fake_vid,
            'scale_filter': self.scale_filter,
            'cache_dir': self.cache_dir,
            'default_emoji': self.default_emoji,
            'no_compress': self.no_compress,
            'processes': self.processes,
            'animated': self.animated,
            'square': self.square
        }
        
    @property
    def size_max(self) -> list[Optional[int]]:
        return [self.size_max_img, self.size_max_vid]
    
    @size_max.setter
    def size_max(self, value: Optional[int]):
        self.size_max_img, self.size_max_vid = to_int(value), to_int(value)
        
    @property
    def format(self) -> list[Union[list[str], str, None]]:
        return [self.format_img, self.format_vid]
    
    @format.setter
    def format(self, value: Union[list[str], str, None]):
        self.format_img, self.format_vid = value, value
    
    @property
    def fps(self) -> list[Optional[int]]:
        return [self.fps_min, self.fps_max]
    
    @fps.setter
    def fps(self, value: Optional[int]):
        self.fps_min, self.fps_max = to_int(value), to_int(value)
        
    @property
    def res(self) -> list[Optional[list[Optional[int]]]]:
        return [self.res_w, self.res_h]
    
    @res.setter
    def res(self, value: Optional[int]):
        self.res_w_min = to_int(value)
        self.res_w_max = to_int(value)
        self.res_h_min = to_int(value)
        self.res_h_max = to_int(value)
    
    @property
    def res_w(self) -> list[Optional[int]]:
        return [self.res_w_min, self.res_w_max]
    
    @res_w.setter
    def res_w(self, value: Optional[int]):
        self.res_w_min, self.res_w_max = to_int(value), to_int(value)
    
    @property
    def res_h(self) -> list[Optional[int]]:
        return [self.res_h_min, self.res_h_max]
    
    @res_h.setter
    def res_h(self, value: Optional[int]):
        self.res_h_min, self.res_h_max = to_int(value), to_int(value)
        
    @property
    def quality(self) -> list[Optional[int]]:
        return [self.quality_min, self.quality_max]
    
    @quality.setter
    def quality(self, value: Optional[int]):
        self.quality_min, self.quality_max = to_int(value), to_int(value)
    
    @property
    def color(self) -> list[Optional[int]]:
        return [self.color_min, self.color_max]
    
    @color.setter
    def color(self, value: Optional[int]):
        self.color_min, self.color_max = to_int(value), to_int(value)
    
    @property
    def duration(self) -> list[Optional[int]]:
        return [self.duration_min, self.duration_max]
    
    @duration.setter
    def duration(self, value: Optional[int]):
        self.duration_min, self.duration_max = to_int(value), to_int(value)
    

class OutputOption(BaseOption):
    def __init__(self, output_config_dict: dict):
        self.option: Optional[str] = output_config_dict.get('option')
        self.dir: Optional[Path] = Path(output_config_dict.get('dir'))
        self.title: Optional[str] = output_config_dict.get('title')
        self.author: Optional[str] = output_config_dict.get('author')
    
    def to_dict(self) -> dict:
        return {
            'option': self.option,
            'dir': self.dir.as_posix(),
            'title': self.title,
            'author': self.author
        }
    
class CredOption(BaseOption):
    def __init__(self, cred_config_dict: dict):
        self.signal_uuid: Optional[str] = cred_config_dict.get('signal', {}).get('uuid')
        self.signal_password: Optional[str] = cred_config_dict.get('signal', {}).get('password')
        self.telegram_token: Optional[str] = cred_config_dict.get('telegram', {}).get('token')
        self.telegram_userid: Optional[str] = cred_config_dict.get('telegram', {}).get('userid')
        self.kakao_auth_token: Optional[str] = cred_config_dict.get('kakao', {}).get('auth_token')
        self.kakao_username: Optional[str] = cred_config_dict.get('kakao', {}).get('username')
        self.kakao_password: Optional[str] = cred_config_dict.get('kakao', {}).get('password')
        self.kakao_country_code: Optional[str] = cred_config_dict.get('kakao', {}).get('country_code')
        self.kakao_phone_number: Optional[str] = cred_config_dict.get('kakao', {}).get('phone_number')
        self.line_cookies: Optional[str] = cred_config_dict.get('line', {}).get('cookies')

    def to_dict(self) -> dict:
        return {
            'signal': {
                'uuid': self.signal_uuid,
                'password': self.signal_password
            },
            'telegram': {
                'token': self.telegram_token,
                'userid': self.telegram_userid
            },
            'kakao': {
                'auth_token': self.kakao_auth_token,
                'username': self.kakao_username,
                'password': self.kakao_password,
                'country_code': self.kakao_country_code,
                'phone_number': self.kakao_phone_number
            },
            'line': {
                'cookies': self.line_cookies
            }
        }
