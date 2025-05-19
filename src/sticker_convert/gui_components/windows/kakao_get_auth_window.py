#!/usr/bin/env python3
import platform
from functools import partial
from threading import Thread
from typing import Any, Optional

from ttkbootstrap import Button, Entry, Frame, Label, LabelFrame  # type: ignore

from sticker_convert.gui_components.frames.right_clicker import RightClicker
from sticker_convert.gui_components.gui_utils import GUIUtils
from sticker_convert.gui_components.windows.base_window import BaseWindow
from sticker_convert.utils.auth.get_kakao_auth import GetKakaoAuth
from sticker_convert.utils.auth.get_kakao_desktop_auth import GetKakaoDesktopAuth


class KakaoGetAuthWindow(BaseWindow):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.title("Get Kakao auth_token")

        self.cb_msg_block_kakao = partial(self.gui.cb_msg_block, parent=self)
        self.cb_ask_str_kakao = partial(self.gui.cb_ask_str, parent=self)

        self.frame_from_desktop = LabelFrame(
            self.scrollable_frame, text="Method 1: From KakaoTalk Desktop"
        )
        self.frame_simulate_login = LabelFrame(
            self.scrollable_frame, text="Method 2: Simulate login"
        )
        self.frame_login_btn = Frame(self.scrollable_frame)

        self.frame_from_desktop.grid(column=0, row=0, sticky="news", padx=3, pady=3)
        self.frame_simulate_login.grid(column=0, row=1, sticky="news", padx=3, pady=3)

        # Method 1 frame
        self.explanation1_1_lbl = Label(
            self.frame_from_desktop,
            text="This will get Kakao auth_token from Kakao Desktop",
            justify="left",
            anchor="w",
        )
        self.explanation1_2_lbl = Label(
            self.frame_from_desktop,
            text="Download Kakao Desktop, login and press 'Get auth_token'",
            justify="left",
            anchor="w",
        )
        self.explanation1_3_lbl = Label(
            self.frame_from_desktop,
            text="This can take about a minute.",
            justify="left",
            anchor="w",
        )
        if platform.system() != "Darwin":
            self.explanation1_4_lbl = Label(
                self.frame_from_desktop,
                text="Note: This will download ProcDump and read memory of KakaoTalk Desktop",
                justify="left",
                anchor="w",
            )
        else:
            self.explanation1_4_lbl = Label(
                self.frame_from_desktop,
                text="Note: This will read memory of KakaoTalk Desktop",
                justify="left",
                anchor="w",
            )
        self.kakao_bin_path_lbl = Label(
            self.frame_from_desktop,
            text="Kakao app path (Optional):",
            justify="left",
            anchor="w",
        )
        self.kakao_bin_path_entry = Entry(
            self.frame_from_desktop,
            textvariable=self.gui.kakao_bin_path_var,
            width=30,
        )
        self.launch_desktop_btn = Button(
            self.frame_from_desktop,
            text="Launch Desktop app",
            command=self.cb_launch_desktop,
            width=24,
            bootstyle="secondary",  # type: ignore
        )
        self.get_auth_desktop_btn = Button(
            self.frame_from_desktop,
            text="Get auth_token",
            command=self.cb_from_desktop,
            width=24,
        )

        self.explanation1_1_lbl.grid(
            column=0, row=0, columnspan=2, sticky="w", padx=3, pady=3
        )
        self.explanation1_2_lbl.grid(
            column=0, row=1, columnspan=2, sticky="w", padx=3, pady=3
        )
        self.explanation1_3_lbl.grid(
            column=0, row=2, columnspan=2, sticky="w", padx=3, pady=3
        )
        self.explanation1_4_lbl.grid(
            column=0, row=3, columnspan=2, sticky="w", padx=3, pady=3
        )
        self.kakao_bin_path_lbl.grid(column=0, row=4, sticky="w", padx=3, pady=3)
        self.kakao_bin_path_entry.grid(column=1, row=4, sticky="w", padx=3, pady=3)
        self.launch_desktop_btn.grid(column=0, row=5, columnspan=2, padx=3, pady=3)
        self.get_auth_desktop_btn.grid(column=0, row=6, columnspan=2, padx=3, pady=3)

        # Method 2 frame
        self.explanation2_1_lbl = Label(
            self.frame_simulate_login,
            text="This will simulate login to Android Kakao app",
            justify="left",
            anchor="w",
        )
        self.explanation2_2_lbl = Label(
            self.frame_simulate_login,
            text="You will send / receive verification code via SMS",
            justify="left",
            anchor="w",
        )
        self.explanation2_3_lbl = Label(
            self.frame_simulate_login,
            text="You will be logged out of existing device",
            justify="left",
            anchor="w",
        )

        self.kakao_username_help_btn = Button(
            self.frame_simulate_login,
            text="?",
            width=1,
            command=lambda: self.cb_msg_block_kakao(
                self.gui.help["cred"]["kakao_username"]
            ),
            bootstyle="secondary",  # type: ignore
        )
        self.kakao_username_lbl = Label(
            self.frame_simulate_login,
            text="Username",
            width=18,
            justify="left",
            anchor="w",
        )
        self.kakao_username_entry = Entry(
            self.frame_simulate_login,
            textvariable=self.gui.kakao_username_var,
            width=30,
        )
        self.kakao_username_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.kakao_password_help_btn = Button(
            self.frame_simulate_login,
            text="?",
            width=1,
            command=lambda: self.cb_msg_block_kakao(
                self.gui.help["cred"]["kakao_password"]
            ),
            bootstyle="secondary",  # type: ignore
        )
        self.kakao_password_lbl = Label(
            self.frame_simulate_login, text="Password", justify="left", anchor="w"
        )
        self.kakao_password_entry = Entry(
            self.frame_simulate_login,
            textvariable=self.gui.kakao_password_var,
            width=30,
        )
        self.kakao_password_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.kakao_country_code_help_btn = Button(
            self.frame_simulate_login,
            text="?",
            width=1,
            command=lambda: self.cb_msg_block_kakao(
                self.gui.help["cred"]["kakao_country_code"]
            ),
            bootstyle="secondary",  # type: ignore
        )
        self.kakao_country_code_lbl = Label(
            self.frame_simulate_login, text="Country code", justify="left", anchor="w"
        )
        self.kakao_country_code_entry = Entry(
            self.frame_simulate_login,
            textvariable=self.gui.kakao_country_code_var,
            width=30,
        )
        self.kakao_country_code_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.kakao_phone_number_help_btn = Button(
            self.frame_simulate_login,
            text="?",
            width=1,
            command=lambda: self.cb_msg_block_kakao(
                self.gui.help["cred"]["kakao_phone_number"]
            ),
            bootstyle="secondary",  # type: ignore
        )
        self.kakao_phone_number_lbl = Label(
            self.frame_simulate_login, text="Phone number", justify="left", anchor="w"
        )
        self.kakao_phone_number_entry = Entry(
            self.frame_simulate_login,
            textvariable=self.gui.kakao_phone_number_var,
            width=30,
        )
        self.kakao_phone_number_entry.bind("<Button-3><ButtonRelease-3>", RightClicker)

        self.login_btn = Button(
            self.frame_simulate_login,
            text="Login and get auth_token",
            command=self.cb_simulate_login,
            width=24,
        )

        self.explanation2_1_lbl.grid(
            column=0, row=0, columnspan=3, sticky="w", padx=3, pady=3
        )
        self.explanation2_2_lbl.grid(
            column=0, row=1, columnspan=3, sticky="w", padx=3, pady=3
        )
        self.explanation2_3_lbl.grid(
            column=0, row=2, columnspan=3, sticky="w", padx=3, pady=3
        )

        self.kakao_username_help_btn.grid(column=0, row=3, sticky="w", padx=3, pady=3)
        self.kakao_username_lbl.grid(column=1, row=3, sticky="w", padx=3, pady=3)
        self.kakao_username_entry.grid(column=2, row=3, sticky="w", padx=3, pady=3)

        self.kakao_password_help_btn.grid(column=0, row=4, sticky="w", padx=3, pady=3)
        self.kakao_password_lbl.grid(column=1, row=4, sticky="w", padx=3, pady=3)
        self.kakao_password_entry.grid(column=2, row=4, sticky="w", padx=3, pady=3)

        self.kakao_country_code_help_btn.grid(
            column=0, row=5, sticky="w", padx=3, pady=3
        )
        self.kakao_country_code_lbl.grid(column=1, row=5, sticky="w", padx=3, pady=3)
        self.kakao_country_code_entry.grid(column=2, row=5, sticky="w", padx=3, pady=3)

        self.kakao_phone_number_help_btn.grid(
            column=0, row=6, sticky="w", padx=3, pady=3
        )
        self.kakao_phone_number_lbl.grid(column=1, row=6, sticky="w", padx=3, pady=3)
        self.kakao_phone_number_entry.grid(column=2, row=6, sticky="w", padx=3, pady=3)
        self.login_btn.grid(column=0, row=7, columnspan=3, padx=3, pady=3)

        GUIUtils.finalize_window(self)

    def cb_simulate_login(self) -> None:
        Thread(target=self.cb_simulate_login_thread, daemon=True).start()

    def cb_simulate_login_thread(self, *_: Any) -> None:
        self.gui.save_creds()
        m = GetKakaoAuth(
            opt_cred=self.gui.get_opt_cred(),
            cb_msg=self.gui.cb_msg,
            cb_msg_block=self.cb_msg_block_kakao,
            cb_ask_str=self.cb_ask_str_kakao,
        )

        auth_token = m.get_cred()

        if auth_token:
            if not self.gui.creds.get("kakao"):
                self.gui.creds["kakao"] = {}
            self.gui.creds["kakao"]["auth_token"] = auth_token
            self.gui.kakao_auth_token_var.set(auth_token)

            self.cb_msg_block_kakao(f"Got auth_token successfully: {auth_token}")
            self.gui.save_creds()
            self.gui.highlight_fields()
        else:
            self.cb_msg_block_kakao("Failed to get auth_token")

    def cb_launch_desktop(self) -> None:
        m = GetKakaoDesktopAuth(
            cb_ask_str=self.cb_ask_str_kakao,
        )
        if self.gui.kakao_bin_path_var.get() != "":
            bin_path = self.gui.kakao_bin_path_var.get()
        else:
            bin_path = m.get_kakao_desktop()

        if bin_path is not None:
            m.launch_kakao(bin_path)
        else:
            self.cb_msg_block_kakao(
                "Error: Cannot launch Kakao Desktop. Is it installed?"
            )

    def cb_from_desktop(self) -> None:
        Thread(target=self.cb_from_desktop_thread, daemon=True).start()

    def cb_from_desktop_thread(self, *_: Any) -> None:
        self.gui.save_creds()
        self.gui.cb_msg("Getting auth_token, this may take a minute...")
        self.gui.cb_bar("indeterminate")
        m = GetKakaoDesktopAuth(
            cb_ask_str=self.cb_ask_str_kakao,
        )

        bin_path: Optional[str]
        if self.gui.kakao_bin_path_var.get() != "":
            bin_path = self.gui.kakao_bin_path_var.get()
        else:
            bin_path = None
        auth_token, msg = m.get_cred(bin_path)

        if auth_token:
            if not self.gui.creds.get("kakao"):
                self.gui.creds["kakao"] = {}
            self.gui.creds["kakao"]["auth_token"] = auth_token
            self.gui.kakao_auth_token_var.set(auth_token)

            self.gui.save_creds()
            self.gui.highlight_fields()

        self.cb_msg_block_kakao(msg)
        self.gui.cb_bar("clear")
