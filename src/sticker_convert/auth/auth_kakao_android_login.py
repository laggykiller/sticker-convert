#!/usr/bin/env python3
import json
import secrets
import uuid
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from sticker_convert.auth.auth_base import AuthBase

OK_MSG = "Got auth_token successfully:\n{auth_token=}\n"


class AuthKakaoAndroidLogin(AuthBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.username = self.opt_cred.kakao_username
        self.password = self.opt_cred.kakao_password
        self.country_code = self.opt_cred.kakao_country_code
        self.phone_number = self.opt_cred.kakao_phone_number

        self.device_uuid = secrets.token_hex(32)
        self.device_ssaid = secrets.token_hex(20)
        self.uuid_c = str(uuid.uuid4())
        self.device_info = (
            f"android/30; uuid={self.device_uuid}; ssaid={self.device_ssaid}; "
            + "model=SDK_GPHONE_X86_64; screen_resolution=1080x1920; sim=310260/1/us; onestore=false; uvc3=null"
        )
        self.app_platform = "android"
        self.app_version_number = self.get_version()
        self.app_language = "en"
        self.app_version = (
            f"{self.app_platform}/{self.app_version_number}/{self.app_language}"
        )

        self.headers = {
            "Host": "katalk.kakao.com",
            "Accept-Language": "en",
            "User-Agent": f"KT/{self.app_version_number} An/11 en",
            "Device-Info": self.device_info,
            "A": self.app_version,
            "C": self.uuid_c,
            "Content-Type": "application/json",
            "Connection": "close",
        }

    def get_version(self) -> str:
        # It is difficult to get app version number from Google Play
        r = requests.get(
            "https://apkpure.net/kakaotalk-messenger/com.kakao.talk/versions"
        )
        soup = BeautifulSoup(r.text, "html.parser")
        for li in soup.find_all("li"):
            a = li.find("a", class_="dt-version-icon")
            if a is None:
                continue
            if "/kakaotalk-messenger/com.kakao.talk/download/" in a.get("href", ""):
                return a.get("href").split("/")[-1]
        return "25.2.1"

    def login(self) -> Tuple[bool, str]:
        msg = "Getting Kakao authorization token by Android login: Logging in"
        self.cb.put(("msg_dynamic", (msg,), None))

        json_data = {
            "id": self.username,
            "password": self.password,
        }

        response = requests.post(
            "https://katalk.kakao.com/android/account2/login",
            headers=self.headers,
            json=json_data,
        )

        response_json = json.loads(response.text)

        self.cb.put(("msg_dynamic", (None,), None))
        if response_json["status"] != 0:
            return False, f"Failed at login: {response.text}"

        self.headers["Ss"] = response.headers["Set-SS"]
        self.country_dicts = response_json["viewData"]["countries"]["all"]

        return True, ""

    def get_country_iso(self) -> Tuple[bool, str]:
        self.country_iso = None
        for country_dict in self.country_dicts:
            if country_dict["code"] == self.country_code:
                self.country_iso = country_dict["iso"]

        if not self.country_iso:
            return False, "Invalid country code"

        return True, ""

    def enter_phone(self) -> Tuple[bool, str]:
        msg = "Getting Kakao authorization token by Android login: Submitting phone number"
        self.cb.put(("msg_dynamic", (msg,), None))

        json_data: Dict[str, Any] = {
            "countryCode": self.country_code,
            "countryIso": self.country_iso,
            "phoneNumber": self.phone_number,
            "termCodes": [],
            "simPhoneNumber": f"+{self.country_code}{self.phone_number}",
        }

        response = requests.post(
            "https://katalk.kakao.com/android/account2/phone-number",
            headers=self.headers,
            json=json_data,
        )

        response_json = json.loads(response.text)

        self.cb.put(("msg_dynamic", (None,), None))
        if response_json["status"] != 0:
            return False, f"Failed at entering phone number: {response.text}"

        self.verify_method = response_json["view"]

        if self.verify_method == "passcode":
            return self.verify_receive_sms()
        if self.verify_method == "mo-send":
            dest_number = response_json["viewData"]["moNumber"]
            msg = response_json["viewData"]["moMessage"]
            return self.verify_send_sms(dest_number, msg)
        return False, f"Unknown verification method: {response.text}"

    def verify_send_sms(self, dest_number: str, verify_msg: str) -> Tuple[bool, str]:
        response = requests.post(
            "https://katalk.kakao.com/android/account2/mo-sent", headers=self.headers
        )

        response_json = json.loads(response.text)

        if response_json["status"] != 0:
            return False, f"Failed at confirm sending SMS: {response.text}"

        prompt = f"Send this SMS message to number {dest_number} then press enter:"
        self.cb.put(
            (
                "ask_str",
                None,
                {
                    "msg": prompt,
                    "initialvalue": verify_msg,
                    "cli_show_initialvalue": False,
                },
            )
        )

        response = requests.post(
            "https://katalk.kakao.com/android/account2/mo-confirm", headers=self.headers
        )

        response_json = json.loads(response.text)

        if response_json["status"] != 0:
            return False, f"Failed at verifying SMS sent: {response.text}"

        if response_json.get("reason") or "error" in response_json.get("message", ""):
            return False, f"Failed at verifying SMS sent: {response.text}"

        self.confirm_url = response_json.get("viewData", {}).get("url")

        return True, ""

    def verify_receive_sms(self) -> Tuple[bool, str]:
        msg = "Enter passcode received from SMS:"
        passcode = self.cb.put(("ask_str", (msg,), None))

        json_data = {
            "passcode": passcode,
        }

        response = requests.post(
            "https://katalk.kakao.com/android/account2/passcode",
            headers=self.headers,
            json=json_data,
        )

        response_json = json.loads(response.text)

        self.cb.put(("msg_dynamic", (None,), None))
        if response_json["status"] != 0:
            return False, f"Failed at verifying passcode: {response.text}"

        self.confirm_url = response_json.get("viewData", {}).get("url")

        return True, ""

    def confirm_device_change(self) -> Tuple[bool, str]:
        msg = (
            "Getting Kakao authorization token by Android login: Confirm device change"
        )
        self.cb.put(("msg_dynamic", (msg,), None))

        confirm_url_parsed = urlparse(self.confirm_url)  # type: ignore
        confirm_url_qs = parse_qs(confirm_url_parsed.query)  # type: ignore
        session_token: str = confirm_url_qs["sessionToken"][0]  # type: ignore

        headers_browser = {
            "Host": "katalk.kakao.com",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Linux; Android 11; Android SDK built for x86 Build/RSR1.210210.001.A1; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.106 Mobile Safari/537.36;KAKAOTALK 2410030",
            "Content-Type": "application/json",
            "Origin": "https://katalk.kakao.com",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": self.confirm_url,
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "close",
        }

        json_data: Dict[str, str] = {
            "decision": "continue",
            "lang": self.app_language,
            "sessionToken": session_token,
            "appVersion": self.app_version_number,
        }

        response = requests.post(
            "https://katalk.kakao.com/android/account2/confirm-device-change",
            headers=headers_browser,
            json=json_data,
        )

        response_json = json.loads(response.text)

        self.cb.put(("msg_dynamic", (None,), None))
        if response_json["status"] != 0:
            return False, f"Failed at confirm device change: {response.text}"

        return True, ""

    def passcode_callback(self) -> Tuple[bool, str]:
        msg = "Getting Kakao authorization token by Android login: Passcode callback"
        self.cb.put(("msg_dynamic", (msg,), None))

        response = requests.get(
            "https://katalk.kakao.com/android/account2/passcode/callback",
            headers=self.headers,
        )

        response_json = json.loads(response.text)

        self.cb.put(("msg_dynamic", (None,), None))
        if response_json["status"] != 0:
            return False, f"Failed at passcode callback: {response.text}"

        return True, ""

    def skip_restoration(self) -> Tuple[bool, str]:
        msg = "Getting Kakao authorization token by Android login: Skip restoration"
        self.cb.put(("msg_dynamic", (msg,), None))

        response = requests.post(
            "https://katalk.kakao.com/android/account2/skip-restoration",
            headers=self.headers,
        )
        response_json = json.loads(response.text)

        if response_json["status"] != 0:
            return False, f"Failed at skip restoration: {response.text}"

        self.nickname = response_json.get("viewData", {}).get("nickname")

        self.cb.put(("msg_dynamic", (None,), None))
        if self.nickname is None:
            return False, f"Failed at passcode callback: {response.text}"

        return True, ""

    def get_profile(self) -> Tuple[bool, str]:
        msg = "Getting Kakao authorization token by Android login: Get profile"
        self.cb.put(("msg_dynamic", (msg,), None))

        json_data = {
            "nickname": self.nickname,
            "profileImageFlag": 1,
            "friendAutomation": True,
        }

        response = requests.post(
            "https://katalk.kakao.com/android/account2/profile",
            headers=self.headers,
            json=json_data,
        )

        response_json = json.loads(response.text)

        self.cb.put(("msg_dynamic", (None,), None))
        if response_json["status"] != 0:
            return False, f"Failed at get profile: {response.text}"

        self.access_token = response_json["signupData"]["oauth2Token"]["accessToken"]

        return True, ""

    def get_cred(self) -> Tuple[Optional[str], str]:
        auth_token = None

        steps = (
            self.login,
            self.get_country_iso,
            self.enter_phone,
            self.confirm_device_change,
            self.passcode_callback,
            self.skip_restoration,
            self.get_profile,
        )

        for step in steps:
            success, msg = step()
            if not success:
                return None, msg

        auth_token = self.access_token + "-" + self.device_uuid
        return auth_token, OK_MSG.format(auth_token=auth_token)
