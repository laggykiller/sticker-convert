#!/usr/bin/env python3
import platform
from functools import partial
from pathlib import Path
from subprocess import Popen
from threading import Thread
from tkinter import filedialog
from typing import Any

from ttkbootstrap import Button, Entry, Frame, Label  # type: ignore

from sticker_convert.gui_components.gui_utils import GUIUtils
from sticker_convert.gui_components.windows.base_window import BaseWindow
from sticker_convert.utils.auth.get_viber_auth import GetViberAuth


class ViberGetAuthWindow(BaseWindow):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.title("Get Viber auth data")

        self.cb_msg_block_viber = partial(self.gui.cb_msg_block, parent=self)
        self.cb_ask_str_viber = partial(self.gui.cb_ask_str, parent=self)

        self.frame_info = Frame(self.scrollable_frame)
        self.frame_btns = Frame(self.scrollable_frame)
        self.frame_config = Frame(self.scrollable_frame)

        self.frame_info.grid(column=0, row=0, sticky="news", padx=3, pady=3)
        self.frame_btns.grid(column=0, row=1, sticky="news", padx=3, pady=3)
        self.frame_config.grid(column=0, row=2, sticky="news", padx=3, pady=3)

        # Info frame
        self.explanation_lbl0 = Label(
            self.frame_info,
            text="Please install Viber Desktop and login first.",
            justify="left",
            anchor="w",
        )
        self.explanation_lbl1 = Label(
            self.frame_info,
            text="It may take a minute to get auth data.",
            justify="left",
            anchor="w",
        )
        self.explanation_lbl2 = None
        if platform.system() == "Darwin":
            self.explanation_lbl2 = Label(
                self.frame_info,
                text="You need to disable SIP and may be asked for user password.",
                justify="left",
                anchor="w",
            )
        else:
            self.explanation_lbl2 = Label(
                self.frame_info,
                text="You may be asked for admin password.",
                justify="left",
                anchor="w",
            )
        if platform.system() != "Darwin":
            self.explanation_lbl3 = Label(
                self.frame_info,
                text="Note: This will download ProcDump and read memory of Viber Desktop",
                justify="left",
                anchor="w",
            )
        else:
            self.explanation_lbl3 = Label(
                self.frame_info,
                text="Note: This will read memory of Viber Desktop",
                justify="left",
                anchor="w",
            )

        self.explanation_lbl0.grid(column=0, row=0, sticky="w", padx=3, pady=3)
        self.explanation_lbl1.grid(column=0, row=1, sticky="w", padx=3, pady=3)
        self.explanation_lbl2.grid(column=0, row=2, sticky="w", padx=3, pady=3)
        self.explanation_lbl3.grid(column=0, row=3, sticky="w", padx=3, pady=3)

        # Start button frame
        self.launch_btn = Button(
            self.frame_btns,
            text="Launch Viber Desktop",
            command=self.cb_launch_viber,
            bootstyle="secondary",  # type: ignore
        )

        self.get_cred_btn = Button(
            self.frame_btns,
            text="Get auth data",
            command=self.cb_get_cred,
            bootstyle="default",  # type: ignore
        )

        self.launch_btn.pack()
        self.get_cred_btn.pack()

        # Config frame
        self.setdir_lbl = Label(
            self.frame_config,
            text=self.gui.help["cred"]["viber_bin_path"],
            justify="left",
            anchor="w",
        )

        self.setdir_entry = Entry(
            self.frame_config,
            textvariable=self.gui.viber_bin_path_var,
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
        Thread(target=self.cb_get_cred_thread, daemon=True).start()

    def cb_get_cred_thread(self) -> None:
        m = GetViberAuth(self.cb_ask_str_viber)

        viber_bin_path = None
        if self.gui.viber_bin_path_var.get():
            viber_bin_path = self.gui.viber_bin_path_var.get()

        viber_auth, msg = m.get_cred(viber_bin_path)

        if viber_auth:
            if not self.gui.creds.get("viber"):
                self.gui.creds["viber"] = {}
            self.gui.creds["viber"]["auth"] = viber_auth
            self.gui.viber_auth_var.set(viber_auth)

            self.gui.save_creds()
            self.gui.highlight_fields()

        self.cb_msg_block_viber(msg)

    def cb_launch_viber(self) -> None:
        m = GetViberAuth(self.cb_ask_str_viber)
        viber_bin_path = m.get_viber_desktop()

        if self.gui.viber_auth_var.get():
            viber_bin_path = self.gui.viber_auth_var.get()

        if viber_bin_path:
            Popen([viber_bin_path])
        else:
            self.cb_msg_block_viber("Error: Viber Desktop not installed.")

    def cb_setdir(self) -> None:
        orig_input_dir = self.gui.viber_bin_path_var.get()
        if not Path(orig_input_dir).is_dir():
            orig_input_dir = ""
        input_dir = filedialog.askdirectory(initialdir=orig_input_dir)
        if input_dir:
            self.gui.viber_bin_path_var.set(input_dir)
