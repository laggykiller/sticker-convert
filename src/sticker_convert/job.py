#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
from datetime import datetime
from multiprocessing import Process, Queue, Value
from multiprocessing.queues import Queue as QueueType
from threading import Thread
from urllib.parse import urlparse
from typing import Optional

from .job_option import InputOption, CompOption, OutputOption, CredOption  # type: ignore

from .downloaders.download_line import DownloadLine # type: ignore
from .downloaders.download_signal import DownloadSignal # type: ignore
from .downloaders.download_telegram import DownloadTelegram # type: ignore
from .downloaders.download_kakao import DownloadKakao # type: ignore

from .uploaders.upload_base import UploadBase
from .uploaders.upload_signal import UploadSignal # type: ignore
from .uploaders.upload_telegram import UploadTelegram # type: ignore
from .uploaders.compress_wastickers import CompressWastickers # type: ignore
from .uploaders.xcode_imessage import XcodeImessage # type: ignore

from .converter import StickerConvert # type: ignore
from .utils.media.codec_info import CodecInfo # type: ignore
from .utils.files.json_manager import JsonManager # type: ignore
from .utils.files.metadata_handler import MetadataHandler # type: ignore

class Job:
    def __init__(self,
        opt_input: InputOption, opt_comp: CompOption,
        opt_output: OutputOption, opt_cred: CredOption, 
        cb_msg, cb_msg_block, cb_bar, cb_ask_bool):

        self.opt_input = opt_input
        self.opt_comp = opt_comp
        self.opt_output = opt_output
        self.opt_cred = opt_cred
        self.cb_msg = cb_msg
        self.cb_msg_block = cb_msg_block
        self.cb_bar = cb_bar
        self.cb_ask_bool = cb_ask_bool

        self.compress_fails: list[str] = []
        self.out_urls: list[str] = []

        self.jobs_queue: QueueType[Optional[tuple[str, str, CompOption]]] = Queue()
        self.results_queue: QueueType[Optional[tuple[bool, str, str, int]]] = Queue()
        self.cb_msg_queue: QueueType[Optional[str]] = Queue()
        self.processes: list[Process] = []

        self.is_cancel_job = Value('i', 0)

        if os.path.isdir(self.opt_input.dir) == False:
            os.makedirs(self.opt_input.dir)

        if os.path.isdir(self.opt_output.dir) == False:
            os.makedirs(self.opt_output.dir)

    def start(self) -> bool:
        self.cb_bar(set_progress_mode='indeterminate')
        self.cb_msg(cls=True)

        tasks = (
            self.verify_input,
            self.cleanup,
            self.download,
            self.compress,
            self.export,
            self.report
        )

        for task in tasks:
            success = task()
            if self.is_cancel_job.value == 1:
                return 2
            if not success:
                return 1

        return 0

    def verify_input(self) -> bool:
        info_msg = ''
        error_msg = ''

        save_to_local_tip = ''
        save_to_local_tip += '    If you want to upload the results by yourself,\n'
        save_to_local_tip += '    select "Save to local directory only" for output\n'

        if self.opt_input.option == 'auto':
            error_msg += '\n'
            error_msg += '[X] Unrecognized URL input source\n'

        if (self.opt_input.option != 'local' and 
            not self.opt_input.url):

            error_msg += '\n'
            error_msg += '[X] URL address cannot be empty.\n'
            error_msg += '    If you only want to use local files,\n'
            error_msg += '    choose "Save to local directory only"\n'
            error_msg += '    in "Input source"\n'
        

        if ((self.opt_input.option == 'telegram' or 
            self.opt_output.option == 'telegram') and 
            not self.opt_cred.telegram_token):

            error_msg += '[X] Downloading from and uploading to telegram requires bot token.\n'
            error_msg += save_to_local_tip

        if (self.opt_output.option == 'telegram' and 
            not self.opt_cred.telegram_userid):

            error_msg += '[X] Uploading to telegram requires user_id \n'
            error_msg += '    (From real account, not bot account).\n'
            error_msg += save_to_local_tip
        

        if (self.opt_output.option == 'signal' and 
            not (self.opt_cred.signal_uuid and self.opt_cred.signal_password)):

            error_msg += '[X] Uploading to signal requires uuid and password.\n'
            error_msg += save_to_local_tip
        
        output_presets = JsonManager.load_json('resources/output.json')

        input_option = self.opt_input.option
        output_option = self.opt_output.option
        
        for metadata in ('title', 'author'):
            if MetadataHandler.check_metadata_required(output_option, metadata) and not getattr(self.opt_output, metadata):
                if not MetadataHandler.check_metadata_provided(self.opt_input.dir, input_option, metadata):
                    error_msg += f'[X] {output_presets[output_option]["full_name"]} requires {metadata}\n'
                    if self.opt_input.option == 'local':
                        error_msg += f'    {metadata} was not supplied and {metadata}.txt is absent\n'
                    else:
                        error_msg += f'    {metadata} was not supplied and input source will not provide {metadata}\n'
                    error_msg += f'    Supply the {metadata} by filling in the option, or\n'
                    error_msg += f'    Create {metadata}.txt with the {metadata} name\n'
                else:
                    info_msg += f'[!] {output_presets[output_option]["full_name"]} requires {metadata}\n'
                    if self.opt_input.option == 'local':
                        info_msg += f'    {metadata} was not supplied but {metadata}.txt is present\n'
                        info_msg += f'    Using {metadata} name in {metadata}.txt\n'
                    else:
                        info_msg += f'    {metadata} was not supplied but input source will provide {metadata}\n'
                        info_msg += f'    Using {metadata} provided by input source\n'
        
        if info_msg != '':
            self.cb_msg(info_msg)

        if error_msg != '':
            self.cb_msg(error_msg)
            return False
        
        # Check if preset not equal to export option
        # Only warn if the compression option is available in export preset
        # Only warn if export option is not local or custom
        # Do not warn if no_compress is true
        if (not self.opt_comp.no_compress and 
            self.opt_output.option != 'local' and
            self.opt_comp.preset != 'custom' and
            self.opt_output.option not in self.opt_comp.preset):

            msg = 'Compression preset does not match export option\n'
            msg += 'You may continue, but the files will need to be compressed again before export\n'
            msg += 'You are recommended to choose the matching option for compression and output. Continue?'

            response = self.cb_ask_bool(msg)

            if response == False:
                return False
        
        # Warn about unable to download animated Kakao stickers with such link
        if (self.opt_output.option == 'kakao' and 
            urlparse(self.opt_input.url).netloc == 'e.kakao.com' and
            not self.opt_cred.kakao_auth_token):

            msg = 'To download ANIMATED stickers from e.kakao.com,\n'
            msg += 'you need to generate auth_token.\n'
            msg += 'Alternatively, you can generate share link (emoticon.kakao.com/items/xxxxx)\n'
            msg += 'from Kakao app on phone.\n'
            msg += 'You are adviced to read documentations.\n'
            msg += 'If you continue, you will only download static stickers. Continue?'

            response = self.cb_ask_bool(msg)

            if response == False:
                return False
            
            response = self.cb_ask_bool(msg)

            if response == False:
                return False
        
        return True

    def cleanup(self) -> bool:
        # If input is 'From local directory', then we should keep files in input/output directory as it maybe edited by user
        # If input is not 'From local directory', then we should move files in input/output directory as new files will be downloaded
        # Output directory should be cleanup unless no_compress is true (meaning files in output directory might be edited by user)

        timestamp = datetime.now().strftime('%Y-%d-%m_%H-%M-%S')
        dir_name = 'archive_' + timestamp

        in_dir_files = [i for i in os.listdir(self.opt_input.dir) if not i.startswith('archive_')]
        out_dir_files = [i for i in os.listdir(self.opt_output.dir) if not i.startswith('archive_')]

        if self.opt_input.option == 'local':
            self.cb_msg('Skip moving old files in input directory as input source is local')
        elif len(in_dir_files) == 0:
            self.cb_msg('Skip moving old files in input directory as input source is empty')
        else:
            archive_dir = os.path.join(self.opt_input.dir, dir_name)
            self.cb_msg(f"Moving old files in input directory to {archive_dir} as input source is not local")
            os.makedirs(archive_dir)
            for i in in_dir_files:
                old_path = os.path.join(self.opt_input.dir, i)
                new_path = os.path.join(archive_dir, i)
                shutil.move(old_path, new_path)

        if self.opt_comp.no_compress:
            self.cb_msg('Skip moving old files in output directory as no_compress is True')
        elif len(out_dir_files) == 0:
            self.cb_msg('Skip moving old files in output directory as output source is empty')
        else:
            archive_dir = os.path.join(self.opt_output.dir, dir_name)
            self.cb_msg(f"Moving old files in output directory to {archive_dir}")
            os.makedirs(archive_dir)
            for i in out_dir_files:
                old_path = os.path.join(self.opt_output.dir, i)
                new_path = os.path.join(archive_dir, i)
                shutil.move(old_path, new_path)
        
        return True

    def download(self) -> bool:
        downloaders = []

        if self.opt_input.option == 'signal':
            downloaders.append(DownloadSignal.start)

        if self.opt_input.option == 'line':
            downloaders.append(DownloadLine.start)
            
        if self.opt_input.option == 'telegram':
            downloaders.append(DownloadTelegram.start)

        if self.opt_input.option == 'kakao':
            downloaders.append(DownloadKakao.start)
        
        if len(downloaders) > 0:
            self.cb_msg('Downloading...')
        else:
            self.cb_msg('Nothing to download')
            return True
        
        for downloader in downloaders:
            success = downloader(
                url=self.opt_input.url, 
                out_dir=self.opt_input.dir, 
                opt_cred=self.opt_cred,
                cb_msg=self.cb_msg, cb_msg_block=self.cb_msg_block, cb_bar=self.cb_bar)
            self.cb_bar(set_progress_mode='indeterminate')
            if success == False:
                return False

        return True

    def compress(self) -> bool:
        if self.opt_comp.no_compress == True:
            self.cb_msg('no_compress is set to True, skip compression')
            in_dir_files = [i for i in sorted(os.listdir(self.opt_input.dir)) if os.path.isfile(os.path.join(self.opt_input.dir, i))]
            out_dir_files = [i for i in sorted(os.listdir(self.opt_output.dir)) if os.path.isfile(os.path.join(self.opt_output.dir, i))]
            if len(in_dir_files) == 0:
                self.cb_msg('Input directory is empty, nothing to copy to output directory')
            elif len(out_dir_files) != 0:
                self.cb_msg('Output directory is not empty, not copying files from input directory')
            else:
                self.cb_msg('Output directory is empty, copying files from input directory')
                for i in in_dir_files:
                    src_f = os.path.join(self.opt_input.dir, i)
                    dst_f = os.path.join(self.opt_output.dir, i)
                    shutil.copy(src_f, dst_f)
            return True
        msg = 'Compressing...'

        input_dir = self.opt_input.dir
        output_dir = self.opt_output.dir
        
        in_fs = []

        # .txt: emoji.txt, title.txt
        # .m4a: line sticker sound effects
        for i in sorted(os.listdir(input_dir)):
            in_f = os.path.join(input_dir, i)
            
            if not os.path.isfile(in_f):
                continue
            elif (CodecInfo.get_file_ext(i) in ('.txt', '.m4a') or
                  os.path.splitext(i)[0] == 'cover'):
                
                shutil.copy(in_f, os.path.join(output_dir, i))
            else:
                in_fs.append(i)

        in_fs_count = len(in_fs)

        self.cb_msg(msg)
        self.cb_bar(set_progress_mode='determinate', steps=in_fs_count)

        Thread(target=self.cb_msg_thread, args=(self.cb_msg_queue,)).start()
        Thread(target=self.processes_watcher_thread, args=(self.results_queue,)).start()

        for i in range(min(self.opt_comp.processes, in_fs_count)):
            process = Process(
                target=Job.compress_worker,
                args=(self.jobs_queue, self.results_queue, self.cb_msg_queue),
                daemon=True
            )

            process.start()
            self.processes.append(process)

        for i in in_fs:
            in_f = os.path.join(input_dir, i)

            if CodecInfo.is_anim(in_f) or self.opt_comp.fake_vid:
                extension = self.opt_comp.format_vid
            else:
                extension = self.opt_comp.format_img

            out_f = os.path.join(output_dir, os.path.splitext(i)[0] + extension)

            self.jobs_queue.put((in_f, out_f, self.opt_comp))

        self.jobs_queue.put(None)

        for process in self.processes:
            process.join()
        
        self.results_queue.put(None)
        self.cb_msg_queue.put(None)

        return True
    
    def processes_watcher_thread(
            self, 
            results_queue: QueueType[Optional[tuple[bool, str, str, int]]]
            ):
        
        for (success, in_f, out_f, size) in iter(results_queue.get, None): # type: ignore[misc]
            if success == False: # type: ignore
                self.compress_fails.append(in_f) # type: ignore[has-type]

            self.cb_bar(update_bar=True)
    
    def cb_msg_thread(
            self, 
            cb_msg_queue: QueueType[Optional[str]]
            ):
        
        for msg in iter(cb_msg_queue.get, None): # type: ignore
            self.cb_msg(msg)

    @staticmethod
    def compress_worker(
        jobs_queue: QueueType[Optional[tuple[str, str, CompOption]]], 
        results_queue: QueueType[Optional[tuple[bool, str, str, int]]], 
        cb_msg_queue: QueueType[Optional[str]]
        ):

        for (in_f, out_f, opt_comp) in iter(jobs_queue.get, None): # type: ignore[misc]
            sticker = StickerConvert(in_f, out_f, opt_comp, cb_msg_queue) # type: ignore
            success, in_f, out_f, size = sticker.convert()
            del sticker
            results_queue.put((success, in_f, out_f, size))
        
        jobs_queue.put(None)

    def export(self) -> bool:
        self.cb_bar(set_progress_mode='indeterminate')

        if self.opt_output.option == 'local':
            self.cb_msg('Saving to local directory only, nothing to export')
            return True
        
        self.cb_msg('Exporting...')

        exporters: list[UploadBase] = []

        if self.opt_output.option == 'whatsapp':
            exporters.append(CompressWastickers.start)

        if self.opt_output.option == 'signal':
            exporters.append(UploadSignal.start)

        if self.opt_output.option == 'telegram':
            exporters.append(UploadTelegram.start)

        if self.opt_output.option == 'imessage':
            exporters.append(XcodeImessage.start)
        
        for exporter in exporters:
            self.out_urls += exporter(
                opt_output=self.opt_output, opt_comp=self.opt_comp, opt_cred=self.opt_cred, 
                cb_msg=self.cb_msg, cb_msg_block=self.cb_msg_block, cb_ask_bool=self.cb_ask_bool, cb_bar=self.cb_bar)
        
        if self.out_urls:
            with open(os.path.join(self.opt_output.dir, 'export-result.txt'), 'w+') as f:
                f.write('\n'.join(self.out_urls))
        else:
            self.cb_msg('An error occured while exporting stickers')
            return False
                
        return True
    
    def report(self) -> bool:
        msg = '##########\n'
        msg += 'Summary:\n'
        msg += '##########\n'
        msg += '\n'

        if self.compress_fails != []:
            msg += f'Warning: The following {len(self.compress_fails)} file{"s" if len(self.compress_fails) > 1 else ""} compression failed:\n'
            msg += "\n".join(self.compress_fails)
            msg += '\n'

        if self.out_urls != []:
            msg += 'Export results:\n'
            msg += '\n'.join(self.out_urls)
        else:
            msg += 'Export result: None'

        self.cb_msg(msg)

        return True