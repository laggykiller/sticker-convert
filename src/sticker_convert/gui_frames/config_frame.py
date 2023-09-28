#!/usr/bin/env python3
import os
import platform
from typing import TYPE_CHECKING

from ttkbootstrap import LabelFrame, Button, Label, Checkbutton # type: ignore

if TYPE_CHECKING:
    from ..gui import GUI # type: ignore
from ..utils.curr_dir import CurrDir # type: ignore
from ..utils.run_bin import RunBin # type: ignore
from ..__init__ import __version__ # type: ignore

class ConfigFrame:
    def __init__(self, gui: "GUI"):
        self.gui = gui
        self.frame = LabelFrame(self.gui.scrollable_frame, borderwidth=1, text='Config')

        self.frame.grid_columnconfigure(1, weight=1)

        self.config_save_cred_lbl = Label(self.frame, text='Save credentials', width=18, justify='left', anchor='w')
        self.config_save_cred_cbox = Checkbutton(self.frame, variable=self.gui.config_save_cred_var, onvalue=True, offvalue=False, bootstyle='success-round-toggle')

        self.config_clear_cred_lbl = Label(self.frame, text='Clear credentials', width=18, justify='left', anchor='w')
        self.config_clear_cred_btn = Button(self.frame, text='Clear...', command=self.cb_clear_cred, bootstyle='secondary')

        self.config_restore_default_lbl = Label(self.frame, text='Restore default', width=18, justify='left', anchor='w')
        self.config_restore_default_btn = Button(self.frame, text='Restore...', command=self.cb_restore_default, bootstyle='secondary')

        self.config_open_dir_lbl = Label(self.frame, text='Config directory', width=18, justify='left', anchor='w')
        self.config_open_dir_btn = Button(self.frame, text='Open...', command=self.cb_open_config_directory, bootstyle='secondary')

        self.config_save_cred_lbl.grid(column=0, row=0, sticky='w', padx=3, pady=3)
        self.config_save_cred_cbox.grid(column=1, row=0, sticky='w', padx=3, pady=3)

        self.config_clear_cred_lbl.grid(column=0, row=1, sticky='w', padx=3, pady=3)
        self.config_clear_cred_btn.grid(column=1, row=1, sticky='w', padx=3, pady=3)

        self.config_restore_default_lbl.grid(column=0, row=2, sticky='w', padx=3, pady=3)
        self.config_restore_default_btn.grid(column=1, row=2, sticky='w', padx=3, pady=3)

        self.config_open_dir_lbl.grid(column=0, row=3, sticky='w', padx=3, pady=3)
        self.config_open_dir_btn.grid(column=1, row=3, sticky='w', padx=3, pady=3)
    
    def cb_clear_cred(self, *args, **kwargs):
        response = self.gui.cb_ask_bool('Are you sure you want to clear credentials?')
        if response == True:
            self.gui.delete_creds()
            self.gui.load_jsons()
            self.gui.apply_creds()
            self.gui.highlight_fields()
            self.gui.cb_msg_block('Credentials cleared.')
    
    def cb_restore_default(self, *args, **kwargs):
        response = self.gui.cb_ask_bool('Are you sure you want to restore default config? (This will not clear credentials.)')
        if response == True:
            self.gui.delete_config()
            self.gui.load_jsons()
            self.gui.apply_config()
            self.gui.highlight_fields()
            self.gui.cb_msg_block('Restored to default config.')
    
    def cb_open_config_directory(self, *args, **kwargs):
        config_dir = CurrDir.get_config_dir()
        self.gui.cb_msg(msg=f'Config is located at {config_dir}')
        if platform.system() == 'Windows':
            os.startfile(config_dir)
        elif platform.system() == 'Darwin':
            RunBin.run_cmd(['open', config_dir], silence=True)
        else:
            RunBin.run_cmd(['xdg-open', config_dir], silence=True)
