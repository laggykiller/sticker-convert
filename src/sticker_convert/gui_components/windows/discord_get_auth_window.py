#!/usr/bin/env python3
from functools import partial
from threading import Thread
from typing import Any

from ttkbootstrap import Button, Frame, Label  # type: ignore

from sticker_convert.gui_components.gui_utils import GUIUtils
from sticker_convert.gui_components.windows.base_window import BaseWindow
from sticker_convert.utils.auth.get_discord_auth import GetDiscordAuth


class DiscordGetAuthWindow(BaseWindow):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(DiscordGetAuthWindow, self).__init__(*args, **kwargs)

        self.title("Get Discord token")

        self.cb_msg_block_discord = partial(self.gui.cb_msg_block, parent=self)
        self.cb_ask_str_discord = partial(self.gui.cb_ask_str, parent=self)

        self.frame_info = Frame(self.scrollable_frame)
        self.frame_start_btn = Frame(self.scrollable_frame)

        self.frame_info.grid(column=0, row=0, sticky="news", padx=3, pady=3)
        self.frame_start_btn.grid(column=0, row=1, sticky="news", padx=3, pady=3)

        # Info frame
        self.explanation1_lbl = Label(
            self.frame_info,
            text="Please install Discord Desktop or Chrome",
            justify="left",
            anchor="w",
        )
        self.explanation2_lbl = Label(
            self.frame_info,
            text="After installation, you need to login to Discord",
            justify="left",
            anchor="w",
        )
        self.explanation3_lbl = Label(
            self.frame_info,
            text="Token will be automatically fetched",
            justify="left",
            anchor="w",
        )

        self.explanation1_lbl.grid(
            column=0, row=0, columnspan=3, sticky="w", padx=3, pady=3
        )
        self.explanation2_lbl.grid(
            column=0, row=1, columnspan=3, sticky="w", padx=3, pady=3
        )
        self.explanation3_lbl.grid(
            column=0, row=2, columnspan=3, sticky="w", padx=3, pady=3
        )

        # Start button frame
        self.login_btn = Button(
            self.frame_start_btn, text="Get token", command=self.cb_login
        )

        self.login_btn.pack()

        GUIUtils.finalize_window(self)

    def cb_login(self) -> None:
        Thread(target=self.cb_login_thread, daemon=True).start()

    def cb_login_thread(self, *args: Any) -> None:
        m = GetDiscordAuth(cb_msg=self.gui.cb_msg)
        discord_token, msg = m.get_cred()
        if discord_token:
            if not self.gui.creds.get("discord"):
                self.gui.creds["discord"] = {}
            self.gui.creds["discord"]["token"] = discord_token
            self.gui.discord_token_var.set(discord_token)

            self.gui.save_creds()
            self.gui.highlight_fields()

        self.cb_msg_block_discord(msg)
