#!/usr/bin/env python3
import os
import platform
from typing import TYPE_CHECKING, Any

from ttkbootstrap import Button, Checkbutton, Label, LabelFrame, OptionMenu  # type: ignore

from sticker_convert.definitions import CONFIG_DIR, RUNTIME_STATE
from sticker_convert.utils.files.run_bin import RunBin
from sticker_convert.utils.translate import SUPPORTED_LANG, I, get_lang

if TYPE_CHECKING:
    from sticker_convert.gui import GUI  # type: ignore


class ConfigFrame(LabelFrame):
    def __init__(self, gui: "GUI", *args: Any, **kwargs: Any) -> None:
        self.gui = gui
        super().__init__(*args, **kwargs)

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(3, weight=1)

        self.settings_save_cred_lbl = Label(
            self, text=I("Save credentials"), width=18, justify="left", anchor="w"
        )
        self.settings_save_cred_cbox = Checkbutton(
            self,
            variable=self.gui.settings_save_cred_var,
            onvalue=True,
            offvalue=False,
            bootstyle="success-round-toggle",  # type: ignore
        )

        self.settings_clear_cred_lbl = Label(
            self,
            text=I("Clear credentials"),
            width=18,
            justify="left",
            anchor="w",
        )
        self.settings_clear_cred_btn = Button(
            self,
            text=I("Clear..."),
            command=self.cb_clear_cred,
            bootstyle="secondary",  # type: ignore
        )

        self.settings_restore_default_lbl = Label(
            self, text=I("Default config"), width=18, justify="left", anchor="w"
        )
        self.settings_restore_default_btn = Button(
            self,
            text=I("Restore..."),
            command=self.cb_restore_default,
            bootstyle="secondary",  # type: ignore
        )

        self.settings_open_dir_lbl = Label(
            self, text=I("Config directory"), width=18, justify="left", anchor="w"
        )
        self.settings_open_dir_btn = Button(
            self,
            text=I("Open..."),
            command=self.cb_open_config_directory,
            bootstyle="secondary",  # type: ignore
        )

        self.settings_lang_lbl = Label(
            self, text=I("Language"), width=18, justify="left", anchor="w"
        )
        self.settings_lang_opt = OptionMenu(
            self,
            self.gui.lang_display_var,
            self.gui.lang_display_var.get(),
            *list(SUPPORTED_LANG.keys()),
            command=self.cb_lang,
            bootstyle="secondary",  # type: ignore
        )
        self.settings_lang_opt.config(width=8)

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

        self.settings_lang_lbl.grid(column=0, row=2, sticky="w", padx=3, pady=3)
        self.settings_lang_opt.grid(column=1, row=2, sticky="w", padx=3, pady=3)

    def cb_clear_cred(self, *_: Any, **kwargs: Any) -> None:
        response = self.gui.cb.put(
            (
                "ask_bool",
                (I("Are you sure you want to clear credentials?"),),
                None,
            )
        )
        if response is True:
            self.gui.delete_creds()
            self.gui.load_jsons()
            self.gui.apply_creds()
            self.gui.highlight_fields()
            self.gui.cb.put(("msg_block", ("Credentials cleared.",), None))

    def cb_restore_default(self, *_: Any, **kwargs: Any) -> None:
        response = self.gui.cb.put(
            (
                "ask_bool",
                (
                    I(
                        "Are you sure you want to restore default config? (This will not clear credentials.)"
                    ),
                ),
                None,
            )
        )
        if response is True:
            self.gui.delete_config()
            self.gui.load_jsons()
            self.gui.apply_config()
            self.gui.highlight_fields()
            self.gui.cb.put(("msg_block", (I("Restored to default config."),), None))

    def cb_open_config_directory(self, *_: Any, **kwargs: Any) -> None:
        self.gui.cb.put(I("Config is located at {}").format(CONFIG_DIR))
        if platform.system() == "Windows":
            os.startfile(CONFIG_DIR)  # type: ignore
        elif platform.system() == "Darwin":
            RunBin.run_cmd(["open", str(CONFIG_DIR)], silence=True)
        else:
            RunBin.run_cmd(["xdg-open", str(CONFIG_DIR)], silence=True)

    def cb_lang(self, *_: Any, **kwargs: Any) -> None:
        self.gui.lang_true_var.set(SUPPORTED_LANG[self.gui.lang_display_var.get()])
        self.gui.save_config()
        RUNTIME_STATE["LANG"] = get_lang()
        RUNTIME_STATE["TRANS"] = None
        self.gui.reset()

    def set_states(self, state: str) -> None:
        self.settings_save_cred_cbox.config(state=state)
        self.settings_clear_cred_btn.config(state=state)
        self.settings_restore_default_btn.config(state=state)
        self.settings_open_dir_btn.config(state=state)
        self.settings_lang_opt.config(state=state)
