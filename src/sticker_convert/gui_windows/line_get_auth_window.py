#!/usr/bin/env python3
import sys
from functools import partial
import webbrowser
from threading import Thread
from typing import TYPE_CHECKING

from ttkbootstrap import Toplevel, Frame, Button, Label, Scrollbar, Canvas, PhotoImage # type: ignore

if TYPE_CHECKING:
    from ..gui import GUI # type: ignore
from ..auth.get_line_auth import GetLineAuth # type: ignore

class LineGetAuthWindow:
    def __init__(self, gui: "GUI"):
        self.gui = gui

        self.get_line_auth_win = Toplevel(self.gui.root)
        self.get_line_auth_win.title('Get Line cookie')
        
        self.icon = PhotoImage(file='resources/appicon.png')
        self.get_line_auth_win.iconphoto(1, self.icon)
        if sys.platform == 'darwin':
            self.get_line_auth_win.iconbitmap(bitmap='resources/appicon.icns')
        elif sys.platform == 'win32':
            self.get_line_auth_win.iconbitmap(bitmap='resources/appicon.ico')
        self.get_line_auth_win.tk.call('wm', 'iconphoto', self.get_line_auth_win._w, self.icon)
        
        self.get_line_auth_win.focus_force()

        self.cb_msg_block_line = partial(self.gui.cb_msg_block, parent=self.get_line_auth_win)

        self.create_scrollable_frame()

        self.frame_info = Frame(self.scrollable_frame)
        self.frame_btn = Frame(self.scrollable_frame)

        self.frame_info.grid(column=0, row=0, sticky='news', padx=3, pady=3)
        self.frame_btn.grid(column=0, row=1, sticky='news', padx=3, pady=3)

        # Info frame
        self.explanation1_lbl = Label(self.frame_info, text='Line cookies are required to create custom message stickers', justify='left', anchor='w')
        self.explanation2_lbl = Label(self.frame_info, text='Please open web browser and login to Line', justify='left', anchor='w')
        self.explanation3_lbl = Label(self.frame_info, text='After that, press "Get cookies"', justify='left', anchor='w')

        self.explanation1_lbl.grid(column=0, row=0, columnspan=3, sticky='w', padx=3, pady=3)
        self.explanation2_lbl.grid(column=0, row=1, columnspan=3, sticky='w', padx=3, pady=3)
        self.explanation3_lbl.grid(column=0, row=2, columnspan=3, sticky='w', padx=3, pady=3)

        # Buttons frame
        self.open_browser_btn = Button(self.frame_btn, text='Open browser', command=self.cb_open_browser)
        self.get_cookies_btn = Button(self.frame_btn, text='Get cookies', command=self.cb_get_cookies)

        self.open_browser_btn.pack()
        self.get_cookies_btn.pack()

        self.resize_window()
    
    def create_scrollable_frame(self):
        self.main_frame = Frame(self.get_line_auth_win)
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
    
    def cb_open_browser(self):
        line_login_site = 'https://store.line.me/login'
        success = webbrowser.open(line_login_site)
        if not success:
            self.gui.cb_ask_str('Cannot open web browser for you. Install web browser and open:', initialvalue=line_login_site)
    
    def cb_get_cookies(self):
        Thread(target=self.cb_get_cookies_thread, daemon=True).start()
    
    def cb_get_cookies_thread(self, *args):
        m = GetLineAuth()

        line_cookies = None
        line_cookies = m.get_cred()

        if line_cookies:
            self.gui.creds['line']['cookies'] = line_cookies
            self.gui.line_cookies_var.set(line_cookies)
            
            self.cb_msg_block_line(f'Got Line cookies successfully')
            self.gui.save_creds()
            self.gui.highlight_fields()
            return
            
        self.cb_msg_block_line('Failed to get Line cookies. Have you logged in the web browser?')
