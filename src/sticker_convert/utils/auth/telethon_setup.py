#!/usr/bin/env python3
from typing import Callable, Optional, Tuple

import anyio
from telethon import TelegramClient  # type: ignore
from telethon.errors import SessionPasswordNeededError  # type: ignore

from sticker_convert.definitions import CONFIG_DIR
from sticker_convert.job_option import CredOption

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


class TelethonSetup:
    def __init__(
        self, opt_cred: CredOption, cb_ask_str: Callable[..., str] = input
    ) -> None:
        self.cb_ask_str = cb_ask_str
        self.opt_cred = opt_cred

    async def signin_async(self) -> Tuple[bool, TelegramClient, int, str]:
        client = TelegramClient(
            CONFIG_DIR / f"telethon-{self.opt_cred.telethon_api_id}.session",
            self.opt_cred.telethon_api_id,
            self.opt_cred.telethon_api_hash,
        )

        await client.connect()
        authed = await client.is_user_authorized()
        if authed is False:
            phone_number = self.cb_ask_str("Enter phone number: ")
            await client.send_code_request(phone_number)
            code = self.cb_ask_str("Enter code: ")
            try:
                await client.sign_in(phone_number, code)
            except SessionPasswordNeededError:
                password = self.cb_ask_str("Enter password: ")
                await client.sign_in(password=password)
            authed = await client.is_user_authorized()

        return (
            authed,
            client,
            self.opt_cred.telethon_api_id,
            self.opt_cred.telethon_api_hash,
        )

    def guide(self) -> None:
        self.cb_ask_str(GUIDE_MSG)

    def get_api_info(self) -> bool:
        api_id_ask = "Enter api_id: "
        wrong_hint = ""

        while True:
            telethon_api_id = self.cb_ask_str(wrong_hint + api_id_ask)
            if telethon_api_id == "":
                return False
            elif telethon_api_id.isnumeric():
                self.opt_cred.telethon_api_id = int(telethon_api_id)
                break
            else:
                wrong_hint = "Error: api_id should be numeric\n"

        self.opt_cred.telethon_api_hash = self.cb_ask_str("Enter api_hash: ")
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
