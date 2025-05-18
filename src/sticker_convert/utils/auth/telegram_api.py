#!/usr/bin/env python3
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union, cast

import anyio
from telegram import InputSticker, PhotoSize, Sticker
from telegram import StickerSet as TGStickerSet
from telegram.error import BadRequest, TelegramError
from telegram.ext import AIORateLimiter, ApplicationBuilder
from telethon.errors.rpcerrorlist import StickersetInvalidError  # type: ignore
from telethon.functions import messages  # type: ignore
from telethon.tl.types.messages import StickerSet as TLStickerSet  # type: ignore
from telethon.types import DocumentAttributeFilename, InputStickerSetShortName, InputStickerSetThumb, Message, TypeDocument  # type: ignore

from sticker_convert.job_option import CredOption
from sticker_convert.utils.auth.telethon_setup import TelethonSetup
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn

# sticker_path: Path, sticker_bytes: bytes, emoji_list: List[str], sticker_format: str
TelegramSticker = Tuple[Path, bytes, List[str], str]


class TelegramAPI(Protocol):
    async def setup(
        self,
        opt_cred: CredOption,
        is_upload: bool,
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> bool: ...
    async def exit(self) -> None: ...
    async def set_upload_pack_type(self, is_emoji: bool) -> None: ...
    async def set_upload_pack_short_name(self, pack_title: str) -> str: ...
    async def check_pack_exist(self) -> bool: ...
    async def pack_del(self) -> bool: ...
    async def pack_new(
        self, stickers_list: List[TelegramSticker], sticker_type: str
    ) -> Tuple[int, int]: ...
    async def pack_add(
        self, stickers_list: List[TelegramSticker], sticker_type: str
    ) -> Tuple[int, int]: ...
    async def pack_thumbnail(self, thumbnail: TelegramSticker) -> bool: ...
    async def get_pack_url(self) -> str: ...
    async def pack_dl(
        self, pack_short_name: str, out_dir: Path
    ) -> Tuple[Dict[str, bool], Dict[str, str]]: ...


class BotAPI(TelegramAPI):
    async def setup(
        self,
        opt_cred: CredOption,
        is_upload: bool,
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> bool:
        self.timeout = 30
        self.cb = cb

        if is_upload and not (opt_cred.telegram_token and opt_cred.telegram_userid):
            self.cb.put("Token and userid required for uploading to telegram")
            return False
        elif is_upload is False and not opt_cred.telegram_token:
            self.cb.put("Token required for downloading from telegram")
            return False

        if opt_cred.telegram_userid.isnumeric():
            self.telegram_userid = int(opt_cred.telegram_userid)
        else:
            self.cb.put("Invalid userid, should contain numbers only")
            return False

        self.application = (  # type: ignore
            ApplicationBuilder()
            .token(opt_cred.telegram_token)
            .rate_limiter(AIORateLimiter(overall_max_rate=4, max_retries=3))
            .connect_timeout(self.timeout)
            .pool_timeout(self.timeout)
            .read_timeout(self.timeout)
            .write_timeout(self.timeout)
            .build()
        )
        await self.application.initialize()

        return True

    async def exit(self) -> None:
        await self.application.shutdown()

    async def set_upload_pack_short_name(self, pack_title: str) -> str:
        self.pack_title = pack_title
        bot_name = self.application.bot.name
        self.pack_short_name = (
            pack_title.replace(" ", "_") + "_by_" + bot_name.replace("@", "")
        )
        self.pack_short_name = re.sub(
            "[^0-9a-zA-Z]+", "_", self.pack_short_name
        )  # name used in url, only alphanum and underscore only
        return self.pack_short_name

    async def set_upload_pack_type(self, is_emoji: bool) -> None:
        self.is_emoji = is_emoji

    async def check_pack_exist(self) -> bool:
        sticker_set: Any = None
        try:
            sticker_set = await self.application.bot.get_sticker_set(
                self.pack_short_name,
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30,
                pool_timeout=30,
            )
        except TelegramError:
            pass

        if sticker_set is not None:
            return True
        return False

    async def pack_del(self) -> bool:
        try:
            await self.application.bot.delete_sticker_set(self.pack_short_name)
        except BadRequest as e:
            msg = f"Cannot delete sticker set {self.pack_short_name} due to {e}"
            if str(e) == "Stickerpack_not_found":
                msg += "\nHint: You might had deleted and recreated pack too quickly. Wait about 3 minutes and try again."
            self.cb.put(msg)
            return False
        except TelegramError as e:
            self.cb.put(f"Cannot delete sticker set {self.pack_short_name} due to {e}")
            return False
        return True

    async def pack_new(
        self, stickers_list: List[TelegramSticker], sticker_type: str
    ) -> Tuple[int, int]:
        init_input_stickers: List[InputSticker] = []
        for i in stickers_list[:50]:
            init_input_stickers.append(
                InputSticker(
                    sticker=i[1],
                    emoji_list=i[2],
                    format=i[3],
                )
            )

        try:
            self.cb.put(
                f"Creating pack and bulk uploading {len(init_input_stickers)} stickers of {self.pack_short_name}"
            )
            await self.application.bot.create_new_sticker_set(
                self.telegram_userid,
                self.pack_short_name,
                self.pack_title,
                init_input_stickers,
                sticker_type,
            )
            self.cb.put(
                f"Created pack and bulk uploaded {len(init_input_stickers)} stickers of {self.pack_short_name}"
            )
            _, success_add = await self.pack_add(stickers_list[50:], sticker_type)
            return len(stickers_list), len(init_input_stickers) + success_add
        except TelegramError as e:
            self.cb.put(
                f"Cannot create pack and bulk upload {len(init_input_stickers)} stickers of {self.pack_short_name} due to {e}"
            )
            return len(stickers_list), 0

    async def pack_add(
        self, stickers_list: List[TelegramSticker], sticker_type: str
    ) -> Tuple[int, int]:
        stickers_ok = 0
        self.cb.put(
            (
                "bar",
                None,
                {
                    "set_progress_mode": "determinate",
                    "steps": len(stickers_list),
                },
            )
        )
        for i in stickers_list:
            input_sticker = InputSticker(
                sticker=i[1],
                emoji_list=i[2],
                format=i[3],
            )
            try:
                # We could use tg.start_soon() here
                # But this would disrupt the order of stickers
                await self.application.bot.add_sticker_to_set(
                    self.telegram_userid,
                    self.pack_short_name,
                    input_sticker,
                )
                self.cb.put(f"Uploaded sticker {i[0]} of {self.pack_short_name}")
                stickers_ok += 1
            except BadRequest as e:
                self.cb.put(
                    f"Cannot upload sticker {i[0]} of {self.pack_short_name} due to {e}"
                )
                if str(e) == "Stickerpack_not_found":
                    self.cb.put(
                        "Hint: You might had deleted and recreated pack too quickly. Wait about 3 minutes and try again."
                    )
            except TelegramError as e:
                self.cb.put(
                    f"Cannot upload sticker {i[0]} of {self.pack_short_name} due to {e}"
                )
            self.cb.put("update_bar")

        self.cb.put(("bar", None, {"set_progress_mode": "indeterminate"}))
        return len(stickers_list), stickers_ok

    async def pack_thumbnail(self, thumbnail: TelegramSticker) -> bool:
        try:
            self.cb.put(f"Uploading cover (thumbnail) of pack {self.pack_short_name}")
            await self.application.bot.set_sticker_set_thumbnail(
                self.pack_short_name,
                self.telegram_userid,
                thumbnail[3],
                thumbnail[1],
            )
            self.cb.put(f"Uploaded cover (thumbnail) of pack {self.pack_short_name}")
            return True
        except TelegramError as e:
            self.cb.put(
                f"Cannot upload cover (thumbnail) of pack {self.pack_short_name} due to {e}"
            )
            return False

    async def get_pack_url(self) -> str:
        if self.is_emoji:
            return f"https://t.me/addemoji/{self.pack_short_name}"
        else:
            return f"https://t.me/addstickers/{self.pack_short_name}"

    async def _download_sticker(
        self,
        sticker: Union[PhotoSize, Sticker],
        f_id: str,
        out_dir: Path,
        results: Dict[str, bool],
        emoji_dict: Dict[str, str],
    ) -> None:
        try:
            sticker_file = await sticker.get_file(
                read_timeout=self.timeout,
                write_timeout=self.timeout,
                connect_timeout=self.timeout,
                pool_timeout=self.timeout,
            )
        except TelegramError as e:
            self.cb.put(f"Failed to download {f_id}: {str(e)}")
            results[f_id] = False
            return
        fpath = sticker_file.file_path
        assert fpath is not None
        ext = Path(fpath).suffix
        f_name = f_id + ext
        f_path = Path(out_dir, f_name)
        await sticker_file.download_to_drive(
            custom_path=f_path,
            read_timeout=self.timeout,
            write_timeout=self.timeout,
            connect_timeout=self.timeout,
            pool_timeout=self.timeout,
        )
        if isinstance(sticker, Sticker) and sticker.emoji is not None:
            emoji_dict[f_id] = sticker.emoji
        self.cb.put(f"Downloaded {f_name}")
        results[f_id] = True
        if f_id != "cover":
            self.cb.put("update_bar")

    async def pack_dl(
        self, pack_short_name: str, out_dir: Path
    ) -> Tuple[Dict[str, bool], Dict[str, str]]:
        results: Dict[str, bool] = {}
        emoji_dict: Dict[str, str] = {}

        try:
            sticker_set: TGStickerSet = await self.application.bot.get_sticker_set(
                pack_short_name,
                read_timeout=self.timeout,
                write_timeout=self.timeout,
                connect_timeout=self.timeout,
                pool_timeout=self.timeout,
            )
        except TelegramError as e:
            self.cb.put(
                f"Failed to download telegram sticker set {pack_short_name} due to: {e}"
            )
            return results, emoji_dict

        self.cb.put(
            (
                "bar",
                None,
                {
                    "set_progress_mode": "determinate",
                    "steps": len(sticker_set.stickers),
                },
            )
        )

        async with anyio.create_task_group() as tg:
            for num, sticker in enumerate(sticker_set.stickers):
                f_id = str(num).zfill(3)
                tg.start_soon(
                    self._download_sticker, sticker, f_id, out_dir, results, emoji_dict
                )

            if sticker_set.thumbnail is not None:
                results_thumb: Dict[str, bool] = {}
                tg.start_soon(
                    self._download_sticker,
                    sticker_set.thumbnail,
                    "cover",
                    out_dir,
                    results_thumb,
                    emoji_dict,
                )

        return results, emoji_dict


class TelethonAPI(TelegramAPI):
    async def setup(
        self,
        opt_cred: CredOption,
        is_upload: bool,
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> bool:
        self.opt_cred = opt_cred
        self.cb = cb
        self.cb_return = cb_return

        success, client, _, _ = await TelethonSetup(
            self.opt_cred, self.cb_ask_str
        ).start_async()

        if success is True and client is not None:
            self.client = client
        return success

    async def exit(self) -> None:
        self.client.disconnect()

    def cb_ask_str(
        self, msg: Optional[str] = None, initialvalue: Optional[str] = None
    ) -> str:
        self.cb.put(("ask_str", (msg,), None))
        response = self.cb_return.get_response()

        assert isinstance(response, str)
        return response

    async def set_upload_pack_short_name(self, pack_title: str) -> str:
        self.pack_title = pack_title
        self.pack_short_name = re.sub(
            "[^0-9a-zA-Z]+", "_", pack_title
        )  # name used in url, only alphanum and underscore only
        return self.pack_short_name

    async def set_upload_pack_type(self, is_emoji: bool) -> None:
        self.is_emoji = is_emoji

    async def check_pack_exist(self) -> bool:
        try:
            await self.client(
                messages.GetStickerSetRequest(
                    InputStickerSetShortName(self.pack_short_name), 0
                )
            )
        except StickersetInvalidError:
            return False

        return True

    async def _send_and_recv(self, msg: Union[str, Path]) -> str:
        if isinstance(msg, str):
            sent_message = await self.client.send_message("Stickers", msg)
        else:
            sent_message = cast(
                Message,
                await self.client.send_file("Stickers", msg, force_document=True),  # type: ignore
            )

        for _ in range(5):
            # https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this
            # In a single chat, avoid sending more than one message per second.
            time.sleep(1)
            last_message = cast(
                List[Message],
                await self.client.get_messages("Stickers", 1),  # type: ignore
            )[0]
            if sent_message.id != last_message.id:
                return last_message.message

        return "timeout"

    async def pack_del(self) -> bool:
        msg_fail = "Cannot delete pack of {} due to {}"
        if self.is_emoji:
            repl = await self._send_and_recv("/delemoji")
        else:
            repl = await self._send_and_recv("/delpack")
        if repl != "Choose the sticker set you want to delete.":
            self.cb.put(msg_fail.format(self.pack_short_name, repl))
            return False
        repl = await self._send_and_recv(self.pack_short_name)
        if "Yes, I am totally sure." not in repl:
            self.cb.put(msg_fail.format(self.pack_short_name, repl))
            return False
        repl = await self._send_and_recv("Yes, I am totally sure.")
        if "Done!" not in repl:
            self.cb.put(msg_fail.format(self.pack_short_name, repl))
            return False

        return True

    async def pack_new(
        self, stickers_list: List[TelegramSticker], sticker_type: str
    ) -> Tuple[int, int]:
        stickers_ok = 0
        if self.is_emoji:
            repl = await self._send_and_recv("/newpack")
        elif stickers_list[0][3] == "static":
            repl = await self._send_and_recv("/newsticker")
        elif stickers_list[0][3] == "video":
            repl = await self._send_and_recv("/newvideo")
        elif stickers_list[0][3] == "animated":
            repl = await self._send_and_recv("/newanimated")
        else:
            self.cb.put(
                f"Cannot upload any sticker to {self.pack_short_name} due to invalid sticker format {stickers_list[0][3]}"
            )
            return len(stickers_list), 0
        if "Yay!" not in repl:
            self.cb.put(f"Cannot upload any sticker due to {repl}")
            return len(stickers_list), 0

        if self.is_emoji:
            repl = await self._send_and_recv(
                f"{stickers_list[0][3].capitalize()} emoji"
            )
            if "Yay!" not in repl:
                self.cb.put(f"Cannot upload any sticker due to {repl}")
                return len(stickers_list), 0

        repl = await self._send_and_recv(self.pack_title)
        if "Alright!" not in repl:
            self.cb.put(f"Cannot upload any sticker due to {repl}")
            return len(stickers_list), 0
        self.cb.put(
            (
                "bar",
                None,
                {
                    "set_progress_mode": "determinate",
                    "steps": len(stickers_list),
                },
            )
        )
        for i in stickers_list:
            repl = await self._send_and_recv(i[0])
            if "Thanks!" not in repl:
                self.cb.put(
                    f"Cannot upload sticker {i[0]} of {self.pack_short_name} due to {repl}"
                )
                self.cb.put("update_bar")
                continue
            repl = await self._send_and_recv("".join(i[2]))
            if "Congratulations." not in repl:
                self.cb.put(
                    f"Cannot upload sticker {i[0]} of {self.pack_short_name} due to {repl}"
                )
                self.cb.put("update_bar")
                continue
            stickers_ok += 1
            self.cb.put("update_bar")
        repl = await self._send_and_recv("/publish")
        if "icon" not in repl:
            self.cb.put(f"Cannot upload pack {self.pack_short_name} due to {repl}")
            return len(stickers_list), 0
        repl = await self._send_and_recv("/skip")
        if "Please provide a short name" not in repl:
            self.cb.put(f"Cannot upload pack {self.pack_short_name} due to {repl}")
            return len(stickers_list), 0
        repl = await self._send_and_recv(self.pack_short_name)
        if "Kaboom!" not in repl:
            self.cb.put(f"Cannot upload pack {self.pack_short_name} due to {repl}")
            return len(stickers_list), 0

        self.cb.put(("bar", None, {"set_progress_mode": "indeterminate"}))

        return len(stickers_list), stickers_ok

    async def pack_add(
        self, stickers_list: List[TelegramSticker], sticker_type: str
    ) -> Tuple[int, int]:
        stickers_ok = 0
        if self.is_emoji:
            repl = await self._send_and_recv("/addemoji")
        else:
            repl = await self._send_and_recv("/addsticker")
        if "Choose" not in repl:
            self.cb.put(
                f"Cannot upload any sticker to {self.pack_short_name} due to {repl}"
            )
            return len(stickers_list), 0
        repl = await self._send_and_recv(self.pack_short_name)
        if "Alright!" not in repl:
            self.cb.put(
                f"Cannot upload any sticker to {self.pack_short_name} due to {repl}"
            )
            return len(stickers_list), 0

        self.cb.put(
            (
                "bar",
                None,
                {
                    "set_progress_mode": "determinate",
                    "steps": len(stickers_list),
                },
            )
        )
        for i in stickers_list:
            repl = await self._send_and_recv(i[0])
            if "Thanks!" not in repl:
                self.cb.put(
                    f"Cannot upload sticker {i[0]} of {self.pack_short_name} due to {repl}"
                )
                self.cb.put("update_bar")
                continue
            repl = await self._send_and_recv("".join(i[2]))
            if "There we go." not in repl:
                self.cb.put(
                    f"Cannot upload sticker {i[0]} of {self.pack_short_name} due to {repl}"
                )
                self.cb.put("update_bar")
                continue
            self.cb.put("update_bar")
            stickers_ok += 1

        self.cb.put(("bar", None, {"set_progress_mode": "indeterminate"}))

        repl = await self._send_and_recv("/done")
        if "OK" not in repl:
            self.cb.put(
                f"Cannot upload any sticker to {self.pack_short_name} due to {repl}"
            )
            return len(stickers_list), 0

        return len(stickers_list), stickers_ok

    async def pack_thumbnail(self, thumbnail: TelegramSticker) -> bool:
        repl = await self._send_and_recv("/setpackicon")
        if "OK" not in repl:
            self.cb.put(
                f"Cannot set pack icon for {self.pack_short_name} due to {repl}"
            )
            return False
        repl = await self._send_and_recv(thumbnail[0])
        if "Enjoy!" not in repl:
            self.cb.put(
                f"Cannot set pack icon for {self.pack_short_name} due to {repl}"
            )
            return False
        return True

    async def get_pack_url(self) -> str:
        if self.is_emoji:
            return f"https://t.me/addemoji/{self.pack_short_name}"
        else:
            return f"https://t.me/addstickers/{self.pack_short_name}"

    async def _download_sticker(
        self,
        sticker: TypeDocument,
        f_id: str,
        out_dir: Path,
        id_to_emoji: Dict[int, str],
        emoji_dict: Dict[str, str],
        results: Dict[str, bool],
    ) -> None:
        fpath_attr = [
            attr
            for attr in sticker.attributes  # type: ignore
            if isinstance(attr, DocumentAttributeFilename)
        ]
        assert len(fpath_attr) > 0
        fpath = fpath_attr[0].file_name
        ext = Path(fpath).suffix
        f_name = f_id + ext
        f_path = Path(out_dir, f_name)

        try:
            await self.client.download_media(sticker, file=f_path)  # type: ignore
        except Exception as e:
            self.cb.put(f"Failed to download {f_id}: {str(e)}")
            results[f_id] = False
            return

        emoji_dict[f_id] = id_to_emoji[sticker.id]
        self.cb.put(f"Downloaded {f_name}")
        results[f_id] = True
        self.cb.put("update_bar")

    async def pack_dl(
        self, pack_short_name: str, out_dir: Path
    ) -> Tuple[Dict[str, bool], Dict[str, str]]:
        results: Dict[str, bool] = {}
        emoji_dict: Dict[str, str] = {}
        id_to_emoji: Dict[int, str] = defaultdict(str)

        sticker_set = cast(
            TLStickerSet,
            await self.client(
                messages.GetStickerSetRequest(
                    InputStickerSetShortName(pack_short_name), 0
                )
            ),
        )

        self.cb.put(
            (
                "bar",
                None,
                {
                    "set_progress_mode": "determinate",
                    "steps": len(sticker_set.documents),
                },
            )
        )

        for pack in sticker_set.packs:
            for document_id in pack.documents:
                id_to_emoji[document_id] += pack.emoticon

        ext = ""
        async with anyio.create_task_group() as tg:
            for num, sticker in enumerate(sticker_set.documents):
                f_id = str(num).zfill(3)
                tg.start_soon(
                    self._download_sticker,
                    sticker,
                    f_id,
                    out_dir,
                    id_to_emoji,
                    emoji_dict,
                    results,
                )

        if sticker_set.set.thumb_version and ext:
            try:
                await self.client.download_file(  # type: ignore
                    InputStickerSetThumb(
                        InputStickerSetShortName(pack_short_name),
                        thumb_version=sticker_set.set.thumb_version,
                    ),
                    f"cover{ext}",
                )
            except Exception as e:
                self.cb.put(f"Failed to download cover{ext}: {str(e)}")

        return results, emoji_dict
