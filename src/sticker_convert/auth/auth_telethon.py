#!/usr/bin/env python3
from typing import Any, Optional, Tuple

import anyio
from telethon import TelegramClient  # type: ignore
from telethon.errors import RPCError, SessionPasswordNeededError  # type: ignore

from sticker_convert.auth.auth_base import AuthBase
from sticker_convert.definitions import CONFIG_DIR

GUIDE_MSG = """1. Visit https://my.telegram.org
2. Login using your phone number
3. Go to "API development tools"
4. Fill form
- App title: sticker-convert
- Short name: sticker-convert
- URL: www.telegram.org
- Platform: Desktop
- Description: sticker-convert
5. Note down api_id and api_hash
Continue when done"""
OK_MSG = "Telethon setup successful"
FAIL_MSG = "Telethon setup failed"


class AuthTelethon(AuthBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    async def signin_async(
        self, try_sign_in: bool = True
    ) -> Tuple[bool, TelegramClient, int, str, str]:
        client = TelegramClient(
            CONFIG_DIR / f"telethon-{self.opt_cred.telethon_api_id}.session",
            self.opt_cred.telethon_api_id,
            self.opt_cred.telethon_api_hash,
        )

        await client.connect()
        authed = await client.is_user_authorized()
        if authed is False and try_sign_in is True:
            error_msg = ""
            while True:
                msg = f"{error_msg}Enter phone number: "
                phone_number = self.cb.put(("ask_str", (msg,), None))
                if phone_number == "":
                    return False, client, 0, "", FAIL_MSG
                try:
                    await client.send_code_request(phone_number)
                    break
                except RPCError as e:
                    error_msg = f"Error: {e}\n"

            error_msg = ""
            while True:
                msg = f"{error_msg}Enter code: "
                code = self.cb.put(("ask_str", (msg,), None))
                if code == "":
                    return False, client, 0, "", FAIL_MSG
                try:
                    await client.sign_in(phone_number, code)
                    break
                except SessionPasswordNeededError:
                    password = self.cb.put(
                        (
                            "ask_str",
                            None,
                            {"question": "Enter password: ", "password": True},
                        )
                    )
                    try:
                        await client.sign_in(password=password)
                        break
                    except RPCError as e:
                        error_msg = f"Error: {e}\n"
                except RPCError as e:
                    error_msg = f"Error: {e}\n"
            authed = await client.is_user_authorized()

        return (
            authed,
            client,
            self.opt_cred.telethon_api_id,
            self.opt_cred.telethon_api_hash,
            OK_MSG if authed else FAIL_MSG,
        )

    def guide(self) -> None:
        self.cb.put(("msg_block", (GUIDE_MSG,), None))

    def get_api_info(self) -> bool:
        api_id_ask = "Enter api_id: "
        wrong_hint = ""

        while True:
            telethon_api_id = self.cb.put(
                (
                    "ask_str",
                    None,
                    {
                        "question": wrong_hint + api_id_ask,
                        "initialvalue": str(self.opt_cred.telethon_api_id),
                    },
                )
            )
            if telethon_api_id == "":
                return False
            elif telethon_api_id.isnumeric():
                self.opt_cred.telethon_api_id = int(telethon_api_id)
                break
            else:
                wrong_hint = "Error: api_id should be numeric\n"

        msg = "Enter api_hash: "
        self.opt_cred.telethon_api_hash = self.cb.put(
            (
                "ask_str",
                None,
                {"question": msg, "initialvalue": self.opt_cred.telethon_api_hash},
            )
        )
        if self.opt_cred.telethon_api_hash == "":
            return False
        return True

    async def start_async(
        self, check_auth_only: bool = False
    ) -> Tuple[bool, Optional[TelegramClient], int, str, str]:
        if self.opt_cred.telethon_api_id != 0 and self.opt_cred.telethon_api_hash != "":
            success, client, api_id, api_hash, msg = await self.signin_async(
                try_sign_in=False
            )
            if check_auth_only:
                client.disconnect()
            if success is True:
                return success, client, api_id, api_hash, msg

        self.guide()
        cred_valid = self.get_api_info()
        if cred_valid:
            success, client, api_id, api_hash, msg = await self.signin_async()
            if check_auth_only:
                client.disconnect()
            return success, client, api_id, api_hash, msg
        else:
            return False, None, 0, "", FAIL_MSG

    def start(
        self, check_auth_only: bool = False
    ) -> Tuple[bool, Optional[TelegramClient], int, str, str]:
        return anyio.run(self.start_async, check_auth_only)
