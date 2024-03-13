#!/usr/bin/env python3
from __future__ import annotations

import platform
from typing import TYPE_CHECKING, Tuple, Union

from ttkbootstrap import Canvas, Frame, PhotoImage, Scrollbar  # type: ignore

from sticker_convert.definitions import ROOT_DIR

if TYPE_CHECKING:
    from sticker_convert.gui import GUI
    from sticker_convert.gui_components.windows.base_window import BaseWindow


class GUIUtils:
    @staticmethod
    def set_icon(window: Union["BaseWindow", "GUI"]) -> None:
        window.icon = PhotoImage(file=ROOT_DIR / "resources/appicon.png")  # type: ignore
        window.iconphoto(1, window.icon)  # type: ignore
        if platform.system() == "Darwin":
            window.iconbitmap(bitmap=ROOT_DIR / "resources/appicon.icns")  # type: ignore
        elif platform.system() == "Windows":
            window.iconbitmap(bitmap=ROOT_DIR / "resources/appicon.ico")  # type: ignore
        window.tk.call("wm", "iconphoto", window._w, window.icon)  # type: ignore

    @staticmethod
    def create_scrollable_frame(
        window: Union["BaseWindow", "GUI"],
    ) -> Tuple[Frame, Frame, Canvas, Scrollbar, Scrollbar, Frame]:
        main_frame = Frame(window)
        main_frame.pack(fill="both", expand=1)

        horizontal_scrollbar_frame = Frame(main_frame)
        horizontal_scrollbar_frame.pack(fill="x", side="bottom")

        canvas = Canvas(main_frame)
        canvas.pack(side="left", fill="both", expand=1)

        x_scrollbar = Scrollbar(
            horizontal_scrollbar_frame,
            orient="horizontal",
            command=canvas.xview,  # type: ignore
        )
        x_scrollbar.pack(side="bottom", fill="x")

        y_scrollbar = Scrollbar(main_frame, orient="vertical", command=canvas.yview)  # type: ignore
        y_scrollbar.pack(side="right", fill="y")

        canvas.configure(xscrollcommand=x_scrollbar.set)
        canvas.configure(yscrollcommand=y_scrollbar.set)
        canvas.bind(
            "<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all"))
        )

        scrollable_frame = Frame(canvas)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        return (
            main_frame,
            horizontal_scrollbar_frame,
            canvas,
            x_scrollbar,
            y_scrollbar,
            scrollable_frame,
        )

    @staticmethod
    def finalize_window(window: Union["GUI", "BaseWindow"]) -> None:
        window.attributes("-alpha", 0)  # type: ignore

        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenwidth()

        window.scrollable_frame.update_idletasks()

        frame_width = window.scrollable_frame.winfo_width()
        frame_height = window.scrollable_frame.winfo_height()

        window_width = frame_width + window.y_scrollbar.winfo_width()
        window_height = frame_height + window.x_scrollbar.winfo_height()

        window_width = min(window_width, screen_width)
        window_height = min(window_height, screen_height)

        frame_width = window_width - window.y_scrollbar.winfo_width()
        frame_height = window_height - window.x_scrollbar.winfo_height()

        window.maxsize(width=window_width, height=window_height)
        window.canvas.configure(width=frame_width, height=frame_height)

        window.place_window_center()

        window.attributes("-alpha", 1)  # type: ignore

        window.focus_force()
