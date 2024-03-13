#!/usr/bin/env python3
from typing import TYPE_CHECKING, Any

from ttkbootstrap import Button, Frame  # type: ignore

if TYPE_CHECKING:
    from sticker_convert.gui import GUI


class ControlFrame(Frame):
    def __init__(self, gui: "GUI", *args: Any, **kwargs: Any) -> None:
        self.gui = gui
        super().__init__(*args, **kwargs)

        self.start_btn = Button(
            self,
            text="Start",
            command=self.cb_start_btn,
            bootstyle="default",  # type: ignore
        )

        self.start_btn.pack(expand=True, fill="x")

    def cb_start_btn(self, *args: Any, **kwargs: Any) -> None:
        if self.gui.job:
            response = self.gui.cb_ask_bool("Cancel job?")
            if response is True:
                self.gui.cancel_job()
        else:
            self.gui.start_job()
