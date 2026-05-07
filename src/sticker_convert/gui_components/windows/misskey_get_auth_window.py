#!/usr/bin/env python3
from threading import Thread
from typing import Any

from ttkbootstrap import Button, Frame, Label  # type: ignore

from sticker_convert.auth.auth_misskey import AuthMisskey
from sticker_convert.gui_components.gui_utils import GUIUtils
from sticker_convert.gui_components.windows.base_window import BaseWindow
from sticker_convert.utils.translate import I


class MisskeyGetAuthWindow(BaseWindow):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.title(I("Get Misskey token"))

        self.frame_info = Frame(self.scrollable_frame)
        self.frame_btn = Frame(self.scrollable_frame)

        self.frame_info.grid(column=0, row=0, sticky="news", padx=3, pady=3)
        self.frame_btn.grid(column=0, row=1, sticky="news", padx=3, pady=3)

        # Info frame
        self.explanation1_lbl = Label(
            self.frame_info,
            text=I("Misskey token are required to upload custom emoji"),
            justify="left",
            anchor="w",
        )
        self.explanation2_lbl = Label(
            self.frame_info,
            text=I("Close all browsers, press 'Get token' and login to Misskey"),
            justify="left",
            anchor="w",
        )

        self.explanation1_lbl.grid(
            column=0, row=0, columnspan=3, sticky="w", padx=3, pady=3
        )
        self.explanation2_lbl.grid(
            column=0, row=1, columnspan=3, sticky="w", padx=3, pady=3
        )

        # Buttons frame
        self.get_token_btn = Button(
            self.frame_btn, text=I("Get token"), command=self.cb_get_token
        )

        self.get_token_btn.pack()

        GUIUtils.finalize_window(self)

    def cb_get_token(self) -> None:
        Thread(target=self.cb_get_token_thread, daemon=True).start()

    def cb_get_token_thread(self, *_: Any) -> None:
        m = AuthMisskey(self.gui.get_opt_cred(), self.gui.cb)

        misskey_token = None
        misskey_token, msg = m.get_cred()
        self.gui.cb.put(("msg_block", None, {"message": msg, "parent": self}))
        if misskey_token:
            if not self.gui.creds.get("misskey"):
                self.gui.creds["misskey"] = {}
            self.gui.creds["misskey"]["token"] = misskey_token
            self.gui.misskey_token_var.set(misskey_token)
            self.gui.save_creds()
            self.gui.highlight_fields()
            return
