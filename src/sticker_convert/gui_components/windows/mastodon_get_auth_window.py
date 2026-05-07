#!/usr/bin/env python3
from threading import Thread
from typing import Any

from ttkbootstrap import Button, Frame, Label  # type: ignore

from sticker_convert.auth.auth_mastodon import AuthMastodon
from sticker_convert.gui_components.gui_utils import GUIUtils
from sticker_convert.gui_components.windows.base_window import BaseWindow
from sticker_convert.utils.translate import I


class MastodonGetAuthWindow(BaseWindow):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.title(I("Get Mastodon cookie"))

        self.frame_info = Frame(self.scrollable_frame)
        self.frame_btn = Frame(self.scrollable_frame)

        self.frame_info.grid(column=0, row=0, sticky="news", padx=3, pady=3)
        self.frame_btn.grid(column=0, row=1, sticky="news", padx=3, pady=3)

        # Info frame
        self.explanation1_lbl = Label(
            self.frame_info,
            text=I("Mastodon cookies are required to upload custom emoji"),
            justify="left",
            anchor="w",
        )
        self.explanation2_lbl = Label(
            self.frame_info,
            text=I("Close all browsers, press 'Get cookies' and login to Mastodon"),
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
        self.get_cookies_btn = Button(
            self.frame_btn, text=I("Get cookies"), command=self.cb_get_cookies
        )

        self.get_cookies_btn.pack()

        GUIUtils.finalize_window(self)

    def cb_get_cookies(self) -> None:
        Thread(target=self.cb_get_cookies_thread, daemon=True).start()

    def cb_get_cookies_thread(self, *_: Any) -> None:
        m = AuthMastodon(self.gui.get_opt_cred(), self.gui.cb)

        mastodon_cookies = None
        mastodon_cookies, msg = m.get_cred()
        self.gui.cb.put(("msg_block", None, {"message": msg, "parent": self}))
        if mastodon_cookies:
            if not self.gui.creds.get("mastodon"):
                self.gui.creds["mastodon"] = {}
            self.gui.creds["mastodon"]["cookies"] = mastodon_cookies
            self.gui.mastodon_cookies_var.set(mastodon_cookies)
            self.gui.save_creds()
            self.gui.highlight_fields()
            return
