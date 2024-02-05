#!/usr/bin/env python3
from multiprocessing.managers import BaseProxy

from typing import Optional, Union

from sticker_convert.job_option import (CompOption, CredOption,  # type: ignore
                                        OutputOption)
from sticker_convert.utils.callback import Callback, CallbackReturn  # type: ignore

class UploadBase:
    def __init__(
        self,
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: Union[BaseProxy, Callback, None] = None,
        cb_return: Optional[CallbackReturn] = None
    ):
        if not cb:
            cb = Callback(silent=True)
            cb_return = CallbackReturn()

        self.opt_output = opt_output
        self.opt_comp = opt_comp
        self.opt_cred = opt_cred
        self.cb = cb
        self.cb_return = cb_return