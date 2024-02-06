#!/usr/bin/env python3
import argparse
from argparse import Namespace
import math
import signal
from json.decoder import JSONDecodeError
from multiprocessing import cpu_count
from pathlib import Path

from sticker_convert.version import __version__
from sticker_convert.definitions import CONFIG_DIR, DEFAULT_DIR, ROOT_DIR
from sticker_convert.job import Job
from sticker_convert.job_option import CompOption, CredOption, InputOption, OutputOption
from sticker_convert.utils.auth.get_kakao_auth import GetKakaoAuth
from sticker_convert.utils.auth.get_line_auth import GetLineAuth
from sticker_convert.utils.auth.get_signal_auth import GetSignalAuth
from sticker_convert.utils.callback import Callback
from sticker_convert.utils.files.json_manager import JsonManager
from sticker_convert.utils.url_detect import UrlDetect


class CLI:
    def __init__(self):
        self.cb = Callback()

    def cli(self):
        try:
            self.help: dict[str, dict[str, str]] = JsonManager.load_json(
                ROOT_DIR / "resources/help.json"
            )
            self.input_presets = JsonManager.load_json(
                ROOT_DIR / "resources/input.json"
            )
            self.compression_presets = JsonManager.load_json(
                ROOT_DIR / "resources/compression.json"
            )
            self.output_presets = JsonManager.load_json(
                ROOT_DIR / "resources/output.json"
            )
        except RuntimeError as e:
            self.cb.msg(e.__str__)
            return

        parser = argparse.ArgumentParser(
            description="CLI for stickers-convert",
            formatter_class=argparse.RawTextHelpFormatter,
        )

        parser.add_argument("--version", action="version", version=__version__)
        parser.add_argument(
            "--no-confirm",
            dest="no_confirm",
            action="store_true",
            help=self.help["global"]["no_confirm"],
        )

        parser_input = parser.add_argument_group("Input options")
        for k, v in self.help["input"].items():
            parser_input.add_argument(f'--{k.replace("_", "-")}', dest=k, help=v)
        parser_input_src = parser_input.add_mutually_exclusive_group()
        for k, v in self.input_presets.items():
            if k == "local":
                continue
            parser_input_src.add_argument(
                f'--download-{k.replace("_", "-")}',
                dest=f"download_{k}",
                help=f'{v["help"]}\n({v["example"]})',
            )

        parser_output = parser.add_argument_group("Output options")
        for k, v in self.help["output"].items():
            parser_output.add_argument(f'--{k.replace("_", "-")}', dest=k, help=v)
        parser_output_dst = parser_output.add_mutually_exclusive_group()
        for k, v in self.output_presets.items():
            if k == "local":
                continue
            parser_output_dst.add_argument(
                f'--export-{k.replace("_", "-")}',
                dest=f"export_{k}",
                action="store_true",
                help=v["help"],
            )

        parser_comp = parser.add_argument_group("Compression options")
        parser_comp.add_argument(
            "--no-compress",
            dest="no_compress",
            action="store_true",
            help=self.help["comp"]["no_compress"],
        )
        parser_comp.add_argument(
            "--preset",
            dest="preset",
            default="auto",
            choices=self.compression_presets.keys(),
            help=self.help["comp"]["preset"],
        )
        flags_int = (
            "steps",
            "processes",
            "fps_min",
            "fps_max",
            "res_min",
            "res_max",
            "res_w_min",
            "res_w_max",
            "res_h_min",
            "res_h_max",
            "quality_min",
            "quality_max",
            "color_min",
            "color_max",
            "duration_min",
            "duration_max",
            "vid_size_max",
            "img_size_max",
        )
        flags_float = ("fps_power", "res_power", "quality_power", "color_power")
        flags_str = (
            "vid_format",
            "img_format",
            "cache_dir",
            "scale_filter",
            "quantize_method",
        )
        flags_bool = "fake_vid"
        for k, v in self.help["comp"].items():
            if k in flags_int:
                keyword_args = {"type": int, "default": None}
            elif k in flags_float:
                keyword_args = {"type": float, "default": None}
            elif k in flags_str:
                keyword_args = {"default": None}
            elif k in flags_bool:
                keyword_args = {"action": "store_true", "default": None}
            else:
                continue
            parser_comp.add_argument(
                f'--{k.replace("_", "-")}',
                **keyword_args,  # type: ignore
                dest=k,
                help=v,
            )
        parser_comp.add_argument(
            "--default-emoji",
            dest="default_emoji",
            default=self.compression_presets["custom"]["default_emoji"],
            help=self.help["comp"]["default_emoji"],
        )

        parser_cred = parser.add_argument_group("Credentials options")
        flags_bool = ("signal_get_auth", "kakao_get_auth", "line_get_auth")
        for k, v in self.help["cred"].items():
            keyword_args = {}
            if k in flags_bool:
                keyword_args = {"action": "store_true"}
            parser_cred.add_argument(
                f'--{k.replace("_", "-")}',
                **keyword_args,  # type: ignore
                dest=k,
                help=v,
            )

        args = parser.parse_args()

        self.cb.no_confirm = args.no_confirm

        self.opt_input = self.get_opt_input(args)
        self.opt_output = self.get_opt_output(args)
        self.opt_comp = self.get_opt_comp(args)
        self.opt_cred = self.get_opt_cred(args)

        job = Job(
            self.opt_input,
            self.opt_comp,
            self.opt_output,
            self.opt_cred,
            self.cb.msg,
            self.cb.msg_block,
            self.cb.bar,
            self.cb.ask_bool,
            self.cb.ask_str,
        )

        signal.signal(signal.SIGINT, job.cancel)
        status = job.start()
        exit(status)

    def get_opt_input(self, args: Namespace) -> InputOption:
        download_options = {
            "auto": args.download_auto,
            "signal": args.download_signal,
            "line": args.download_line,
            "telegram": args.download_telegram,
            "kakao": args.download_kakao,
        }

        download_option = "local"
        url = ""
        for k, v in download_options.items():
            if v:
                download_option = k
                url = v
                break

        if download_option == "auto":
            download_option = UrlDetect.detect(url)
            self.cb.msg(f"Detected URL input source: {download_option}")
            if not download_option:
                self.cb.msg(f"Error: Unrecognied URL input source for url: {url}")
                exit()

        opt_input = InputOption(
            option=download_option,
            url=url,
            dir=Path(args.input_dir).resolve()
            if args.input_dir
            else DEFAULT_DIR / "stickers_input",
        )

        return opt_input

    def get_opt_output(self, args: Namespace) -> OutputOption:
        if args.export_whatsapp:
            export_option = "whatsapp"
        elif args.export_signal:
            export_option = "signal"
        elif args.export_telegram:
            export_option = "telegram"
        elif args.export_imessage:
            export_option = "imessage"
        else:
            export_option = "local"

        opt_output = OutputOption(
            option=export_option,
            dir=Path(args.output_dir).resolve()
            if args.output_dir
            else DEFAULT_DIR / "stickers_output",
            title=args.title,
            author=args.author,
        )

        return opt_output

    def get_opt_comp(self, args: Namespace) -> CompOption:
        preset: str = args.preset if args.preset else "auto"
        if args.preset == "custom":
            if (
                sum(
                    (
                        args.export_whatsapp,
                        args.export_signal,
                        args.export_telegram,
                        args.export_imessage,
                    )
                )
                > 1
            ):
                # Let the verify functions in export do the compression
                args.no_compress = True
            elif args.export_whatsapp:
                preset = "whatsapp"
            elif args.export_signal:
                preset = "signal"
            elif args.export_telegram:
                preset = "telegram"
            elif args.export_imessage:
                preset = "imessage_small"
        elif args.preset == "auto":
            output_option = (
                self.opt_output.option if self.opt_output.option else "local"
            )
            if output_option == "local":
                preset = "custom"
                args.no_compress = True
                self.cb.msg(
                    "Auto compression option set to no_compress (Reason: Export to local directory only)"
                )
            elif output_option == "imessage":
                preset = "imessage_small"
                self.cb.msg(f"Auto compression option set to {preset}")
            else:
                preset = output_option
                self.cb.msg(f"Auto compression option set to {preset}")

        opt_comp = CompOption(
            preset=preset,
            size_max_img=self.compression_presets[preset]["size_max"]["img"]
            if args.img_size_max is None
            else args.img_size_max,
            size_max_vid=self.compression_presets[preset]["size_max"]["vid"]
            if args.vid_size_max is None
            else args.vid_size_max,
            format_img=[
                self.compression_presets[preset]["format"]["img"]
                if args.img_format is None
                else args.img_format
            ],
            format_vid=[
                self.compression_presets[preset]["format"]["vid"]
                if args.vid_format is None
                else args.vid_format
            ],
            fps_min=self.compression_presets[preset]["fps"]["min"]
            if args.fps_min is None
            else args.fps_min,
            fps_max=self.compression_presets[preset]["fps"]["max"]
            if args.fps_max is None
            else args.fps_max,
            fps_power=self.compression_presets[preset]["fps"]["power"]
            if args.fps_power is None
            else args.fps_power,
            res_w_min=self.compression_presets[preset]["res"]["w"]["min"]
            if args.res_w_min is None
            else args.res_w_min,
            res_w_max=self.compression_presets[preset]["res"]["w"]["max"]
            if args.res_w_max is None
            else args.res_w_max,
            res_h_min=self.compression_presets[preset]["res"]["h"]["min"]
            if args.res_h_min is None
            else args.res_h_min,
            res_h_max=self.compression_presets[preset]["res"]["h"]["max"]
            if args.res_h_max is None
            else args.res_h_max,
            res_power=self.compression_presets[preset]["res"]["power"]
            if args.res_power is None
            else args.res_power,
            quality_min=self.compression_presets[preset]["quality"]["min"]
            if args.quality_min is None
            else args.quality_min,
            quality_max=self.compression_presets[preset]["quality"]["max"]
            if args.quality_max is None
            else args.quality_max,
            quality_power=self.compression_presets[preset]["quality"]["power"]
            if args.quality_power is None
            else args.quality_power,
            color_min=self.compression_presets[preset]["color"]["min"]
            if args.color_min is None
            else args.color_min,
            color_max=self.compression_presets[preset]["color"]["max"]
            if args.color_max is None
            else args.color_max,
            color_power=self.compression_presets[preset]["color"]["power"]
            if args.color_power is None
            else args.color_power,
            duration_min=self.compression_presets[preset]["duration"]["min"]
            if args.duration_min is None
            else args.duration_min,
            duration_max=self.compression_presets[preset]["duration"]["max"]
            if args.duration_max is None
            else args.duration_max,
            steps=self.compression_presets[preset]["steps"]
            if args.steps is None
            else args.steps,
            fake_vid=self.compression_presets[preset]["fake_vid"]
            if args.fake_vid is None
            else args.fake_vid,
            cache_dir=args.cache_dir,
            scale_filter=self.compression_presets[preset]["scale_filter"]
            if args.scale_filter is None
            else args.scale_filter,
            quantize_method=self.compression_presets[preset]["quantize_method"]
            if args.quantize_method is None
            else args.quantize_method,
            default_emoji=self.compression_presets[preset]["default_emoji"]
            if args.default_emoji is None
            else args.default_emoji,
            no_compress=args.no_compress,
            processes=args.processes if args.processes else math.ceil(cpu_count() / 2),
        )

        return opt_comp

    def get_opt_cred(self, args: Namespace) -> CredOption:
        creds_path = CONFIG_DIR / "creds.json"
        creds = {}
        try:
            creds = JsonManager.load_json(creds_path)
        except JSONDecodeError:
            self.cb.msg("Warning: creds.json content is corrupted")

        if creds:
            self.cb.msg("Loaded credentials from creds.json")

        opt_cred = CredOption(
            signal_uuid=args.signal_uuid
            if args.signal_uuid
            else creds.get("signal", {}).get("uuid"),
            signal_password=args.signal_password
            if args.signal_password
            else creds.get("signal", {}).get("password"),
            telegram_token=args.telegram_token
            if args.telegram_token
            else creds.get("telegram", {}).get("token"),
            telegram_userid=args.telegram_userid
            if args.telegram_userid
            else creds.get("telegram", {}).get("userid"),
            kakao_auth_token=args.kakao_auth_token
            if args.kakao_auth_token
            else creds.get("kakao", {}).get("auth_token"),
            kakao_username=args.kakao_username
            if args.kakao_username
            else creds.get("kakao", {}).get("username"),
            kakao_password=args.kakao_password
            if args.kakao_password
            else creds.get("kakao", {}).get("password"),
            kakao_country_code=args.kakao_country_code
            if args.kakao_country_code
            else creds.get("kakao", {}).get("country_code"),
            kakao_phone_number=args.kakao_phone_number
            if args.kakao_phone_number
            else creds.get("kakao", {}).get("phone_number"),
            line_cookies=args.line_cookies
            if args.line_cookies
            else creds.get("line", {}).get("cookies"),
        )

        if args.kakao_get_auth:
            m = GetKakaoAuth(
                opt_cred=opt_cred,
                cb_msg=self.cb.msg,
                cb_msg_block=self.cb.msg_block,
                cb_ask_str=self.cb.ask_str,
            )
            auth_token = m.get_cred()

            if auth_token:
                opt_cred.kakao_auth_token = auth_token

                self.cb.msg(f"Got auth_token successfully: {auth_token}")

        if args.signal_get_auth:
            m = GetSignalAuth(cb_msg=self.cb.msg, cb_ask_str=self.cb.ask_str)

            uuid, password = None, None
            while True:
                uuid, password = m.get_cred()

                if uuid and password:
                    opt_cred.signal_uuid = uuid
                    opt_cred.signal_password = password

                    self.cb.msg(
                        f"Got uuid and password successfully: {uuid}, {password}"
                    )
                    break

        if args.line_get_auth:
            m = GetLineAuth()

            line_cookies = m.get_cred()

            if line_cookies:
                opt_cred.line_cookies = line_cookies

                self.cb.msg("Got Line cookies successfully")
            else:
                self.cb.msg(
                    "Failed to get Line cookies. Have you logged in the web browser?"
                )

        if args.save_cred:
            creds_path = CONFIG_DIR / "creds.json"
            JsonManager.save_json(creds_path, opt_cred.to_dict())
            self.cb.msg("Saved credentials to creds.json")

        return opt_cred
