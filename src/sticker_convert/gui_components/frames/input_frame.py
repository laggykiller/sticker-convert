#!/usr/bin/env python3
from pathlib import Path
from tkinter import filedialog
from typing import TYPE_CHECKING, Any

from ttkbootstrap import Button, Entry, Label, LabelFrame, OptionMenu  # type: ignore

from sticker_convert.definitions import DEFAULT_DIR
from sticker_convert.gui_components.frames.right_clicker import RightClicker
from sticker_convert.utils.url_detect import UrlDetect

if TYPE_CHECKING:
    from sticker_convert.gui import GUI  # type: ignore


class InputFrame(LabelFrame):
    def __init__(self, gui: "GUI", *args: Any, **kwargs: Any) -> None:
        self.gui = gui
        super().__init__(*args, **kwargs)

        self.input_option_lbl = Label(
            self, text="Input source", width=15, justify="left", anchor="w"
        )
        input_full_names = [i["full_name"] for i in self.gui.input_presets.values()]
        default_input_full_name = self.gui.input_presets[self.gui.default_input_mode][
            "full_name"
        ]
        self.input_option_opt = OptionMenu(
            self,
            self.gui.input_option_display_var,
            default_input_full_name,
            *input_full_names,
            command=self.cb_input_option,
            bootstyle="secondary",  # type: ignore
        )
        self.input_option_opt.config(width=32)

        self.input_setdir_lbl = Label(
            self, text="Input directory", width=35, justify="left", anchor="w"
        )
        self.input_setdir_entry = Entry(
            self,
            textvariable=self.gui.input_setdir_var,
            width=60,
            validatecommand=self.gui.highlight_fields,
        )
        self.input_setdir_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.setdir_btn = Button(
            self,
            text="Choose directory",
            command=self.cb_set_indir,
            width=16,
            bootstyle="secondary",  # type: ignore
        )

        self.address_lbl = Label(
            self,
            text=self.gui.input_presets[self.gui.default_input_mode]["address_lbls"],
            width=18,
            justify="left",
            anchor="w",
        )
        self.address_entry = Entry(
            self,
            textvariable=self.gui.input_address_var,
            width=80,
            validate="focusout",
            validatecommand=self.cb_input_option,
        )
        self.address_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.address_tip = Label(
            self,
            text=self.gui.input_presets[self.gui.default_input_mode]["example"],
            justify="left",
            anchor="w",
        )

        self.input_option_lbl.grid(column=0, row=0, sticky="w", padx=3, pady=3)
        self.input_option_opt.grid(
            column=1, row=0, columnspan=2, sticky="w", padx=3, pady=3
        )
        self.input_setdir_lbl.grid(
            column=0, row=1, columnspan=2, sticky="w", padx=3, pady=3
        )
        self.input_setdir_entry.grid(column=1, row=1, sticky="w", padx=3, pady=3)
        self.setdir_btn.grid(column=2, row=1, sticky="e", padx=3, pady=3)
        self.address_lbl.grid(column=0, row=2, sticky="w", padx=3, pady=3)
        self.address_entry.grid(
            column=1, row=2, columnspan=2, sticky="w", padx=3, pady=3
        )
        self.address_tip.grid(column=0, row=3, columnspan=3, sticky="w", padx=3, pady=3)

        preset = [
            k
            for k, v in self.gui.input_presets.items()
            if v["full_name"] == self.gui.input_option_display_var.get()
        ][0]
        if preset == "local":
            self.address_entry.config(state="disabled")
        else:
            self.address_entry.config(state="normal")

    def cb_set_indir(self, *_args: Any) -> None:
        orig_input_dir = self.gui.input_setdir_var.get()
        if not Path(orig_input_dir).is_dir():
            orig_input_dir = DEFAULT_DIR
        input_dir = filedialog.askdirectory(initialdir=orig_input_dir)
        if input_dir:
            self.gui.input_setdir_var.set(input_dir)

    def cb_input_option(self, *_: Any) -> bool:
        input_option_display = self.gui.get_input_display_name()

        if input_option_display == "auto":
            url = self.gui.input_address_var.get()
            download_option = UrlDetect.detect(url)

            if download_option is None:
                self.gui.input_option_true_var.set(
                    self.gui.input_presets["auto"]["full_name"]
                )
            else:
                self.gui.input_option_true_var.set(
                    self.gui.input_presets[download_option]["full_name"]
                )
        else:
            self.gui.input_option_true_var.set(self.gui.input_option_display_var.get())

        self.gui.highlight_fields()

        return True

    def set_states(self, state: str) -> None:
        self.input_option_opt.config(state=state)
        self.address_entry.config(state=state)
        self.input_setdir_entry.config(state=state)
        self.setdir_btn.config(state=state)
