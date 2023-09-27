#!/usr/bin/env python3

class UploadBase:
    def __init__(self, opt_output, opt_comp, opt_cred, cb_msg=print, cb_msg_block=input, cb_bar=None, out_dir=None):
        self.opt_output = opt_output
        self.opt_comp = opt_comp
        self.opt_cred = opt_cred
        self.cb_msg = cb_msg
        self.cb_msg_block = cb_msg_block
        self.cb_bar = cb_bar

        self.fake_vid = self.opt_comp.get('fake_vid', False)
        self.in_dir = self.opt_output['dir']
        self.out_dir = out_dir if out_dir else self.opt_output['dir']