#!/usr/bin/env python3
import os
from typing import TYPE_CHECKING

from tkinter import filedialog
from ttkbootstrap import LabelFrame, OptionMenu, Button, Entry, Label # type: ignore

if TYPE_CHECKING:
    from ...gui import GUI # type: ignore
from ...utils.files.dir_utils import DirUtils # type: ignore
from .right_clicker import RightClicker # type: ignore

class OutputFrame(LabelFrame):
    def __init__(self, gui: "GUI", *args, **kwargs):
        self.gui = gui
        super(OutputFrame, self).__init__(*args, **kwargs)

        self.output_option_lbl = Label(self, text='Output options', width=18, justify='left', anchor='w')
        output_full_names = [i['full_name'] for i in self.gui.output_presets.values()]
        defult_output_full_name = self.gui.output_presets[self.gui.default_output_mode]['full_name']
        self.output_option_opt = OptionMenu(self, self.gui.output_option_display_var, defult_output_full_name, *output_full_names, command=self.cb_output_option, bootstyle='secondary')
        self.output_option_opt.config(width=32)

        self.output_setdir_lbl = Label(self, text='Output directory', justify='left', anchor='w')
        self.output_setdir_entry = Entry(self, textvariable=self.gui.output_setdir_var, width=60, validatecommand=self.gui.highlight_fields)
        self.output_setdir_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        
        self.output_setdir_btn = Button(self, text='Choose directory', command=self.cb_set_outdir, width=16, bootstyle='secondary')

        self.title_lbl = Label(self, text='Title')
        self.title_entry = Entry(self, textvariable=self.gui.title_var, width=80, validate="focusout", validatecommand=self.gui.highlight_fields)
        self.title_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        
        self.author_lbl = Label(self, text='Author')
        self.author_entry = Entry(self, textvariable=self.gui.author_var, width=80, validate="focusout", validatecommand=self.gui.highlight_fields)
        self.author_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.output_option_lbl.grid(column=0, row=0, sticky='w', padx=3, pady=3)
        self.output_option_opt.grid(column=1, row=0, columnspan=2, sticky='w', padx=3, pady=3)
        self.output_setdir_lbl.grid(column=0, row=1, columnspan=2, sticky='w', padx=3, pady=3)
        self.output_setdir_entry.grid(column=1, row=1, sticky='w', padx=3, pady=3)
        self.output_setdir_btn.grid(column=2, row=1, sticky='e', padx=3, pady=3)
        self.title_lbl.grid(column=0, row=2, sticky='w', padx=3, pady=3)
        self.title_entry.grid(column=1, columnspan=2, row=2, sticky='w', padx=3, pady=3)
        self.author_lbl.grid(column=0, row=3, sticky='w', padx=3, pady=3)
        self.author_entry.grid(column=1, columnspan=2, row=3, sticky='w', padx=3, pady=3)
    
    def cb_set_outdir(self, *args):
        orig_output_dir = self.gui.output_setdir_var.get()
        if not os.path.isdir(orig_output_dir):
            orig_output_dir = DirUtils.get_curr_dir()
        output_dir = filedialog.askdirectory(initialdir=orig_output_dir)
        if output_dir:
            self.gui.output_setdir_var.set(output_dir)
    
    def cb_output_option(self, *args):
        self.gui.output_option_true_var.set(self.gui.output_option_display_var.get())
        self.gui.comp_frame.cb_comp_apply_preset()
        self.gui.highlight_fields()
    
    def set_states(self, state: str):
        self.title_entry.config(state=state)
        self.author_entry.config(state=state)
        self.output_option_opt.config(state=state)
        self.output_setdir_entry.config(state=state)
        self.output_setdir_btn.config(state=state)
