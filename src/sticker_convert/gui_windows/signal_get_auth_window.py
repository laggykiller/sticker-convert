#!/usr/bin/env python3
import sys
from functools import partial
from threading import Thread
from typing import TYPE_CHECKING

from ttkbootstrap import Toplevel, Frame, Button, Label, Scrollbar, Canvas, PhotoImage # type: ignore

if TYPE_CHECKING:
    from ..gui import GUI # type: ignore
from ..auth.get_signal_auth import GetSignalAuth # type: ignore

class SignalGetAuthWindow:
    def __init__(self, gui: "GUI"):
        self.gui = gui

        self.get_signal_auth_win = Toplevel(self.gui.root)
        self.get_signal_auth_win.title('Get Signal uuid and password')
        
        self.icon = PhotoImage(file='resources/appicon.png')
        self.get_signal_auth_win.iconphoto(1, self.icon)
        if sys.platform == 'darwin':
            self.get_signal_auth_win.iconbitmap(bitmap='resources/appicon.icns')
        elif sys.platform == 'win32':
            self.get_signal_auth_win.iconbitmap(bitmap='resources/appicon.ico')
        self.get_signal_auth_win.tk.call('wm', 'iconphoto', self.get_signal_auth_win._w, self.icon)
        
        self.get_signal_auth_win.focus_force()

        self.cb_msg_block_signal = partial(self.gui.cb_msg_block, parent=self.get_signal_auth_win)
        self.cb_ask_str_signal = partial(self.gui.cb_ask_str, parent=self.get_signal_auth_win)

        self.create_scrollable_frame()

        self.frame_info = Frame(self.scrollable_frame)
        self.frame_start_btn = Frame(self.scrollable_frame)

        self.frame_info.grid(column=0, row=0, sticky='news', padx=3, pady=3)
        self.frame_start_btn.grid(column=0, row=1, sticky='news', padx=3, pady=3)

        # Info frame
        self.explanation1_lbl = Label(self.frame_info, text='Please install Signal Desktop BETA VERSION', justify='left', anchor='w')
        self.explanation2_lbl = Label(self.frame_info, text='After installation, you need to login to Signal Desktop', justify='left', anchor='w')
        self.explanation3_lbl = Label(self.frame_info, text='uuid and password will be automatically fetched', justify='left', anchor='w')

        self.explanation1_lbl.grid(column=0, row=0, columnspan=3, sticky='w', padx=3, pady=3)
        self.explanation2_lbl.grid(column=0, row=1, columnspan=3, sticky='w', padx=3, pady=3)
        self.explanation3_lbl.grid(column=0, row=2, columnspan=3, sticky='w', padx=3, pady=3)

        # Start button frame
        self.login_btn = Button(self.frame_start_btn, text='Get uuid and password', command=self.cb_login)

        self.login_btn.pack()

        self.resize_window()
    
    def create_scrollable_frame(self):
        self.main_frame = Frame(self.get_signal_auth_win)
        self.main_frame.pack(fill='both', expand=1)

        self.horizontal_scrollbar_frame = Frame(self.main_frame)
        self.horizontal_scrollbar_frame.pack(fill='x', side='bottom')

        self.canvas = Canvas(self.main_frame)
        self.canvas.pack(side='left', fill='both', expand=1)

        self.x_scrollbar = Scrollbar(self.horizontal_scrollbar_frame, orient='horizontal', command=self.canvas.xview)
        self.x_scrollbar.pack(side='bottom', fill='x')

        self.y_scrollbar = Scrollbar(self.main_frame, orient='vertical', command=self.canvas.yview)
        self.y_scrollbar.pack(side='right', fill='y')

        self.canvas.configure(xscrollcommand=self.x_scrollbar.set)
        self.canvas.configure(yscrollcommand=self.y_scrollbar.set)
        self.canvas.bind("<Configure>",lambda e: self.canvas.config(scrollregion= self.canvas.bbox('all'))) 

        self.scrollable_frame = Frame(self.canvas)
        self.canvas.create_window((0,0),window= self.scrollable_frame, anchor="nw")

    def resize_window(self):
        self.scrollable_frame.update_idletasks()
        width = self.scrollable_frame.winfo_width()
        height = self.scrollable_frame.winfo_height()

        screen_width = self.gui.root.winfo_screenwidth()
        screen_height = self.gui.root.winfo_screenwidth()

        if width > screen_width * 0.8:
            width = int(screen_width * 0.8)
        if height > screen_height * 0.8:
            height = int(screen_height * 0.8)

        self.canvas.configure(width=width, height=height)
    
    def cb_login(self):
        Thread(target=self.cb_login_thread, daemon=True).start()
    
    def cb_login_thread(self, *args):
        m = GetSignalAuth(cb_msg=self.gui.cb_msg, cb_ask_str=self.cb_ask_str_signal)

        uuid, password = None, None
        while Toplevel.winfo_exists(self.get_signal_auth_win):
            uuid, password = m.get_cred()

            if uuid and password:
                self.gui.creds['signal']['uuid'] = uuid
                self.gui.creds['signal']['password'] = password
                self.gui.signal_uuid_var.set(uuid)
                self.gui.signal_password_var.set(password)
                
                self.cb_msg_block_signal(f'Got uuid and password successfully:\nuuid={uuid}\npassword={password}')
                self.gui.save_creds()
                self.gui.highlight_fields()
                return
            
        self.cb_msg_block_signal('Failed to get uuid and password')
