#!/usr/bin/env python3
import webbrowser
from typing import TYPE_CHECKING, Any

from ttkbootstrap import Button, Entry, Label, LabelFrame  # type: ignore

from sticker_convert.gui_components.frames.right_clicker import RightClicker
from sticker_convert.gui_components.windows.discord_get_auth_window import DiscordGetAuthWindow
from sticker_convert.gui_components.windows.kakao_get_auth_window import KakaoGetAuthWindow
from sticker_convert.gui_components.windows.line_get_auth_window import LineGetAuthWindow
from sticker_convert.gui_components.windows.signal_get_auth_window import SignalGetAuthWindow
from sticker_convert.gui_components.windows.viber_get_auth_window import ViberGetAuthWindow
from sticker_convert.utils.auth.telethon_setup import TelethonSetup

if TYPE_CHECKING:
    from sticker_convert.gui import GUI  # type: ignore


class CredFrame(LabelFrame):
    def __init__(self, gui: "GUI", *args: Any, **kwargs: Any) -> None:
        self.gui = gui
        super().__init__(*args, **kwargs)

        self.grid_columnconfigure(1, weight=1)

        self.signal_uuid_lbl = Label(
            self, text="Signal uuid", width=18, justify="left", anchor="w"
        )
        self.signal_uuid_entry = Entry(
            self,
            textvariable=self.gui.signal_uuid_var,
            width=50,
            validate="focusout",
            validatecommand=self.gui.highlight_fields,
        )
        self.signal_uuid_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.signal_password_lbl = Label(
            self, text="Signal password", justify="left", anchor="w"
        )
        self.signal_password_entry = Entry(
            self,
            textvariable=self.gui.signal_password_var,
            width=50,
            validate="focusout",
            validatecommand=self.gui.highlight_fields,
        )
        self.signal_password_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.signal_get_auth_btn = Button(
            self,
            text="Generate",
            command=self.cb_signal_get_auth,
            bootstyle="secondary",  # type: ignore
        )

        self.telegram_token_lbl = Label(
            self, text="Telegram token", justify="left", anchor="w"
        )
        self.telegram_token_entry = Entry(
            self,
            textvariable=self.gui.telegram_token_var,
            width=50,
            validate="focusout",
            validatecommand=self.gui.highlight_fields,
        )
        self.telegram_token_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.telegram_userid_lbl = Label(
            self, text="Telegram user_id", justify="left", anchor="w"
        )
        self.telegram_userid_entry = Entry(
            self,
            textvariable=self.gui.telegram_userid_var,
            width=50,
            validate="focusout",
            validatecommand=self.gui.highlight_fields,
        )
        self.telegram_userid_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.telethon_auth_lbl = Label(
            self, text="Telethon authorization", justify="left", anchor="w"
        )
        self.telethon_auth_btn = Button(
            self,
            text="Generate",
            command=self.cb_telethon_get_auth,
            bootstyle="secondary",  # type: ignore
        )

        self.kakao_auth_token_lbl = Label(
            self, text="Kakao auth_token", justify="left", anchor="w"
        )
        self.kakao_auth_token_entry = Entry(
            self, textvariable=self.gui.kakao_auth_token_var, width=35
        )
        self.kakao_auth_token_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.kakao_get_auth_btn = Button(
            self,
            text="Generate",
            command=self.cb_kakao_get_auth,
            bootstyle="secondary",  # type: ignore
        )

        self.line_cookies_lbl = Label(
            self, text="Line cookies", width=18, justify="left", anchor="w"
        )
        self.line_cookies_entry = Entry(
            self, textvariable=self.gui.line_cookies_var, width=35
        )
        self.line_cookies_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.line_get_auth_btn = Button(
            self,
            text="Generate",
            command=self.cb_line_get_auth,
            bootstyle="secondary",  # type: ignore
        )

        self.viber_auth_lbl = Label(
            self, text="Viber auth", width=18, justify="left", anchor="w"
        )
        self.viber_auth_entry = Entry(
            self, textvariable=self.gui.viber_auth_var, width=35
        )
        self.viber_auth_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.viber_get_auth_btn = Button(
            self,
            text="Generate",
            command=self.cb_viber_get_auth,
            bootstyle="secondary",  # type: ignore
        )

        self.discord_token_lbl = Label(
            self, text="Discord token", width=18, justify="left", anchor="w"
        )
        self.discord_token_entry = Entry(
            self, textvariable=self.gui.discord_token_var, width=35
        )
        self.discord_token_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.discord_get_auth_btn = Button(
            self,
            text="Generate",
            command=self.cb_discord_get_auth,
            bootstyle="secondary",  # type: ignore
        )

        self.help_btn = Button(
            self,
            text="Get help",
            command=self.cb_cred_help,
            bootstyle="secondary",  # type: ignore
        )

        self.signal_uuid_lbl.grid(column=0, row=0, sticky="w", padx=3, pady=3)
        self.signal_uuid_entry.grid(
            column=1, row=0, columnspan=2, sticky="w", padx=3, pady=3
        )
        self.signal_password_lbl.grid(column=0, row=1, sticky="w", padx=3, pady=3)
        self.signal_password_entry.grid(
            column=1, row=1, columnspan=2, sticky="w", padx=3, pady=3
        )
        self.signal_get_auth_btn.grid(column=2, row=2, sticky="e", padx=3, pady=3)
        self.telegram_token_lbl.grid(column=0, row=3, sticky="w", padx=3, pady=3)
        self.telegram_token_entry.grid(
            column=1, row=3, columnspan=2, sticky="w", padx=3, pady=3
        )
        self.telegram_userid_lbl.grid(column=0, row=4, sticky="w", padx=3, pady=3)
        self.telegram_userid_entry.grid(
            column=1, row=4, columnspan=2, sticky="w", padx=3, pady=3
        )
        self.telethon_auth_lbl.grid(column=0, row=5, sticky="w", padx=3, pady=3)
        self.telethon_auth_btn.grid(column=2, row=5, sticky="e", padx=3, pady=3)
        self.kakao_auth_token_lbl.grid(column=0, row=6, sticky="w", padx=3, pady=3)
        self.kakao_auth_token_entry.grid(column=1, row=6, sticky="w", padx=3, pady=3)
        self.kakao_get_auth_btn.grid(column=2, row=6, sticky="e", padx=3, pady=3)
        self.line_cookies_lbl.grid(column=0, row=7, sticky="w", padx=3, pady=3)
        self.line_cookies_entry.grid(column=1, row=7, sticky="w", padx=3, pady=3)
        self.line_get_auth_btn.grid(column=2, row=7, sticky="e", padx=3, pady=3)
        self.viber_auth_lbl.grid(column=0, row=8, sticky="w", padx=3, pady=3)
        self.viber_auth_entry.grid(column=1, row=8, sticky="w", padx=3, pady=3)
        self.viber_get_auth_btn.grid(column=2, row=8, sticky="e", padx=3, pady=3)
        self.discord_token_lbl.grid(column=0, row=9, sticky="w", padx=3, pady=3)
        self.discord_token_entry.grid(column=1, row=9, sticky="w", padx=3, pady=3)
        self.discord_get_auth_btn.grid(column=2, row=9, sticky="e", padx=3, pady=3)
        self.help_btn.grid(column=2, row=10, sticky="e", padx=3, pady=3)

    def cb_cred_help(self, *_: Any) -> None:
        faq_site = "https://github.com/laggykiller/sticker-convert#faq"
        success = webbrowser.open(faq_site)
        if not success:
            self.gui.cb_ask_str("You can get help from:", initialvalue=faq_site)

    def cb_telethon_get_auth(self, *_: Any) -> None:
        success, _client, api_id, api_hash = TelethonSetup(
            self.gui.get_opt_cred(), self.gui.cb_ask_str
        ).start()
        if success:
            self.gui.telethon_api_id_var.set(api_id)
            self.gui.telethon_api_hash_var.set(api_hash)
            self.gui.save_creds()
            self.gui.cb_msg_block("Telethon setup successful")
        else:
            self.gui.cb_msg_block("Telethon setup failed")

    def cb_kakao_get_auth(self, *_: Any) -> None:
        KakaoGetAuthWindow(self.gui)

    def cb_signal_get_auth(self, *_: Any) -> None:
        SignalGetAuthWindow(self.gui)

    def cb_line_get_auth(self, *_: Any) -> None:
        LineGetAuthWindow(self.gui)

    def cb_viber_get_auth(self, *_: Any) -> None:
        ViberGetAuthWindow(self.gui)

    def cb_discord_get_auth(self, *_: Any) -> None:
        DiscordGetAuthWindow(self.gui)

    def set_states(self, state: str) -> None:
        self.signal_uuid_entry.config(state=state)
        self.signal_password_entry.config(state=state)
        self.signal_get_auth_btn.config(state=state)
        self.telegram_token_entry.config(state=state)
        self.telegram_userid_entry.config(state=state)
        self.kakao_auth_token_entry.config(state=state)
        self.kakao_get_auth_btn.config(state=state)
        self.line_cookies_entry.config(state=state)
        self.line_get_auth_btn.config(state=state)
        self.viber_auth_entry.config(state=state)
        self.viber_get_auth_btn.config(state=state)
        self.discord_token_entry.config(state=state)
        self.discord_get_auth_btn.config(state=state)
