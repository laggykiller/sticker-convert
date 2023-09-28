#!/usr/bin/env python3
import sys
from functools import partial
from threading import Thread
from typing import TYPE_CHECKING

from ttkbootstrap import Toplevel, LabelFrame, Frame, Button, Entry, Label, Scrollbar, Canvas, PhotoImage # type: ignore

from ..auth.get_kakao_auth import GetKakaoAuth # type: ignore
from ..gui_frames.right_clicker import RightClicker # type: ignore
if TYPE_CHECKING:
    from ..gui import GUI # type: ignore

class KakaoGetAuthWindow:
    def __init__(self, gui: "GUI"):
        self.gui = gui

        self.get_kakao_auth_win = Toplevel(self.gui.root)
        self.get_kakao_auth_win.title('Get Kakao auth_token')
        
        self.icon = PhotoImage(file='resources/appicon.png')
        self.get_kakao_auth_win.iconphoto(1, self.icon)
        if sys.platform == 'darwin':
            self.get_kakao_auth_win.iconbitmap(bitmap='resources/appicon.icns')
        elif sys.platform == 'win32':
            self.get_kakao_auth_win.iconbitmap(bitmap='resources/appicon.ico')
        self.get_kakao_auth_win.tk.call('wm', 'iconphoto', self.get_kakao_auth_win._w, self.icon)
        
        self.get_kakao_auth_win.focus_force()

        self.cb_msg_block_kakao = partial(self.gui.cb_msg_block, parent=self.get_kakao_auth_win)
        self.cb_ask_str_kakao = partial(self.gui.cb_ask_str, parent=self.get_kakao_auth_win)

        self.create_scrollable_frame()

        self.frame_login_info = LabelFrame(self.scrollable_frame, text='Kakao login info')
        self.frame_login_btn = Frame(self.scrollable_frame)

        self.frame_login_info.grid(column=0, row=0, sticky='news', padx=3, pady=3)
        self.frame_login_btn.grid(column=0, row=1, sticky='news', padx=3, pady=3)

        # Login info frame
        self.explanation1_lbl = Label(self.frame_login_info, text='This will simulate login to Android Kakao app', justify='left', anchor='w')
        self.explanation2_lbl = Label(self.frame_login_info, text='You will send / receive verification code via SMS', justify='left', anchor='w')
        self.explanation3_lbl = Label(self.frame_login_info, text='You maybe logged out of existing device', justify='left', anchor='w')

        self.kakao_username_help_btn = Button(self.frame_login_info, text='?', width=1, command=lambda: self.cb_msg_block_kakao(self.gui.help['cred']['kakao_username']), bootstyle='secondary')
        self.kakao_username_lbl = Label(self.frame_login_info, text='Username', width=18, justify='left', anchor='w')
        self.kakao_username_entry = Entry(self.frame_login_info, textvariable=self.gui.kakao_username_var, width=30)
        self.kakao_username_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.kakao_password_help_btn = Button(self.frame_login_info, text='?', width=1, command=lambda: self.cb_msg_block_kakao(self.gui.help['cred']['kakao_password']), bootstyle='secondary')
        self.kakao_password_lbl = Label(self.frame_login_info, text='Password', justify='left', anchor='w')
        self.kakao_password_entry = Entry(self.frame_login_info, textvariable=self.gui.kakao_password_var, width=30)
        self.kakao_password_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.kakao_country_code_help_btn = Button(self.frame_login_info, text='?', width=1, command=lambda: self.cb_msg_block_kakao(self.gui.help['cred']['kakao_country_code']), bootstyle='secondary')
        self.kakao_country_code_lbl = Label(self.frame_login_info, text='Country code', justify='left', anchor='w')
        self.kakao_country_code_entry = Entry(self.frame_login_info, textvariable=self.gui.kakao_country_code_var, width=30)
        self.kakao_country_code_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.kakao_phone_number_help_btn = Button(self.frame_login_info, text='?', width=1, command=lambda: self.cb_msg_block_kakao(self.gui.help['cred']['kakao_phone_number']), bootstyle='secondary')
        self.kakao_phone_number_lbl = Label(self.frame_login_info, text='Phone number', justify='left', anchor='w')
        self.kakao_phone_number_entry = Entry(self.frame_login_info, textvariable=self.gui.kakao_phone_number_var, width=30)
        self.kakao_phone_number_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.explanation1_lbl.grid(column=0, row=0, columnspan=3, sticky='w', padx=3, pady=3)
        self.explanation2_lbl.grid(column=0, row=1, columnspan=3, sticky='w', padx=3, pady=3)
        self.explanation3_lbl.grid(column=0, row=2, columnspan=3, sticky='w', padx=3, pady=3)

        self.kakao_username_help_btn.grid(column=0, row=3, sticky='w', padx=3, pady=3)
        self.kakao_username_lbl.grid(column=1, row=3, sticky='w', padx=3, pady=3)
        self.kakao_username_entry.grid(column=2, row=3, sticky='w', padx=3, pady=3)

        self.kakao_password_help_btn.grid(column=0, row=4, sticky='w', padx=3, pady=3)
        self.kakao_password_lbl.grid(column=1, row=4, sticky='w', padx=3, pady=3)
        self.kakao_password_entry.grid(column=2, row=4, sticky='w', padx=3, pady=3)

        self.kakao_country_code_help_btn.grid(column=0, row=5, sticky='w', padx=3, pady=3)
        self.kakao_country_code_lbl.grid(column=1, row=5, sticky='w', padx=3, pady=3)
        self.kakao_country_code_entry.grid(column=2, row=5, sticky='w', padx=3, pady=3)

        self.kakao_phone_number_help_btn.grid(column=0, row=6, sticky='w', padx=3, pady=3)
        self.kakao_phone_number_lbl.grid(column=1, row=6, sticky='w', padx=3, pady=3)
        self.kakao_phone_number_entry.grid(column=2, row=6, sticky='w', padx=3, pady=3)

        # Login button frame
        self.login_btn = Button(self.frame_login_btn, text='Login and get auth_token', command=self.cb_login)

        self.login_btn.pack()

        self.resize_window()
    
    def create_scrollable_frame(self):
        self.main_frame = Frame(self.get_kakao_auth_win)
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
        self.gui.save_creds()
        m = GetKakaoAuth(opt_cred=self.gui.creds, cb_msg=self.gui.cb_msg, cb_msg_block=self.cb_msg_block_kakao, cb_ask_str=self.cb_ask_str_kakao)

        auth_token = m.get_cred()

        if auth_token:
            self.gui.creds['kakao']['auth_token'] = auth_token
            self.gui.kakao_auth_token_var.set(auth_token)
        
            self.cb_msg_block_kakao(f'Got auth_token successfully: {auth_token}')
            self.gui.save_creds()
            self.gui.highlight_fields()
        else:
            self.cb_msg_block_kakao('Failed to get auth_token')
