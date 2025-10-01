#!/usr/bin/env python3
from typing import Optional

from sticker_convert.job_option import CredOption
from sticker_convert.utils.callback import CallbackCli, CallbackProtocol


class AuthBase:
    def __init__(
        self,
        opt_cred: CredOption,
        cb: Optional[CallbackProtocol] = None,
    ) -> None:
        self.opt_cred = opt_cred
        self.cb: CallbackProtocol
        if cb is None:
            self.cb = CallbackCli()
        else:
            self.cb = cb
