#!/usr/bin/env python3
from typing import TYPE_CHECKING, Any

from tqdm import tqdm
from ttkbootstrap import LabelFrame, Progressbar  # type: ignore
from ttkbootstrap.scrolled import ScrolledText  # type: ignore

if TYPE_CHECKING:
    from sticker_convert.gui import GUI  # type: ignore

from sticker_convert.gui_components.frames.right_clicker import RightClicker


class ProgressFrame(LabelFrame):
    progress_bar_cli = None
    progress_bar_steps = 0
    auto_scroll = True

    def __init__(self, gui: "GUI", *args: Any, **kwargs: Any):
        self.gui = gui
        super(ProgressFrame, self).__init__(*args, **kwargs)  # type: ignore

        self.message_box = ScrolledText(self, height=15, wrap="word")
        self.message_box._text.bind("<Button-3><ButtonRelease-3>", RightClicker)  # type: ignore
        self.message_box._text.config(state="disabled")  # type: ignore
        self.progress_bar = Progressbar(self, orient="horizontal", mode="determinate")

        self.message_box.bind("<Enter>", self.cb_disable_autoscroll)
        self.message_box.bind("<Leave>", self.cb_enable_autoscroll)

        self.message_box.pack(expand=True, fill="x")
        self.progress_bar.pack(expand=True, fill="x")

    def update_progress_bar(
        self, set_progress_mode: str = "", steps: int = 0, update_bar: bool = False
    ):
        if update_bar and self.progress_bar_cli:
            self.progress_bar_cli.update()
            self.progress_bar["value"] += 100 / self.progress_bar_steps
        elif set_progress_mode == "determinate":
            self.progress_bar_cli = tqdm(total=steps)
            self.progress_bar.config(mode="determinate")
            self.progress_bar_steps = steps
            self.progress_bar.stop()
            self.progress_bar["value"] = 0
        elif set_progress_mode == "indeterminate":
            if self.progress_bar_cli:
                self.progress_bar_cli.close()
                self.progress_bar_cli = None
            self.progress_bar["value"] = 0
            self.progress_bar.config(mode="indeterminate")
            self.progress_bar.start(50)
        elif set_progress_mode == "clear":
            if self.progress_bar_cli:
                self.progress_bar_cli.reset()
            self.progress_bar.config(mode="determinate")
            self.progress_bar.stop()
            self.progress_bar["value"] = 0

    def update_message_box(self, *args: Any, **kwargs: Any):
        msg = kwargs.get("msg")
        cls = kwargs.get("cls")
        file = kwargs.get("file")

        if not msg and len(args) == 1:
            msg = str(args[0])

        if msg:
            if self.progress_bar_cli:
                self.progress_bar_cli.write(msg)
            elif file:
                print(msg, file=file)
            else:
                print(msg)
            msg += "\n"

        self.message_box._text.config(state="normal")  # type: ignore

        if cls:
            self.message_box.delete(1.0, "end")  # type: ignore

        if msg:
            self.message_box.insert("end", msg)  # type: ignore

            if self.auto_scroll:
                self.message_box._text.yview_moveto(1.0)  # type: ignore

        self.message_box._text.config(state="disabled")  # type: ignore

    def cb_disable_autoscroll(self, *args: Any):
        self.auto_scroll = False

    def cb_enable_autoscroll(self, *args: Any):
        self.auto_scroll = True
