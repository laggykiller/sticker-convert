#!/usr/bin/env python3
from ttkbootstrap import Frame, Button

class ControlFrame:
    def __init__(self, gui):
        self.gui = gui
        self.frame = Frame(self.gui.scrollable_frame, borderwidth=1)

        self.start_btn = Button(self.frame, text='Start', command=self.gui.start)
        
        self.start_btn.pack(expand=True, fill='x')
