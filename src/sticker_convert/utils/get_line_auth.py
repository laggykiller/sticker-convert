#!/usr/bin/env python3
import json

import browser_cookie3
import requests

class GetLineAuth:
    def get_cred(self):
        cookies_jar = browser_cookie3.load(domain_name='store.line.me')

        if not GetLineAuth.validate_cookies(cookies_jar):
            return

        cookies_dict = requests.utils.dict_from_cookiejar(cookies_jar)
        cookies_list = ['%s=%s' % (name, value) for (name, value) in cookies_dict.items()]
        cookies = ';'.join(cookies_list)

        return cookies
    
    @staticmethod
    def validate_cookies(cookies):
        headers = {
            'x-requested-with': 'XMLHttpRequest',
        }

        params = {
            'text': 'test'
        }

        response = requests.get(
            'https://store.line.me/api/custom-sticker/validate/13782/en',
            params=params,
            cookies=cookies,
            headers=headers,
        )

        response_dict = json.loads(response.text)

        if response_dict['errorMessage']:
            return False
        else:
            return True