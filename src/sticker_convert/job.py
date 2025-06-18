#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import traceback
from datetime import datetime
from multiprocessing import Manager, Process, Value
from pathlib import Path
from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from sticker_convert.converter import StickerConvert
from sticker_convert.downloaders.download_band import DownloadBand
from sticker_convert.downloaders.download_discord import DownloadDiscord
from sticker_convert.downloaders.download_kakao import DownloadKakao
from sticker_convert.downloaders.download_line import DownloadLine
from sticker_convert.downloaders.download_ogq import DownloadOgq
from sticker_convert.downloaders.download_signal import DownloadSignal
from sticker_convert.downloaders.download_telegram import DownloadTelegram
from sticker_convert.downloaders.download_viber import DownloadViber
from sticker_convert.job_option import CompOption, CredOption, InputOption, OutputOption
from sticker_convert.uploaders.compress_wastickers import CompressWastickers
from sticker_convert.uploaders.upload_signal import UploadSignal
from sticker_convert.uploaders.upload_telegram import UploadTelegram
from sticker_convert.uploaders.upload_viber import UploadViber
from sticker_convert.uploaders.xcode_imessage import XcodeImessage
from sticker_convert.utils.callback import CallbackReturn, CbQueueType, ResultsListType, WorkQueueType
from sticker_convert.utils.files.json_resources_loader import OUTPUT_JSON
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.media.codec_info import CodecInfo
from sticker_convert.utils.singletons import singletons


class Executor:
    def __init__(
        self,
        cb_msg: Callable[..., None],
        cb_msg_block: Callable[..., None],
        cb_bar: Callable[..., None],
        cb_ask_bool: Callable[..., bool],
        cb_ask_str: Callable[..., str],
    ) -> None:
        self.cb_msg = cb_msg
        self.cb_msg_block = cb_msg_block
        self.cb_bar = cb_bar
        self.cb_ask_bool = cb_ask_bool
        self.cb_ask_str = cb_ask_str

        self.manager = Manager()
        self.work_queue: WorkQueueType = self.manager.Queue()
        self.cb_queue: CbQueueType = self.manager.Queue()
        self.results_list: ResultsListType = self.manager.list()
        self.cb_return = CallbackReturn(self.manager)
        self.processes: List[Process] = []

        self.is_cancel_job = Value("i", 0)

        self.cb_thread_instance: Optional[Thread] = None

    def cb_thread(
        self,
        cb_queue: CbQueueType,
        processes: int,
    ) -> None:
        processes_done = 0
        for i in iter(cb_queue.get, None):
            if i == "__PROCESS_DONE__":
                processes_done += 1
                if processes_done == processes:
                    cb_queue.put(None)
                continue
            if isinstance(i, tuple):
                action = i[0]
                if len(i) >= 2:
                    args: Tuple[str, ...] = i[1] if i[1] else tuple()
                else:
                    args = tuple()
                if len(i) >= 3:
                    kwargs: Dict[str, str] = i[2] if i[2] else {}
                else:
                    kwargs = {}
            else:
                action = i
                args = tuple()
                kwargs = {}
            self.cb(action, args, kwargs)

    def cb(
        self,
        action: Optional[str],
        args: Optional[Tuple[str, ...]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = {}
        if action == "msg":
            self.cb_msg(*args, **kwargs)
        elif action == "bar":
            self.cb_bar(*args, **kwargs)
        elif action == "update_bar":
            self.cb_bar(update_bar=1)
        elif action == "msg_block":
            self.cb_return.set_response(self.cb_msg_block(*args, **kwargs))
        elif action == "ask_bool":
            self.cb_return.set_response(self.cb_ask_bool(*args, **kwargs))
        elif action == "ask_str":
            self.cb_return.set_response(self.cb_ask_str(*args, **kwargs))
        else:
            self.cb_msg(action)

    @staticmethod
    def worker(
        work_queue: WorkQueueType,
        results_list: ResultsListType,
        cb_queue: CbQueueType,
        cb_return: CallbackReturn,
    ) -> None:
        for work_func, work_args in iter(work_queue.get, None):
            try:
                results = work_func(*work_args, cb_queue, cb_return)
                results_list.append(results)
            except Exception:
                arg_dump: List[Any] = []
                for i in work_args:
                    if isinstance(i, CredOption):
                        arg_dump.append("CredOption(REDACTED)")
                    else:
                        arg_dump.append(i)
                e = "##### EXCEPTION #####\n"
                e += "Function: " + repr(work_func) + "\n"
                e += "Arguments: " + repr(arg_dump) + "\n"
                e += traceback.format_exc()
                e += "#####################"
                cb_queue.put(e)

        work_queue.put(None)
        cb_queue.put("__PROCESS_DONE__")
        singletons.close()

    def start_workers(self, processes: int = 1) -> None:
        self.cb_thread_instance = Thread(
            target=self.cb_thread,
            args=(self.cb_queue, processes),
        )
        self.cb_thread_instance.start()

        self.results_list[:] = []
        while not self.work_queue.empty():
            self.work_queue.get()
        for _ in range(processes):
            process = Process(
                target=Executor.worker,
                args=(
                    self.work_queue,
                    self.results_list,
                    self.cb_queue,
                    self.cb_return,
                ),
                daemon=True,
            )

            process.start()
            self.processes.append(process)

    def add_work(
        self, work_func: Callable[..., Any], work_args: Tuple[Any, ...]
    ) -> None:
        self.work_queue.put((work_func, work_args))

    def join_workers(self) -> None:
        self.work_queue.put(None)
        try:
            for process in self.processes:
                process.join()
                if process.exitcode != 0 and self.is_cancel_job.value == 0:
                    self.cb_msg(
                        f"Warning: A process exited with error (code {process.exitcode})"
                    )
        except KeyboardInterrupt:
            pass

        self.processes.clear()

    def kill_workers(self, *_: Any, **__: Any) -> None:
        self.is_cancel_job.value = 1  # type: ignore

        for process in self.processes:
            process.terminate()

        self.cb_msg("Job cancelled.")
        self.cleanup()

    def cleanup(self) -> None:
        self.cb_bar("clear")
        self.cb_queue.put(None)
        if self.cb_thread_instance:
            self.cb_thread_instance.join()


class Job:
    def __init__(
        self,
        opt_input: InputOption,
        opt_comp: CompOption,
        opt_output: OutputOption,
        opt_cred: CredOption,
        cb_msg: Callable[..., None],
        cb_msg_block: Callable[..., None],
        cb_bar: Callable[..., None],
        cb_ask_bool: Callable[..., bool],
        cb_ask_str: Callable[..., str],
    ) -> None:
        self.opt_input = opt_input
        self.opt_comp = opt_comp
        self.opt_output = opt_output
        self.opt_cred = opt_cred
        self.cb_msg = cb_msg
        self.cb_msg_block = cb_msg_block
        self.cb_bar = cb_bar
        self.cb_ask_bool = cb_ask_bool
        self.cb_ask_str = cb_ask_str

        self.out_urls: List[str] = []

        self.executor = Executor(
            self.cb_msg,
            self.cb_msg_block,
            self.cb_bar,
            self.cb_ask_bool,
            self.cb_ask_str,
        )

    def start(self) -> int:
        if Path(self.opt_input.dir).is_dir() is False:
            os.makedirs(self.opt_input.dir)

        if Path(self.opt_output.dir).is_dir() is False:
            os.makedirs(self.opt_output.dir)

        self.executor.cb("msg", kwargs={"cls": True})

        tasks: Tuple[Callable[..., Tuple[bool, Optional[str]]], ...] = (
            self.verify_input,
            self.cleanup,
            self.download,
            self.compress,
            self.export,
        )

        code = 0
        summaries: List[str] = []
        for task in tasks:
            self.executor.cb("bar", kwargs={"set_progress_mode": "indeterminate"})
            success, summary = task()
            if summary is not None:
                summaries.append(summary)

            if self.executor.is_cancel_job.value == 1:  # type: ignore
                code = 2
                break
            if not success:
                code = 1
                self.executor.cb("An error occured during this run.")
                break

        msg = "##########\n"
        msg += "Summary:\n"
        msg += "##########\n"

        msg += "\n"
        msg += "\n".join(summaries)
        msg += "\n"

        if self.out_urls:
            msg += "Export results:\n"
            msg += "\n".join(self.out_urls)
        else:
            msg += "Export result: None"

        self.executor.cb(msg)

        self.executor.cleanup()

        return code

    def cancel(self, *_: Any, **_kwargs: Any) -> None:
        self.executor.kill_workers()

    def verify_input(self) -> Tuple[bool, None]:
        info_msg = ""
        error_msg = ""

        save_to_local_tip = ""
        save_to_local_tip += "    If you want to upload the results by yourself,\n"
        save_to_local_tip += '    select "Save to local directory only" for output\n'

        if Path(self.opt_input.dir).resolve() == Path(self.opt_output.dir).resolve():
            error_msg += "\n"
            error_msg += "[X] Input and output directories cannot be the same\n"

        if self.opt_input.option == "auto":
            error_msg += "\n"
            error_msg += "[X] Unrecognized URL input source\n"

        if self.opt_input.option != "local" and not self.opt_input.url:
            error_msg += "\n"
            error_msg += "[X] URL address cannot be empty.\n"
            error_msg += "    If you only want to use local files,\n"
            error_msg += '    choose "Save to local directory only"\n'
            error_msg += '    in "Input source"\n'

        if (
            self.opt_input.option == "telegram" or self.opt_output.option == "telegram"
        ) and not self.opt_cred.telegram_token:
            error_msg += (
                "[X] Downloading from and uploading to telegram requires bot token.\n"
            )
            error_msg += save_to_local_tip

        if (
            self.opt_input.option.startswith("discord")
            and not self.opt_cred.discord_token
        ):
            error_msg += "[X] Downloading from Discord requires token.\n"

        if self.opt_output.option == "telegram" and not self.opt_cred.telegram_userid:
            error_msg += "[X] Uploading to telegram requires user_id \n"
            error_msg += "    (From real account, not bot account).\n"
            error_msg += save_to_local_tip

        if self.opt_output.option == "signal" and not (
            self.opt_cred.signal_uuid and self.opt_cred.signal_password
        ):
            error_msg += "[X] Uploading to signal requires uuid and password.\n"
            error_msg += save_to_local_tip

        if self.opt_output.option == "viber" and not self.opt_cred.viber_auth:
            error_msg += "[X] Uploading to Viber requires auth data.\n"
            error_msg += save_to_local_tip

        output_presets = OUTPUT_JSON

        input_option = self.opt_input.option
        output_option = self.opt_output.option

        for metadata in ("title", "author"):
            if MetadataHandler.check_metadata_required(
                output_option, metadata
            ) and not getattr(self.opt_output, metadata):
                if not MetadataHandler.check_metadata_provided(
                    self.opt_input.dir, input_option, metadata
                ):
                    error_msg += f"[X] {output_presets[output_option]['full_name']} requires {metadata}\n"
                    if self.opt_input.option == "local":
                        error_msg += f"    {metadata} was not supplied and {metadata}.txt is absent\n"
                    else:
                        error_msg += f"    {metadata} was not supplied and input source will not provide {metadata}\n"
                    error_msg += (
                        f"    Supply the {metadata} by filling in the option, or\n"
                    )
                    error_msg += f"    Create {metadata}.txt with the {metadata} name\n"
                else:
                    info_msg += f"[!] {output_presets[output_option]['full_name']} requires {metadata}\n"
                    if self.opt_input.option == "local":
                        info_msg += f"    {metadata} was not supplied but {metadata}.txt is present\n"
                        info_msg += f"    Using {metadata} name in {metadata}.txt\n"
                    else:
                        info_msg += f"    {metadata} was not supplied but input source will provide {metadata}\n"
                        info_msg += f"    Using {metadata} provided by input source\n"

        if info_msg != "":
            self.executor.cb(info_msg)

        if error_msg != "":
            self.executor.cb(error_msg)
            return False, None

        # Check if preset not equal to export option
        # Only warn if the compression option is available in export preset
        # Only warn if export option is not local or custom
        # Do not warn if no_compress is true
        if (
            not self.opt_comp.no_compress
            and self.opt_output.option != "local"
            and self.opt_comp.preset != "custom"
            and (
                self.opt_output.option not in self.opt_comp.preset
                and self.opt_comp.preset not in self.opt_output.option
            )
        ):
            msg = "Compression preset does not match export option\n"
            msg += "You may continue, but the files will need to be compressed again before export\n"
            msg += "You are recommended to choose the matching option for compression and output. Continue?"

            self.executor.cb("ask_bool", (msg,))
            response = self.executor.cb_return.get_response()

            if response is False:
                return False, None

        for param, value in (
            ("fps_power", self.opt_comp.fps_power),
            ("res_power", self.opt_comp.res_power),
            ("quality_power", self.opt_comp.quality_power),
            ("color_power", self.opt_comp.color_power),
        ):
            if value < -1:
                error_msg += "\n"
                error_msg += f"[X] {param} should be between -1 and positive infinity. {value} was given."

        if self.opt_comp.scale_filter not in (
            "nearest",
            "box",
            "bilinear",
            "hamming",
            "bicubic",
            "lanczos",
        ):
            error_msg += "\n"
            error_msg += (
                f"[X] scale_filter {self.opt_comp.scale_filter} is not valid option"
            )
            error_msg += (
                "    Valid options: nearest, box, bilinear, hamming, bicubic, lanczos"
            )

        if self.opt_comp.quantize_method not in ("imagequant", "fastoctree", "none"):
            error_msg += "\n"
            error_msg += f"[X] quantize_method {self.opt_comp.quantize_method} is not valid option"
            error_msg += "    Valid options: imagequant, fastoctree, none"

        if self.opt_comp.bg_color:
            try:
                _, _, _ = bytes.fromhex(self.opt_comp.bg_color)
            except ValueError:
                error_msg += "\n"
                error_msg += (
                    f"[X] bg_color {self.opt_comp.bg_color} is not valid color hex"
                )

        # Warn about unable to download animated Kakao stickers with such link
        if (
            self.opt_output.option == "kakao"
            and urlparse(self.opt_input.url).netloc == "e.kakao.com"
            and not self.opt_cred.kakao_auth_token
        ):
            msg = "To download ANIMATED stickers from e.kakao.com,\n"
            msg += "you need to generate auth_token.\n"
            msg += "Alternatively, you can generate share link (emoticon.kakao.com/items/xxxxx)\n"
            msg += "from Kakao app on phone.\n"
            msg += "You are adviced to read documentations.\n"
            msg += "If you continue, you will only download static stickers. Continue?"

            self.executor.cb("ask_bool", (msg,))
            response = self.executor.cb_return.get_response()

            if response is False:
                return False, None

        # Warn about in/output directories that might contain other files
        # Directory is safe if the name is stickers_input/stickers_output, or
        # all contents are related to sticker-convert
        for path_type, path, default_name in (
            ("Input", self.opt_input.dir, "stickers_input"),
            ("Output", self.opt_output.dir, "stickers_output"),
        ):
            if path_type == "Input" and (
                path.name == "stickers_input"
                or self.opt_input.option == "local"
                or not any(path.iterdir())
            ):
                continue
            if path_type == "Output" and (
                path.name == "stickers_output"
                or self.opt_comp.no_compress
                or not any(path.iterdir())
            ):
                continue

            related_files = MetadataHandler.get_files_related_to_sticker_convert(path)
            if any(i for i in path.iterdir() if i not in related_files):
                msg = "WARNING: {} directory is set to {}.\n"
                msg += 'It does not have default name of "{}",\n'
                msg += "and It seems like it contains PERSONAL DATA.\n"
                msg += "During execution, contents of this directory\n"
                msg += 'maybe MOVED to "archive_*".\n'
                msg += "THIS MAY CAUSE DAMAGE TO YOUR DATA. Continue?"

                self.executor.cb(
                    "ask_bool", (msg.format(path_type, path, default_name),)
                )
                response = self.executor.cb_return.get_response()

                if response is False:
                    return False, None

                break

        return True, None

    def cleanup(self) -> Tuple[bool, None]:
        # If input is 'From local directory', then we should keep files in input/output directory as it maybe edited by user
        # If input is not 'From local directory', then we should move files in input/output directory as new files will be downloaded
        # Output directory should be cleanup unless no_compress is true (meaning files in output directory might be edited by user)

        timestamp = datetime.now().strftime("%Y-%d-%m_%H-%M-%S")
        dir_name = "archive_" + timestamp

        in_dir_files = MetadataHandler.get_files_related_to_sticker_convert(
            self.opt_input.dir, include_archive=False
        )
        out_dir_files = MetadataHandler.get_files_related_to_sticker_convert(
            self.opt_output.dir, include_archive=False
        )

        if self.opt_input.option == "local":
            self.executor.cb(
                "Skip moving old files in input directory as input source is local"
            )
        elif len(in_dir_files) == 0:
            self.executor.cb(
                "Skip moving old files in input directory as input source is empty"
            )
        else:
            archive_dir = Path(self.opt_input.dir, dir_name)
            self.executor.cb(
                f"Moving old files in input directory to {archive_dir} as input source is not local"
            )
            archive_dir.mkdir(exist_ok=True)
            for old_path in in_dir_files:
                new_path = Path(archive_dir, old_path.name)
                old_path.rename(new_path)

        if self.opt_comp.no_compress:
            self.executor.cb(
                "Skip moving old files in output directory as no_compress is True"
            )
        elif len(out_dir_files) == 0:
            self.executor.cb(
                "Skip moving old files in output directory as output source is empty"
            )
        else:
            archive_dir = Path(self.opt_output.dir, dir_name)
            self.executor.cb(f"Moving old files in output directory to {archive_dir}")
            os.makedirs(archive_dir)
            for old_path in out_dir_files:
                new_path = Path(archive_dir, old_path.name)
                old_path.rename(new_path)

        return True, None

    def download(self) -> Tuple[bool, str]:
        downloaders: List[Callable[..., Tuple[int, int]]] = []

        if self.opt_input.option == "signal":
            downloaders.append(DownloadSignal.start)

        if self.opt_input.option == "line":
            downloaders.append(DownloadLine.start)

        if self.opt_input.option.startswith("telegram"):
            downloaders.append(DownloadTelegram.start)

        if self.opt_input.option == "kakao":
            downloaders.append(DownloadKakao.start)

        if self.opt_input.option == "band":
            downloaders.append(DownloadBand.start)

        if self.opt_input.option == "ogq":
            downloaders.append(DownloadOgq.start)

        if self.opt_input.option == "viber":
            downloaders.append(DownloadViber.start)

        if self.opt_input.option.startswith("discord"):
            downloaders.append(DownloadDiscord.start)

        if len(downloaders) > 0:
            self.executor.cb("Downloading...")
        else:
            self.executor.cb("Skipped download (No files to download)")
            return True, "Download: Skipped (No files to download)"

        self.executor.start_workers(processes=1)

        for downloader in downloaders:
            self.executor.add_work(
                work_func=downloader,
                work_args=(self.opt_input, self.opt_cred),
            )

        self.executor.join_workers()

        # Return False if any of the job returns failure
        stickers_ok = 0
        stickers_total = 0
        success = True
        for result in self.executor.results_list:
            stickers_ok += result[0]
            stickers_total += result[1]
            success = (
                success if stickers_ok == stickers_total and stickers_ok > 0 else False
            )

        return (
            success,
            f"Download: {stickers_ok}/{stickers_total} stickers success",
        )

    def compress(self) -> Tuple[bool, str]:
        if self.opt_comp.no_compress is True:
            self.executor.cb("Skipped compression (no_compress is set to True)")
            in_dir_files = [
                i
                for i in sorted(self.opt_input.dir.iterdir())
                if Path(self.opt_input.dir, i.name).is_file()
            ]
            out_dir_files = [
                i
                for i in sorted(self.opt_output.dir.iterdir())
                if Path(self.opt_output.dir, i.name).is_file()
            ]
            if len(in_dir_files) == 0:
                self.executor.cb(
                    "Input directory is empty, nothing to copy to output directory"
                )
            elif len(out_dir_files) != 0:
                self.executor.cb(
                    "Output directory is not empty, not copying files from input directory"
                )
            else:
                self.executor.cb(
                    "Output directory is empty, copying files from input directory"
                )
                for i in in_dir_files:
                    src_f = Path(self.opt_input.dir, i.name)
                    dst_f = Path(self.opt_output.dir, i.name)
                    shutil.copy(src_f, dst_f)
            return True, "Compress: Skipped (no_compress is set to True)"
        msg = "Compressing..."

        input_dir = Path(self.opt_input.dir)
        output_dir = Path(self.opt_output.dir)

        in_fs: List[Path] = []

        # .txt: emoji.txt, title.txt
        # .m4a: line sticker sound effects
        for i in sorted(input_dir.iterdir()):
            in_f = input_dir / i

            if not in_f.is_file():
                continue
            if (
                CodecInfo.get_file_ext(i) in (".txt", ".m4a")
                or (
                    self.opt_comp.preset != "signal" and Path(i).stem == "cover"
                )  # Signal cover has same spec as normal sticker
            ):
                shutil.copy(in_f, output_dir / i.name)
            else:
                in_fs.append(i)

        in_fs_count = len(in_fs)
        if in_fs_count == 0:
            self.executor.cb("Skipped compression (No files to compress)")
            return True, "Compress: Skipped (No files to compress)"

        self.executor.cb(msg)
        self.executor.cb(
            "bar", kwargs={"set_progress_mode": "determinate", "steps": in_fs_count}
        )

        self.executor.start_workers(processes=min(self.opt_comp.processes, in_fs_count))

        for i in in_fs:
            in_f = input_dir / i.name
            out_f = output_dir / Path(i).stem

            self.executor.add_work(
                work_func=StickerConvert.convert, work_args=(in_f, out_f, self.opt_comp)
            )

        self.executor.join_workers()

        success = True
        stickers_ok = 0
        stickers_total = 0
        fails: List[str] = []
        for result in self.executor.results_list:
            stickers_total += 1
            if result[0] is False:
                success = False
                fails.append(str(result[1]))
            else:
                stickers_ok += 1

        msg_append = ""
        if success is False:
            msg_append = " (Failed: " + ", ".join(fails) + ")"

        return (
            success,
            f"Compress: {stickers_ok}/{stickers_total} stickers success" + msg_append,
        )

    def export(self) -> Tuple[bool, str]:
        if self.opt_output.option == "local":
            self.executor.cb("Skipped export (Saving to local directory only)")
            return True, "Export: Skipped (Saving to local directory only)"

        self.executor.cb("Exporting...")

        exporters: List[Callable[..., Tuple[int, int, List[str]]]] = []

        if self.opt_output.option == "whatsapp":
            exporters.append(CompressWastickers.start)

        if self.opt_output.option == "signal":
            exporters.append(UploadSignal.start)

        if self.opt_output.option.startswith("telegram"):
            exporters.append(UploadTelegram.start)

        if self.opt_output.option == "imessage":
            exporters.append(XcodeImessage.start)

        if self.opt_output.option == "viber":
            exporters.append(UploadViber.start)

        self.executor.start_workers(processes=1)

        for exporter in exporters:
            self.executor.add_work(
                work_func=exporter,
                work_args=(self.opt_output, self.opt_comp, self.opt_cred),
            )

        self.executor.join_workers()

        stickers_ok = 0
        stickers_total = 0
        for result in self.executor.results_list:
            stickers_ok += result[0]
            stickers_total += result[1]
            self.out_urls.extend(result[2])

        if self.out_urls:
            with open(
                Path(self.opt_output.dir, "export-result.txt"), "w+", encoding="utf-8"
            ) as f:
                f.write("\n".join(self.out_urls))
        else:
            self.executor.cb("An error occured while exporting stickers")
            return False, f"Export: {stickers_ok}/{stickers_total} stickers success"

        return True, f"Export: {stickers_ok}/{stickers_total} stickers success"
