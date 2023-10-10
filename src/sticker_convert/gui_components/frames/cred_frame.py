#!/usr/bin/env python3
import webbrowser
from typing import TYPE_CHECKING

from ttkbootstrap import LabelFrame, Button, Entry, Label # type: ignore

if TYPE_CHECKING:
    from ...gui import GUI # type: ignore
from ..windows.signal_get_auth_window import SignalGetAuthWindow # type: ignore
from ..windows.line_get_auth_window import LineGetAuthWindow # type: ignore
from ..windows.kakao_get_auth_window import KakaoGetAuthWindow # type: ignore
from .right_clicker import RightClicker # type: ignore

class CredFrame(LabelFrame):
    def __init__(self, gui: "GUI", *args, **kwargs):
        self.gui = gui
        super(CredFrame, self).__init__(*args, **kwargs)

        self.grid_columnconfigure(1, weight=1)

        self.signal_uuid_lbl = Label(self, text='Signal uuid', width=18, justify='left', anchor='w')
        self.signal_uuid_entry = Entry(self, textvariable=self.gui.signal_uuid_var, width=50, validate="focusout", validatecommand=self.gui.highlight_fields)
        self.signal_uuid_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.signal_password_lbl = Label(self, text='Signal password', justify='left', anchor='w')
        self.signal_password_entry = Entry(self, textvariable=self.gui.signal_password_var, width=50, validate="focusout", validatecommand=self.gui.highlight_fields)
        self.signal_password_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.signal_get_auth_btn = Button(self, text='Generate', command=self.cb_signal_get_auth, bootstyle='secondary')

        self.telegram_token_lbl = Label(self, text='Telegram token', justify='left', anchor='w')
        self.telegram_token_entry = Entry(self, textvariable=self.gui.telegram_token_var, width=50, validate="focusout", validatecommand=self.gui.highlight_fields)
        self.telegram_token_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.telegram_userid_lbl = Label(self, text='Telegram user_id', justify='left', anchor='w')
        self.telegram_userid_entry = Entry(self, textvariable=self.gui.telegram_userid_var, width=50, validate="focusout", validatecommand=self.gui.highlight_fields)
        self.telegram_userid_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.kakao_auth_token_lbl = Label(self, text='Kakao auth_token', justify='left', anchor='w')
        self.kakao_auth_token_entry = Entry(self, textvariable=self.gui.kakao_auth_token_var, width=35)
        self.kakao_auth_token_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.kakao_get_auth_btn = Button(self, text='Generate', command=self.cb_kakao_get_auth, bootstyle='secondary')

        self.line_cookies_lbl = Label(self, text='Line cookies', width=18, justify='left', anchor='w')
        self.line_cookies_entry = Entry(self, textvariable=self.gui.line_cookies_var, width=35)
        self.line_cookies_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.line_get_auth_btn = Button(self, text='Generate', command=self.cb_line_get_auth, bootstyle='secondary')

        self.help_btn = Button(self, text='Get help', command=self.cb_cred_help, bootstyle='secondary')

        self.signal_uuid_lbl.grid(column=0, row=0, sticky='w', padx=3, pady=3)
        self.signal_uuid_entry.grid(column=1, row=0, columnspan=2, sticky='w', padx=3, pady=3)
        self.signal_password_lbl.grid(column=0, row=1, sticky='w', padx=3, pady=3)
        self.signal_password_entry.grid(column=1, row=1, columnspan=2, sticky='w', padx=3, pady=3)
        self.signal_get_auth_btn.grid(column=2, row=2, sticky='e', padx=3, pady=3)
        self.telegram_token_lbl.grid(column=0, row=3, sticky='w', padx=3, pady=3)
        self.telegram_token_entry.grid(column=1, row=3, columnspan=2, sticky='w', padx=3, pady=3)
        self.telegram_userid_lbl.grid(column=0, row=4, sticky='w', padx=3, pady=3)
        self.telegram_userid_entry.grid(column=1, row=4, columnspan=2, sticky='w', padx=3, pady=3)
        self.kakao_auth_token_lbl.grid(column=0, row=5, sticky='w', padx=3, pady=3)
        self.kakao_auth_token_entry.grid(column=1, row=5, sticky='w', padx=3, pady=3)
        self.kakao_get_auth_btn.grid(column=2, row=5, sticky='e', padx=3, pady=3)
        self.line_cookies_lbl.grid(column=0, row=6, sticky='w', padx=3, pady=3)
        self.line_cookies_entry.grid(column=1, row=6, sticky='w', padx=3, pady=3)
        self.line_get_auth_btn.grid(column=2, row=6, sticky='e', padx=3, pady=3)
        self.help_btn.grid(column=2, row=8, sticky='e', padx=3, pady=3)
    
    def cb_cred_help(self, *args):
        faq_site = 'https://github.com/laggykiller/sticker-convert#faq'
        success = webbrowser.open(faq_site)
        if not success:
            self.gui.cb_ask_str('You can get help from:', initialvalue=faq_site)
    
    def cb_kakao_get_auth(self, *args):
        KakaoGetAuthWindow(self.gui)
    
    def cb_signal_get_auth(self, *args):
        SignalGetAuthWindow(self.gui)
    
    def cb_line_get_auth(self, *args):
        LineGetAuthWindow(self.gui)
    
    def set_states(self, state: str):
        self.signal_uuid_entry.config(state=state)
        self.signal_password_entry.config(state=state)
        self.signal_get_auth_btn.config(state=state)
        self.telegram_token_entry.config(state=state)
        self.telegram_userid_entry.config(state=state)
        self.kakao_auth_token_entry.config(state=state)
        self.kakao_get_auth_btn.config(state=state)
        self.line_cookies_entry.config(state=state)
        self.line_get_auth_btn.config(state=state)
