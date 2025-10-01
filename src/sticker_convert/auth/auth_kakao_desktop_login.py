#!/usr/bin/env python3
import base64
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import time
import uuid
from typing import Any, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from sticker_convert.auth.auth_base import AuthBase

OK_MSG = "Login successful, auth_token: {auth_token}"


class AuthKakaoDesktopLogin(AuthBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.username = self.opt_cred.kakao_username
        self.password = self.opt_cred.kakao_password

        if platform.system() == "Darwin":
            self.plat = "mac"
            user_agent_os = "Mc"
            self.os_version = platform.mac_ver()[0]
            version = self.macos_get_ver()
            if version is None:
                version = "25.2.0"
        else:
            self.plat = "win32"
            user_agent_os = "Wd"
            if platform.system() == "Windows":
                self.os_version = platform.uname().version
            else:
                self.os_version = "10.0"
            version = self.windows_get_ver()
            if version is None:
                version = "25.8.2"

        user_agent = f"KT/{version} {user_agent_os}/{self.os_version} en"
        self.headers = {
            "user-agent": user_agent,
            "a": f"{self.plat}/{version}/en",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en",
            "host": "katalk.kakao.com",
            "Connection": "close",
        }

        self.device_name = socket.gethostname()
        if platform.system() != "Darwin":
            self.device_name = self.device_name.upper()
        self.device_uuid = self.get_device_uuid()

        hash = hashlib.sha512(
            f"KLEAL|{self.username}|{self.device_uuid}|LCNUE|{user_agent}".encode(
                "utf-8"
            )
        ).hexdigest()
        xvc = hash[:16]

        self.headers_login = self.headers.copy()
        self.headers_login["x-vc"] = xvc

    def pkcs7_pad(self, m: str) -> str:
        return m + chr(16 - len(m) % 16) * (16 - len(m) % 16)

    def windows_get_ver(self) -> Optional[str]:
        r = requests.get(
            "https://api.github.com/repos/microsoft/winget-pkgs/contents/manifests/k/Kakao/KakaoTalk"
        )
        rjson = json.loads(r.text)
        if len(rjson) == 0:
            return None
        ver = rjson[-1]["name"]
        return ".".join(ver.split(".")[:3])

    def macos_get_ver(self) -> Optional[str]:
        country = "us"
        app_name = "kakaotalk-messenger"
        app_id = "362057947"

        url = f"https://apps.apple.com/{country}/app/{app_name}/id{app_id}"

        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        version_tag = soup.find("p", {"class": re.compile(".*latest__version")})
        version_str = None
        if version_tag is not None:
            version_str = version_tag.text.replace("Version ", "")
        return version_str

    def windows_get_pragma(self, use_wine: bool = False) -> Optional[str]:
        sys_uuid = None
        hdd_model = None
        hdd_serial = None

        if use_wine and shutil.which("wine") is None:
            return None

        regkey = "HKEY_CURRENT_USER\\Software\\Kakao\\KakaoTalk\\DeviceInfo"
        wine = "wine " if use_wine else ""
        cmd = f"{wine}reg query '{regkey}' /v Last"
        last_device_info = subprocess.run(
            cmd, stdout=subprocess.PIPE, shell=True
        ).stdout.decode()
        if "REG_SZ" not in last_device_info:
            return None
        last_device_info = last_device_info.split("\n")[2].split()[2]

        if self.opt_cred.kakao_device_uuid:
            sys_uuid = self.opt_cred.kakao_device_uuid
        else:
            cmd = f"{wine}reg query '{regkey}\\{last_device_info}' /v sys_uuid"
            sys_uuid = subprocess.run(
                cmd, stdout=subprocess.PIPE, shell=True
            ).stdout.decode()
            if "REG_SZ" in sys_uuid:
                sys_uuid = sys_uuid.split("\n")[2].split()[2]

        cmd = f"{wine}reg query '{regkey}\\{last_device_info}' /v hdd_model"
        hdd_model = subprocess.run(
            cmd, stdout=subprocess.PIPE, shell=True
        ).stdout.decode()
        if "REG_SZ" in hdd_model:
            hdd_model = hdd_model.split("\n")[2].split()[2]

        cmd = f"{wine}reg query '{regkey}\\{last_device_info}' /v hdd_serial"
        hdd_serial = subprocess.run(
            cmd, stdout=subprocess.PIPE, shell=True
        ).stdout.decode()
        if "REG_SZ" in hdd_serial:
            hdd_serial = hdd_serial.split("\n")[2].split()[2]

        if sys_uuid and hdd_model and hdd_serial:
            return f"{sys_uuid}|{hdd_model}|{hdd_serial}"
        else:
            return None

    def get_device_uuid(self) -> str:
        if platform.system() == "Darwin":
            cmd = "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID | awk '{print $3}'"
            result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, check=True)
            hwid = result.stdout.decode().strip().replace('"', "")

            hwid_sha1 = bytes.fromhex(hashlib.sha1(hwid.encode()).hexdigest())
            hwid_sha256 = bytes.fromhex(hashlib.sha256(hwid.encode()).hexdigest())

            return base64.b64encode(hwid_sha1 + hwid_sha256).decode()
        else:
            use_wine = True if platform.system != "Windows" else False
            pragma = self.windows_get_pragma(use_wine=use_wine)
            if pragma is None:
                if platform.system == "Windows":
                    if self.opt_cred.kakao_device_uuid:
                        sys_uuid = self.opt_cred.kakao_device_uuid
                    else:
                        cmd = "wmic csproduct get uuid"
                        result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
                        sys_uuid = result.stdout.decode().split("\n")[1].strip()
                    cmd = "wmic diskdrive get Model"
                    result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
                    hdd_model = result.stdout.decode().split("\n")[1].strip()
                    cmd = "wmic diskdrive get SerialNumber"
                    result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
                    hdd_serial = result.stdout.decode().split("\n")[1].strip()
                else:
                    if self.opt_cred.kakao_device_uuid:
                        sys_uuid = self.opt_cred.kakao_device_uuid
                    else:
                        product_uuid_path = "/sys/devices/virtual/dmi/id/product_uuid"
                        sys_uuid = None
                        if os.access(product_uuid_path, os.R_OK):
                            cmd = f"cat {product_uuid_path}"
                            result = subprocess.run(
                                cmd, stdout=subprocess.PIPE, shell=True
                            )
                            if result.returncode == 0:
                                sys_uuid = result.stdout.decode().strip()
                        if sys_uuid is None:
                            sys_uuid = str(uuid.uuid4()).upper()
                            self.opt_cred.kakao_device_uuid = sys_uuid
                    hdd_model = "Wine Disk Drive"
                    hdd_serial = ""
                pragma = f"{sys_uuid}|{hdd_model}|{hdd_serial}"

            aes_key = bytes.fromhex("9FBAE3118FDE5DEAEB8279D08F1D4C79")
            aes_iv = bytes.fromhex("00000000000000000000000000000000")

            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(aes_iv))
            encryptor = cipher.encryptor()
            padded = self.pkcs7_pad(pragma).encode()
            encrypted_pragma = encryptor.update(padded) + encryptor.finalize()
            pragma_hash = hashlib.sha512(encrypted_pragma).digest()

            return base64.b64encode(pragma_hash).decode()

    def login(self, forced: bool = False):
        data = {
            "device_name": self.device_name,
            "device_uuid": self.device_uuid,
            "email": self.username,
            "os_version": self.os_version,
            "password": self.password,
            "permanent": "1",
        }

        if forced:
            data["forced"] = "1"

        headers = self.headers_login.copy()
        headers["content-type"] = "application/x-www-form-urlencoded"
        response = requests.post(
            f"https://katalk.kakao.com/{self.plat}/account/login.json",
            headers=headers,
            data=data,
        )

        return json.loads(response.text)

    def generate_passcode(self):
        data = {
            "password": self.password,
            "permanent": True,
            "device": {
                "name": self.device_name,
                "osVersion": self.os_version,
                "uuid": self.device_uuid,
            },
            "email": self.username,
        }

        if platform.system() == "Darwin":
            cmd = "sysctl -n hw.model"
            result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, check=True)
            data["device"]["model"] = result.stdout.decode().strip()  # type: ignore

        headers = self.headers_login.copy()
        headers["content-type"] = "application/json"
        response = requests.post(
            f"https://katalk.kakao.com/{self.plat}/account/passcodeLogin/generate",
            headers=headers,
            json=data,
        )

        return json.loads(response.text)

    def register_device(self):
        data = {
            "device": {"uuid": self.device_uuid},
            "email": self.username,
            "password": self.password,
        }

        headers = self.headers_login.copy()
        headers["content-type"] = "application/json"
        response = None

        response = requests.post(
            f"https://katalk.kakao.com/{self.plat}/account/passcodeLogin/registerDevice",
            headers=headers,
            json=data,
        )
        return json.loads(response.text)

    def get_cred(self) -> Tuple[Optional[str], str]:
        msg = "Getting Kakao authorization token by desktop login..."
        self.cb.put(("msg_dynamic", (msg,), None))
        rjson = self.login()
        access_token = rjson.get("access_token")
        if access_token is not None:
            auth_token = access_token + "-" + self.device_uuid
            return auth_token, OK_MSG.format(auth_token=auth_token)

        rjson = self.generate_passcode()
        if rjson.get("status") != 0:
            return None, f"Failed to generate passcode: {rjson}"
        passcode = rjson["passcode"]

        fail_reason = None
        self.cb.put(("msg_dynamic", (None,), None))
        while True:
            rjson = self.register_device()
            if rjson["status"] == 0:
                break
            elif rjson["status"] == -110:
                fail_reason = "Timeout"
                break
            elif rjson["status"] != -100:
                fail_reason = str(rjson)
                break
            time_remaining = rjson.get("remainingSeconds")
            next_req_time = rjson.get("nextRequestIntervalInSeconds")
            if time_remaining is None or next_req_time is None:
                fail_reason = str(rjson)
            msg = f"Please enter passcode in Kakao app on mobile device within {time_remaining} seconds: {passcode}"
            msg_dynamic_window_exist = self.cb.put(("msg_dynamic", (msg,), None))
            if msg_dynamic_window_exist is False:
                fail_reason = "Cancelled"
                break
            time.sleep(next_req_time)
        self.cb.put(("msg_dynamic", (None,), None))
        if fail_reason is not None:
            return None, f"Failed to register device: {fail_reason}"

        rjson = self.login()
        if rjson.get("status") == -101:
            rjson = self.login(forced=True)
        access_token = rjson.get("access_token")
        if access_token is None:
            return None, f"Failed to login after registering device: {rjson}"

        auth_token = access_token + "-" + self.device_uuid
        return auth_token, OK_MSG.format(auth_token=auth_token)
