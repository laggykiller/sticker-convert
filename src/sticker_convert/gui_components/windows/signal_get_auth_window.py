#!/usr/bin/env python3
from functools import partial
from subprocess import Popen
from typing import Any

from ttkbootstrap import Button, Frame, Label  # type: ignore

from sticker_convert.gui_components.gui_utils import GUIUtils
from sticker_convert.gui_components.windows.base_window import BaseWindow
from sticker_convert.utils.auth.get_signal_auth import GetSignalAuth


class SignalGetAuthWindow(BaseWindow):
    def __init__(self, *args: Any, **kwargs: Any):
        super(SignalGetAuthWindow, self).__init__(*args, **kwargs)

        self.title("Get Signal uuid and password")

        self.cb_msg_block_signal = partial(self.gui.cb_msg_block, parent=self)
        self.cb_ask_str_signal = partial(self.gui.cb_ask_str, parent=self)

        self.frame_info = Frame(self.scrollable_frame)
        self.frame_btns = Frame(self.scrollable_frame)

        self.frame_info.grid(column=0, row=0, sticky="news", padx=3, pady=3)
        self.frame_btns.grid(column=0, row=1, sticky="news", padx=3, pady=3)

        # Info frame
        self.explanation_lbl = Label(
            self.frame_info,
            text="Please install Signal Desktop and login first.",
            justify="left",
            anchor="w",
        )

        self.explanation_lbl.grid(
            column=0, row=0, columnspan=3, sticky="w", padx=3, pady=3
        )

        # Start button frame
        self.launch_btn = Button(
            self.frame_btns, text="Launch Signal Desktop", command=self.cb_launch_signal
        )

        self.login_btn = Button(
            self.frame_btns, text="Get uuid and password", command=self.cb_login
        )

        self.launch_btn.pack()
        self.login_btn.pack()

        GUIUtils.finalize_window(self)

    def cb_login(self):
        m = GetSignalAuth()
        uuid, password, msg = m.get_cred()

        if uuid and password:
            if not self.gui.creds.get("signal"):
                self.gui.creds["signal"] = {}
            self.gui.creds["signal"]["uuid"] = uuid
            self.gui.creds["signal"]["password"] = password
            self.gui.signal_uuid_var.set(uuid)
            self.gui.signal_password_var.set(password)

            self.gui.save_creds()
            self.gui.highlight_fields()

        self.cb_msg_block_signal(msg)

    def cb_launch_signal(self):
        m = GetSignalAuth()
        signal_bin_path, signal_user_data_dir = m.get_signal_desktop()
        if signal_bin_path:
            Popen(
                [
                    signal_bin_path,
                    "--no-sandbox",
                    f"--user-data-dir={signal_user_data_dir}",
                ]
            )
        else:
            self.cb_msg_block_signal("Error: Signal Desktop not installed.")
