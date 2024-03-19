#!/usr/bin/env python3
from queue import Queue
from typing import Union

from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.utils.callback import Callback, CallbackReturn, CbQueueItemType


class UploadBase:
    def __init__(
        self,
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: "Union[Queue[CbQueueItemType], Callback]",
        cb_return: CallbackReturn,
    ) -> None:
        if not cb:
            cb = Callback(silent=True)
            cb_return = CallbackReturn()

        self.opt_output = opt_output
        self.opt_comp = opt_comp
        self.opt_cred = opt_cred
        self.cb = cb
        self.cb_return = cb_return

        self.base_spec = CompOption(
            fps_power=self.opt_comp.fps_power,
            res_power=self.opt_comp.res_power,
            quality_min=self.opt_comp.quality_min,
            quality_max=self.opt_comp.quality_max,
            quality_power=self.opt_comp.quality_power,
            color_min=self.opt_comp.color_min,
            color_max=self.opt_comp.color_max,
            color_power=self.opt_comp.color_power,
            quantize_method=self.opt_comp.quantize_method,
            scale_filter=self.opt_comp.scale_filter,
            steps=self.opt_comp.steps,
            cache_dir=self.opt_comp.cache_dir,
        )
