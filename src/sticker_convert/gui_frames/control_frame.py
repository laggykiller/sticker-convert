#!/usr/bin/env python3
from typing import TYPE_CHECKING

from ttkbootstrap import Frame, Button # type: ignore

if TYPE_CHECKING:
    from ..gui import GUI # type: ignore

class ControlFrame:
    def __init__(self, gui: "GUI"):
        self.gui = gui
        self.frame = Frame(self.gui.scrollable_frame, borderwidth=1)

        self.start_btn = Button(self.frame, text='Start', command=self.gui.start)
        
        self.start_btn.pack(expand=True, fill='x')
