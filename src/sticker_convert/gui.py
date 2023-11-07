#!/usr/bin/env python3
import os
import sys
import platform
import time
import math
from multiprocessing import cpu_count
from threading import Thread, Lock, current_thread, main_thread
from queue import Queue
from functools import partial
from uuid import uuid4
from urllib.parse import urlparse
from typing import Optional, Any

from PIL import ImageFont
from ttkbootstrap import Window, StringVar, BooleanVar, IntVar # type: ignore
from ttkbootstrap.dialogs import Messagebox, Querybox # type: ignore

from .job import Job # type: ignore
from .job_option import InputOption, CompOption, OutputOption, CredOption  # type: ignore
from .utils.files.json_manager import JsonManager # type: ignore
from .utils.files.dir_utils import DirUtils # type: ignore
from .utils.files.metadata_handler import MetadataHandler # type: ignore
from .utils.url_detect import UrlDetect # type: ignore
from .gui_components.gui_utils import GUIUtils # type: ignore
from .__init__ import __version__ # type: ignore

from .gui_components.frames.input_frame import InputFrame # type: ignore
from .gui_components.frames.comp_frame import CompFrame # type: ignore
from .gui_components.frames.cred_frame import CredFrame # type: ignore
from .gui_components.frames.output_frame import OutputFrame # type: ignore
from .gui_components.frames.config_frame import ConfigFrame # type: ignore
from .gui_components.frames.progress_frame import ProgressFrame # type: ignore
from .gui_components.frames.control_frame import ControlFrame # type: ignore

class GUI(Window):
    def __init__(self):
        super(GUI, self).__init__(themename='darkly', alpha=0)
        self.init_done = False
        self.load_jsons()

        self.emoji_font = ImageFont.truetype("./resources/NotoColorEmoji.ttf", 109)

        GUIUtils.set_icon(self)

        self.title(f'sticker-convert {__version__}')
        self.protocol('WM_DELETE_WINDOW', self.quit)

        (
            self.main_frame,
            self.horizontal_scrollbar_frame,
            self.canvas,
            self.x_scrollbar,
            self.y_scrollbar,
            self.scrollable_frame
        ) = GUIUtils.create_scrollable_frame(self)

        self.declare_variables()
        self.apply_config()
        self.apply_creds()
        self.init_frames()
        self.pack_frames()
        self.warn_tkinter_bug()
        GUIUtils.finalize_window(self)

        self.after(500, self.poll_actions)
    
    def __enter__(self):
        return self

    def gui(self):
        self.init_done = True
        self.highlight_fields()
        self.mainloop()

    def quit(self):
        if self.job:
            response = self.cb_ask_bool('Job is running, really quit?')
            if response == False:
                return

        self.cb_msg(msg='Quitting, please wait...')

        self.save_config()
        if self.settings_save_cred_var.get() == True:
            self.save_creds()
        else:
            self.delete_creds()
        
        if self.job:
            self.cancel_job()
        self.destroy()
            
    def declare_variables(self):
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
        self.res_w_min_var = IntVar(self)
        self.res_w_max_var = IntVar(self)
        self.res_w_disable_var = BooleanVar()
        self.res_h_min_var = IntVar(self)
        self.res_h_max_var = IntVar(self)
        self.res_h_disable_var = BooleanVar()
        self.quality_min_var = IntVar(self)
        self.quality_max_var = IntVar(self)
        self.quality_disable_var = BooleanVar()
        self.color_min_var = IntVar(self)
        self.color_max_var = IntVar(self)
        self.color_disable_var = BooleanVar()
        self.duration_min_var = IntVar(self)
        self.duration_max_var = IntVar(self)
        self.duration_disable_var = BooleanVar()
        self.img_size_max_var = IntVar(self)
        self.vid_size_max_var = IntVar(self)
        self.size_disable_var = BooleanVar()
        self.img_format_var = StringVar(self)
        self.vid_format_var = StringVar(self)
        self.fake_vid_var = BooleanVar()
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
        self.kakao_auth_token_var = StringVar(self)
        self.kakao_username_var = StringVar(self)
        self.kakao_password_var = StringVar(self)
        self.kakao_country_code_var = StringVar(self)
        self.kakao_phone_number_var = StringVar(self)
        self.line_cookies_var = StringVar(self)

        # Config
        self.settings_save_cred_var = BooleanVar()

        # Other
        self.msg_lock = Lock()
        self.bar_lock = Lock()
        self.response_dict_lock = Lock()
        self.response_dict = {}
        self.action_queue = Queue()
        self.job = None

    def init_frames(self):
        self.input_frame = InputFrame(self, self.scrollable_frame, borderwidth=1, text='Input')
        self.comp_frame = CompFrame(self, self.scrollable_frame, borderwidth=1, text='Compression options')
        self.output_frame = OutputFrame(self, self.scrollable_frame, borderwidth=1, text='Output')
        self.cred_frame = CredFrame(self, self.scrollable_frame, borderwidth=1, text='Credentials')
        self.settings_frame = ConfigFrame(self, self.scrollable_frame, borderwidth=1, text='Config')
        self.progress_frame = ProgressFrame(self, self.scrollable_frame, borderwidth=1, text='Progress')
        self.control_frame = ControlFrame(self, self.scrollable_frame, borderwidth=1)
    
    def pack_frames(self):
        self.input_frame.grid(column=0, row=0, sticky='w', padx=5, pady=5)
        self.comp_frame.grid(column=1, row=0, sticky='news', padx=5, pady=5)
        self.output_frame.grid(column=0, row=1, sticky='w', padx=5, pady=5)
        self.cred_frame.grid(column=1, row=1, rowspan=2, sticky='w', padx=5, pady=5)
        self.settings_frame.grid(column=0, row=2, sticky='news', padx=5, pady=5)
        self.progress_frame.grid(column=0, row=3, columnspan=2, sticky='news', padx=5, pady=5)
        self.control_frame.grid(column=0, row=4, columnspan=2, sticky='news', padx=5, pady=5)
    
    def warn_tkinter_bug(self):
        if (platform.system() == 'Darwin' and
            platform.mac_ver()[0].split('.')[0] == '14' and
            sys.version_info[0] == 3 and
            sys.version_info[1] == 11 and
            sys.version_info[2] <= 6):
            msg = 'NOTICE: If buttons are not responsive, try to press '
            msg += 'on title bar or move mouse cursor away from window for a while.'
            self.cb_msg(msg)
            msg = '(This is due to a bug in tkinter specific to macOS 14 python <=3.11.6)'
            self.cb_msg(msg)
            msg = '(https://github.com/python/cpython/issues/110218)'
            self.cb_msg(msg)
    
    def load_jsons(self):
        self.help = JsonManager.load_json('resources/help.json')
        self.input_presets = JsonManager.load_json('resources/input.json')
        self.compression_presets = JsonManager.load_json('resources/compression.json')
        self.output_presets = JsonManager.load_json('resources/output.json')
        self.emoji_list = JsonManager.load_json('resources/emoji.json')

        if not (self.compression_presets and self.input_presets and self.output_presets):
            Messagebox.show_error(message='Warning: json(s) under "resources" directory cannot be found', title='sticker-convert')
            sys.exit()

        self.settings_path = os.path.join(DirUtils.get_config_dir(), 'config.json')
        if os.path.isfile(self.settings_path):
            self.settings = JsonManager.load_json(self.settings_path)
        else:
            self.settings = {}
        
        self.creds_path = os.path.join(DirUtils.get_config_dir(), 'creds.json')
        if os.path.isfile(self.creds_path):
            self.creds = JsonManager.load_json(self.creds_path)
        else:
            self.creds = {}
    
    def save_config(self):
        # Only update comp_custom if custom preset is selected
        if self.comp_preset_var.get() == 'custom':
            comp_custom = self.get_opt_comp()
            del comp_custom['preset']
            del comp_custom['no_compress']
        else:
            comp_custom = self.compression_presets.get('custom')

        self.settings = {
            'input': self.get_opt_input(),
            'comp': {
                'no_compress': self.no_compress_var.get(),
                'preset': self.comp_preset_var.get(),
                'cache_dir': self.cache_dir_var.get(),
                'processes': self.processes_var.get()
            },
            'comp_custom': comp_custom,
            'output': self.get_opt_output(),
            'creds': {
                'save_cred': self.settings_save_cred_var.get()
            }
        }

        JsonManager.save_json(self.settings_path, self.settings)
        
    def save_creds(self):
        self.creds = self.get_opt_cred()

        JsonManager.save_json(self.creds_path, self.creds)
    
    def delete_creds(self):
        if os.path.isfile(self.creds_path):
            os.remove(self.creds_path)
    
    def delete_config(self):
        if os.path.isfile(self.settings_path):
            os.remove(self.settings_path)
    
    def apply_config(self):
        # Input
        self.default_input_mode = self.settings.get('input', {}).get('option', 'auto')
        self.input_address_var.set(self.settings.get('input', {}).get('url', ''))
        default_stickers_input_dir = os.path.join(DirUtils.get_curr_dir(), 'stickers_input')
        self.input_setdir_var.set(self.settings.get('input', {}).get('dir', default_stickers_input_dir))
        if not os.path.isdir(self.input_setdir_var.get()):
            self.input_setdir_var.set(default_stickers_input_dir)
        self.input_option_display_var.set(self.input_presets[self.default_input_mode]['full_name'])
        self.input_option_true_var.set(self.input_presets[self.default_input_mode]['full_name'])

        # Compression
        self.no_compress_var.set(self.settings.get('comp', {}).get('no_compress', False))
        default_comp_preset = list(self.compression_presets.keys())[0]
        self.comp_preset_var.set(self.settings.get('comp', {}).get('preset', default_comp_preset))
        if self.settings.get('comp_custom'):
            self.compression_presets['custom'] = self.settings.get('comp_custom')
        self.cache_dir_var.set(self.settings.get('comp', {}).get('cache_dir', ''))
        self.processes_var.set(self.settings.get('comp', {}).get('processes', math.ceil(cpu_count() / 2)))
        self.default_output_mode = self.settings.get('output', {}).get('option', 'signal')

        # Output
        default_stickers_output_dir = os.path.join(DirUtils.get_curr_dir(), 'stickers_output')
        self.output_setdir_var.set(self.settings.get('output', {}).get('dir', default_stickers_output_dir))
        if not os.path.isdir(self.output_setdir_var.get()):
            self.output_setdir_var.set(default_stickers_output_dir)
        self.title_var.set(self.settings.get('output', {}).get('title', ''))
        self.author_var.set(self.settings.get('output', {}).get('author', ''))
        self.settings_save_cred_var.set(self.settings.get('creds', {}).get('save_cred', True))
        self.output_option_display_var.set(self.output_presets[self.default_output_mode]['full_name'])
        self.output_option_true_var.set(self.output_presets[self.default_output_mode]['full_name'])
    
    def apply_creds(self):
        self.signal_uuid_var.set(self.creds.get('signal', {}).get('uuid', ''))
        self.signal_password_var.set(self.creds.get('signal', {}).get('password', ''))
        self.telegram_token_var.set(self.creds.get('telegram', {}).get('token', ''))
        self.telegram_userid_var.set(self.creds.get('telegram', {}).get('userid', ''))
        self.kakao_auth_token_var.set(self.creds.get('kakao', {}).get('auth_token', ''))
        self.kakao_username_var.set(self.creds.get('kakao', {}).get('username', ''))
        self.kakao_password_var.set(self.creds.get('kakao', {}).get('password', ''))
        self.kakao_country_code_var.set(self.creds.get('kakao', {}).get('country_code', ''))
        self.kakao_phone_number_var.set(self.creds.get('kakao', {}).get('phone_number', ''))
        self.line_cookies_var.set(self.creds.get('line', {}). get('cookies', ''))
    
    def get_input_name(self) -> str:
        return [k for k, v in self.input_presets.items() if v['full_name'] == self.input_option_true_var.get()][0]

    def get_input_display_name(self) -> str:
        return [k for k, v in self.input_presets.items() if v['full_name'] == self.input_option_display_var.get()][0]

    def get_output_name(self) -> str:
        return [k for k, v in self.output_presets.items() if v['full_name'] == self.output_option_true_var.get()][0]

    def get_output_display_name(self) -> str:
        return [k for k, v in self.output_presets.items() if v['full_name'] == self.output_option_display_var.get()][0]

    def get_preset(self) -> str:
        selection = self.comp_preset_var.get()
        if selection == 'auto':
            output_option = self.get_output_name()
            if output_option == 'imessage':
                return 'imessage_small'
            elif output_option == 'local':
                return selection
            else:
                return output_option
            
        else:
            return selection
    
    def start_job(self):
        Thread(target=self.start_process, daemon=True).start()
    
    def get_opt_input(self) -> dict:
        return {
            'option': self.get_input_name(),
            'url': self.input_address_var.get(),
            'dir': self.input_setdir_var.get()
        }
    
    def get_opt_output(self) -> dict:
        return {
            'option': self.get_output_name(),
            'dir': self.output_setdir_var.get(),
            'title': self.title_var.get(),
            'author': self.author_var.get()
        }
    
    def get_opt_comp(self) -> dict:
        return {
            'preset': self.get_preset(),
            'size_max': {
                'img': self.img_size_max_var.get() if not self.size_disable_var.get() else None,
                'vid': self.vid_size_max_var.get() if not self.size_disable_var.get() else None
            },
            'format': {
                'img': self.img_format_var.get(),
                'vid': self.vid_format_var.get()
            },
            'fps': {
                'min': self.fps_min_var.get() if not self.fps_disable_var.get() else None,
                'max': self.fps_max_var.get() if not self.fps_disable_var.get() else None
            },
            'res': {
                'w': {
                    'min': self.res_w_min_var.get() if not self.res_w_disable_var.get() else None,
                    'max': self.res_w_max_var.get() if not self.res_w_disable_var.get() else None
                },
                'h': {
                    'min': self.res_h_min_var.get() if not self.res_h_disable_var.get() else None,
                    'max': self.res_h_max_var.get() if not self.res_h_disable_var.get() else None
                }
            },
            'quality': {
                'min': self.quality_min_var.get() if not self.quality_disable_var.get() else None,
                'max': self.quality_max_var.get() if not self.quality_disable_var.get() else None
            },
            'color': {
                'min': self.color_min_var.get() if not self.color_disable_var.get() else None,
                'max': self.color_max_var.get() if not self.color_disable_var.get() else None
            },
            'duration': {
                'min': self.duration_min_var.get() if not self.duration_disable_var.get() else None,
                'max': self.duration_max_var.get() if not self.duration_disable_var.get() else None
            },
            'steps': self.steps_var.get(),
            'fake_vid': self.fake_vid_var.get(),
            'cache_dir': self.cache_dir_var.get() if self.cache_dir_var.get() != '' else None,
            'default_emoji': self.default_emoji_var.get(),
            'no_compress': self.no_compress_var.get(),
            'processes': self.processes_var.get()
        }
    
    def get_opt_cred(self) -> dict:
        return {
            'signal': {
                'uuid': self.signal_uuid_var.get(),
                'password': self.signal_password_var.get()
            },
            'telegram': {
                'token': self.telegram_token_var.get(),
                'userid': self.telegram_userid_var.get()
            },
            'kakao': {
                'auth_token': self.kakao_auth_token_var.get(),
                'username': self.kakao_username_var.get(),
                'password': self.kakao_password_var.get(),
                'country_code': self.kakao_country_code_var.get(),
                'phone_number': self.kakao_phone_number_var.get()
            },
            'line': {
                'cookies': self.line_cookies_var.get()
            }
        }

    def start_process(self):
        self.save_config()
        if self.settings_save_cred_var.get() == True:
            self.save_creds()
        else:
            self.delete_creds()

        self.control_frame.start_btn.config(text='Cancel', bootstyle='danger')
        self.set_inputs('disabled')
    
        opt_input = InputOption(self.get_opt_input())
        opt_output = OutputOption(self.get_opt_output())
        opt_comp = CompOption(self.get_opt_comp())
        opt_cred = CredOption(self.get_opt_cred())
        
        self.job = Job(
            opt_input, opt_comp, opt_output, opt_cred, 
            self.cb_msg, self.cb_msg_block, self.cb_bar, self.cb_ask_bool
            )
        
        status = self.job.start()

        self.job = None

        if status == 1:
            self.cb_msg(msg='An error occured during this run.')
        elif status == 2:
            self.cb_msg(msg='Job cancelled.')

        self.stop_job()
    
    def stop_job(self):
        self.progress_frame.update_progress_bar(set_progress_mode='clear')
        self.set_inputs('normal')
        self.control_frame.start_btn.config(text='Start', bootstyle='default')
    
    def cancel_job(self):
        self.cb_msg(msg='Cancelling job...')
        self.job.is_cancel_job.value = 1
        while not self.job.jobs_queue.empty():
            self.job.jobs_queue.get()
        for process in self.job.processes:
            process.terminate()
            process.join()

    def set_inputs(self, state: str):
        # state: 'normal', 'disabled'

        self.input_frame.set_states(state=state)
        self.comp_frame.set_states(state=state)
        self.output_frame.set_states(state=state)
        self.cred_frame.set_states(state=state)
        self.settings_frame.set_states(state=state)

        if state == 'normal':
            self.input_frame.cb_input_option()
            self.comp_frame.cb_no_compress()
    
    def poll_actions(self):
        if self.action_queue.empty():
            self.after(500, self.poll_actions)
            return
        
        action = self.action_queue.get_nowait()
        response_id = action[0]
        response = action[1]()
        if response_id:
            with self.response_dict_lock:
                self.response_dict[response_id] = response

        self.after(500, self.poll_actions)
    
    def get_response_from_id(self, response_id: str) -> Any:
        # If executed from main thread, need to poll_actions() manually as it got blocked
        if current_thread() is main_thread():
            self.poll_actions()

        while response_id not in self.response_dict:
            time.sleep(0.1)
        
        with self.response_dict_lock:
            response = self.response_dict[response_id]
            del self.response_dict[response_id]

        return response

    def exec_in_main(self, action) -> Any:
        response_id = str(uuid4())
        self.action_queue.put([response_id, action])
        response = self.get_response_from_id(response_id)
        return response
    
    def cb_ask_str(self, 
                   question: str, 
                   initialvalue: Optional[str] = None, 
                   cli_show_initialvalue: bool = True, 
                   parent: Optional[object] = None) -> str:
        return self.exec_in_main(partial(Querybox.get_string, question, title='sticker-convert', initialvalue=initialvalue, parent=parent))

    def cb_ask_bool(self, question, parent=None) -> bool:
        response = self.exec_in_main(partial(Messagebox.yesno, question, title='sticker-convert', parent=parent))

        if response == 'Yes':
            return True
        return False

    def cb_msg(self, *args, **kwargs):
        with self.msg_lock:
            self.progress_frame.update_message_box(*args, **kwargs)
    
    def cb_msg_block(self, 
                     message: Optional[str] = None, 
                     parent: Optional[object] = None, 
                     *args, **kwargs):
        if message == None and len(args) > 0:
            message = ' '.join(str(i) for i in args)
        self.exec_in_main(partial(Messagebox.show_info, message, title='sticker-convert', parent=parent))
    
    def cb_bar(self, *args, **kwargs):
        with self.bar_lock:
            self.progress_frame.update_progress_bar(*args, **kwargs)
        
    def highlight_fields(self) -> bool:
        if not self.init_done:
            return True
        
        input_option = self.get_input_name()
        input_option_display = self.get_input_display_name()
        output_option = self.get_output_name()
        # output_option_display = self.get_output_display_name()
        url = self.input_address_var.get()

        # Input
        if os.path.isdir(self.input_setdir_var.get()):
            self.input_frame.input_setdir_entry.config(bootstyle='default')
        else:
            self.input_frame.input_setdir_entry.config(bootstyle='danger')

        self.input_frame.address_lbl.config(text=self.input_presets[input_option_display]['address_lbls'])
        self.input_frame.address_entry.config(bootstyle='default')

        if input_option == 'local':
            self.input_frame.address_entry.config(state='disabled')
            self.input_frame.address_tip.config(text=self.input_presets[input_option_display]['example'])

        else:
            self.input_frame.address_entry.config(state='normal')
            self.input_frame.address_tip.config(text=self.input_presets[input_option_display]['example'])
            download_option = UrlDetect.detect(url)

            if not url:
                self.input_frame.address_entry.config(bootstyle='warning')

            elif (download_option != input_option and
                  not (input_option in ('kakao', 'line') and url.isnumeric())):
                
                self.input_frame.address_entry.config(bootstyle='danger')
                self.input_frame.address_tip.config(text=f"Invalid URL. {self.input_presets[input_option_display]['example']}")
        
            elif input_option_display == 'auto' and download_option:
                self.input_frame.address_tip.config(text=f'Detected URL: {download_option}')

        # Output
        if os.path.isdir(self.output_setdir_var.get()):
            self.output_frame.output_setdir_entry.config(bootstyle='default')
        else:
            self.output_frame.output_setdir_entry.config(bootstyle='danger')

        if (MetadataHandler.check_metadata_required(output_option, 'title') and
            not MetadataHandler.check_metadata_provided(self.input_setdir_var.get(), input_option, 'title') and
            not self.title_var.get()):

            self.output_frame.title_entry.config(bootstyle='warning')
        else:
            self.output_frame.title_entry.config(bootstyle='default')

        if (MetadataHandler.check_metadata_required(output_option, 'author') and
            not MetadataHandler.check_metadata_provided(self.input_setdir_var.get(), input_option, 'author') and
            not self.author_var.get()):
            
            self.output_frame.author_entry.config(bootstyle='warning')
        else:
            self.output_frame.author_entry.config(bootstyle='default')
        
        if self.comp_preset_var.get() == 'auto':
            if output_option == 'local':
                self.no_compress_var.set(True)
            else:
                self.no_compress_var.set(False)
            self.comp_frame.cb_no_compress()
        
        # Credentials
        if output_option == 'signal' and not self.signal_uuid_var.get():
            self.cred_frame.signal_uuid_entry.config(bootstyle='warning')
        else:
            self.cred_frame.signal_uuid_entry.config(bootstyle='default')

        if output_option == 'signal' and not self.signal_password_var.get():
            self.cred_frame.signal_password_entry.config(bootstyle='warning')
        else:
            self.cred_frame.signal_password_entry.config(bootstyle='default')

        if (input_option == 'telegram' or output_option == 'telegram') and not self.telegram_token_var.get():
            self.cred_frame.telegram_token_entry.config(bootstyle='warning')
        else:
            self.cred_frame.telegram_token_entry.config(bootstyle='default')

        if output_option == 'telegram' and not self.telegram_userid_var.get():
            self.cred_frame.telegram_userid_entry.config(bootstyle='warning')
        else:
            self.cred_frame.telegram_userid_entry.config(bootstyle='default')
        
        if urlparse(url).netloc == 'e.kakao.com' and not self.kakao_auth_token_var.get():
            self.cred_frame.kakao_auth_token_entry.config(bootstyle='warning')
        else:
            self.cred_frame.kakao_auth_token_entry.config(bootstyle='default')
        
        # Check for Input and Compression mismatch
        if (not self.no_compress_var.get() and 
            self.get_output_name() != 'local' and
            self.comp_preset_var.get() not in ('auto', 'custom') and
            self.get_output_name() not in self.comp_preset_var.get()):

            self.comp_frame.comp_preset_opt.config(bootstyle='warning')
            self.output_frame.output_option_opt.config(bootstyle='warning')
        else:
            self.comp_frame.comp_preset_opt.config(bootstyle='secondary')
            self.output_frame.output_option_opt.config(bootstyle='secondary')
        
        return True