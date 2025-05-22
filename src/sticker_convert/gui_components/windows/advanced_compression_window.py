#!/usr/bin/env python3
from __future__ import annotations

import re
from functools import partial
from tkinter import colorchooser
from typing import Any, List, Tuple

from PIL import Image, ImageDraw, ImageTk
from ttkbootstrap import Button, Canvas, Checkbutton, Entry, Frame, Label, LabelFrame, OptionMenu, Scrollbar, StringVar  # type: ignore

from sticker_convert.gui_components.frames.right_clicker import RightClicker
from sticker_convert.gui_components.gui_utils import GUIUtils
from sticker_convert.gui_components.windows.base_window import BaseWindow


class AdvancedCompressionWindow(BaseWindow):
    emoji_column_per_row = 8
    emoji_visible_rows = 5
    emoji_btns: List[Tuple[Button, ImageTk.PhotoImage]] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.categories = list({entry["category"] for entry in self.gui.emoji_list})

        self.title("Advanced compression options")

        self.frame_advcomp = LabelFrame(
            self.scrollable_frame, text="Advanced compression option"
        )
        self.frame_emoji_search = LabelFrame(
            self.scrollable_frame, text="Setting default emoji"
        )
        self.frame_emoji_canvas = Frame(self.scrollable_frame)

        self.frame_advcomp.grid_columnconfigure(6, weight=1)

        self.fps_help_btn = self.add_help_btn(self.gui.help["comp"]["fps"])
        self.fps_lbl = Label(self.frame_advcomp, text="Output FPS")
        self.fps_min_lbl = Label(self.frame_advcomp, text="Min:")
        self.fps_min_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.fps_min_var, width=8
        )
        self.fps_min_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.fps_max_lbl = Label(self.frame_advcomp, text="Max:")
        self.fps_max_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.fps_max_var, width=8
        )
        self.fps_max_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.fps_disable_cbox = Checkbutton(
            self.frame_advcomp,
            text="X",
            variable=self.gui.fps_disable_var,
            command=self.cb_disable_fps,
            onvalue=True,
            offvalue=False,
            bootstyle="danger-round-toggle",  # type: ignore
        )

        self.res_w_help_btn = self.add_help_btn(self.gui.help["comp"]["res"])
        self.res_w_lbl = Label(self.frame_advcomp, text="Output resolution (Width)")
        self.res_w_min_lbl = Label(self.frame_advcomp, text="Min:")
        self.res_w_min_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.res_w_min_var, width=8
        )
        self.res_w_min_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.res_w_max_lbl = Label(self.frame_advcomp, text="Max:")
        self.res_w_max_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.res_w_max_var, width=8
        )
        self.res_w_max_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.res_w_disable_cbox = Checkbutton(
            self.frame_advcomp,
            text="X",
            variable=self.gui.res_w_disable_var,
            command=self.cb_disable_res_w,
            onvalue=True,
            offvalue=False,
            bootstyle="danger-round-toggle",  # type: ignore
        )

        self.res_h_help_btn = self.add_help_btn(self.gui.help["comp"]["res"])
        self.res_h_lbl = Label(self.frame_advcomp, text="Output resolution (Height)")
        self.res_h_min_lbl = Label(self.frame_advcomp, text="Min:")
        self.res_h_min_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.res_h_min_var, width=8
        )
        self.res_h_min_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.res_h_max_lbl = Label(self.frame_advcomp, text="Max:")
        self.res_h_max_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.res_h_max_var, width=8
        )
        self.res_h_max_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.res_h_disable_cbox = Checkbutton(
            self.frame_advcomp,
            text="X",
            variable=self.gui.res_h_disable_var,
            command=self.cb_disable_res_h,
            onvalue=True,
            offvalue=False,
            bootstyle="danger-round-toggle",  # type: ignore
        )

        self.quality_help_btn = self.add_help_btn(self.gui.help["comp"]["quality"])
        self.quality_lbl = Label(self.frame_advcomp, text="Output quality (0-100)")
        self.quality_min_lbl = Label(self.frame_advcomp, text="Min:")
        self.quality_min_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.quality_min_var, width=8
        )
        self.quality_min_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.quality_max_lbl = Label(self.frame_advcomp, text="Max:")
        self.quality_max_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.quality_max_var, width=8
        )
        self.quality_max_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.quality_disable_cbox = Checkbutton(
            self.frame_advcomp,
            text="X",
            variable=self.gui.quality_disable_var,
            command=self.cb_disable_quality,
            onvalue=True,
            offvalue=False,
            bootstyle="danger-round-toggle",  # type: ignore
        )

        self.color_help_btn = self.add_help_btn(self.gui.help["comp"]["color"])
        self.color_lbl = Label(self.frame_advcomp, text="Colors (0-256)")
        self.color_min_lbl = Label(self.frame_advcomp, text="Min:")
        self.color_min_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.color_min_var, width=8
        )
        self.color_min_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.color_max_lbl = Label(self.frame_advcomp, text="Max:")
        self.color_max_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.color_max_var, width=8
        )
        self.color_max_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.color_disable_cbox = Checkbutton(
            self.frame_advcomp,
            text="X",
            variable=self.gui.color_disable_var,
            command=self.cb_disable_color,
            onvalue=True,
            offvalue=False,
            bootstyle="danger-round-toggle",  # type: ignore
        )

        self.duration_help_btn = self.add_help_btn(self.gui.help["comp"]["duration"])
        self.duration_lbl = Label(self.frame_advcomp, text="Duration (Miliseconds)")
        self.duration_min_lbl = Label(self.frame_advcomp, text="Min:")
        self.duration_min_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.duration_min_var, width=8
        )
        self.duration_min_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.duration_max_lbl = Label(self.frame_advcomp, text="Max:")
        self.duration_max_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.duration_max_var, width=8
        )
        self.duration_max_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.duration_disable_cbox = Checkbutton(
            self.frame_advcomp,
            text="X",
            variable=self.gui.duration_disable_var,
            command=self.cb_disable_duration,
            onvalue=True,
            offvalue=False,
            bootstyle="danger-round-toggle",  # type: ignore
        )

        self.size_help_btn = self.add_help_btn(self.gui.help["comp"]["size"])
        self.size_lbl = Label(self.frame_advcomp, text="Maximum file size (bytes)")
        self.img_size_max_lbl = Label(self.frame_advcomp, text="Img:")
        self.img_size_max_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.img_size_max_var, width=8
        )
        self.img_size_max_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.vid_size_max_lbl = Label(self.frame_advcomp, text="Vid:")
        self.vid_size_max_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.vid_size_max_var, width=8
        )
        self.vid_size_max_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.size_disable_cbox = Checkbutton(
            self.frame_advcomp,
            text="X",
            variable=self.gui.size_disable_var,
            command=self.cb_disable_size,
            onvalue=True,
            offvalue=False,
            bootstyle="danger-round-toggle",  # type: ignore
        )

        self.format_help_btn = self.add_help_btn(self.gui.help["comp"]["format"])
        self.format_lbl = Label(self.frame_advcomp, text="File format")
        self.img_format_lbl = Label(self.frame_advcomp, text="Img:")
        self.img_format_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.img_format_var, width=8
        )
        self.img_format_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.vid_format_lbl = Label(self.frame_advcomp, text="Vid:")
        self.vid_format_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.vid_format_var, width=8
        )
        self.vid_format_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.power_help_btn1 = self.add_help_btn(self.gui.help["comp"]["fps_power"])
        self.power_lbl1 = Label(self.frame_advcomp, text="Power (Importance)")
        self.fps_power_lbl = Label(self.frame_advcomp, text="FPS:")
        self.fps_power_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.fps_power_var, width=8
        )
        self.fps_power_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.res_power_lbl = Label(self.frame_advcomp, text="Res:")
        self.res_power_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.res_power_var, width=8
        )
        self.res_power_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.power_help_btn2 = self.add_help_btn(self.gui.help["comp"]["fps_power"])
        self.power_lbl2 = Label(self.frame_advcomp, text="Power (Importance)")
        self.quality_power_lbl = Label(self.frame_advcomp, text="Quality:")
        self.quality_power_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.quality_power_var, width=8
        )
        self.quality_power_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)
        self.color_power_lbl = Label(self.frame_advcomp, text="Color:")
        self.color_power_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.color_power_var, width=8
        )
        self.color_power_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.padding_percent_help_btn = self.add_help_btn(
            self.gui.help["comp"]["padding_percent"]
        )
        self.padding_percent_lbl1 = Label(self.frame_advcomp, text="Padding")
        self.padding_percent_lbl2 = Label(self.frame_advcomp, text="0-100%")
        self.padding_percent_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.padding_percent_var, width=8
        )
        self.padding_percent_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.fake_vid_help_btn = self.add_help_btn(self.gui.help["comp"]["fake_vid"])
        self.fake_vid_lbl = Label(
            self.frame_advcomp, text="Convert (faking) image to video"
        )
        self.fake_vid_cbox = Checkbutton(
            self.frame_advcomp,
            variable=self.gui.fake_vid_var,
            onvalue=True,
            offvalue=False,
            bootstyle="success-round-toggle",  # type: ignore
        )

        self.bg_color_help_btn = self.add_help_btn(self.gui.help["comp"]["bg_color"])
        self.bg_color_lbl = Label(self.frame_advcomp, text="Background color")
        self.bg_color_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.bg_color_var, width=8
        )
        self.bg_color_btn = Button(
            self.frame_advcomp,
            text="Set",
            command=self.cb_bg_color,
            bootstyle="secondary",  # type: ignore
        )

        self.scale_filter_help_btn = self.add_help_btn(
            self.gui.help["comp"]["scale_filter"]
        )
        self.scale_filter_lbl = Label(self.frame_advcomp, text="Scale filter")
        self.scale_filter_opt = OptionMenu(
            self.frame_advcomp,
            self.gui.scale_filter_var,
            self.gui.scale_filter_var.get(),
            "nearest",
            "box",
            "bilinear",
            "hamming",
            "bicubic",
            "lanczos",
            bootstyle="secondary",  # type: ignore
        )

        self.quantize_method_help_btn = self.add_help_btn(
            self.gui.help["comp"]["quantize_method"]
        )
        self.quantize_method_lbl = Label(self.frame_advcomp, text="Quantize method")
        self.quantize_method_opt = OptionMenu(
            self.frame_advcomp,
            self.gui.quantize_method_var,
            self.gui.quantize_method_var.get(),
            "imagequant",
            "fastoctree",
            "none",
            bootstyle="secondary",  # type: ignore
        )

        self.chromium_path_help_btn = self.add_help_btn(
            self.gui.help["comp"]["chromium_path"]
        )
        self.chromium_path_lbl = Label(
            self.frame_advcomp, text="Chromium/Chrome directory"
        )
        self.chromium_path_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.chromium_path_var, width=30
        )
        self.chromium_path_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.cache_dir_help_btn = self.add_help_btn(self.gui.help["comp"]["cache_dir"])
        self.cache_dir_lbl = Label(self.frame_advcomp, text="Custom cache directory")
        self.cache_dir_entry = Entry(
            self.frame_advcomp, textvariable=self.gui.cache_dir_var, width=30
        )
        self.cache_dir_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.default_emoji_help_btn = self.add_help_btn(
            self.gui.help["comp"]["default_emoji"]
        )
        self.default_emoji_lbl = Label(self.frame_advcomp, text="Default emoji")
        self.im: Image.Image = Image.new("RGBA", (32, 32), (255, 255, 255, 0))
        self.ph_im = ImageTk.PhotoImage(self.im)
        self.default_emoji_dsp = Label(self.frame_advcomp, image=self.ph_im)

        r = 0
        self.fps_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.fps_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.fps_min_lbl.grid(column=2, row=r, sticky="w", padx=3, pady=3)
        self.fps_min_entry.grid(column=3, row=r, sticky="nes", padx=3, pady=3)
        self.fps_max_lbl.grid(column=4, row=r, sticky="w", padx=3, pady=3)
        self.fps_max_entry.grid(column=5, row=r, sticky="nes", padx=3, pady=3)
        self.fps_disable_cbox.grid(column=6, row=r, sticky="nes", padx=3, pady=3)
        r += 1
        self.res_w_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.res_w_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.res_w_min_lbl.grid(column=2, row=r, sticky="w", padx=3, pady=3)
        self.res_w_min_entry.grid(column=3, row=r, sticky="nes", padx=3, pady=3)
        self.res_w_max_lbl.grid(column=4, row=r, sticky="w", padx=3, pady=3)
        self.res_w_max_entry.grid(column=5, row=r, sticky="nes", padx=3, pady=3)
        self.res_w_disable_cbox.grid(column=6, row=r, sticky="nes", padx=3, pady=3)
        r += 1
        self.res_h_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.res_h_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.res_h_min_lbl.grid(column=2, row=r, sticky="w", padx=3, pady=3)
        self.res_h_min_entry.grid(column=3, row=r, sticky="nes", padx=3, pady=3)
        self.res_h_max_lbl.grid(column=4, row=r, sticky="w", padx=3, pady=3)
        self.res_h_max_entry.grid(column=5, row=r, sticky="nes", padx=3, pady=3)
        self.res_h_disable_cbox.grid(column=6, row=r, sticky="nes", padx=3, pady=3)
        r += 1
        self.quality_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.quality_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.quality_min_lbl.grid(column=2, row=r, sticky="w", padx=3, pady=3)
        self.quality_min_entry.grid(column=3, row=r, sticky="nes", padx=3, pady=3)
        self.quality_max_lbl.grid(column=4, row=r, sticky="w", padx=3, pady=3)
        self.quality_max_entry.grid(column=5, row=r, sticky="nes", padx=3, pady=3)
        self.quality_disable_cbox.grid(column=6, row=r, sticky="nes", padx=3, pady=3)
        r += 1
        self.color_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.color_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.color_min_lbl.grid(column=2, row=r, sticky="w", padx=3, pady=3)
        self.color_min_entry.grid(column=3, row=r, sticky="nes", padx=3, pady=3)
        self.color_max_lbl.grid(column=4, row=r, sticky="w", padx=3, pady=3)
        self.color_max_entry.grid(column=5, row=r, sticky="nes", padx=3, pady=3)
        self.color_disable_cbox.grid(column=6, row=r, sticky="nes", padx=3, pady=3)
        r += 1
        self.duration_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.duration_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.duration_min_lbl.grid(column=2, row=r, sticky="w", padx=3, pady=3)
        self.duration_min_entry.grid(column=3, row=r, sticky="nes", padx=3, pady=3)
        self.duration_max_lbl.grid(column=4, row=r, sticky="w", padx=3, pady=3)
        self.duration_max_entry.grid(column=5, row=r, sticky="nes", padx=3, pady=3)
        self.duration_disable_cbox.grid(column=6, row=r, sticky="nes", padx=3, pady=3)
        r += 1
        self.size_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.size_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.img_size_max_lbl.grid(column=2, row=r, sticky="w", padx=3, pady=3)
        self.img_size_max_entry.grid(column=3, row=r, sticky="nes", padx=3, pady=3)
        self.vid_size_max_lbl.grid(column=4, row=r, sticky="w", padx=3, pady=3)
        self.vid_size_max_entry.grid(column=5, row=r, sticky="nes", padx=3, pady=3)
        self.size_disable_cbox.grid(column=6, row=r, sticky="nes", padx=3, pady=3)
        r += 1
        self.format_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.format_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.img_format_lbl.grid(column=2, row=r, sticky="w", padx=3, pady=3)
        self.img_format_entry.grid(column=3, row=r, sticky="nes", padx=3, pady=3)
        self.vid_format_lbl.grid(column=4, row=r, sticky="w", padx=3, pady=3)
        self.vid_format_entry.grid(column=5, row=r, sticky="nes", padx=3, pady=3)
        r += 1
        self.power_help_btn1.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.power_lbl1.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.fps_power_lbl.grid(column=2, row=r, sticky="w", padx=3, pady=3)
        self.fps_power_entry.grid(column=3, row=r, sticky="w", padx=3, pady=3)
        self.res_power_lbl.grid(column=4, row=r, sticky="w", padx=3, pady=3)
        self.res_power_entry.grid(column=5, row=r, sticky="w", padx=3, pady=3)
        r += 1
        self.power_help_btn2.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.power_lbl2.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.quality_power_lbl.grid(column=2, row=r, sticky="w", padx=3, pady=3)
        self.quality_power_entry.grid(column=3, row=r, sticky="w", padx=3, pady=3)
        self.color_power_lbl.grid(column=4, row=r, sticky="w", padx=3, pady=3)
        self.color_power_entry.grid(column=5, row=r, sticky="w", padx=3, pady=3)
        r += 1
        self.padding_percent_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.padding_percent_lbl1.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.padding_percent_lbl2.grid(column=2, row=r, sticky="w", padx=3, pady=3)
        self.padding_percent_entry.grid(column=3, row=r, sticky="w", padx=3, pady=3)
        r += 1
        self.fake_vid_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.fake_vid_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.fake_vid_cbox.grid(column=6, row=r, sticky="nes", padx=3, pady=3)
        r += 1
        self.bg_color_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.bg_color_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.bg_color_entry.grid(column=5, row=r, sticky="w", padx=3, pady=3)
        self.bg_color_btn.grid(column=6, row=r, sticky="nes", padx=3, pady=3)
        r += 1
        self.scale_filter_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.scale_filter_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.scale_filter_opt.grid(
            column=2, row=r, columnspan=4, sticky="nes", padx=3, pady=3
        )
        r += 1
        self.quantize_method_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.quantize_method_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.quantize_method_opt.grid(
            column=2, row=r, columnspan=4, sticky="nes", padx=3, pady=3
        )
        r += 1
        self.chromium_path_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.chromium_path_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.chromium_path_entry.grid(
            column=2, row=r, columnspan=4, sticky="nes", padx=3, pady=3
        )
        r += 1
        self.cache_dir_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.cache_dir_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.cache_dir_entry.grid(
            column=2, row=r, columnspan=4, sticky="nes", padx=3, pady=3
        )
        r += 1
        self.default_emoji_help_btn.grid(column=0, row=r, sticky="w", padx=3, pady=3)
        self.default_emoji_lbl.grid(column=1, row=r, sticky="w", padx=3, pady=3)
        self.default_emoji_dsp.grid(column=6, row=r, sticky="nes", padx=3, pady=3)

        # https://stackoverflow.com/questions/43731784/tkinter-canvas-scrollbar-with-grid
        # Create a frame for the canvas with non-zero row&column weights
        self.frame_emoji_canvas.grid_rowconfigure(0, weight=1)
        self.frame_emoji_canvas.grid_columnconfigure(0, weight=1)
        # Set grid_propagate to False to allow buttons resizing later
        self.frame_emoji_canvas.grid_propagate(False)

        self.frame_advcomp.grid(column=0, row=0, sticky="news", padx=3, pady=3)
        self.frame_emoji_search.grid(column=0, row=1, sticky="news", padx=3, pady=3)
        self.frame_emoji_canvas.grid(column=0, row=2, sticky="news", padx=3, pady=3)

        self.categories_lbl = Label(
            self.frame_emoji_search,
            text="Category",
            width=15,
            justify="left",
            anchor="w",
        )
        self.categories_var = StringVar(self.scrollable_frame)
        self.categories_var.set("Smileys & Emotion")
        self.categories_opt = OptionMenu(
            self.frame_emoji_search,
            self.categories_var,
            "Smileys & Emotion",
            *self.categories,
            command=self.render_emoji_list,
            bootstyle="secondary",  # type: ignore
        )
        self.categories_opt.config(width=30)

        self.search_lbl = Label(self.frame_emoji_search, text="Search")
        self.search_var = StringVar(self.frame_emoji_search)
        self.search_var.trace_add("write", self.render_emoji_list)
        self.search_entry = Entry(self.frame_emoji_search, textvariable=self.search_var)
        self.search_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.categories_lbl.grid(column=0, row=0, sticky="nsw", padx=3, pady=3)
        self.categories_opt.grid(column=1, row=0, sticky="news", padx=3, pady=3)
        self.search_lbl.grid(column=0, row=1, sticky="nsw", padx=3, pady=3)
        self.search_entry.grid(column=1, row=1, sticky="news", padx=3, pady=3)

        # Add a canvas in frame_emoji_canvas
        self.emoji_canvas = Canvas(self.frame_emoji_canvas)
        self.emoji_canvas.grid(row=0, column=0, sticky="news")

        # Link a scrollbar to the canvas
        self.vsb = Scrollbar(
            self.frame_emoji_canvas,
            orient="vertical",
            command=self.emoji_canvas.yview,  # type: ignore
        )
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.emoji_canvas.configure(yscrollcommand=self.vsb.set)

        self.frame_buttons = Frame(self.emoji_canvas)
        self.emoji_canvas.create_window((0, 0), window=self.frame_buttons, anchor="nw")

        self.render_emoji_list()

        self.set_emoji_btn()
        self.cb_disable_fps()
        self.cb_disable_res_w()
        self.cb_disable_res_h()
        self.cb_disable_quality()
        self.cb_disable_color()
        self.cb_disable_duration()
        self.cb_disable_size()
        self.cb_disable_format()
        self.cb_disable_fake_vid()

        GUIUtils.finalize_window(self)

    def cb_disable_fps(self, *_: Any) -> None:
        if self.gui.fps_disable_var.get() is True:
            state = "disabled"
        else:
            state = "normal"

        self.fps_min_entry.config(state=state)
        self.fps_max_entry.config(state=state)

    def cb_disable_res_w(self, *_: Any) -> None:
        if self.gui.res_w_disable_var.get() is True:
            state = "disabled"
        else:
            state = "normal"

        self.res_w_min_entry.config(state=state)
        self.res_w_max_entry.config(state=state)

    def cb_disable_res_h(self, *_: Any) -> None:
        if self.gui.res_h_disable_var.get() is True:
            state = "disabled"
        else:
            state = "normal"

        self.res_h_min_entry.config(state=state)
        self.res_h_max_entry.config(state=state)

    def cb_disable_quality(self, *_: Any) -> None:
        if self.gui.quality_disable_var.get() is True:
            state = "disabled"
        else:
            state = "normal"

        self.quality_min_entry.config(state=state)
        self.quality_max_entry.config(state=state)

    def cb_disable_color(self, *_: Any) -> None:
        if self.gui.color_disable_var.get() is True:
            state = "disabled"
        else:
            state = "normal"

        self.color_min_entry.config(state=state)
        self.color_max_entry.config(state=state)

    def cb_disable_duration(self, *_: Any) -> None:
        if (
            self.gui.duration_disable_var.get() is True
            or self.gui.comp_preset_var.get() == "auto"
        ):
            state = "disabled"
        else:
            state = "normal"

        self.duration_min_entry.config(state=state)
        self.duration_max_entry.config(state=state)

    def cb_disable_size(self, *_: Any) -> None:
        if (
            self.gui.size_disable_var.get() is True
            or self.gui.comp_preset_var.get() == "auto"
        ):
            state = "disabled"
        else:
            state = "normal"

        self.img_size_max_entry.config(state=state)
        self.vid_size_max_entry.config(state=state)

    def cb_disable_format(self, *_: Any) -> None:
        if self.gui.comp_preset_var.get() == "auto":
            state = "disabled"
        else:
            state = "normal"

        self.img_format_entry.config(state=state)
        self.vid_format_entry.config(state=state)

    def cb_disable_fake_vid(self, *_: Any) -> None:
        if self.gui.comp_preset_var.get() == "auto":
            state = "disabled"
        else:
            state = "normal"

        self.fake_vid_cbox.config(state=state)

    def cb_bg_color(self, *_: Any) -> None:
        color_init = "#" + self.gui.bg_color_var.get()[:6]
        color_init = (
            color_init if re.search(r"^#(?:[0-9a-fA-F]{3}){1,2}$", color_init) else None
        )
        color = colorchooser.askcolor(
            title="Choose color",
            color=color_init,
            parent=self,
        )[1]
        if color:
            self.gui.bg_color_var.set(color.replace("#", "") + "00")
        self.lift()  # type: ignore
        self.attributes("-topmost", True)  # type: ignore
        self.attributes("-topmost", False)  # type: ignore

    def cb_bound_to_mousewheel(self, event: Any) -> None:
        for i in self.mousewheel:
            self.emoji_canvas.bind_all(i, self.cb_on_mousewheel)

    def cb_unbound_to_mousewheel(self, event: Any) -> None:
        for i in self.mousewheel:
            self.emoji_canvas.unbind_all(i)

    def cb_on_mousewheel(self, event: Any) -> None:
        self.emoji_canvas.yview_scroll(
            int(-1 * (event.delta / self.delta_divide)), "units"
        )  # type: ignore

    def cb_set_emoji(self, emoji: str) -> None:
        self.gui.default_emoji_var.set(emoji)
        self.set_emoji_btn()

    def add_help_btn(self, msg: str) -> Button:
        cb_msg_block_adv_comp_win = partial(self.gui.cb_msg_block, parent=self)

        return Button(
            self.frame_advcomp,
            text="?",
            width=1,
            command=lambda: cb_msg_block_adv_comp_win(msg),
            bootstyle="secondary",  # type: ignore
        )

    def set_emoji_btn(self) -> None:
        self.im = Image.new("RGBA", (128, 128), (255, 255, 255, 0))
        ImageDraw.Draw(self.im).text(  # type: ignore
            (0, 0),
            self.gui.default_emoji_var.get(),
            embedded_color=True,
            font=self.gui.emoji_font,
        )  # type: ignore
        self.im = self.im.resize((32, 32))
        self.ph_im = ImageTk.PhotoImage(self.im)
        self.default_emoji_dsp.config(image=self.ph_im)

    def render_emoji_list(self, *_: Any) -> None:
        category = self.categories_var.get()

        for emoji_btn, ph_im in self.emoji_btns:
            emoji_btn.destroy()
            del ph_im

        column = 0
        row = 0

        self.emoji_btns = []
        for entry in self.gui.emoji_list:
            # Filtering
            search_term = self.search_var.get().lower()
            emoji = entry["emoji"]
            keywords = entry["aliases"] + entry["tags"] + [emoji]
            if search_term == "":
                if entry["category"] != category:
                    continue
            else:
                ok = False

                if search_term in keywords:
                    ok = True
                elif len(search_term) >= 3:
                    for i in keywords:
                        if search_term in i:
                            ok = True

                if ok is False:
                    continue

            im = Image.new("RGBA", (196, 196), (255, 255, 255, 0))
            ImageDraw.Draw(im).text(  # type: ignore
                (16, 16), emoji, embedded_color=True, font=self.gui.emoji_font
            )  # type: ignore
            im = im.resize((32, 32))
            ph_im = ImageTk.PhotoImage(im)

            button = Button(
                self.frame_buttons,
                command=lambda i=emoji: self.cb_set_emoji(i),  # type: ignore
                bootstyle="dark",  # type: ignore
            )
            button.config(image=ph_im)
            button.grid(column=column, row=row)

            column += 1

            if column == self.emoji_column_per_row:
                column = 0
                row += 1

            self.emoji_btns.append((button, ph_im))

        # Update buttons frames idle tasks to let tkinter calculate buttons sizes
        self.frame_buttons.update_idletasks()

        # Resize the canvas frame to show specified number of buttons and the scrollbar
        if len(self.emoji_btns) > 0:
            in_view_columns_width = (
                self.emoji_btns[0][0].winfo_width() * self.emoji_column_per_row
            )
            in_view_rows_height = (
                self.emoji_btns[0][0].winfo_height() * self.emoji_visible_rows
            )
            self.frame_emoji_canvas.config(
                width=in_view_columns_width + self.vsb.winfo_width(),
                height=in_view_rows_height,
            )

        # Set the canvas scrolling region
        self.emoji_canvas.config(scrollregion=self.emoji_canvas.bbox("all"))

        # https://stackoverflow.com/questions/17355902/tkinter-binding-mousewheel-to-scrollbar
        self.emoji_canvas.bind("<Enter>", self.cb_bound_to_mousewheel)
        self.emoji_canvas.bind("<Leave>", self.cb_unbound_to_mousewheel)
