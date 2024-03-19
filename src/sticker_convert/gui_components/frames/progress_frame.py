#!/usr/bin/env python3
from typing import TYPE_CHECKING, Any, Optional

from tqdm import tqdm
from ttkbootstrap import LabelFrame, Progressbar  # type: ignore
from ttkbootstrap.scrolled import ScrolledText  # type: ignore

from sticker_convert.gui_components.frames.right_clicker import RightClicker

if TYPE_CHECKING:
    from sticker_convert.gui import GUI  # type: ignore


class ProgressFrame(LabelFrame):
    progress_bar_cli = None
    progress_bar_steps = 0
    auto_scroll = True
    msg_cls = False
    msg_buffer = ""
    bar_mode_changed = False
    bar_mode = "clear"
    bar_updates = 0
    bar_steps = 0

    def __init__(self, gui: "GUI", *args: Any, **kwargs: Any) -> None:
        self.gui = gui
        super().__init__(*args, **kwargs)  # type: ignore

        self.message_box = ScrolledText(self, height=15, wrap="word")
        self.message_box._text.bind("<Button-3><ButtonRelease-3>", RightClicker)  # type: ignore
        self.message_box._text.config(state="disabled")  # type: ignore
        self.progress_bar = Progressbar(self, orient="horizontal", mode="determinate")

        self.message_box.bind("<Enter>", self.cb_disable_autoscroll)
        self.message_box.bind("<Leave>", self.cb_enable_autoscroll)

        self.message_box.pack(expand=True, fill="x")
        self.progress_bar.pack(expand=True, fill="x")

        self.after(40, self.update_ui)

    def update_progress_bar(
        self,
        set_progress_mode: Optional[str] = None,
        steps: int = 0,
        update_bar: int = 0,
    ) -> None:
        if update_bar:
            self.bar_updates += update_bar
        elif set_progress_mode:
            self.bar_mode = set_progress_mode
            self.bar_steps = steps
            self.bar_updates = 0
            self.bar_mode_changed = True

    def update_message_box(self, *args: Any, **kwargs: Any) -> None:
        msg = kwargs.get("msg")
        cls = kwargs.get("cls")

        if not msg and len(args) == 1:
            msg = str(args[0])

        if cls:
            self.msg_cls = True
            self.msg_buffer = ""

        if msg:
            self.msg_buffer += msg + "\n"

    def update_ui(self) -> None:
        if self.msg_cls or self.msg_buffer:
            self.message_box._text.config(state="normal")  # type: ignore

            if self.msg_cls:
                self.message_box.delete(1.0, "end")  # type: ignore

            if self.msg_buffer:
                msg = self.msg_buffer.strip()
                if self.progress_bar_cli:
                    self.progress_bar_cli.write(msg)
                else:
                    print(msg)

                self.message_box.insert("end", msg + "\n")  # type: ignore

                if self.auto_scroll:
                    self.message_box._text.yview_moveto(1.0)  # type: ignore

            self.msg_cls = False
            self.msg_buffer = ""

            self.message_box._text.config(state="disabled")  # type: ignore

        if self.bar_mode_changed:
            if self.bar_mode == "determinate":
                self.progress_bar_cli = tqdm(total=self.bar_steps)
                self.progress_bar.config(mode="determinate")
                self.progress_bar_steps = self.bar_steps
                self.progress_bar.stop()
            elif self.progress_bar_cli:
                self.progress_bar_cli.close()
                self.progress_bar_cli = None

            if self.bar_mode == "indeterminate":
                self.progress_bar.config(mode="indeterminate")
                self.progress_bar.start(50)
            elif self.bar_mode == "clear":
                self.progress_bar.config(mode="determinate")
                self.progress_bar.stop()

            self.progress_bar["value"] = 0

        if self.bar_updates and self.progress_bar_cli:
            self.progress_bar_cli.update(self.bar_updates)
            self.progress_bar["value"] += (
                100 / self.progress_bar_steps * self.bar_updates
            )
            self.update_progress_bar(update_bar=self.bar_updates)

        self.bar_mode_changed = False
        self.bar_updates = 0

        self.after(40, self.update_ui)

    def cb_disable_autoscroll(self, *_: Any) -> None:
        self.auto_scroll = False

    def cb_enable_autoscroll(self, *_: Any) -> None:
        self.auto_scroll = True
