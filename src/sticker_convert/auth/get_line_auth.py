#!/usr/bin/env python3
import json
from typing import Optional

import rookiepy # type: ignore
import requests

class GetLineAuth:
    def get_cred(self) -> Optional[str]:
        cookies_rookie = [c for c in rookiepy.load() if c.domain == 'store.line.me']
        cookies_dict = rookiepy.to_dict(cookies_rookie)
        cookies_jar = rookiepy.to_cookiejar(cookies_rookie)

        if not GetLineAuth.validate_cookies(cookies_jar):
            return None
                
        cookies_list = ['%s=%s' % (i['name'], i['value']) for i in cookies_dict]
        cookies = ';'.join(cookies_list)

        return cookies
    
    @staticmethod
    def validate_cookies(cookies: str) -> bool:
        headers = {
            'x-requested-with': 'XMLHttpRequest',
        }

        params = {
            'text': 'test'
        }

        response = requests.get(
            'https://store.line.me/api/custom-sticker/validate/13782/en',
            params=params,
            cookies=cookies, # type: ignore[arg-type]
            headers=headers,
        )

        response_dict = json.loads(response.text)

        if response_dict['errorMessage']:
            return False
        else:
            return True