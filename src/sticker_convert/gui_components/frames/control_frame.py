#!/usr/bin/env python3
from typing import TYPE_CHECKING

from ttkbootstrap import Frame, Button # type: ignore

if TYPE_CHECKING:
    from ...gui import GUI # type: ignore

class ControlFrame(Frame):
    def __init__(self, gui: "GUI", *args, **kwargs):
        self.gui = gui
        super(ControlFrame, self).__init__(*args, **kwargs)

        self.start_btn = Button(self, text='Start', command=self.cb_start_btn, bootstyle='default')
        
        self.start_btn.pack(expand=True, fill='x')
    
    def cb_start_btn(self, *args, **kwargs):
        if self.gui.job:
            response = self.gui.cb_ask_bool('Cancel job?')
            if response == True:
                self.gui.cancel_job()
        else:
            self.gui.start_job()