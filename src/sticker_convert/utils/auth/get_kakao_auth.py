#!/usr/bin/env python3
import json
import secrets
import uuid
from typing import Any, Callable, Dict, Optional
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from sticker_convert.job_option import CredOption


class GetKakaoAuth:
    def __init__(
        self,
        opt_cred: CredOption,
        cb_msg: Callable[..., None] = print,
        cb_msg_block: Callable[..., Any] = input,
        cb_ask_str: Callable[..., str] = input,
    ) -> None:
        self.username = opt_cred.kakao_username
        self.password = opt_cred.kakao_password
        self.country_code = opt_cred.kakao_country_code
        self.phone_number = opt_cred.kakao_phone_number

        self.cb_msg = cb_msg
        self.cb_msg_block = cb_msg_block
        self.cb_ask_str = cb_ask_str

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

    def login(self) -> bool:
        self.cb_msg("Logging in")

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

        if response_json["status"] != 0:
            self.cb_msg_block(f"Failed at login: {response.text}")
            return False

        self.headers["Ss"] = response.headers["Set-SS"]
        self.country_dicts = response_json["viewData"]["countries"]["all"]

        return True

    def get_country_iso(self) -> bool:
        self.country_iso = None
        for country_dict in self.country_dicts:
            if country_dict["code"] == self.country_code:
                self.country_iso = country_dict["iso"]

        if not self.country_iso:
            self.cb_msg_block("Invalid country code")
            return False

        return True

    def enter_phone(self) -> bool:
        self.cb_msg("Submitting phone number")

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

        if response_json["status"] != 0:
            self.cb_msg_block(f"Failed at entering phone number: {response.text}")
            return False

        self.verify_method = response_json["view"]

        if self.verify_method == "passcode":
            return self.verify_receive_sms()
        if self.verify_method == "mo-send":
            dest_number = response_json["viewData"]["moNumber"]
            msg = response_json["viewData"]["moMessage"]
            return self.verify_send_sms(dest_number, msg)
        self.cb_msg_block(f"Unknown verification method: {response.text}")
        return False

    def verify_send_sms(self, dest_number: str, msg: str) -> bool:
        self.cb_msg("Verification by sending SMS")

        response = requests.post(
            "https://katalk.kakao.com/android/account2/mo-sent", headers=self.headers
        )

        response_json = json.loads(response.text)

        if response_json["status"] != 0:
            self.cb_msg_block(f"Failed at confirm sending SMS: {response.text}")
            return False

        prompt = f"Send this SMS message to number {dest_number} then press enter:"
        self.cb_msg(msg)
        if self.cb_ask_str != input:
            self.cb_ask_str(prompt, initialvalue=msg, cli_show_initialvalue=False)
        else:
            input(prompt)

        response = requests.post(
            "https://katalk.kakao.com/android/account2/mo-confirm", headers=self.headers
        )

        response_json = json.loads(response.text)

        if response_json["status"] != 0:
            self.cb_msg_block(f"Failed at verifying SMS sent: {response.text}")
            return False

        if response_json.get("reason") or "error" in response_json.get("message", ""):
            self.cb_msg_block(f"Failed at verifying SMS sent: {response.text}")
            return False

        self.confirm_url = response_json.get("viewData", {}).get("url")

        return True

    def verify_receive_sms(self) -> bool:
        self.cb_msg("Verification by receiving SMS")

        passcode = self.cb_ask_str("Enter passcode received from SMS:")

        json_data = {
            "passcode": passcode,
        }

        response = requests.post(
            "https://katalk.kakao.com/android/account2/passcode",
            headers=self.headers,
            json=json_data,
        )

        response_json = json.loads(response.text)

        if response_json["status"] != 0:
            self.cb_msg_block(f"Failed at verifying passcode: {response.text}")
            return False

        self.confirm_url = response_json.get("viewData", {}).get("url")

        return True

    def confirm_device_change(self) -> bool:
        self.cb_msg("Confirm device change")

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

        if response_json["status"] != 0:
            self.cb_msg_block(f"Failed at confirm device change: {response.text}")
            return False

        return True

    def passcode_callback(self) -> bool:
        self.cb_msg("Passcode callback")

        response = requests.get(
            "https://katalk.kakao.com/android/account2/passcode/callback",
            headers=self.headers,
        )

        response_json = json.loads(response.text)

        if response_json["status"] != 0:
            self.cb_msg_block(f"Failed at passcode callback: {response.text}")
            return False

        return True

    def skip_restoration(self) -> bool:
        self.cb_msg("Skip restoration")

        response = requests.post(
            "https://katalk.kakao.com/android/account2/skip-restoration",
            headers=self.headers,
        )
        response_json = json.loads(response.text)

        if response_json["status"] != 0:
            self.cb_msg_block(f"Failed at skip restoration: {response.text}")
            return False

        self.nickname = response_json.get("viewData", {}).get("nickname")

        if self.nickname is None:
            self.cb_msg_block(f"Failed at passcode callback: {response.text}")
            return False

        return True

    def get_profile(self) -> bool:
        self.cb_msg("Get profile")

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

        if response_json["status"] != 0:
            self.cb_msg_block(f"Failed at get profile: {response.text}")
            return False

        self.access_token = response_json["signupData"]["oauth2Token"]["accessToken"]

        return True

    def get_cred(self) -> Optional[str]:
        self.cb_msg("Get authorization token")

        authorization_token = None

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
            success = step()
            if not success:
                return None

        authorization_token = self.access_token + "-" + self.device_uuid
        return authorization_token
