#!/usr/bin/env python3
from typing import TYPE_CHECKING

from ttkbootstrap import LabelFrame, Progressbar # type: ignore
from ttkbootstrap.scrolled import ScrolledText # type: ignore
from tqdm import tqdm

if TYPE_CHECKING:
    from ...gui import GUI # type: ignore
from .right_clicker import RightClicker # type: ignore

class ProgressFrame(LabelFrame):
    progress_bar_cli = None
    progress_bar_steps = 0
    auto_scroll = True

    def __init__(self, gui: "GUI", *args, **kwargs):
        self.gui = gui
        super(ProgressFrame, self).__init__(*args, **kwargs)

        self.message_box = ScrolledText(self, height=15, wrap='word')
        self.message_box._text.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.message_box._text.config(state='disabled')
        self.progress_bar = Progressbar(self, orient='horizontal', mode='determinate')

        self.message_box.bind('<Enter>', self.cb_disable_autoscroll)
        self.message_box.bind('<Leave>', self.cb_enable_autoscroll)

        self.message_box.pack(expand=True, fill='x')
        self.progress_bar.pack(expand=True, fill='x')
    
    def update_progress_bar(self, set_progress_mode: str = '', steps: int = 0, update_bar: bool = False):
        if update_bar and self.progress_bar_cli:
            self.progress_bar_cli.update()
            self.progress_bar['value'] += 100 / self.progress_bar_steps
        elif set_progress_mode == 'determinate':
            self.progress_bar_cli = tqdm(total=steps)
            self.progress_bar.config(mode='determinate')
            self.progress_bar_steps = steps
            self.progress_bar.stop()
            self.progress_bar['value'] = 0
        elif set_progress_mode == 'indeterminate':
            if self.progress_bar_cli:
                self.progress_bar_cli.close()
                self.progress_bar_cli = None
            self.progress_bar['value'] = 0
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(50)
        elif set_progress_mode == 'clear':
            if self.progress_bar_cli:
                self.progress_bar_cli.reset()
            self.progress_bar.config(mode='determinate')
            self.progress_bar.stop()
            self.progress_bar['value'] = 0

    def update_message_box(self, *args, **kwargs):
        msg = kwargs.get('msg')
        cls = kwargs.get('cls')

        if not msg and len(args) == 1:
            msg = str(args[0])
        
        if msg:
            if self.progress_bar_cli:
                self.progress_bar_cli.write(msg)
            else:
                print(msg)
            msg += '\n'

        self.message_box._text.config(state='normal')

        if cls:
            self.message_box.delete(1.0, 'end')

        if msg:
            self.message_box.insert('end', msg)

            if self.auto_scroll:
                self.message_box._text.yview_moveto(1.0)

        self.message_box._text.config(state='disabled')
    
    def cb_disable_autoscroll(self, *args):
        self.auto_scroll = False
        
    def cb_enable_autoscroll(self, *args):
        self.auto_scroll = True
