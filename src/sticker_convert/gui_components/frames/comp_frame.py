#!/usr/bin/env python3
from typing import TYPE_CHECKING, Any

from ttkbootstrap import Button, Checkbutton, Entry, Label, LabelFrame, OptionMenu  # type: ignore

from sticker_convert.gui_components.frames.right_clicker import RightClicker
from sticker_convert.gui_components.windows.advanced_compression_window import AdvancedCompressionWindow

if TYPE_CHECKING:
    from sticker_convert.gui import GUI  # type: ignore


class CompFrame(LabelFrame):
    def __init__(self, gui: "GUI", *args: Any, **kwargs: Any) -> None:
        self.gui = gui
        super().__init__(*args, **kwargs)

        self.grid_columnconfigure(2, weight=1)

        self.no_compress_help_btn = Button(
            self,
            text="?",
            width=1,
            command=lambda: self.gui.cb_msg_block(self.gui.help["comp"]["no_compress"]),
            bootstyle="secondary",  # type: ignore
        )
        self.no_compress_lbl = Label(self, text="No compression")
        self.no_compress_cbox = Checkbutton(
            self,
            variable=self.gui.no_compress_var,
            command=self.cb_no_compress,
            onvalue=True,
            offvalue=False,
            bootstyle="danger-round-toggle",  # type: ignore
        )

        self.comp_preset_help_btn = Button(
            self,
            text="?",
            width=1,
            command=lambda: self.gui.cb_msg_block(self.gui.help["comp"]["preset"]),
            bootstyle="secondary",  # type: ignore
        )
        self.comp_preset_lbl = Label(self, text="Preset")
        self.comp_preset_opt = OptionMenu(
            self,
            self.gui.comp_preset_var,
            self.gui.comp_preset_var.get(),
            *self.gui.compression_presets.keys(),
            command=self.cb_comp_apply_preset,
            bootstyle="secondary",  # type: ignore
        )
        self.comp_preset_opt.config(width=15)

        self.steps_help_btn = Button(
            self,
            text="?",
            width=1,
            command=lambda: self.gui.cb_msg_block(self.gui.help["comp"]["steps"]),
            bootstyle="secondary",  # type: ignore
        )
        self.steps_lbl = Label(self, text="Number of steps")
        self.steps_entry = Entry(self, textvariable=self.gui.steps_var, width=8)
        self.steps_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.processes_help_btn = Button(
            self,
            text="?",
            width=1,
            command=lambda: self.gui.cb_msg_block(self.gui.help["comp"]["processes"]),
            bootstyle="secondary",  # type: ignore
        )
        self.processes_lbl = Label(self, text="Number of processes")
        self.processes_entry = Entry(self, textvariable=self.gui.processes_var, width=8)
        self.processes_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.comp_advanced_btn = Button(
            self,
            text="Advanced...",
            command=self.cb_compress_advanced,
            bootstyle="secondary",  # type: ignore
        )

        self.no_compress_help_btn.grid(column=0, row=0, sticky="w", padx=3, pady=3)
        self.no_compress_lbl.grid(column=1, row=0, sticky="w", padx=3, pady=3)
        self.no_compress_cbox.grid(column=2, row=0, sticky="nes", padx=3, pady=3)

        self.comp_preset_help_btn.grid(column=0, row=1, sticky="w", padx=3, pady=3)
        self.comp_preset_lbl.grid(column=1, row=1, sticky="w", padx=3, pady=3)
        self.comp_preset_opt.grid(column=2, row=1, sticky="nes", padx=3, pady=3)

        self.steps_help_btn.grid(column=0, row=2, sticky="w", padx=3, pady=3)
        self.steps_lbl.grid(column=1, row=2, sticky="w", padx=3, pady=3)
        self.steps_entry.grid(column=2, row=2, sticky="nes", padx=3, pady=3)

        self.processes_help_btn.grid(column=0, row=3, sticky="w", padx=3, pady=3)
        self.processes_lbl.grid(column=1, row=3, sticky="w", padx=3, pady=3)
        self.processes_entry.grid(column=2, row=3, sticky="nes", padx=3, pady=3)

        self.comp_advanced_btn.grid(column=2, row=4, sticky="nes", padx=3, pady=3)

        self.cb_comp_apply_preset()
        self.cb_no_compress()

    def cb_comp_apply_preset(self, *_: Any) -> None:
        selection = self.gui.get_preset()
        if selection == "auto":
            if self.gui.get_input_name() == "local":
                self.gui.no_compress_var.set(True)
            else:
                self.gui.no_compress_var.set(False)

        preset = self.gui.compression_presets[selection]
        self.gui.fps_min_var.set(preset.get("fps", {}).get("min"))
        self.gui.fps_max_var.set(preset.get("fps", {}).get("max"))
        self.gui.fps_power_var.set(preset.get("fps", {}).get("power"))
        self.gui.res_w_min_var.set(preset.get("res", {}).get("w", {}).get("min"))
        self.gui.res_w_max_var.set(preset.get("res", {}).get("w", {}).get("max"))
        self.gui.res_h_min_var.set(preset.get("res", {}).get("h", {}).get("min"))
        self.gui.res_h_max_var.set(preset.get("res", {}).get("h", {}).get("max"))
        self.gui.res_power_var.set(preset.get("res", {}).get("power"))
        self.gui.quality_min_var.set(preset.get("quality", {}).get("min"))
        self.gui.quality_max_var.set(preset.get("quality", {}).get("max"))
        self.gui.quality_power_var.set(preset.get("quality", {}).get("power"))
        self.gui.color_min_var.set(preset.get("color", {}).get("min"))
        self.gui.color_max_var.set(preset.get("color", {}).get("max"))
        self.gui.color_power_var.set(preset.get("color", {}).get("power"))
        self.gui.duration_min_var.set(preset.get("duration", {}).get("min"))
        self.gui.duration_max_var.set(preset.get("duration", {}).get("max"))
        self.gui.img_size_max_var.set(preset.get("size_max", {}).get("img"))
        self.gui.vid_size_max_var.set(preset.get("size_max", {}).get("vid"))
        self.gui.img_format_var.set(preset.get("format", {}).get("img"))
        self.gui.vid_format_var.set(preset.get("format", {}).get("vid"))
        self.gui.bg_color_var.set(preset.get("bg_color"))
        self.gui.fake_vid_var.set(preset.get("fake_vid"))
        self.gui.scale_filter_var.set(preset.get("scale_filter"))
        self.gui.quantize_method_var.set(preset.get("quantize_method"))
        self.gui.default_emoji_var.set(preset.get("default_emoji"))
        self.gui.steps_var.set(preset.get("steps"))

        self.cb_no_compress()
        self.gui.highlight_fields()

    def cb_compress_advanced(self, *_: Any) -> None:
        AdvancedCompressionWindow(self.gui)

    def cb_no_compress(self, *_: Any) -> None:
        if self.gui.no_compress_var.get() is True:
            state = "disabled"
        else:
            state = "normal"

        self.comp_advanced_btn.config(state=state)
        self.steps_entry.config(state=state)
        self.processes_entry.config(state=state)

    def set_inputs_comp(self, state: str) -> None:
        self.comp_preset_opt.config(state=state)
        self.comp_advanced_btn.config(state=state)
        self.steps_entry.config(state=state)
        self.processes_entry.config(state=state)

    def set_states(self, state: str) -> None:
        self.no_compress_cbox.config(state=state)
        self.set_inputs_comp(state=state)
