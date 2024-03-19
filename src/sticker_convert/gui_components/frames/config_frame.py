#!/usr/bin/env python3
import os
import platform
from typing import TYPE_CHECKING, Any

from ttkbootstrap import Button, Checkbutton, Label, LabelFrame  # type: ignore

from sticker_convert.definitions import CONFIG_DIR
from sticker_convert.utils.files.run_bin import RunBin

if TYPE_CHECKING:
    from sticker_convert.gui import GUI  # type: ignore


class ConfigFrame(LabelFrame):
    def __init__(self, gui: "GUI", *args: Any, **kwargs: Any) -> None:
        self.gui = gui
        super().__init__(*args, **kwargs)

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(3, weight=1)

        self.settings_save_cred_lbl = Label(
            self, text="Save credentials", width=18, justify="left", anchor="w"
        )
        self.settings_save_cred_cbox = Checkbutton(
            self,
            variable=self.gui.settings_save_cred_var,
            onvalue=True,
            offvalue=False,
            bootstyle="success-round-toggle",  # type: ignore
        )

        self.settings_clear_cred_lbl = Label(
            self, text="Clear credentials", width=18, justify="left", anchor="w"
        )
        self.settings_clear_cred_btn = Button(
            self,
            text="Clear...",
            command=self.cb_clear_cred,
            bootstyle="secondary",  # type: ignore
        )

        self.settings_restore_default_lbl = Label(
            self, text="Default config", width=18, justify="left", anchor="w"
        )
        self.settings_restore_default_btn = Button(
            self,
            text="Restore...",
            command=self.cb_restore_default,
            bootstyle="secondary",  # type: ignore
        )

        self.settings_open_dir_lbl = Label(
            self, text="Config directory", width=18, justify="left", anchor="w"
        )
        self.settings_open_dir_btn = Button(
            self,
            text="Open...",
            command=self.cb_open_config_directory,
            bootstyle="secondary",  # type: ignore
        )

        self.settings_save_cred_lbl.grid(column=0, row=0, sticky="w", padx=3, pady=3)
        self.settings_save_cred_cbox.grid(column=1, row=0, sticky="w", padx=3, pady=3)

        self.settings_clear_cred_lbl.grid(column=2, row=0, sticky="w", padx=3, pady=3)
        self.settings_clear_cred_btn.grid(column=3, row=0, sticky="w", padx=3, pady=3)

        self.settings_open_dir_lbl.grid(column=0, row=1, sticky="w", padx=3, pady=3)
        self.settings_open_dir_btn.grid(column=1, row=1, sticky="w", padx=3, pady=3)

        self.settings_restore_default_lbl.grid(
            column=2, row=1, sticky="w", padx=3, pady=3
        )
        self.settings_restore_default_btn.grid(
            column=3, row=1, sticky="w", padx=3, pady=3
        )

    def cb_clear_cred(self, *_: Any, **kwargs: Any) -> None:
        response = self.gui.cb_ask_bool("Are you sure you want to clear credentials?")
        if response is True:
            self.gui.delete_creds()
            self.gui.load_jsons()
            self.gui.apply_creds()
            self.gui.highlight_fields()
            self.gui.cb_msg_block("Credentials cleared.")

    def cb_restore_default(self, *_: Any, **kwargs: Any) -> None:
        response = self.gui.cb_ask_bool(
            "Are you sure you want to restore default config? (This will not clear credentials.)"
        )
        if response is True:
            self.gui.delete_config()
            self.gui.load_jsons()
            self.gui.apply_config()
            self.gui.highlight_fields()
            self.gui.cb_msg_block("Restored to default config.")

    def cb_open_config_directory(self, *_: Any, **kwargs: Any) -> None:
        self.gui.cb_msg(msg=f"Config is located at {CONFIG_DIR}")
        if platform.system() == "Windows":
            os.startfile(CONFIG_DIR)  # type: ignore
        elif platform.system() == "Darwin":
            RunBin.run_cmd(["open", str(CONFIG_DIR)], silence=True)
        else:
            RunBin.run_cmd(["xdg-open", str(CONFIG_DIR)], silence=True)

    def set_states(self, state: str) -> None:
        self.settings_save_cred_cbox.config(state=state)
        self.settings_clear_cred_btn.config(state=state)
        self.settings_restore_default_btn.config(state=state)
        self.settings_open_dir_btn.config(state=state)
