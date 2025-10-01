#!/usr/bin/env python3
from threading import Thread
from typing import Any

from ttkbootstrap import Button, Frame, Label  # type: ignore

from sticker_convert.auth.auth_signal import AuthSignal
from sticker_convert.gui_components.gui_utils import GUIUtils
from sticker_convert.gui_components.windows.base_window import BaseWindow


class SignalGetAuthWindow(BaseWindow):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(SignalGetAuthWindow, self).__init__(*args, **kwargs)

        self.title("Get Signal uuid and password")

        self.frame_info = Frame(self.scrollable_frame)
        self.frame_start_btn = Frame(self.scrollable_frame)

        self.frame_info.grid(column=0, row=0, sticky="news", padx=3, pady=3)
        self.frame_start_btn.grid(column=0, row=1, sticky="news", padx=3, pady=3)

        # Info frame
        self.explanation1_lbl = Label(
            self.frame_info,
            text="Please install Signal Desktop",
            justify="left",
            anchor="w",
        )
        self.explanation2_lbl = Label(
            self.frame_info,
            text="After installation, you need to login to Signal Desktop",
            justify="left",
            anchor="w",
        )
        self.explanation3_lbl = Label(
            self.frame_info,
            text="uuid and password will be automatically fetched",
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
            self.frame_start_btn, text="Get uuid and password", command=self.cb_login
        )

        self.login_btn.pack()

        GUIUtils.finalize_window(self)

    def cb_login(self) -> None:
        Thread(target=self.cb_login_thread, daemon=True).start()

    def cb_login_thread(self, *args: Any) -> None:
        m = AuthSignal(self.gui.get_opt_cred(), self.gui.cb)

        uuid, password, msg = m.get_cred()
        self.gui.cb.put(("msg_block", None, {"message": msg, "parent": self}))
        if uuid and password:
            if not self.gui.creds.get("signal"):
                self.gui.creds["signal"] = {}
            self.gui.creds["signal"]["uuid"] = uuid
            self.gui.creds["signal"]["password"] = password
            self.gui.signal_uuid_var.set(uuid)
            self.gui.signal_password_var.set(password)

            self.gui.save_creds()
            self.gui.highlight_fields()
            return
