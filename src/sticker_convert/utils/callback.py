#!/usr/bin/env python3
from abc import ABC
import copy
from multiprocessing import Event
from typing import Callable, Optional, Union, Any

from tqdm import tqdm


class DummyCallbackReturn(ABC):
    def set_response(self, response: Any):
        pass

    def get_response(self):
        pass


class CallbackReturn(DummyCallbackReturn):
    def __init__(self):
        self.response_event = Event()
        self.response = None

    def set_response(self, response: Any):
        self.response = response
        self.response_event.set()

    def get_response(self):
        self.response_event.wait()

        response = copy.deepcopy(self.response)
        self.response = None

        self.response_event.clear()

        return response


class DummyCallback(ABC):
    def put(
        self,
        i: Union[
            tuple[Optional[str], Optional[tuple[Any, ...]], Optional[dict[str, Any]]],
            str,
        ],
    ) -> Union[str, bool, None]:
        pass


class Callback(DummyCallback):
    def __init__(
        self,
        msg: Optional[Callable[..., None]] = None,
        bar: Optional[Callable[..., None]] = None,
        msg_block: Optional[Callable[..., None]] = None,
        ask_bool: Optional[Callable[..., bool]] = None,
        ask_str: Optional[Callable[..., str]] = None,
        silent: bool = False,
        no_confirm: bool = False,
    ):
        self.progress_bar = None

        if msg:
            self.msg = msg
        else:
            self.msg = self.cb_msg

        if bar:
            self.bar = bar
        else:
            self.bar = self.cb_bar

        if msg_block:
            self.msg_block = msg_block
        else:
            self.msg_block = self.cb_msg_block

        if ask_bool:
            self.ask_bool = ask_bool
        else:
            self.ask_bool = self.cb_ask_bool

        if ask_str:
            self.ask_str = ask_str
        else:
            self.ask_str = self.cb_ask_str

        self.silent = silent
        self.no_confirm = no_confirm

    def cb_msg(self, *args: Any, **kwargs: Any):
        if self.silent:
            return

        msg = kwargs.get("msg")
        file = kwargs.get("file")

        if not msg and len(args) == 1:
            msg = str(args[0])

        if msg:
            if self.progress_bar:
                self.progress_bar.write(msg)
            elif file:
                print(msg, file=file)
            else:
                print(msg)

    def cb_bar(
        self,
        set_progress_mode: Optional[str] = None,
        steps: Optional[int] = None,
        update_bar: bool = False,
    ):
        if self.silent:
            return

        if self.progress_bar:
            if update_bar:
                self.progress_bar.update()
            elif set_progress_mode == "indeterminate":
                self.progress_bar.close()
                self.progress_bar = None
            elif set_progress_mode == "clear":
                self.progress_bar.reset()
        elif set_progress_mode == "determinate":
            self.progress_bar = tqdm(total=steps)

    def cb_msg_block(self, *args: Any):
        if self.silent:
            return
        if len(args) > 0:
            msg = " ".join(str(i) for i in args)
            self.msg(msg)
        if not self.no_confirm:
            input("Press Enter to continue...")

    def cb_ask_bool(self, *args: Any, **kwargs: Any) -> bool:
        question = args[0]

        self.msg(question)

        if self.no_confirm:
            self.msg(
                '"--no-confirm" flag is set. Continue with this run without asking questions'
            )
            return True
        else:
            self.msg(
                'If you do not want to get asked by this question, add "--no-confirm" flag'
            )
            self.msg()
            result = input("Continue? [y/N] > ")
            if result.lower() != "y":
                self.msg("Cancelling this run")
                return False
            else:
                return True

    def cb_ask_str(
        self,
        msg: Optional[str] = None,
        initialvalue: Optional[str] = None,
        cli_show_initialvalue: bool = True,
    ) -> str:
        self.msg(msg)

        hint = ""
        if cli_show_initialvalue and initialvalue:
            hint = f" [Default: {initialvalue}]"

        response = input(f"Enter your response and press enter{hint} > ")

        if initialvalue and not response:
            response = initialvalue

        return response

    def put(
        self,
        i: Union[
            tuple[Optional[str], Optional[tuple[Any, ...]], Optional[dict[str, Any]]],
            str,
        ],
    ) -> Union[str, bool, None]:
        if isinstance(i, tuple):
            action = i[0]
            if len(i) >= 2:
                args: tuple[str, ...] = i[1] if i[1] else tuple()
            else:
                args = tuple()
            if len(i) >= 3:
                kwargs: dict[str, Any] = i[2] if i[2] else dict()
            else:
                kwargs = dict()
        else:
            action = i
            args = tuple()
            kwargs = dict()

        # Fake implementation for Queue.put()
        if action is None:
            return
        elif action == "msg":
            self.msg(*args, **kwargs)
        elif action == "bar":
            self.bar(**kwargs)
        elif action == "update_bar":
            self.bar(update_bar=True)
        elif action == "msg_block":
            return self.msg_block(*args, **kwargs)
        elif action == "ask_bool":
            return self.ask_bool(*args, **kwargs)
        elif action == "ask_str":
            return self.ask_str(**kwargs)
        else:
            self.msg(action)
