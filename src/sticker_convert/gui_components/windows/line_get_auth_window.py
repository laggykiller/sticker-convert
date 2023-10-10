#!/usr/bin/env python3
from functools import partial
import webbrowser
from threading import Thread

from ttkbootstrap import Frame, Button, Label # type: ignore

from ...utils.auth.get_line_auth import GetLineAuth # type: ignore
from .base_window import BaseWindow # type: ignore
from ..gui_utils import GUIUtils # type: ignore

class LineGetAuthWindow(BaseWindow):
    def __init__(self, *args, **kwargs):
        super(LineGetAuthWindow, self).__init__(*args, **kwargs)

        self.title('Get Line cookie')
        
        self.cb_msg_block_line = partial(self.gui.cb_msg_block, parent=self)

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

        GUIUtils.finalize_window(self)
        
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
            if not self.gui.creds.get('line'):
                self.gui.creds['line'] = {}
            self.gui.creds['line']['cookies'] = line_cookies
            self.gui.line_cookies_var.set(line_cookies)
            
            self.cb_msg_block_line('Got Line cookies successfully')
            self.gui.save_creds()
            self.gui.highlight_fields()
            return
            
        self.cb_msg_block_line('Failed to get Line cookies. Have you logged in the web browser?')
