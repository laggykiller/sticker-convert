#!/usr/bin/env python3
from __future__ import annotations
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
        self.option = input_config_dict.get('option')
        self.url = input_config_dict.get('url')
        self.dir = input_config_dict.get('dir')
        
    def to_dict(self) -> dict:
        return {
            'option': self.option,
            'url': self.url,
            'dir': self.dir
        }

class CompOption(BaseOption):
    def __init__(self, comp_config_dict: dict):
        self.preset = comp_config_dict.get('preset')

        size_max = comp_config_dict.get('size_max')
        if isinstance(size_max, dict):
            self.size_max_img = to_int(size_max.get('img'))
            self.size_max_vid = to_int(size_max.get('vid'))
        else:
            self.size_max_img = to_int(size_max)
            self.size_max_vid = to_int(size_max)
        
        fmt = comp_config_dict.get('format')
        if isinstance(fmt, dict):
            self.format_img = fmt.get('img')
            self.format_vid = fmt.get('vid')
        else:
            self.format_img = fmt
            self.format_vid = fmt
        
        fps = comp_config_dict.get('fps')
        if isinstance(fps, dict):
            self.fps_min = to_int(fps.get('min'))
            self.fps_max = to_int(fps.get('max'))
        else:
            self.fps_min = to_int(fps)
            self.fps_max = to_int(fps)
        
        self.res_w_min = None
        self.res_w_max = None
        self.res_h_min = None
        self.res_h_max = None
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
        else:
            self.res_w_min = to_int(res)
            self.res_w_max = to_int(res)
            self.res_h_min = to_int(res)
            self.res_h_max = to_int(res)
        
        quality = comp_config_dict.get('quality')
        if isinstance(quality, dict):
            self.quality_min = to_int(quality.get('min'))
            self.quality_max = to_int(quality.get('max'))
        else:
            self.quality_min = to_int(quality)
            self.quality_max = to_int(quality)
        
        color = comp_config_dict.get('color')
        if isinstance(color, dict):
            self.color_min = to_int(color.get('min'))
            self.color_max = to_int(color.get('max'))
        else:
            self.color_min = to_int(color)
            self.color_max = to_int(color)
        
        duration = comp_config_dict.get('duration')
        if isinstance(duration, dict):
            self.duration_min = to_int(duration.get('min'))
            self.duration_max = to_int(duration.get('max'))
        else:
            self.duration_min = to_int(duration)
            self.duration_max = to_int(duration)
        
        self.steps = to_int(comp_config_dict.get('steps'))
        self.fake_vid = comp_config_dict.get('fake_vid')
        self.scale_filter = comp_config_dict.get('scale_filter', 'lanczos')
        self.cache_dir = comp_config_dict.get('cache_dir')
        self.default_emoji = comp_config_dict.get('default_emoji')
        self.no_compress = comp_config_dict.get('no_compress')
        self.processes = to_int(comp_config_dict.get('processes'))

        # Only used for format verification
        self.animated = comp_config_dict.get('animated')
        self.square = comp_config_dict.get('square')

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
                'max': self.fps_max
            },
            'res': {
                'w': {
                    'min': self.res_w_min,
                    'max': self.res_w_max
                },
                'h': {
                    'min': self.res_h_min,
                    'max': self.res_h_max
                }
            },
            'quality': {
                'min': self.quality_min,
                'max': self.quality_max
            },
            'color': {
                'min': self.color_min,
                'max': self.color_max
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
        self.option = output_config_dict.get('option')
        self.dir = output_config_dict.get('dir')
        self.title = output_config_dict.get('title')
        self.author = output_config_dict.get('author')
    
    def to_dict(self) -> dict:
        return {
            'option': self.option,
            'dir': self.dir,
            'title': self.title,
            'author': self.author
        }
    
class CredOption(BaseOption):
    def __init__(self, cred_config_dict: dict):
        self.signal_uuid = cred_config_dict.get('signal', {}).get('uuid')
        self.signal_password = cred_config_dict.get('signal', {}).get('password')
        self.telegram_token = cred_config_dict.get('telegram', {}).get('token')
        self.telegram_userid = cred_config_dict.get('telegram', {}).get('userid')
        self.kakao_auth_token = cred_config_dict.get('kakao', {}).get('auth_token')
        self.kakao_username = cred_config_dict.get('kakao', {}).get('username')
        self.kakao_password = cred_config_dict.get('kakao', {}).get('password')
        self.kakao_country_code = cred_config_dict.get('kakao', {}).get('country_code')
        self.kakao_phone_number = cred_config_dict.get('kakao', {}).get('phone_number')
        self.line_cookies = cred_config_dict.get('line', {}).get('cookies')

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
