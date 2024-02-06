#!/usr/bin/env python3
from queue import Queue
from typing import Union, Optional

from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.utils.callback import Callback, CallbackReturn


class UploadBase:
    def __init__(
        self,
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: Union[
            Queue[
                Union[
                    tuple[str, Optional[tuple[str]], Optional[dict[str, str]]],
                    str,
                    None,
                ]
            ],
            Callback,
        ],
        cb_return: CallbackReturn,
    ):
        if not cb:
            cb = Callback(silent=True)
            cb_return = CallbackReturn()

        self.opt_output = opt_output
        self.opt_comp = opt_comp
        self.opt_cred = opt_cred
        self.cb = cb
        self.cb_return = cb_return
