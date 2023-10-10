#!/usr/bin/env python3


class FakeCbMsg:
    def __init__(self, msg_protocol=print, silent=False):
        self.msg_protocol = msg_protocol
        self.silent = silent

    def put(self, msg: str):
        if not self.silent:
            self.msg_protocol(msg)  # type: ignore[operator]
