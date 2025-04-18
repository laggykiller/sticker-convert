#!/usr/bin/env python3
import locale
import os
import platform
import signal
import sys
from functools import partial
from json.decoder import JSONDecodeError
from math import ceil
from multiprocessing import Event, cpu_count
from pathlib import Path
from threading import Thread
from typing import Any, Callable, Dict, Optional, Union, cast
from urllib.parse import urlparse

from mergedeep import merge  # type: ignore
from PIL import ImageFont
from ttkbootstrap import BooleanVar, DoubleVar, IntVar, StringVar, Toplevel, Window  # type: ignore
from ttkbootstrap.dialogs import Messagebox, Querybox  # type: ignore

from sticker_convert.definitions import CONFIG_DIR, DEFAULT_DIR, ROOT_DIR
from sticker_convert.gui_components.frames.comp_frame import CompFrame
from sticker_convert.gui_components.frames.config_frame import ConfigFrame
from sticker_convert.gui_components.frames.control_frame import ControlFrame
from sticker_convert.gui_components.frames.cred_frame import CredFrame
from sticker_convert.gui_components.frames.input_frame import InputFrame
from sticker_convert.gui_components.frames.output_frame import OutputFrame
from sticker_convert.gui_components.frames.progress_frame import ProgressFrame
from sticker_convert.gui_components.gui_utils import GUIUtils
from sticker_convert.job import Job
from sticker_convert.job_option import CompOption, CredOption, InputOption, OutputOption
from sticker_convert.utils.files.json_manager import JsonManager
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.url_detect import UrlDetect
from sticker_convert.version import __version__


class GUI(Window):
    def __init__(self) -> None:
        super().__init__(themename="darkly", alpha=0)  # type: ignore
        self.init_done = False
        self.load_jsons()

        font_path = ROOT_DIR / "resources/NotoColorEmoji.ttf"
        self.emoji_font = ImageFont.truetype(font_path.as_posix(), 109)

        GUIUtils.set_icon(self)

        self.title(f"sticker-convert {__version__}")
        self.protocol("WM_DELETE_WINDOW", self.quit)

        (
            self.main_frame,
            self.horizontal_scrollbar_frame,
            self.canvas,
            self.x_scrollbar,
            self.y_scrollbar,
            self.scrollable_frame,
        ) = GUIUtils.create_scrollable_frame(self)

        self.declare_variables()
        self.apply_config()
        self.apply_creds()
        self.init_frames()
        self.pack_frames()
        self.author_info()
        self.warn_tkinter_bug()
        GUIUtils.finalize_window(self)

        self.bind("<<exec_in_main>>", self.exec_in_main)  # type: ignore

    def __enter__(self) -> "GUI":
        return self

    def gui(self) -> None:
        self.init_done = True
        self.highlight_fields()
        self.mainloop()

    def quit(self) -> None:
        if self.job:
            response = self.cb_ask_bool("Job is running, really quit?")
            if response is False:
                return

        self.cb_msg(msg="Quitting, please wait...")

        self.save_config()
        if self.settings_save_cred_var.get() is True:
            self.save_creds()
        else:
            self.delete_creds()

        if self.job:
            self.cancel_job()
        self.destroy()

    def declare_variables(self) -> None:
        # Input
        self.input_option_display_var = StringVar(self)
        self.input_option_true_var = StringVar(self)
        self.input_setdir_var = StringVar(self)
        self.input_address_var = StringVar(self)

        # Compression
        self.no_compress_var = BooleanVar()
        self.comp_preset_var = StringVar(self)
        self.fps_min_var = IntVar(self)
        self.fps_max_var = IntVar(self)
        self.fps_disable_var = BooleanVar()
        self.fps_power_var = DoubleVar()
        self.res_w_min_var = IntVar(self)
        self.res_w_max_var = IntVar(self)
        self.res_w_disable_var = BooleanVar()
        self.res_h_min_var = IntVar(self)
        self.res_h_max_var = IntVar(self)
        self.res_h_disable_var = BooleanVar()
        self.res_power_var = DoubleVar()
        self.quality_min_var = IntVar(self)
        self.quality_max_var = IntVar(self)
        self.quality_disable_var = BooleanVar()
        self.quality_power_var = DoubleVar()
        self.color_min_var = IntVar(self)
        self.color_max_var = IntVar(self)
        self.color_disable_var = BooleanVar()
        self.color_power_var = DoubleVar()
        self.duration_min_var = IntVar(self)
        self.duration_max_var = IntVar(self)
        self.duration_disable_var = BooleanVar()
        self.padding_percent_var = IntVar(self)
        self.img_size_max_var = IntVar(self)
        self.vid_size_max_var = IntVar(self)
        self.size_disable_var = BooleanVar()
        self.bg_color_var = StringVar()
        self.img_format_var = StringVar(self)
        self.vid_format_var = StringVar(self)
        self.fake_vid_var = BooleanVar()
        self.scale_filter_var = StringVar(self)
        self.quantize_method_var = StringVar(self)
        self.chromium_path_var = StringVar(self)
        self.cache_dir_var = StringVar(self)
        self.default_emoji_var = StringVar(self)
        self.steps_var = IntVar(self)
        self.processes_var = IntVar(self)

        # Output
        self.output_option_display_var = StringVar(self)
        self.output_option_true_var = StringVar(self)
        self.output_setdir_var = StringVar(self)
        self.title_var = StringVar(self)
        self.author_var = StringVar(self)

        # Credentials
        self.signal_uuid_var = StringVar(self)
        self.signal_password_var = StringVar(self)
        self.telegram_token_var = StringVar(self)
        self.telegram_userid_var = StringVar(self)
        self.telethon_api_id_var = IntVar(self)
        self.telethon_api_hash_var = StringVar(self)
        self.kakao_auth_token_var = StringVar(self)
        self.kakao_username_var = StringVar(self)
        self.kakao_password_var = StringVar(self)
        self.kakao_country_code_var = StringVar(self)
        self.kakao_phone_number_var = StringVar(self)
        self.kakao_bin_path_var = StringVar(self)
        self.line_cookies_var = StringVar(self)
        self.viber_auth_var = StringVar(self)
        self.viber_bin_path_var = StringVar(self)
        self.discord_token_var = StringVar(self)

        # Config
        self.settings_save_cred_var = BooleanVar()

        # Other
        self.response_event = Event()
        self.response = None
        self.action: Optional[Callable[..., Any]] = None
        self.job: Optional[Job] = None

    def init_frames(self) -> None:
        self.input_frame = InputFrame(
            self, self.scrollable_frame, borderwidth=1, text="Input"
        )
        self.comp_frame = CompFrame(
            self, self.scrollable_frame, borderwidth=1, text="Compression options"
        )
        self.output_frame = OutputFrame(
            self, self.scrollable_frame, borderwidth=1, text="Output"
        )
        self.cred_frame = CredFrame(
            self, self.scrollable_frame, borderwidth=1, text="Credentials"
        )
        self.settings_frame = ConfigFrame(
            self, self.scrollable_frame, borderwidth=1, text="Config"
        )
        self.progress_frame = ProgressFrame(
            self, self.scrollable_frame, borderwidth=1, text="Progress"
        )
        self.control_frame = ControlFrame(self, self.scrollable_frame, borderwidth=1)

    def pack_frames(self) -> None:
        self.input_frame.grid(column=0, row=0, sticky="w", padx=5, pady=5)
        self.comp_frame.grid(column=1, row=0, sticky="news", padx=5, pady=5)
        self.output_frame.grid(column=0, row=1, sticky="w", padx=5, pady=5)
        self.cred_frame.grid(column=1, row=1, rowspan=2, sticky="w", padx=5, pady=5)
        self.settings_frame.grid(column=0, row=2, sticky="news", padx=5, pady=5)
        self.progress_frame.grid(
            column=0, row=3, columnspan=2, sticky="news", padx=5, pady=5
        )
        self.control_frame.grid(
            column=0, row=4, columnspan=2, sticky="news", padx=5, pady=5
        )

    def is_cn(self) -> bool:
        cn_locs = ("zh_chs", "zh_cn", "chinese")
        loc = locale.getlocale()[0]
        winloc = ""
        if platform.system() == "Windows":
            import ctypes

            windll = ctypes.windll.kernel32  # type: ignore
            winloc_id = cast(int, windll.GetUserDefaultUILanguage())  # type: ignore
            winloc = cast(str, locale.windows_locale[winloc_id])  # type: ignore

        if loc is not None and (
            loc.lower().startswith(cn_locs) or winloc.lower().startswith(cn_locs)
        ):
            return True
        return False

    def author_info(self) -> None:
        if self.is_cn():
            msg = "sticker-convert是laggykiller创作的免费开源项目，严禁翻售\n"
            msg += "https://github.com/laggykiller/sticker-convert\n"
            msg += "尊重知识产权，做个文明人，请不要转售贴图！\n"
        else:
            msg = "sticker-convert is Free and Opensource software by laggykiller\n"
            msg += "https://github.com/laggykiller/sticker-convert\n"
            msg += "Please use the stickers with your friends only.\n"
            msg += "It is illegal and immoral to sell stickers downloaded from this program.\n"

        self.cb_msg(msg)

    def warn_tkinter_bug(self) -> None:
        if (
            platform.system() == "Darwin"
            and platform.mac_ver()[0].split(".")[0] == "14"
            and sys.version_info[0] == 3
            and sys.version_info[1] == 11
            and sys.version_info[2] <= 6
        ):
            msg = "NOTICE: If buttons are not responsive, try to press "
            msg += "on title bar or move mouse cursor away from window for a while.\n"
            msg += "(This is a bug in tkinter specific to macOS 14 python <=3.11.6)\n"
            msg += "(https://github.com/python/cpython/issues/110218)\n"
            self.cb_msg(msg)

    def load_jsons(self) -> None:
        try:
            from sticker_convert.utils.files.json_resources_loader import COMPRESSION_JSON, EMOJI_JSON, HELP_JSON, INPUT_JSON, OUTPUT_JSON
        except RuntimeError as e:
            self.cb_msg(str(e))
            return

        self.help = HELP_JSON
        self.input_presets = INPUT_JSON
        self.compression_presets = COMPRESSION_JSON
        self.output_presets = OUTPUT_JSON
        self.emoji_list = EMOJI_JSON

        if not (
            self.compression_presets and self.input_presets and self.output_presets
        ):
            Messagebox.show_error(  # type: ignore
                message='Warning: json(s) under "resources" directory cannot be found',
                title="sticker-convert",
            )
            sys.exit()

        self.settings_path = CONFIG_DIR / "config.json"
        if self.settings_path.is_file():
            try:
                self.settings: Dict[Any, Any] = JsonManager.load_json(
                    self.settings_path
                )
            except JSONDecodeError:
                self.cb_msg("Warning: config.json content is corrupted")
                self.settings = {}
        else:
            self.settings = {}

        self.creds_path = CONFIG_DIR / "creds.json"
        if self.creds_path.is_file():
            try:
                self.creds = JsonManager.load_json(self.creds_path)
            except JSONDecodeError:
                self.cb_msg("Warning: creds.json content is corrupted")
                self.creds = {}
        else:
            self.creds = {}

    def save_config(self) -> None:
        # Only update comp_custom if custom preset is selected
        if self.comp_preset_var.get() == "custom":
            comp_custom: Dict[Any, Any] = merge(  # type: ignore
                self.compression_presets.get("custom"),  # type: ignore
                self.get_opt_comp().to_dict(),
            )
            comp_custom["format"]["img"] = comp_custom["format"]["img"][0]
            comp_custom["format"]["vid"] = comp_custom["format"]["vid"][0]
            del comp_custom["preset"]
            del comp_custom["no_compress"]
        else:
            compression_presets_custom = self.compression_presets.get("custom")
            if compression_presets_custom is None:
                comp_custom = {}
            else:
                comp_custom = compression_presets_custom

        self.settings = {
            "input": self.get_opt_input().to_dict(),
            "comp": {
                "no_compress": self.no_compress_var.get(),
                "preset": self.comp_preset_var.get(),
                "chromium_path": self.chromium_path_var.get(),
                "cache_dir": self.cache_dir_var.get(),
                "processes": self.processes_var.get(),
            },
            "comp_custom": comp_custom,
            "output": self.get_opt_output().to_dict(),
            "creds": {"save_cred": self.settings_save_cred_var.get()},
        }

        JsonManager.save_json(self.settings_path, self.settings)

    def save_creds(self) -> None:
        self.creds = self.get_opt_cred().to_dict()

        JsonManager.save_json(self.creds_path, self.creds)

    def delete_creds(self) -> None:
        if self.creds_path.is_file():
            os.remove(self.creds_path)

    def delete_config(self) -> None:
        if self.settings_path.is_file():
            os.remove(self.settings_path)

    def apply_config(self) -> None:
        # Input
        self.default_input_mode: str = self.settings.get("input", {}).get(
            "option", "auto"
        )
        self.input_address_var.set(self.settings.get("input", {}).get("url", ""))
        default_stickers_input_dir = str(DEFAULT_DIR / "stickers_input")
        self.input_setdir_var.set(
            self.settings.get("input", {}).get("dir", default_stickers_input_dir)
        )
        if not Path(self.input_setdir_var.get()).is_dir():
            self.input_setdir_var.set(default_stickers_input_dir)
        self.input_option_display_var.set(
            self.input_presets[self.default_input_mode]["full_name"]
        )
        self.input_option_true_var.set(
            self.input_presets[self.default_input_mode]["full_name"]
        )

        # Compression
        self.no_compress_var.set(
            self.settings.get("comp", {}).get("no_compress", False)
        )
        default_comp_preset = list(self.compression_presets.keys())[0]
        self.comp_preset_var.set(
            self.settings.get("comp", {}).get("preset", default_comp_preset)
        )
        comp_custom = self.settings.get("comp_custom")
        if comp_custom:
            self.compression_presets["custom"] = merge(
                self.compression_presets["custom"], comp_custom
            )
        self.cache_dir_var.set(self.settings.get("comp", {}).get("cache_dir", ""))
        self.chromium_path_var.set(
            self.settings.get("comp", {}).get("chromium_path", "")
        )
        self.processes_var.set(
            self.settings.get("comp", {}).get("processes", ceil(cpu_count() / 2))
        )
        self.default_output_mode: str = self.settings.get("output", {}).get(
            "option", "signal"
        )

        # Output
        default_stickers_output_dir = str(DEFAULT_DIR / "stickers_output")
        self.output_setdir_var.set(
            self.settings.get("output", {}).get("dir", default_stickers_output_dir)
        )
        if not Path(self.output_setdir_var.get()).is_dir():
            self.output_setdir_var.set(default_stickers_output_dir)
        self.title_var.set(self.settings.get("output", {}).get("title", ""))
        self.author_var.set(self.settings.get("output", {}).get("author", ""))
        self.settings_save_cred_var.set(
            self.settings.get("creds", {}).get("save_cred", True)
        )
        self.output_option_display_var.set(
            self.output_presets[self.default_output_mode]["full_name"]
        )
        self.output_option_true_var.set(
            self.output_presets[self.default_output_mode]["full_name"]
        )

    def apply_creds(self) -> None:
        self.signal_uuid_var.set(self.creds.get("signal", {}).get("uuid", ""))
        self.signal_password_var.set(self.creds.get("signal", {}).get("password", ""))
        self.telegram_token_var.set(self.creds.get("telegram", {}).get("token", ""))
        self.telegram_userid_var.set(self.creds.get("telegram", {}).get("userid", ""))
        self.telethon_api_id_var.set(self.creds.get("telethon", {}).get("api_id", 0))
        self.telethon_api_hash_var.set(
            self.creds.get("telethon", {}).get("api_hash", "")
        )
        self.kakao_auth_token_var.set(self.creds.get("kakao", {}).get("auth_token", ""))
        self.kakao_username_var.set(self.creds.get("kakao", {}).get("username", ""))
        self.kakao_password_var.set(self.creds.get("kakao", {}).get("password", ""))
        self.kakao_country_code_var.set(
            self.creds.get("kakao", {}).get("country_code", "")
        )
        self.kakao_phone_number_var.set(
            self.creds.get("kakao", {}).get("phone_number", "")
        )
        self.line_cookies_var.set(self.creds.get("line", {}).get("cookies", ""))
        self.viber_auth_var.set(self.creds.get("viber", {}).get("auth", ""))
        self.discord_token_var.set(self.creds.get("discord", {}).get("token", ""))

    def get_input_name(self) -> str:
        return [
            k
            for k, v in self.input_presets.items()
            if v["full_name"] == self.input_option_true_var.get()
        ][0]

    def get_input_display_name(self) -> str:
        return [
            k
            for k, v in self.input_presets.items()
            if v["full_name"] == self.input_option_display_var.get()
        ][0]

    def get_output_name(self) -> str:
        return [
            k
            for k, v in self.output_presets.items()
            if v["full_name"] == self.output_option_true_var.get()
        ][0]

    # def get_output_display_name(self) -> str:
    #     return [
    #         k
    #         for k, v in self.output_presets.items()
    #         if v["full_name"] == self.output_option_display_var.get()
    #     ][0]

    def get_preset(self) -> str:
        selection = self.comp_preset_var.get()
        if selection == "auto":
            output_option = self.get_output_name()
            if "telegram_emoji" in output_option:
                return "telegram_emoji"
            if "telegram" in output_option:
                return "telegram"
            if output_option == "imessage":
                return "imessage_small"
            if output_option == "local":
                return selection
            return output_option

        return selection

    def start_job(self) -> None:
        self.save_config()
        if self.settings_save_cred_var.get() is True:
            self.save_creds()
        else:
            self.delete_creds()

        self.control_frame.start_btn.config(text="Cancel", bootstyle="danger")  # type: ignore
        self.set_inputs("disabled")

        opt_input = self.get_opt_input()
        opt_output = self.get_opt_output()
        opt_comp = self.get_opt_comp()
        opt_cred = self.get_opt_cred()

        self.job = Job(
            opt_input,
            opt_comp,
            opt_output,
            opt_cred,
            self.cb_msg,
            self.cb_msg_block,
            self.cb_bar,
            self.cb_ask_bool,
            self.cb_ask_str,
        )

        signal.signal(signal.SIGINT, self.job.cancel)

        Thread(target=self.start_process, daemon=True).start()

    def get_opt_input(self) -> InputOption:
        return InputOption(
            option=self.get_input_name(),
            url=self.input_address_var.get(),
            dir=Path(self.input_setdir_var.get()),
        )

    def get_opt_output(self) -> OutputOption:
        return OutputOption(
            option=self.get_output_name(),
            dir=Path(self.output_setdir_var.get()),
            title=self.title_var.get(),
            author=self.author_var.get(),
        )

    def get_opt_comp(self) -> CompOption:
        return CompOption(
            preset=self.get_preset(),
            size_max_img=self.img_size_max_var.get()
            if not self.size_disable_var.get()
            else None,
            size_max_vid=self.vid_size_max_var.get()
            if not self.size_disable_var.get()
            else None,
            format_img=(self.img_format_var.get(),),
            format_vid=(self.vid_format_var.get(),),
            fps_min=self.fps_min_var.get() if not self.fps_disable_var.get() else None,
            fps_max=self.fps_max_var.get() if not self.fps_disable_var.get() else None,
            fps_power=self.fps_power_var.get(),
            res_w_min=self.res_w_min_var.get()
            if not self.res_w_disable_var.get()
            else None,
            res_w_max=self.res_w_max_var.get()
            if not self.res_w_disable_var.get()
            else None,
            res_h_min=self.res_h_min_var.get()
            if not self.res_h_disable_var.get()
            else None,
            res_h_max=self.res_h_max_var.get()
            if not self.res_h_disable_var.get()
            else None,
            res_power=self.res_power_var.get(),
            quality_min=self.quality_min_var.get()
            if not self.quality_disable_var.get()
            else None,
            quality_max=self.quality_max_var.get()
            if not self.quality_disable_var.get()
            else None,
            quality_power=self.quality_power_var.get(),
            color_min=self.color_min_var.get()
            if not self.color_disable_var.get()
            else None,
            color_max=self.color_max_var.get()
            if not self.color_disable_var.get()
            else None,
            color_power=self.color_power_var.get(),
            duration_min=self.duration_min_var.get()
            if not self.duration_disable_var.get()
            else None,
            duration_max=self.duration_max_var.get()
            if not self.duration_disable_var.get()
            else None,
            bg_color=self.bg_color_var.get(),
            padding_percent=self.padding_percent_var.get(),
            steps=self.steps_var.get(),
            fake_vid=self.fake_vid_var.get(),
            scale_filter=self.scale_filter_var.get(),
            quantize_method=self.quantize_method_var.get(),
            chromium_path=self.chromium_path_var.get()
            if self.chromium_path_var.get() != ""
            else None,
            cache_dir=self.cache_dir_var.get()
            if self.cache_dir_var.get() != ""
            else None,
            default_emoji=self.default_emoji_var.get(),
            no_compress=self.no_compress_var.get(),
            processes=self.processes_var.get(),
        )

    def get_opt_cred(self) -> CredOption:
        return CredOption(
            signal_uuid=self.signal_uuid_var.get(),
            signal_password=self.signal_password_var.get(),
            telegram_token=self.telegram_token_var.get(),
            telegram_userid=self.telegram_userid_var.get(),
            telethon_api_id=self.telethon_api_id_var.get(),
            telethon_api_hash=self.telethon_api_hash_var.get(),
            kakao_auth_token=self.kakao_auth_token_var.get(),
            kakao_username=self.kakao_username_var.get(),
            kakao_password=self.kakao_password_var.get(),
            kakao_country_code=self.kakao_country_code_var.get(),
            kakao_phone_number=self.kakao_phone_number_var.get(),
            line_cookies=self.line_cookies_var.get(),
            viber_auth=self.viber_auth_var.get(),
            discord_token=self.discord_token_var.get(),
        )

    def start_process(self) -> None:
        if self.job:
            self.job.start()
        self.job = None

        self.stop_job()

    def stop_job(self) -> None:
        self.set_inputs("normal")
        self.control_frame.start_btn.config(text="Start", bootstyle="default")  # type: ignore

    def cancel_job(self) -> None:
        if self.job:
            # Need to start new thread or else GUI may freeze
            Thread(target=self.job.cancel, daemon=True).start()

    def set_inputs(self, state: str) -> None:
        # state: 'normal', 'disabled'

        self.input_frame.set_states(state=state)
        self.comp_frame.set_states(state=state)
        self.output_frame.set_states(state=state)
        self.cred_frame.set_states(state=state)
        self.settings_frame.set_states(state=state)

        if state == "normal":
            self.input_frame.cb_input_option()
            self.comp_frame.cb_no_compress()

    def exec_in_main(self, _evt: Any) -> Any:
        if self.action:
            self.response = self.action()
        self.response_event.set()

    def cb_ask_str(
        self,
        question: str,
        initialvalue: Optional[str] = None,
        cli_show_initialvalue: bool = True,
        parent: Optional[object] = None,
    ) -> str:
        self.action = partial(
            Querybox.get_string,  # type: ignore
            question,
            title="sticker-convert",
            initialvalue=initialvalue,
            parent=parent,
        )
        self.event_generate("<<exec_in_main>>")
        self.response_event.wait()
        self.response_event.clear()

        if self.response is None:
            return ""
        elif isinstance(self.response, str):
            return self.response
        else:
            raise RuntimeError(f"Invalid response in cb_ask_str: {self.response}")

    def cb_ask_bool(
        self, question: str, parent: Union[Window, Toplevel, None] = None
    ) -> bool:
        self.action = partial(
            Messagebox.yesno,  # type: ignore
            question,
            title="sticker-convert",
            parent=parent,
        )
        self.event_generate("<<exec_in_main>>")
        self.response_event.wait()
        self.response_event.clear()

        if self.response == "Yes":
            return True
        return False

    def cb_msg(self, *args: Any, **kwargs: Any) -> None:
        self.progress_frame.update_message_box(*args, **kwargs)

    def cb_msg_block(
        self,
        *args: Any,
        message: Optional[str] = None,
        parent: Optional[object] = None,
        **_kwargs: Any,
    ) -> Any:
        if message is None and len(args) > 0:
            message = " ".join(str(i) for i in args)
        self.action = partial(
            Messagebox.show_info,  # type: ignore
            message,
            title="sticker-convert",
            parent=parent,
        )
        self.event_generate("<<exec_in_main>>")
        self.response_event.wait()
        self.response_event.clear()

        return self.response

    def cb_bar(
        self,
        set_progress_mode: Optional[str] = None,
        steps: int = 0,
        update_bar: int = 0,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.progress_frame.update_progress_bar(
            set_progress_mode, steps, update_bar, *args, **kwargs
        )

    def highlight_fields(self) -> bool:
        if not self.init_done:
            return True

        input_option = self.get_input_name()
        input_option_display = self.get_input_display_name()
        output_option = self.get_output_name()
        # output_option_display = self.get_output_display_name()
        url = self.input_address_var.get()

        in_out_dir_same = (
            Path(self.input_setdir_var.get()).absolute()
            == Path(self.output_setdir_var.get()).absolute()
        )

        # Input
        if in_out_dir_same is True:
            self.input_frame.input_setdir_entry.config(bootstyle="danger")  # type: ignore
        elif not Path(self.input_setdir_var.get()).is_dir():
            self.input_frame.input_setdir_entry.config(bootstyle="warning")  # type: ignore
        else:
            self.input_frame.input_setdir_entry.config(bootstyle="default")  # type: ignore

        self.input_frame.address_lbl.config(
            text=self.input_presets[input_option_display]["address_lbls"]
        )
        self.input_frame.address_entry.config(bootstyle="default")  # type: ignore

        if input_option == "local":
            self.input_frame.address_entry.config(state="disabled")
            self.input_frame.address_tip.config(
                text=self.input_presets[input_option_display]["example"]
            )

        else:
            self.input_frame.address_entry.config(state="normal")
            self.input_frame.address_tip.config(
                text=self.input_presets[input_option_display]["example"]
            )
            download_option = UrlDetect.detect(url)

            if not url:
                self.input_frame.address_entry.config(bootstyle="warning")  # type: ignore

            elif (
                download_option is None
                or input_option.startswith(download_option) is False
                and not (
                    input_option
                    in ("kakao", "band", "line", "discord", "discord_emoji")
                    and url.isnumeric()
                )
            ):
                self.input_frame.address_entry.config(bootstyle="danger")  # type: ignore
                self.input_frame.address_tip.config(
                    text=f"Invalid URL. {self.input_presets[input_option_display]['example']}"
                )

            elif input_option_display == "auto" and download_option:
                self.input_frame.address_tip.config(
                    text=f"Detected URL: {download_option}"
                )

        # Output
        if in_out_dir_same is True:
            self.output_frame.output_setdir_entry.config(bootstyle="danger")  # type: ignore
        elif not Path(self.output_setdir_var.get()).is_dir():
            self.output_frame.output_setdir_entry.config(bootstyle="warning")  # type: ignore
        else:
            self.output_frame.output_setdir_entry.config(bootstyle="default")  # type: ignore

        if (
            MetadataHandler.check_metadata_required(output_option, "title")
            and not MetadataHandler.check_metadata_provided(
                Path(self.input_setdir_var.get()), input_option, "title"
            )
            and not self.title_var.get()
        ):
            self.output_frame.title_entry.config(bootstyle="warning")  # type: ignore
        else:
            self.output_frame.title_entry.config(bootstyle="default")  # type: ignore

        if (
            MetadataHandler.check_metadata_required(output_option, "author")
            and not MetadataHandler.check_metadata_provided(
                Path(self.input_setdir_var.get()), input_option, "author"
            )
            and not self.author_var.get()
        ):
            self.output_frame.author_entry.config(bootstyle="warning")  # type: ignore
        else:
            self.output_frame.author_entry.config(bootstyle="default")  # type: ignore

        if self.comp_preset_var.get() == "auto":
            if output_option == "local":
                self.no_compress_var.set(True)
            else:
                self.no_compress_var.set(False)
            self.comp_frame.cb_no_compress()

        # Credentials
        if output_option == "signal" and not self.signal_uuid_var.get():
            self.cred_frame.signal_uuid_entry.config(bootstyle="warning")  # type: ignore
        else:
            self.cred_frame.signal_uuid_entry.config(bootstyle="default")  # type: ignore

        if output_option == "signal" and not self.signal_password_var.get():
            self.cred_frame.signal_password_entry.config(bootstyle="warning")  # type: ignore
        else:
            self.cred_frame.signal_password_entry.config(bootstyle="default")  # type: ignore

        if (
            input_option == "telegram" or output_option == "telegram"
        ) and not self.telegram_token_var.get():
            self.cred_frame.telegram_token_entry.config(bootstyle="warning")  # type: ignore
        else:
            self.cred_frame.telegram_token_entry.config(bootstyle="default")  # type: ignore

        if output_option == "telegram" and not self.telegram_userid_var.get():
            self.cred_frame.telegram_userid_entry.config(bootstyle="warning")  # type: ignore
        else:
            self.cred_frame.telegram_userid_entry.config(bootstyle="default")  # type: ignore

        if output_option == "viber" and not self.viber_auth_var.get():
            self.cred_frame.viber_auth_entry.config(bootstyle="warning")  # type: ignore
        else:
            self.cred_frame.viber_auth_entry.config(bootstyle="default")  # type: ignore

        if (
            urlparse(url).netloc == "e.kakao.com"
            and not self.kakao_auth_token_var.get()
        ):
            self.cred_frame.kakao_auth_token_entry.config(bootstyle="warning")  # type: ignore
        else:
            self.cred_frame.kakao_auth_token_entry.config(bootstyle="default")  # type: ignore

        if input_option.startswith("discord") and not self.discord_token_var.get():
            self.cred_frame.discord_token_entry.config(bootstyle="warning")  # type: ignore
        else:
            self.cred_frame.discord_token_entry.config(bootstyle="default")  # type: ignore

        # Check for Input and Compression mismatch
        if (
            not self.no_compress_var.get()
            and self.get_output_name() != "local"
            and self.comp_preset_var.get() not in ("auto", "custom")
            and self.get_output_name() not in self.comp_preset_var.get()
        ):
            self.comp_frame.comp_preset_opt.config(bootstyle="warning")  # type: ignore
            self.output_frame.output_option_opt.config(bootstyle="warning")  # type: ignore
        else:
            self.comp_frame.comp_preset_opt.config(bootstyle="secondary")  # type: ignore
            self.output_frame.output_option_opt.config(bootstyle="secondary")  # type: ignore

        return True
