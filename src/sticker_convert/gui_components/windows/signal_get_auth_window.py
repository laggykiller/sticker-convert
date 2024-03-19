#!/usr/bin/env python3
from functools import partial
from pathlib import Path
from subprocess import Popen
from tkinter import filedialog
from typing import Any

from ttkbootstrap import Button, Entry, Frame, Label  # type: ignore

from sticker_convert.gui_components.gui_utils import GUIUtils
from sticker_convert.gui_components.windows.base_window import BaseWindow
from sticker_convert.utils.auth.get_signal_auth import GetSignalAuth


class SignalGetAuthWindow(BaseWindow):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.title("Get Signal uuid and password")

        self.cb_msg_block_signal = partial(self.gui.cb_msg_block, parent=self)
        self.cb_ask_str_signal = partial(self.gui.cb_ask_str, parent=self)

        self.frame_info = Frame(self.scrollable_frame)
        self.frame_btns = Frame(self.scrollable_frame)
        self.frame_config = Frame(self.scrollable_frame)

        self.frame_info.grid(column=0, row=0, sticky="news", padx=3, pady=3)
        self.frame_btns.grid(column=0, row=1, sticky="news", padx=3, pady=3)
        self.frame_config.grid(column=0, row=2, sticky="news", padx=3, pady=3)

        # Info frame
        self.explanation_lbl = Label(
            self.frame_info,
            text="Please install Signal Desktop and login first.",
            justify="left",
            anchor="w",
        )

        self.explanation_lbl.grid(column=0, row=0, sticky="w", padx=3, pady=3)

        # Start button frame
        self.launch_btn = Button(
            self.frame_btns,
            text="Launch Signal Desktop",
            command=self.cb_launch_signal,
            bootstyle="secondary",  # type: ignore
        )

        self.get_cred_btn = Button(
            self.frame_btns,
            text="Get uuid and password",
            command=self.cb_get_cred,
            bootstyle="default",  # type: ignore
        )

        self.launch_btn.pack()
        self.get_cred_btn.pack()

        # Config frame
        self.setdir_lbl = Label(
            self.frame_config,
            text=self.gui.help["cred"]["signal_data_dir"],
            justify="left",
            anchor="w",
        )

        self.setdir_entry = Entry(
            self.frame_config,
            textvariable=self.gui.signal_data_dir_var,
            width=32,
        )
        self.setdir_btn = Button(
            self.frame_config,
            text="Choose",
            command=self.cb_setdir,
            width=8,
            bootstyle="secondary",  # type: ignore
        )

        self.setdir_lbl.grid(column=0, row=0, columnspan=2, sticky="w", padx=3, pady=3)
        self.setdir_entry.grid(column=0, row=1, sticky="w", padx=3, pady=3)
        self.setdir_btn.grid(column=1, row=1, sticky="e", padx=3, pady=3)

        GUIUtils.finalize_window(self)

    def cb_get_cred(self) -> None:
        m = GetSignalAuth()

        signal_bin_path = None
        signal_user_data_dir = None
        if self.gui.signal_data_dir_var.get():
            signal_bin_path = "(User specified)"
            signal_user_data_dir = self.gui.signal_data_dir_var.get()

        uuid, password, msg = m.get_cred(signal_bin_path, signal_user_data_dir)

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

    def cb_launch_signal(self) -> None:
        m = GetSignalAuth()
        signal_bin_path, signal_user_data_dir = m.get_signal_desktop()

        if self.gui.signal_data_dir_var.get():
            signal_user_data_dir = self.gui.signal_data_dir_var.get()

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

    def cb_setdir(self) -> None:
        orig_input_dir = self.gui.signal_data_dir_var.get()
        if not Path(orig_input_dir).is_dir():
            orig_input_dir = ""
        input_dir = filedialog.askdirectory(initialdir=orig_input_dir)
        if input_dir:
            self.gui.signal_data_dir_var.set(input_dir)
