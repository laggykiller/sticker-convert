#!/usr/bin/env python3
from __future__ import annotations
import platform
from typing import Union, TYPE_CHECKING

from ttkbootstrap import Frame, Canvas, Scrollbar, PhotoImage

if TYPE_CHECKING:
    from .windows.base_window import BaseWindow  # type: ignore
    from ..gui import GUI  # type: ignore


class GUIUtils:
    @staticmethod
    def set_icon(window: Union["BaseWindow", "GUI"]):
        window.icon = PhotoImage(file="resources/appicon.png")
        window.iconphoto(1, window.icon)
        if platform.system() == "Darwin":
            window.iconbitmap(bitmap="resources/appicon.icns")
        elif platform.system() == "Windows":
            window.iconbitmap(bitmap="resources/appicon.ico")
        window.tk.call("wm", "iconphoto", window._w, window.icon)

    @staticmethod
    def create_scrollable_frame(
        window: Union["BaseWindow", "GUI"]
    ) -> tuple[Frame, Frame, Canvas, Scrollbar, Scrollbar, Frame]:
        main_frame = Frame(window)
        main_frame.pack(fill="both", expand=1)

        horizontal_scrollbar_frame = Frame(main_frame)
        horizontal_scrollbar_frame.pack(fill="x", side="bottom")

        canvas = Canvas(main_frame)
        canvas.pack(side="left", fill="both", expand=1)

        x_scrollbar = Scrollbar(
            horizontal_scrollbar_frame, orient="horizontal", command=canvas.xview
        )
        x_scrollbar.pack(side="bottom", fill="x")

        y_scrollbar = Scrollbar(main_frame, orient="vertical", command=canvas.yview)
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
    def finalize_window(window: Union["GUI", "BaseWindow"]):
        window.attributes("-alpha", 0)

        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenwidth()

        window.scrollable_frame.update_idletasks()

        frame_width = window.scrollable_frame.winfo_width()
        frame_height = window.scrollable_frame.winfo_height()

        window_width = frame_width + window.y_scrollbar.winfo_width()
        window_height = frame_height + window.x_scrollbar.winfo_height()

        if window_width > screen_width:
            window_width = screen_width
        if window_height > screen_height:
            window_height = screen_height

        frame_width = window_width - window.y_scrollbar.winfo_width()
        frame_height = window_height - window.x_scrollbar.winfo_height()

        window.maxsize(width=window_width, height=window_height)
        window.canvas.configure(width=frame_width, height=frame_height)

        window.place_window_center()

        window.attributes("-alpha", 1)

        window.focus_force()
