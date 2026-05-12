#!/usr/bin/env python3
from threading import Thread
from typing import Any

from ttkbootstrap import Button, Entry, Frame, Label  # type: ignore

from sticker_convert.auth.auth_whatsapp import AuthWhatsapp
from sticker_convert.gui_components.gui_utils import GUIUtils
from sticker_convert.gui_components.windows.base_window import BaseWindow
from sticker_convert.utils.translate import I


class WhatsappGetAuthWindow(BaseWindow):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(WhatsappGetAuthWindow, self).__init__(*args, **kwargs)

        self.title("Setup WhatsApp")

        self.frame_info = Frame(self.scrollable_frame)
        self.frame_start_btn = Frame(self.scrollable_frame)

        self.frame_info.grid(column=0, row=0, sticky="news", padx=3, pady=3)
        self.frame_start_btn.grid(column=0, row=1, sticky="news", padx=3, pady=3)

        # Info frame
        self.explanation_lbl = Label(
            self.frame_info,
            text=I("This wizard will guide you through logging in WhatsApp Web"),
            justify="left",
            anchor="w",
        )
        self.whatsapp_phone_number_help_btn = Button(
            self.frame_info,
            text="?",
            width=1,
            command=lambda: self.gui.cb.put(
                (
                    "msg_block",
                    (self.gui.help["cred"]["whatsapp_phone_number"], self),
                    None,
                )
            ),
            bootstyle="secondary",  # type: ignore
        )
        self.whatsapp_phone_number_lbl = Label(
            self.frame_info,
            text=I("Phone number (Optional)"),
            justify="left",
            anchor="w",
        )
        self.whatsapp_phone_number_entry = Entry(
            self.frame_info,
            textvariable=self.gui.whatsapp_phone_number_var,
            width=20,
            validate="focusout",
        )

        self.explanation_lbl.grid(
            column=0, row=0, columnspan=3, sticky="w", padx=3, pady=3
        )
        self.whatsapp_phone_number_help_btn.grid(
            column=0, row=1, sticky="w", padx=3, pady=3
        )
        self.whatsapp_phone_number_lbl.grid(column=1, row=1, sticky="w", padx=3, pady=3)
        self.whatsapp_phone_number_entry.grid(
            column=2, row=1, sticky="w", padx=3, pady=3
        )

        # Start button frame
        self.login_btn = Button(
            self.frame_start_btn,
            text=I("Login"),
            command=self.cb_login,
        )

        self.login_btn.pack()

        GUIUtils.finalize_window(self)

    def cb_login(self) -> None:
        Thread(target=self.cb_login_thread, daemon=True).start()

    def cb_login_thread(self, *args: Any) -> None:
        m = AuthWhatsapp(self.gui.get_opt_cred(), self.gui.cb)

        _, msg = m.get_cred()
        self.gui.cb.put(("msg_block", None, {"message": msg, "parent": self}))
