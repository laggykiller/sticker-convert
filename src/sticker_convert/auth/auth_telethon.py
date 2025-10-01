#!/usr/bin/env python3
from typing import Any, Optional, Tuple

import anyio
from telethon import TelegramClient  # type: ignore
from telethon.errors import SessionPasswordNeededError  # type: ignore

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


class AuthTelethon(AuthBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    async def signin_async(self) -> Tuple[bool, TelegramClient, int, str]:
        client = TelegramClient(
            CONFIG_DIR / f"telethon-{self.opt_cred.telethon_api_id}.session",
            self.opt_cred.telethon_api_id,
            self.opt_cred.telethon_api_hash,
        )

        await client.connect()
        authed = await client.is_user_authorized()
        if authed is False:
            msg = "Enter phone number: "
            phone_number = self.cb.put(("ask_str", (msg,), None))
            await client.send_code_request(phone_number)
            msg = "Enter code: "
            code = self.cb.put(("ask_str", (msg,), None))
            try:
                await client.sign_in(phone_number, code)
            except SessionPasswordNeededError:
                password = self.cb.put(
                    (
                        "ask_str",
                        None,
                        {"question": "Enter password: ", "password": True},
                    )
                )
                await client.sign_in(password=password)
            authed = await client.is_user_authorized()

        return (
            authed,
            client,
            self.opt_cred.telethon_api_id,
            self.opt_cred.telethon_api_hash,
        )

    def guide(self) -> None:
        self.cb.put(("ask_str", (GUIDE_MSG,), None))

    def get_api_info(self) -> bool:
        api_id_ask = "Enter api_id: "
        wrong_hint = ""

        while True:
            telethon_api_id = self.cb.put(("ask_str", (wrong_hint + api_id_ask,), None))
            if telethon_api_id == "":
                return False
            elif telethon_api_id.isnumeric():
                self.opt_cred.telethon_api_id = int(telethon_api_id)
                break
            else:
                wrong_hint = "Error: api_id should be numeric\n"

        msg = "Enter api_hash: "
        self.opt_cred.telethon_api_hash = self.cb.put(("ask_str", (msg,), None))

        if self.opt_cred.telethon_api_hash == "":
            return False
        return True

    def signin(self) -> Tuple[bool, TelegramClient, int, str]:
        return anyio.run(self.signin_async)

    def start(self) -> Tuple[bool, Optional[TelegramClient], int, str]:
        cred_valid = False
        if self.opt_cred.telethon_api_id == 0 or self.opt_cred.telethon_api_hash == "":
            self.guide()
            cred_valid = self.get_api_info()
        if cred_valid:
            return self.signin()
        else:
            return False, None, 0, ""

    async def start_async(self) -> Tuple[bool, Optional[TelegramClient], int, str]:
        if self.opt_cred.telethon_api_id == 0 or self.opt_cred.telethon_api_hash == "":
            self.guide()
            self.get_api_info()
        return await self.signin_async()
