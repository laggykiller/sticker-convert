#!/usr/bin/env python3
import os
import sys
import time
from multiprocessing import cpu_count
from threading import Thread, Lock, current_thread, main_thread
from queue import Queue
import webbrowser
from functools import partial
from uuid import uuid4

from PIL import Image, ImageTk, ImageDraw, ImageFont
from tkinter import filedialog
from ttkbootstrap import Window, Toplevel, LabelFrame, Frame, OptionMenu, Button, Progressbar, Entry, Label, Checkbutton, Scrollbar, Menu, Canvas, PhotoImage, StringVar, BooleanVar, IntVar
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.dialogs import Messagebox, Querybox
from tqdm import tqdm

from .flow import Flow
from .utils.json_manager import JsonManager
from .utils.get_kakao_auth import GetKakaoAuth
from .utils.get_signal_auth import GetSignalAuth
from .utils.get_line_auth import GetLineAuth
from .utils.curr_dir import CurrDir
from .utils.metadata_handler import MetadataHandler
from .__init__ import __version__

# Reference: https://stackoverflow.com/a/57704013
class RightClicker:
    def __init__(self, event):
        right_click_menu = Menu(None, tearoff=0, takefocus=0)

        for txt in ['Cut', 'Copy', 'Paste']:
            right_click_menu.add_command(
                label=txt, command=lambda event=event, text=txt:
                self.right_click_command(event, text))

        right_click_menu.tk_popup(event.x_root, event.y_root, entry='0')

    def right_click_command(self, event, cmd):
        event.widget.event_generate(f'<<{cmd}>>')

class GUI:
    default_input_mode = 'telegram'
    default_output_mode = 'signal'

    def __init__(self):
        self.load_jsons()

        self.emoji_font = ImageFont.truetype("./resources/NotoColorEmoji.ttf", 109)

        self.root = Window(themename='darkly')

        self.icon = PhotoImage(file='resources/appicon.png')
        self.root.iconphoto(1, self.icon)
        if sys.platform == 'darwin':
            self.root.iconbitmap(bitmap='resources/appicon.icns')
        elif sys.platform == 'win32':
            self.root.iconbitmap(bitmap='resources/appicon.ico')
        self.root.tk.call('wm', 'iconphoto', self.root._w, self.icon)
        self.root.title(f'sticker-convert {__version__}')

        self.create_scrollable_frame()
        self.declare_variables()
        self.set_creds()
        self.init_frames()
        self.pack_frames()
        self.highlight_fields()
        self.resize_window()

        self.msg_lock = Lock()
        self.bar_lock = Lock()
        self.response_dict_lock = Lock()
        self.response_dict = {}
        self.action_queue = Queue()
        self.root.after(500, self.poll_actions)
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save_creds()
        
    def create_scrollable_frame(self):
        self.main_frame = Frame(self.root)
        self.main_frame.pack(fill='both', expand=1)

        self.horizontal_scrollbar_frame = Frame(self.main_frame)
        self.horizontal_scrollbar_frame.pack(fill='x', side='bottom')

        self.canvas = Canvas(self.main_frame)
        self.canvas.pack(side='left', fill='both', expand=1)

        self.x_scrollbar = Scrollbar(self.horizontal_scrollbar_frame, orient='horizontal', command=self.canvas.xview)
        self.x_scrollbar.pack(side='bottom', fill='x')

        self.y_scrollbar = Scrollbar(self.main_frame, orient='vertical', command=self.canvas.yview)
        self.y_scrollbar.pack(side='right', fill='y')

        self.canvas.configure(xscrollcommand=self.x_scrollbar.set)
        self.canvas.configure(yscrollcommand=self.y_scrollbar.set)
        self.canvas.bind("<Configure>",lambda e: self.canvas.config(scrollregion= self.canvas.bbox('all'))) 

        self.scrollable_frame = Frame(self.canvas)
        self.canvas.create_window((0,0),window= self.scrollable_frame, anchor="nw")
    
    def declare_variables(self):
        # Input
        self.input_option_var = StringVar(self.root)
        self.input_setdir_var = StringVar(self.root)
        self.input_address_var = StringVar(self.root)

        self.input_option_var.set(self.input_presets[self.default_input_mode]['full_name'])
        stickers_input_dir = os.path.join(CurrDir.get_curr_dir(), 'stickers_input')
        self.input_setdir_var.set(stickers_input_dir)

        # Compression
        self.no_compress_var = BooleanVar()
        self.comp_preset_var = StringVar(self.root)
        self.default_comp_preset = list(self.compression_presets.keys())[0]
        self.fps_min_var = IntVar(self.root)
        self.fps_max_var = IntVar(self.root)
        self.fps_disable_var = BooleanVar()
        self.res_w_min_var = IntVar(self.root)
        self.res_w_max_var = IntVar(self.root)
        self.res_w_disable_var = BooleanVar()
        self.res_h_min_var = IntVar(self.root)
        self.res_h_max_var = IntVar(self.root)
        self.res_h_disable_var = BooleanVar()
        self.quality_min_var = IntVar(self.root)
        self.quality_max_var = IntVar(self.root)
        self.quality_disable_var = BooleanVar()
        self.color_min_var = IntVar(self.root)
        self.color_max_var = IntVar(self.root)
        self.color_disable_var = BooleanVar()
        self.duration_min_var = IntVar(self.root)
        self.duration_max_var = IntVar(self.root)
        self.duration_disable_var = BooleanVar()
        self.img_size_max_var = IntVar(self.root)
        self.vid_size_max_var = IntVar(self.root)
        self.size_disable_var = BooleanVar()
        self.img_format_var = StringVar(self.root)
        self.vid_format_var = StringVar(self.root)
        self.fake_vid_var = BooleanVar()
        self.cache_dir_var = StringVar(self.root)
        self.default_emoji_var = StringVar(self.root)
        self.steps_var = IntVar(self.root) 
        self.processes_var = IntVar(self.root)

        self.comp_preset_var.set(self.default_comp_preset)
        self.processes_var.set(cpu_count())

        # Output
        self.output_option_var = StringVar(self.root)
        self.output_setdir_var = StringVar(self.root)
        self.title_var = StringVar(self.root)
        self.author_var = StringVar(self.root)

        self.output_option_var.set(self.output_presets[self.default_output_mode]['full_name'])
        stickers_output_dir = os.path.join(CurrDir.get_curr_dir(), 'stickers_output')
        self.output_setdir_var.set(stickers_output_dir)

        # Credentials
        self.signal_uuid_var = StringVar(self.root)
        self.signal_password_var = StringVar(self.root)
        self.telegram_token_var = StringVar(self.root)
        self.telegram_userid_var = StringVar(self.root)
        self.kakao_auth_token_var = StringVar(self.root)
        self.kakao_username_var = StringVar(self.root)
        self.kakao_password_var = StringVar(self.root)
        self.kakao_country_code_var = StringVar(self.root)
        self.kakao_phone_number_var = StringVar(self.root)
        self.line_cookies_var = StringVar(self.root)

    def init_frames(self):
        self.input_frame = InputFrame(self)
        self.comp_frame = CompFrame(self)
        self.output_frame = OutputFrame(self)
        self.cred_frame = CredFrame(self)
        self.progress_frame = ProgressFrame(self)
        self.control_frame = ControlFrame(self)
    
    def pack_frames(self):
        self.input_frame.frame.grid(column=0, row=0, sticky='w', padx=5, pady=5)
        self.comp_frame.frame.grid(column=1, row=0, sticky='news', padx=5, pady=5)
        self.output_frame.frame.grid(column=0, row=1, sticky='w', padx=5, pady=5)
        self.cred_frame.frame.grid(column=1, row=1, sticky='w', padx=5, pady=5)
        self.progress_frame.frame.grid(column=0, row=2, columnspan=2, sticky='news', padx=5, pady=5)
        self.control_frame.frame.grid(column=0, row=3, columnspan=2, sticky='news', padx=5, pady=5)
    
    def resize_window(self):
        self.scrollable_frame.update_idletasks()
        width = self.scrollable_frame.winfo_width()
        height = self.scrollable_frame.winfo_height()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenwidth()

        if width > screen_width * 0.8:
            width = int(screen_width * 0.8)
        if height > screen_height * 0.8:
            height = int(screen_height * 0.8)

        self.canvas.configure(width=width, height=height)
    
    def load_jsons(self):
        self.help = JsonManager.load_json('resources/help.json')
        self.input_presets = JsonManager.load_json('resources/input.json')
        self.compression_presets = JsonManager.load_json('resources/compression.json')
        self.output_presets = JsonManager.load_json('resources/output.json')
        self.emoji_list = JsonManager.load_json('resources/emoji.json')

        if not (self.compression_presets and self.input_presets and self.output_presets):
            Messagebox.show_error(message='Warning: json(s) under "resources" directory cannot be found', title='sticker-convert')
            sys.exit()
        
        creds_path = os.path.join(CurrDir.get_creds_dir(), 'creds.json')
        if os.path.isfile(creds_path):
            self.creds = JsonManager.load_json(creds_path)
        else:
            self.creds = {
            'signal': {
                'uuid': '',
                'password': ''
            },
            'telegram': {
                'token': '',
                'userid': ''
            },
            'kakao': {
                'auth_token': '',
                'username': '',
                'password': '',
                'country_code': '',
                'phone_number': ''
            },
            'line': {
                'cookies': ''
            }
        }
        
    def save_creds(self):
        self.creds = {
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

        creds_path = os.path.join(CurrDir.get_creds_dir(), 'creds.json')
        JsonManager.save_json(creds_path, self.creds)
    
    def set_creds(self):
        if not self.creds:
            return

        self.signal_uuid_var.set(self.creds.get('signal', {}).get('uuid'))
        self.signal_password_var.set(self.creds.get('signal', {}).get('password'))
        self.telegram_token_var.set(self.creds.get('telegram', {}).get('token'))
        self.telegram_userid_var.set(self.creds.get('telegram', {}).get('userid'))
        self.kakao_auth_token_var.set(self.creds.get('kakao', {}).get('auth_token'))
        self.kakao_username_var.set(self.creds.get('kakao', {}).get('username'))
        self.kakao_password_var.set(self.creds.get('kakao', {}).get('password'))
        self.kakao_country_code_var.set(self.creds.get('kakao', {}).get('country_code'))
        self.kakao_phone_number_var.set(self.creds.get('kakao', {}).get('phone_number'))
        self.line_cookies_var.set(self.creds.get('line', {}). get('cookies'))

    def start(self):
        Thread(target=self.start_process, daemon=True).start()

    def start_process(self):
        self.save_creds()
        self.set_inputs('disabled')
        self.control_frame.start_btn.config(state='disabled')
    
        opt_input = {
            'option': [k for k, v in self.input_presets.items() if v['full_name'] == self.input_option_var.get()][0],
            'url': self.input_address_var.get(),
            'dir': self.input_setdir_var.get()
        }

        opt_output = {
            'option': [k for k, v in self.output_presets.items() if v['full_name'] == self.output_option_var.get()][0],
            'dir': self.output_setdir_var.get(),
            'title': self.title_var.get(),
            'author': self.author_var.get()
        }

        opt_comp = {
            'preset': self.comp_preset_var.get(),
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

        opt_cred = {
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
        
        flow = Flow(
            opt_input, opt_comp, opt_output, opt_cred, 
            self.input_presets, self.output_presets,
            self.cb_msg, self.cb_msg_block, self.cb_bar, self.cb_ask_bool
            )
        
        success = flow.start()

        if not success:
            self.cb_msg(msg='An error occured during this run.')

        self.stop()
    
    def stop(self):
        self.progress_frame.update_progress_bar(set_progress_mode='clear')
        self.set_inputs('normal')
        self.control_frame.start_btn.config(state='normal')

    def set_inputs(self, state):
        # state: 'normal', 'disabled'

        self.input_frame.set_states(state=state)
        self.comp_frame.set_states(state=state)
        self.output_frame.set_states(state=state)
        self.cred_frame.set_states(state=state)

        if state == 'normal':
            self.input_frame.cb_input_option()
            self.comp_frame.cb_nocompress()
    
    def poll_actions(self):
        if self.action_queue.empty():
            self.root.after(500, self.poll_actions)
            return
        
        action = self.action_queue.get_nowait()
        response_id = action[0]
        response = action[1]()
        if response_id:
            with self.response_dict_lock:
                self.response_dict[response_id] = response

        self.root.after(500, self.poll_actions)
    
    def get_response_from_id(self, response_id):
        # If executed from main thread, need to poll_actions() manually as it got blocked
        if current_thread() is main_thread():
            self.poll_actions()

        while response_id not in self.response_dict:
            time.sleep(0.1)
        
        with self.response_dict_lock:
            response = self.response_dict[response_id]
            del self.response_dict[response_id]

        return response

    def exec_in_main(self, action):
        response_id = str(uuid4())
        self.action_queue.put([response_id, action])
        response = self.get_response_from_id(response_id)
        return response
    
    def cb_ask_str(self, question, initialvalue: str=None, cli_show_initialvalue: bool=True, parent=None):
        return self.exec_in_main(partial(Querybox.get_string, question, title='sticker-convert', initialvalue=initialvalue, parent=parent))

    def cb_ask_bool(self, question, parent=None):
        response = self.exec_in_main(partial(Messagebox.yesno, question, title='sticker-convert', parent=parent))

        if response == 'Yes':
            return True
        return False

    def cb_msg(self, *args, **kwargs):
        with self.msg_lock:
            self.progress_frame.update_message_box(*args, **kwargs)
    
    def cb_msg_block(self, message=None, parent=None, *args, **kwargs):
        if message == None and len(args) > 0:
            message = ' '.join(str(i) for i in args)
        self.exec_in_main(partial(Messagebox.show_info, message, title='sticker-convert', parent=parent))
    
    def cb_bar(self, *args, **kwargs):
        with self.bar_lock:
            self.progress_frame.update_progress_bar(*args, **kwargs)
        
    def highlight_fields(self):
        input_option = [k for k, v in self.input_presets.items() if v['full_name'] == self.input_option_var.get()][0]
        output_option = [k for k, v in self.output_presets.items() if v['full_name'] == self.output_option_var.get()][0]

        if input_option != 'local' and not self.input_address_var.get():
            self.input_frame.address_entry.config(bootstyle='warning')
        else:
            self.input_frame.address_entry.config(bootstyle='default')

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
        
        return True

class InputFrame:
    def __init__(self, gui):
        self.gui = gui
        self.frame = LabelFrame(self.gui.scrollable_frame, borderwidth=1, text='Input')

        self.input_option_lbl = Label(self.frame, text='Input source', width=15, justify='left', anchor='w')
        input_full_names = [i['full_name'] for i in self.gui.input_presets.values()]
        default_input_full_name = self.gui.input_presets[self.gui.default_input_mode]['full_name']
        self.input_option_opt = OptionMenu(self.frame, self.gui.input_option_var, default_input_full_name, *input_full_names, command=self.cb_input_option, bootstyle='secondary')
        self.input_option_opt.config(width=32)

        self.input_setdir_lbl = Label(self.frame, text='Input directory', width=35, justify='left', anchor='w')
        self.input_setdir_entry = Entry(self.frame, textvariable=self.gui.input_setdir_var, width=60)
        self.input_setdir_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.setdir_btn = Button(self.frame, text='Choose directory...', command=self.cb_set_indir, width=16, bootstyle='secondary')

        self.address_lbl = Label(self.frame, text=self.gui.input_presets[self.gui.default_input_mode]['address_lbls'], width=18, justify='left', anchor='w')
        self.address_entry = Entry(self.frame, textvariable=self.gui.input_address_var, width=80, validate="focusout", validatecommand=self.gui.highlight_fields)
        self.address_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.address_tip = Label(self.frame, text=self.gui.input_presets[self.gui.default_input_mode]['example'], justify='left', anchor='w')

        self.input_option_lbl.grid(column=0, row=0, sticky='w', padx=3, pady=3)
        self.input_option_opt.grid(column=1, row=0, columnspan=2, sticky='w', padx=3, pady=3)
        self.input_setdir_lbl.grid(column=0, row=1, columnspan=2, sticky='w', padx=3, pady=3)
        self.input_setdir_entry.grid(column=1, row=1, sticky='w', padx=3, pady=3)
        self.setdir_btn.grid(column=2, row=1, sticky='e', padx=3, pady=3)
        self.address_lbl.grid(column=0, row=2, sticky='w', padx=3, pady=3)
        self.address_entry.grid(column=1, row=2, columnspan=2, sticky='w', padx=3, pady=3)
        self.address_tip.grid(column=0, row=3, columnspan=3, sticky='w', padx=3, pady=3)
    
    def cb_set_indir(self, *args):
        orig_input_dir = self.gui.input_setdir_var.get()
        if not os.path.isdir(orig_input_dir):
            orig_input_dir = CurrDir.get_curr_dir()
        input_dir = filedialog.askdirectory(initialdir=orig_input_dir)
        if input_dir:
            self.gui.input_setdir_var.set(input_dir)
    
    def cb_input_option(self, *args):
        for i in self.gui.input_presets.keys():
            if self.gui.input_option_var.get() == self.gui.input_presets[i]['full_name']:
                self.address_tip.config(text=self.gui.input_presets[i]['example'])
                self.address_lbl.config(text=self.gui.input_presets[i]['address_lbls'])
                if i == 'local':
                    self.address_entry.config(state='disabled')
                else:
                    self.address_entry.config(state='normal')
                break
        
        self.gui.highlight_fields()
    
    def set_states(self, state):
        self.input_option_opt.config(state=state)
        self.address_entry.config(state=state)
        self.input_setdir_entry.config(state=state)
        self.setdir_btn.config(state=state)

class CompFrame:
    def __init__(self, gui):
        self.gui = gui
        self.frame = LabelFrame(self.gui.scrollable_frame, borderwidth=1, text='Compression options')
        self.frame.grid_columnconfigure(2, weight = 1)

        self.no_compress_help_btn = Button(self.frame, text='?', width=1, command=lambda: self.gui.cb_msg_block(self.gui.help['comp']['no_compress']), bootstyle='secondary')
        self.no_compress_lbl = Label(self.frame, text='No compression')
        self.no_compress_cbox = Checkbutton(self.frame, variable=self.gui.no_compress_var, command=self.cb_nocompress, onvalue=True, offvalue=False, bootstyle='danger-round-toggle')

        self.comp_preset_help_btn = Button(self.frame, text='?', width=1, command=lambda: self.gui.cb_msg_block(self.gui.help['comp']['preset']), bootstyle='secondary')
        self.comp_preset_lbl = Label(self.frame, text='Preset')
        self.comp_preset_opt = OptionMenu(self.frame, self.gui.comp_preset_var, self.gui.default_comp_preset, *self.gui.compression_presets.keys(), command=self.cb_comp_apply_preset, bootstyle='secondary')
        self.comp_preset_opt.config(width=15)

        self.steps_help_btn = Button(self.frame, text='?', width=1, command=lambda: self.gui.cb_msg_block(self.gui.help['comp']['steps']), bootstyle='secondary')
        self.steps_lbl = Label(self.frame, text='Number of steps')       
        self.steps_entry = Entry(self.frame, textvariable=self.gui.steps_var, width=8)
        self.steps_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.processes_help_btn = Button(self.frame, text='?', width=1, command=lambda: self.gui.cb_msg_block(self.gui.help['comp']['processes']), bootstyle='secondary')
        self.processes_lbl = Label(self.frame, text='Number of processes')
        self.processes_entry = Entry(self.frame, textvariable=self.gui.processes_var, width=8)
        self.processes_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.comp_advanced_btn = Button(self.frame, text='Advanced...', command=self.cb_compress_advanced, bootstyle='secondary')

        self.no_compress_help_btn.grid(column=0, row=0, sticky='w', padx=3, pady=3)
        self.no_compress_lbl.grid(column=1, row=0, sticky='w', padx=3, pady=3)
        self.no_compress_cbox.grid(column=2, row=0, sticky='nes', padx=3, pady=3)

        self.comp_preset_help_btn.grid(column=0, row=1, sticky='w', padx=3, pady=3)
        self.comp_preset_lbl.grid(column=1, row=1, sticky='w', padx=3, pady=3)
        self.comp_preset_opt.grid(column=2, row=1, sticky='nes', padx=3, pady=3)

        self.steps_help_btn.grid(column=0, row=2, sticky='w', padx=3, pady=3)
        self.steps_lbl.grid(column=1, row=2, sticky='w', padx=3, pady=3)
        self.steps_entry.grid(column=2, row=2, sticky='nes', padx=3, pady=3)

        self.processes_help_btn.grid(column=0, row=3, sticky='w', padx=3, pady=3)
        self.processes_lbl.grid(column=1, row=3, sticky='w', padx=3, pady=3)
        self.processes_entry.grid(column=2, row=3, sticky='nes', padx=3, pady=3)

        self.comp_advanced_btn.grid(column=2, row=4, sticky='nes', padx=3, pady=3)

        self.cb_comp_apply_preset()
    
    def cb_comp_apply_preset(self, *args):
        selection = self.gui.comp_preset_var.get()
        self.gui.fps_min_var.set(self.gui.compression_presets[selection]['fps']['min'])
        self.gui.fps_max_var.set(self.gui.compression_presets[selection]['fps']['max'])
        self.gui.res_w_min_var.set(self.gui.compression_presets[selection]['res']['w']['min'])
        self.gui.res_w_max_var.set(self.gui.compression_presets[selection]['res']['w']['max'])
        self.gui.res_h_min_var.set(self.gui.compression_presets[selection]['res']['h']['min'])
        self.gui.res_h_max_var.set(self.gui.compression_presets[selection]['res']['h']['max'])
        self.gui.quality_min_var.set(self.gui.compression_presets[selection]['quality']['min'])
        self.gui.quality_max_var.set(self.gui.compression_presets[selection]['quality']['max'])
        self.gui.color_min_var.set(self.gui.compression_presets[selection]['color']['min'])
        self.gui.color_max_var.set(self.gui.compression_presets[selection]['color']['max'])
        self.gui.duration_min_var.set(self.gui.compression_presets[selection]['duration']['min'])
        self.gui.duration_max_var.set(self.gui.compression_presets[selection]['duration']['max'])
        self.gui.img_size_max_var.set(self.gui.compression_presets[selection]['size_max']['img'])
        self.gui.vid_size_max_var.set(self.gui.compression_presets[selection]['size_max']['vid'])
        self.gui.img_format_var.set(self.gui.compression_presets[selection]['format']['img'])
        self.gui.vid_format_var.set(self.gui.compression_presets[selection]['format']['vid'])
        self.gui.fake_vid_var.set(self.gui.compression_presets[selection]['fake_vid'])
        self.gui.default_emoji_var.set(self.gui.compression_presets[selection]['default_emoji'])
        self.gui.steps_var.set(self.gui.compression_presets[selection]['steps'])
    
    def cb_compress_advanced(self, *args):
        AdvancedCompressionWindow(self.gui)
    
    def cb_nocompress(self, *args):
        if self.gui.no_compress_var.get() == True:
            self.set_inputs_comp(state='disabled')
        else:
            self.set_inputs_comp(state='normal')
    
    def set_inputs_comp(self, state):
        self.comp_preset_opt.config(state=state)
        self.comp_advanced_btn.config(state=state)
        self.steps_entry.config(state=state)
        self.processes_entry.config(state=state)
            
    def set_states(self, state):
        self.no_compress_cbox.config(state=state)
        self.set_inputs_comp(state=state)

class OutputFrame:
    def __init__(self, gui):
        self.gui = gui
        self.frame = LabelFrame(self.gui.scrollable_frame, borderwidth=1, text='Output')

        self.output_option_lbl = Label(self.frame, text='Output options', width=18, justify='left', anchor='w')
        output_full_names = [i['full_name'] for i in self.gui.output_presets.values()]
        defult_output_full_name = self.gui.output_presets[self.gui.default_output_mode]['full_name']
        self.output_option_opt = OptionMenu(self.frame, self.gui.output_option_var, defult_output_full_name, *output_full_names, command=self.cb_output_option, bootstyle='secondary')
        self.output_option_opt.config(width=32)

        self.output_setdir_lbl = Label(self.frame, text='Output directory', justify='left', anchor='w')
        self.output_setdir_entry = Entry(self.frame, textvariable=self.gui.output_setdir_var, width=60)
        self.output_setdir_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        
        self.output_setdir_btn = Button(self.frame, text='Choose directory...', command=self.cb_set_outdir, width=16, bootstyle='secondary')

        self.title_lbl = Label(self.frame, text='Title')
        self.title_entry = Entry(self.frame, textvariable=self.gui.title_var, width=80, validate="focusout", validatecommand=self.gui.highlight_fields)
        self.title_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        
        self.author_lbl = Label(self.frame, text='Author')
        self.author_entry = Entry(self.frame, textvariable=self.gui.author_var, width=80, validate="focusout", validatecommand=self.gui.highlight_fields)
        self.author_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.output_option_lbl.grid(column=0, row=0, sticky='w', padx=3, pady=3)
        self.output_option_opt.grid(column=1, row=0, columnspan=2, sticky='w', padx=3, pady=3)
        self.output_setdir_lbl.grid(column=0, row=1, columnspan=2, sticky='w', padx=3, pady=3)
        self.output_setdir_entry.grid(column=1, row=1, sticky='w', padx=3, pady=3)
        self.output_setdir_btn.grid(column=2, row=1, sticky='e', padx=3, pady=3)
        self.title_lbl.grid(column=0, row=2, sticky='w', padx=3, pady=3)
        self.title_entry.grid(column=1, columnspan=2, row=2, sticky='w', padx=3, pady=3)
        self.author_lbl.grid(column=0, row=3, sticky='w', padx=3, pady=3)
        self.author_entry.grid(column=1, columnspan=2, row=3, sticky='w', padx=3, pady=3)
    
    def cb_set_outdir(self, *args):
        orig_output_dir = self.gui.output_setdir_var.get()
        if not os.path.isdir(orig_output_dir):
            orig_output_dir = CurrDir.get_curr_dir()
        output_dir = filedialog.askdirectory(initialdir=orig_output_dir)
        if output_dir:
            self.gui.output_setdir_var.set(output_dir)
    
    def cb_output_option(self, *args):
        self.gui.highlight_fields()
    
    def set_states(self, state):
        self.title_entry.config(state=state)
        self.author_entry.config(state=state)
        self.output_option_opt.config(state=state)
        self.output_setdir_entry.config(state=state)
        self.output_setdir_btn.config(state=state)

class CredFrame:
    def __init__(self, gui):
        self.gui = gui
        self.frame = LabelFrame(self.gui.scrollable_frame, borderwidth=1, text='Credentials')

        self.frame.grid_columnconfigure(1, weight=1)

        self.signal_uuid_lbl = Label(self.frame, text='Signal uuid', width=18, justify='left', anchor='w')
        self.signal_uuid_entry = Entry(self.frame, textvariable=self.gui.signal_uuid_var, width=50, validate="focusout", validatecommand=self.gui.highlight_fields)
        self.signal_uuid_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.signal_password_lbl = Label(self.frame, text='Signal password', justify='left', anchor='w')
        self.signal_password_entry = Entry(self.frame, textvariable=self.gui.signal_password_var, width=50, validate="focusout", validatecommand=self.gui.highlight_fields)
        self.signal_password_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.signal_get_auth_btn = Button(self.frame, text='Generate', command=self.cb_signal_get_auth, bootstyle='secondary')

        self.telegram_token_lbl = Label(self.frame, text='Telegram token', justify='left', anchor='w')
        self.telegram_token_entry = Entry(self.frame, textvariable=self.gui.telegram_token_var, width=50, validate="focusout", validatecommand=self.gui.highlight_fields)
        self.telegram_token_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.telegram_userid_lbl = Label(self.frame, text='Telegram user_id', justify='left', anchor='w')
        self.telegram_userid_entry = Entry(self.frame, textvariable=self.gui.telegram_userid_var, width=50, validate="focusout", validatecommand=self.gui.highlight_fields)
        self.telegram_userid_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.kakao_auth_token_lbl = Label(self.frame, text='Kakao auth_token', justify='left', anchor='w')
        self.kakao_auth_token_entry = Entry(self.frame, textvariable=self.gui.kakao_auth_token_var, width=35)
        self.kakao_auth_token_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.kakao_get_auth_btn = Button(self.frame, text='Generate', command=self.cb_kakao_get_auth, bootstyle='secondary')

        self.line_cookies_lbl = Label(self.frame, text='Line cookies', width=18, justify='left', anchor='w')
        self.line_cookies_entry = Entry(self.frame, textvariable=self.gui.line_cookies_var, width=35)
        self.line_cookies_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.line_get_auth_btn = Button(self.frame, text='Generate', command=self.cb_line_get_auth, bootstyle='secondary')

        self.help_btn = Button(self.frame, text='Get help', command=self.cb_cred_help, bootstyle='secondary')

        self.signal_uuid_lbl.grid(column=0, row=0, sticky='w', padx=3, pady=3)
        self.signal_uuid_entry.grid(column=1, row=0, columnspan=2, sticky='w', padx=3, pady=3)
        self.signal_password_lbl.grid(column=0, row=1, sticky='w', padx=3, pady=3)
        self.signal_password_entry.grid(column=1, row=1, columnspan=2, sticky='w', padx=3, pady=3)
        self.signal_get_auth_btn.grid(column=2, row=2, sticky='e', padx=3, pady=3)
        self.telegram_token_lbl.grid(column=0, row=3, sticky='w', padx=3, pady=3)
        self.telegram_token_entry.grid(column=1, row=3, columnspan=2, sticky='w', padx=3, pady=3)
        self.telegram_userid_lbl.grid(column=0, row=4, sticky='w', padx=3, pady=3)
        self.telegram_userid_entry.grid(column=1, row=4, columnspan=2, sticky='w', padx=3, pady=3)
        self.kakao_auth_token_lbl.grid(column=0, row=5, sticky='w', padx=3, pady=3)
        self.kakao_auth_token_entry.grid(column=1, row=5, sticky='w', padx=3, pady=3)
        self.kakao_get_auth_btn.grid(column=2, row=5, sticky='e', padx=3, pady=3)
        self.line_cookies_lbl.grid(column=0, row=6, sticky='w', padx=3, pady=3)
        self.line_cookies_entry.grid(column=1, row=6, sticky='w', padx=3, pady=3)
        self.line_get_auth_btn.grid(column=2, row=6, sticky='e', padx=3, pady=3)
        self.help_btn.grid(column=2, row=7, sticky='e', padx=3, pady=3)
    
    def cb_cred_help(self, *args):
        faq_site = 'https://github.com/laggykiller/sticker-convert#faq'
        success = webbrowser.open(faq_site)
        if not success:
            self.gui.cb_ask_str('You can get help from:', initialvalue=faq_site)
    
    def cb_kakao_get_auth(self, *args):
        KakaoGetAuthWindow(self.gui)
    
    def cb_signal_get_auth(self, *args):
        SignalGetAuthWindow(self.gui)
    
    def cb_line_get_auth(self, *args):
        LineGetAuthWindow(self.gui)
    
    def set_states(self, state):
        self.signal_uuid_entry.config(state=state)
        self.signal_password_entry.config(state=state)
        self.signal_get_auth_btn.config(state=state)
        self.telegram_token_entry.config(state=state)
        self.telegram_userid_entry.config(state=state)
        self.kakao_auth_token_entry.config(state=state)
        self.kakao_get_auth_btn.config(state=state)
        self.line_cookies_entry.config(state=state)
        self.line_get_auth_btn.config(state=state)

class ProgressFrame:
    progress_bar_cli = None
    progress_bar_steps = 0
    auto_scroll = True

    def __init__(self, gui):
        self.gui = gui
        self.frame = LabelFrame(self.gui.scrollable_frame, borderwidth=1, text='Progress')

        self.message_box = ScrolledText(self.frame, height=15, wrap='word')
        self.message_box._text.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.message_box._text.config(state='disabled')
        self.progress_bar = Progressbar(self.frame, orient='horizontal', mode='determinate')

        self.message_box.bind('<Enter>', self.cb_disable_autoscroll)
        self.message_box.bind('<Leave>', self.cb_enable_autoscroll)

        self.message_box.pack(expand=True, fill='x')
        self.progress_bar.pack(expand=True, fill='x')
    
    def update_progress_bar(self, set_progress_mode='', steps=0, update_bar=False):
        if update_bar:
            self.progress_bar_cli.update()
            self.progress_bar['value'] += 100 / self.progress_bar_steps
        elif set_progress_mode == 'determinate':
            self.progress_bar_cli = tqdm(total=steps)
            self.progress_bar.config(mode='determinate')
            self.progress_bar_steps = steps
            self.progress_bar.stop()
            self.progress_bar['value'] = 0
        elif set_progress_mode == 'indeterminate':
            if self.progress_bar_cli:
                self.progress_bar_cli.close()
                self.progress_bar_cli = None
            self.progress_bar['value'] = 0
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(50)
        elif set_progress_mode == 'clear':
            if self.progress_bar_cli:
                self.progress_bar_cli.reset()
            self.progress_bar.config(mode='determinate')
            self.progress_bar.stop()
            self.progress_bar['value'] = 0

    def update_message_box(self, *args, **kwargs):
        msg = kwargs.get('msg')
        cls = kwargs.get('cls')

        # scrollbar_prev_loc = self.message_box.yview()[1]

        if not msg and len(args) == 1:
            msg = str(args[0])
        
        if msg:
            if self.progress_bar_cli:
                self.progress_bar_cli.write(msg)
            else:
                print(msg)
            msg += '\n'

        self.message_box._text.config(state='normal')

        if cls:
            self.message_box.delete(1.0, 'end')

        if msg:
            self.message_box.insert('end', msg)

            # Follow the end of the box if it was at the end
            # if scrollbar_prev_loc == 1.0:
            if self.auto_scroll:
                self.message_box._text.yview_moveto(1.0)

        self.message_box._text.config(state='disabled')
    
    def cb_disable_autoscroll(self, *args):
        self.auto_scroll = False
        
    def cb_enable_autoscroll(self, *args):
        self.auto_scroll = True

class ControlFrame:
    def __init__(self, gui):
        self.gui = gui
        self.frame = Frame(self.gui.scrollable_frame, borderwidth=1)

        self.start_btn = Button(self.frame, text='Start', command=self.gui.start)
        
        self.start_btn.pack(expand=True, fill='x')

class KakaoGetAuthWindow:
    def __init__(self, gui):
        self.gui = gui

        self.get_kakao_auth_win = Toplevel(self.gui.root)
        self.get_kakao_auth_win.title('Get Kakao auth_token')
        
        self.icon = PhotoImage(file='resources/appicon.png')
        self.get_kakao_auth_win.iconphoto(1, self.icon)
        if sys.platform == 'darwin':
            self.get_kakao_auth_win.iconbitmap(bitmap='resources/appicon.icns')
        elif sys.platform == 'win32':
            self.get_kakao_auth_win.iconbitmap(bitmap='resources/appicon.ico')
        self.get_kakao_auth_win.tk.call('wm', 'iconphoto', self.get_kakao_auth_win._w, self.icon)
        
        self.get_kakao_auth_win.focus_force()

        self.cb_msg_block_kakao = partial(self.gui.cb_msg_block, parent=self.get_kakao_auth_win)
        self.cb_ask_str_kakao = partial(self.gui.cb_ask_str, parent=self.get_kakao_auth_win)

        self.create_scrollable_frame()

        self.frame_login_info = LabelFrame(self.scrollable_frame, text='Kakao login info')
        self.frame_login_btn = Frame(self.scrollable_frame)

        self.frame_login_info.grid(column=0, row=0, sticky='news', padx=3, pady=3)
        self.frame_login_btn.grid(column=0, row=1, sticky='news', padx=3, pady=3)

        # Login info frame
        self.explanation1_lbl = Label(self.frame_login_info, text='This will simulate login to Android Kakao app', justify='left', anchor='w')
        self.explanation2_lbl = Label(self.frame_login_info, text='You will send / receive verification code via SMS', justify='left', anchor='w')
        self.explanation3_lbl = Label(self.frame_login_info, text='You maybe logged out of existing device', justify='left', anchor='w')

        self.kakao_username_help_btn = Button(self.frame_login_info, text='?', width=1, command=lambda: self.cb_msg_block_kakao(self.gui.help['cred']['kakao_username']), bootstyle='secondary')
        self.kakao_username_lbl = Label(self.frame_login_info, text='Username', width=18, justify='left', anchor='w')
        self.kakao_username_entry = Entry(self.frame_login_info, textvariable=self.gui.kakao_username_var, width=30)
        self.kakao_username_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.kakao_password_help_btn = Button(self.frame_login_info, text='?', width=1, command=lambda: self.cb_msg_block_kakao(self.gui.help['cred']['kakao_password']), bootstyle='secondary')
        self.kakao_password_lbl = Label(self.frame_login_info, text='Password', justify='left', anchor='w')
        self.kakao_password_entry = Entry(self.frame_login_info, textvariable=self.gui.kakao_password_var, width=30)
        self.kakao_password_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.kakao_country_code_help_btn = Button(self.frame_login_info, text='?', width=1, command=lambda: self.cb_msg_block_kakao(self.gui.help['cred']['kakao_country_code']), bootstyle='secondary')
        self.kakao_country_code_lbl = Label(self.frame_login_info, text='Country code', justify='left', anchor='w')
        self.kakao_country_code_entry = Entry(self.frame_login_info, textvariable=self.gui.kakao_country_code_var, width=30)
        self.kakao_country_code_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.kakao_phone_number_help_btn = Button(self.frame_login_info, text='?', width=1, command=lambda: self.cb_msg_block_kakao(self.gui.help['cred']['kakao_phone_number']), bootstyle='secondary')
        self.kakao_phone_number_lbl = Label(self.frame_login_info, text='Phone number', justify='left', anchor='w')
        self.kakao_phone_number_entry = Entry(self.frame_login_info, textvariable=self.gui.kakao_phone_number_var, width=30)
        self.kakao_phone_number_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.explanation1_lbl.grid(column=0, row=0, columnspan=3, sticky='w', padx=3, pady=3)
        self.explanation2_lbl.grid(column=0, row=1, columnspan=3, sticky='w', padx=3, pady=3)
        self.explanation3_lbl.grid(column=0, row=2, columnspan=3, sticky='w', padx=3, pady=3)

        self.kakao_username_help_btn.grid(column=0, row=3, sticky='w', padx=3, pady=3)
        self.kakao_username_lbl.grid(column=1, row=3, sticky='w', padx=3, pady=3)
        self.kakao_username_entry.grid(column=2, row=3, sticky='w', padx=3, pady=3)

        self.kakao_password_help_btn.grid(column=0, row=4, sticky='w', padx=3, pady=3)
        self.kakao_password_lbl.grid(column=1, row=4, sticky='w', padx=3, pady=3)
        self.kakao_password_entry.grid(column=2, row=4, sticky='w', padx=3, pady=3)

        self.kakao_country_code_help_btn.grid(column=0, row=5, sticky='w', padx=3, pady=3)
        self.kakao_country_code_lbl.grid(column=1, row=5, sticky='w', padx=3, pady=3)
        self.kakao_country_code_entry.grid(column=2, row=5, sticky='w', padx=3, pady=3)

        self.kakao_phone_number_help_btn.grid(column=0, row=6, sticky='w', padx=3, pady=3)
        self.kakao_phone_number_lbl.grid(column=1, row=6, sticky='w', padx=3, pady=3)
        self.kakao_phone_number_entry.grid(column=2, row=6, sticky='w', padx=3, pady=3)

        # Login button frame
        self.login_btn = Button(self.frame_login_btn, text='Login and get auth_token', command=self.cb_login)

        self.login_btn.pack()

        self.resize_window()
    
    def create_scrollable_frame(self):
        self.main_frame = Frame(self.get_kakao_auth_win)
        self.main_frame.pack(fill='both', expand=1)

        self.horizontal_scrollbar_frame = Frame(self.main_frame)
        self.horizontal_scrollbar_frame.pack(fill='x', side='bottom')

        self.canvas = Canvas(self.main_frame)
        self.canvas.pack(side='left', fill='both', expand=1)

        self.x_scrollbar = Scrollbar(self.horizontal_scrollbar_frame, orient='horizontal', command=self.canvas.xview)
        self.x_scrollbar.pack(side='bottom', fill='x')

        self.y_scrollbar = Scrollbar(self.main_frame, orient='vertical', command=self.canvas.yview)
        self.y_scrollbar.pack(side='right', fill='y')

        self.canvas.configure(xscrollcommand=self.x_scrollbar.set)
        self.canvas.configure(yscrollcommand=self.y_scrollbar.set)
        self.canvas.bind("<Configure>",lambda e: self.canvas.config(scrollregion= self.canvas.bbox('all'))) 

        self.scrollable_frame = Frame(self.canvas)
        self.canvas.create_window((0,0),window= self.scrollable_frame, anchor="nw")

    def resize_window(self):
        self.scrollable_frame.update_idletasks()
        width = self.scrollable_frame.winfo_width()
        height = self.scrollable_frame.winfo_height()

        screen_width = self.gui.root.winfo_screenwidth()
        screen_height = self.gui.root.winfo_screenwidth()

        if width > screen_width * 0.8:
            width = int(screen_width * 0.8)
        if height > screen_height * 0.8:
            height = int(screen_height * 0.8)

        self.canvas.configure(width=width, height=height)
    
    def cb_login(self):
        Thread(target=self.cb_login_thread, daemon=True).start()
    
    def cb_login_thread(self, *args):
        self.gui.save_creds()
        m = GetKakaoAuth(opt_cred=self.gui.creds, cb_msg=self.gui.cb_msg, cb_msg_block=self.cb_msg_block_kakao, cb_ask_str=self.cb_ask_str_kakao)

        auth_token = m.get_cred()

        if auth_token:
            self.gui.creds['kakao']['auth_token'] = auth_token
            self.gui.kakao_auth_token_var.set(auth_token)
        
            self.cb_msg_block_kakao(f'Got auth_token successfully: {auth_token}')
            self.gui.save_creds()
            self.gui.highlight_fields()
        else:
            self.cb_msg_block_kakao('Failed to get auth_token')

class SignalGetAuthWindow:
    def __init__(self, gui):
        self.gui = gui

        self.get_signal_auth_win = Toplevel(self.gui.root)
        self.get_signal_auth_win.title('Get Signal uuid and password')
        
        self.icon = PhotoImage(file='resources/appicon.png')
        self.get_signal_auth_win.iconphoto(1, self.icon)
        if sys.platform == 'darwin':
            self.get_signal_auth_win.iconbitmap(bitmap='resources/appicon.icns')
        elif sys.platform == 'win32':
            self.get_signal_auth_win.iconbitmap(bitmap='resources/appicon.ico')
        self.get_signal_auth_win.tk.call('wm', 'iconphoto', self.get_signal_auth_win._w, self.icon)
        
        self.get_signal_auth_win.focus_force()

        self.cb_msg_block_signal = partial(self.gui.cb_msg_block, parent=self.get_signal_auth_win)
        self.cb_ask_str_signal = partial(self.gui.cb_ask_str, parent=self.get_signal_auth_win)

        self.create_scrollable_frame()

        self.frame_info = Frame(self.scrollable_frame)
        self.frame_start_btn = Frame(self.scrollable_frame)

        self.frame_info.grid(column=0, row=0, sticky='news', padx=3, pady=3)
        self.frame_start_btn.grid(column=0, row=1, sticky='news', padx=3, pady=3)

        # Info frame
        self.explanation1_lbl = Label(self.frame_info, text='Please install Signal Desktop BETA VERSION', justify='left', anchor='w')
        self.explanation2_lbl = Label(self.frame_info, text='After installation, you need to login to Signal Desktop', justify='left', anchor='w')
        self.explanation3_lbl = Label(self.frame_info, text='uuid and password will be automatically fetched', justify='left', anchor='w')

        self.explanation1_lbl.grid(column=0, row=0, columnspan=3, sticky='w', padx=3, pady=3)
        self.explanation2_lbl.grid(column=0, row=1, columnspan=3, sticky='w', padx=3, pady=3)
        self.explanation3_lbl.grid(column=0, row=2, columnspan=3, sticky='w', padx=3, pady=3)

        # Start button frame
        self.login_btn = Button(self.frame_start_btn, text='Get uuid and password', command=self.cb_login)

        self.login_btn.pack()

        self.resize_window()
    
    def create_scrollable_frame(self):
        self.main_frame = Frame(self.get_signal_auth_win)
        self.main_frame.pack(fill='both', expand=1)

        self.horizontal_scrollbar_frame = Frame(self.main_frame)
        self.horizontal_scrollbar_frame.pack(fill='x', side='bottom')

        self.canvas = Canvas(self.main_frame)
        self.canvas.pack(side='left', fill='both', expand=1)

        self.x_scrollbar = Scrollbar(self.horizontal_scrollbar_frame, orient='horizontal', command=self.canvas.xview)
        self.x_scrollbar.pack(side='bottom', fill='x')

        self.y_scrollbar = Scrollbar(self.main_frame, orient='vertical', command=self.canvas.yview)
        self.y_scrollbar.pack(side='right', fill='y')

        self.canvas.configure(xscrollcommand=self.x_scrollbar.set)
        self.canvas.configure(yscrollcommand=self.y_scrollbar.set)
        self.canvas.bind("<Configure>",lambda e: self.canvas.config(scrollregion= self.canvas.bbox('all'))) 

        self.scrollable_frame = Frame(self.canvas)
        self.canvas.create_window((0,0),window= self.scrollable_frame, anchor="nw")

    def resize_window(self):
        self.scrollable_frame.update_idletasks()
        width = self.scrollable_frame.winfo_width()
        height = self.scrollable_frame.winfo_height()

        screen_width = self.gui.root.winfo_screenwidth()
        screen_height = self.gui.root.winfo_screenwidth()

        if width > screen_width * 0.8:
            width = int(screen_width * 0.8)
        if height > screen_height * 0.8:
            height = int(screen_height * 0.8)

        self.canvas.configure(width=width, height=height)
    
    def cb_login(self):
        Thread(target=self.cb_login_thread, daemon=True).start()
    
    def cb_login_thread(self, *args):
        m = GetSignalAuth(cb_msg=self.gui.cb_msg, cb_ask_str=self.cb_ask_str_signal)

        uuid, password = None, None
        while Toplevel.winfo_exists(self.get_signal_auth_win):
            uuid, password = m.get_cred()

            if uuid and password:
                self.gui.creds['signal']['uuid'] = uuid
                self.gui.creds['signal']['password'] = password
                self.gui.signal_uuid_var.set(uuid)
                self.gui.signal_password_var.set(password)
                
                self.cb_msg_block_signal(f'Got uuid and password successfully:\nuuid={uuid}\npassword={password}')
                self.gui.save_creds()
                self.gui.highlight_fields()
                return
            
        self.cb_msg_block_signal('Failed to get uuid and password')

class LineGetAuthWindow:
    def __init__(self, gui):
        self.gui = gui

        self.get_line_auth_win = Toplevel(self.gui.root)
        self.get_line_auth_win.title('Get Line cookie')
        
        self.icon = PhotoImage(file='resources/appicon.png')
        self.get_line_auth_win.iconphoto(1, self.icon)
        if sys.platform == 'darwin':
            self.get_line_auth_win.iconbitmap(bitmap='resources/appicon.icns')
        elif sys.platform == 'win32':
            self.get_line_auth_win.iconbitmap(bitmap='resources/appicon.ico')
        self.get_line_auth_win.tk.call('wm', 'iconphoto', self.get_line_auth_win._w, self.icon)
        
        self.get_line_auth_win.focus_force()

        self.cb_msg_block_line = partial(self.gui.cb_msg_block, parent=self.get_line_auth_win)

        self.create_scrollable_frame()

        self.frame_info = Frame(self.scrollable_frame)
        self.frame_btn = Frame(self.scrollable_frame)

        self.frame_info.grid(column=0, row=0, sticky='news', padx=3, pady=3)
        self.frame_btn.grid(column=0, row=1, sticky='news', padx=3, pady=3)

        # Info frame
        self.explanation1_lbl = Label(self.frame_info, text='Line cookies are required to create custom message stickers', justify='left', anchor='w')
        self.explanation2_lbl = Label(self.frame_info, text='Please open web browser and login to Line', justify='left', anchor='w')
        self.explanation3_lbl = Label(self.frame_info, text='After that, press "Get cookies"', justify='left', anchor='w')

        self.explanation1_lbl.grid(column=0, row=0, columnspan=3, sticky='w', padx=3, pady=3)
        self.explanation2_lbl.grid(column=0, row=1, columnspan=3, sticky='w', padx=3, pady=3)
        self.explanation3_lbl.grid(column=0, row=2, columnspan=3, sticky='w', padx=3, pady=3)

        # Buttons frame
        self.open_browser_btn = Button(self.frame_btn, text='Open browser', command=self.cb_open_browser)
        self.get_cookies_btn = Button(self.frame_btn, text='Get cookies', command=self.cb_get_cookies)

        self.open_browser_btn.pack()
        self.get_cookies_btn.pack()

        self.resize_window()
    
    def create_scrollable_frame(self):
        self.main_frame = Frame(self.get_line_auth_win)
        self.main_frame.pack(fill='both', expand=1)

        self.horizontal_scrollbar_frame = Frame(self.main_frame)
        self.horizontal_scrollbar_frame.pack(fill='x', side='bottom')

        self.canvas = Canvas(self.main_frame)
        self.canvas.pack(side='left', fill='both', expand=1)

        self.x_scrollbar = Scrollbar(self.horizontal_scrollbar_frame, orient='horizontal', command=self.canvas.xview)
        self.x_scrollbar.pack(side='bottom', fill='x')

        self.y_scrollbar = Scrollbar(self.main_frame, orient='vertical', command=self.canvas.yview)
        self.y_scrollbar.pack(side='right', fill='y')

        self.canvas.configure(xscrollcommand=self.x_scrollbar.set)
        self.canvas.configure(yscrollcommand=self.y_scrollbar.set)
        self.canvas.bind("<Configure>",lambda e: self.canvas.config(scrollregion= self.canvas.bbox('all'))) 

        self.scrollable_frame = Frame(self.canvas)
        self.canvas.create_window((0,0),window= self.scrollable_frame, anchor="nw")

    def resize_window(self):
        self.scrollable_frame.update_idletasks()
        width = self.scrollable_frame.winfo_width()
        height = self.scrollable_frame.winfo_height()

        screen_width = self.gui.root.winfo_screenwidth()
        screen_height = self.gui.root.winfo_screenwidth()

        if width > screen_width * 0.8:
            width = int(screen_width * 0.8)
        if height > screen_height * 0.8:
            height = int(screen_height * 0.8)

        self.canvas.configure(width=width, height=height)
    
    def cb_open_browser(self):
        line_login_site = 'https://store.line.me/login'
        success = webbrowser.open(line_login_site)
        if not success:
            self.gui.cb_ask_str('Cannot open web browser for you. Install web browser and open:', initialvalue=line_login_site)
    
    def cb_get_cookies(self):
        Thread(target=self.cb_get_cookies_thread, daemon=True).start()
    
    def cb_get_cookies_thread(self, *args):
        m = GetLineAuth()

        line_cookies = None
        line_cookies = m.get_cred()

        if line_cookies:
            self.gui.creds['line']['cookies'] = line_cookies
            self.gui.line_cookies_var.set(line_cookies)
            
            self.cb_msg_block_line(f'Got Line cookies successfully')
            self.gui.save_creds()
            self.gui.highlight_fields()
            return
            
        self.cb_msg_block_line('Failed to get Line cookies. Have you logged in the web browser?')

class AdvancedCompressionWindow:
    emoji_column_per_row = 10
    emoji_visible_rows = 5
    emoji_btns = []

    def __init__(self, gui):
        self.gui = gui
        self.categories = list({entry['category'] for entry in self.gui.emoji_list})

        self.adv_comp_win = Toplevel(self.gui.root)
        self.adv_comp_win.title('Advanced compression options')

        self.icon = PhotoImage(file='resources/appicon.png')
        self.adv_comp_win.iconphoto(1, self.icon)
        if sys.platform == 'darwin':
            self.adv_comp_win.iconbitmap(bitmap='resources/appicon.icns')
        elif sys.platform == 'win32':
            self.adv_comp_win.iconbitmap(bitmap='resources/appicon.ico')
        self.adv_comp_win.tk.call('wm', 'iconphoto', self.adv_comp_win._w, self.icon)
        
        self.adv_comp_win.focus_force()

        if sys.platform.startswith('win32') or sys.platform.startswith('cygwin'):
            self.mousewheel = ('<MouseWheel>',)
            self.delta_divide = 120
        elif sys.platform.startswith('darwin'):
            self.mousewheel = ('<MouseWheel>',)
            self.delta_divide = 1
        else:
            self.mousewheel = ('<Button-4>', '<Button-5>')
            self.delta_divide = 120

        self.create_scrollable_frame()

        self.frame_advcomp = LabelFrame(self.scrollable_frame, text='Advanced compression option')
        self.frame_emoji_search = LabelFrame(self.scrollable_frame, text='Setting default emoji')
        self.frame_emoji_canvas = Frame(self.scrollable_frame)

        self.frame_advcomp.grid_columnconfigure(6, weight=1)

        cb_msg_block_adv_comp_win = partial(self.gui.cb_msg_block, parent=self.adv_comp_win)

        self.fps_help_btn = Button(self.frame_advcomp, text='?', width=1, command=lambda: cb_msg_block_adv_comp_win(self.gui.help['comp']['fps']), bootstyle='secondary')
        self.fps_lbl = Label(self.frame_advcomp, text='Output FPS')
        self.fps_min_lbl = Label(self.frame_advcomp, text='Min:')
        self.fps_min_entry = Entry(self.frame_advcomp, textvariable=self.gui.fps_min_var, width=8)
        self.fps_min_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.fps_max_lbl = Label(self.frame_advcomp, text='Max:')
        self.fps_max_entry = Entry(self.frame_advcomp, textvariable=self.gui.fps_max_var, width=8)
        self.fps_max_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.fps_disable_cbox = Checkbutton(self.frame_advcomp, text="X", variable=self.gui.fps_disable_var, command=self.cb_disable_fps, onvalue=True, offvalue=False, bootstyle='danger-round-toggle')

        self.res_w_help_btn = Button(self.frame_advcomp, text='?', width=1, command=lambda: cb_msg_block_adv_comp_win(self.gui.help['comp']['res']), bootstyle='secondary')
        self.res_w_lbl = Label(self.frame_advcomp, text='Output resolution (Width)')
        self.res_w_min_lbl = Label(self.frame_advcomp, text='Min:')
        self.res_w_min_entry = Entry(self.frame_advcomp, textvariable=self.gui.res_w_min_var, width=8)
        self.res_w_min_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.res_w_max_lbl = Label(self.frame_advcomp, text='Max:')
        self.res_w_max_entry = Entry(self.frame_advcomp, textvariable=self.gui.res_w_max_var, width=8)
        self.res_w_max_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.res_w_disable_cbox = Checkbutton(self.frame_advcomp, text="X", variable=self.gui.res_w_disable_var, command=self.cb_disable_res_w, onvalue=True, offvalue=False, bootstyle='danger-round-toggle')
        
        self.res_h_help_btn = Button(self.frame_advcomp, text='?', width=1, command=lambda: cb_msg_block_adv_comp_win(self.gui.help['comp']['res']), bootstyle='secondary')
        self.res_h_lbl = Label(self.frame_advcomp, text='Output resolution (Height)')
        self.res_h_min_lbl = Label(self.frame_advcomp, text='Min:')
        self.res_h_min_entry = Entry(self.frame_advcomp, textvariable=self.gui.res_h_min_var, width=8)
        self.res_h_min_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.res_h_max_lbl = Label(self.frame_advcomp, text='Max:')
        self.res_h_max_entry = Entry(self.frame_advcomp, textvariable=self.gui.res_h_max_var, width=8)
        self.res_h_max_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.res_h_disable_cbox = Checkbutton(self.frame_advcomp, text="X", variable=self.gui.res_h_disable_var, command=self.cb_disable_res_h, onvalue=True, offvalue=False, bootstyle='danger-round-toggle')

        self.quality_help_btn = Button(self.frame_advcomp, text='?', width=1, command=lambda: cb_msg_block_adv_comp_win(self.gui.help['comp']['quality']), bootstyle='secondary')
        self.quality_lbl = Label(self.frame_advcomp, text='Output quality (0-100)')
        self.quality_min_lbl = Label(self.frame_advcomp, text='Min:')
        self.quality_min_entry = Entry(self.frame_advcomp, textvariable=self.gui.quality_min_var, width=8)
        self.quality_min_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.quality_max_lbl = Label(self.frame_advcomp, text='Max:')
        self.quality_max_entry = Entry(self.frame_advcomp, textvariable=self.gui.quality_max_var, width=8)
        self.quality_max_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.quality_disable_cbox = Checkbutton(self.frame_advcomp, text="X", variable=self.gui.quality_disable_var, command=self.cb_disable_quality, onvalue=True, offvalue=False, bootstyle='danger-round-toggle')

        self.color_help_btn = Button(self.frame_advcomp, text='?', width=1, command=lambda: cb_msg_block_adv_comp_win(self.gui.help['comp']['color']), bootstyle='secondary')
        self.color_lbl = Label(self.frame_advcomp, text='Colors (0-256)')
        self.color_min_lbl = Label(self.frame_advcomp, text='Min:')
        self.color_min_entry = Entry(self.frame_advcomp, textvariable=self.gui.color_min_var, width=8)
        self.color_min_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.color_max_lbl = Label(self.frame_advcomp, text='Max:')
        self.color_max_entry = Entry(self.frame_advcomp, textvariable=self.gui.color_max_var, width=8)
        self.color_max_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.color_disable_cbox = Checkbutton(self.frame_advcomp, text="X", variable=self.gui.color_disable_var, command=self.cb_disable_color, onvalue=True, offvalue=False, bootstyle='danger-round-toggle')

        self.duration_help_btn = Button(self.frame_advcomp, text='?', width=1, command=lambda: cb_msg_block_adv_comp_win(self.gui.help['comp']['duration']), bootstyle='secondary')
        self.duration_lbl = Label(self.frame_advcomp, text='Duration (Miliseconds)')
        self.duration_min_lbl = Label(self.frame_advcomp, text='Min:')
        self.duration_min_entry = Entry(self.frame_advcomp, textvariable=self.gui.duration_min_var, width=8)
        self.duration_min_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.duration_max_lbl = Label(self.frame_advcomp, text='Max:')
        self.duration_max_entry = Entry(self.frame_advcomp, textvariable=self.gui.duration_max_var, width=8)
        self.duration_max_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.duration_disable_cbox = Checkbutton(self.frame_advcomp, text="X", variable=self.gui.duration_disable_var, command=self.cb_disable_duration, onvalue=True, offvalue=False, bootstyle='danger-round-toggle')

        self.size_help_btn = Button(self.frame_advcomp, text='?', width=1, command=lambda: cb_msg_block_adv_comp_win(self.gui.help['comp']['size']), bootstyle='secondary')
        self.size_lbl = Label(self.frame_advcomp, text='Maximum file size (bytes)')
        self.img_size_max_lbl = Label(self.frame_advcomp, text='Img:')
        self.img_size_max_entry = Entry(self.frame_advcomp, textvariable=self.gui.img_size_max_var, width=8)
        self.img_size_max_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.vid_size_max_lbl = Label(self.frame_advcomp, text='Vid:')
        self.vid_size_max_entry = Entry(self.frame_advcomp, textvariable=self.gui.vid_size_max_var, width=8)
        self.vid_size_max_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.size_disable_cbox = Checkbutton(self.frame_advcomp, text="X", variable=self.gui.size_disable_var, command=self.cb_disable_size, onvalue=True, offvalue=False, bootstyle='danger-round-toggle')

        self.format_help_btn = Button(self.frame_advcomp, text='?', width=1, command=lambda: cb_msg_block_adv_comp_win(self.gui.help['comp']['format']), bootstyle='secondary')
        self.format_lbl = Label(self.frame_advcomp, text='File format')
        self.img_format_lbl = Label(self.frame_advcomp, text='Img:')
        self.img_format_entry = Entry(self.frame_advcomp, textvariable=self.gui.img_format_var, width=8)
        self.img_format_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)
        self.vid_format_lbl = Label(self.frame_advcomp, text='Vid:')
        self.vid_format_entry = Entry(self.frame_advcomp, textvariable=self.gui.vid_format_var, width=8)
        self.vid_format_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.fake_vid_help_btn = Button(self.frame_advcomp, text='?', width=1, command=lambda: cb_msg_block_adv_comp_win(self.gui.help['comp']['fake_vid']), bootstyle='secondary')
        self.fake_vid_lbl = Label(self.frame_advcomp, text='Convert (faking) image to video')
        self.fake_vid_cbox = Checkbutton(self.frame_advcomp, variable=self.gui.fake_vid_var, onvalue=True, offvalue=False, bootstyle='success-round-toggle')

        self.cache_dir_help_btn = Button(self.frame_advcomp, text='?', width=1, command=lambda: cb_msg_block_adv_comp_win(self.gui.help['comp']['cache_dir']), bootstyle='secondary')
        self.cache_dir_lbl = Label(self.frame_advcomp, text='Custom cache directory')
        self.cache_dir_entry = Entry(self.frame_advcomp, textvariable=self.gui.cache_dir_var, width=30)
        self.cache_dir_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.default_emoji_help_btn = Button(self.frame_advcomp, text='?', width=1, command=lambda: cb_msg_block_adv_comp_win(self.gui.help['comp']['default_emoji']), bootstyle='secondary')
        self.default_emoji_lbl = Label(self.frame_advcomp, text='Default emoji')
        self.im = Image.new("RGBA", (32, 32), (255,255,255,0))
        self.ph_im = ImageTk.PhotoImage(self.im)
        self.default_emoji_dsp = Label(self.frame_advcomp, image=self.ph_im)

        self.fps_help_btn.grid(column=0, row=2, sticky='w', padx=3, pady=3)
        self.fps_lbl.grid(column=1, row=2, sticky='w', padx=3, pady=3)
        self.fps_min_lbl.grid(column=2, row=2, sticky='w', padx=3, pady=3)
        self.fps_min_entry.grid(column=3, row=2, sticky='nes', padx=3, pady=3)
        self.fps_max_lbl.grid(column=4, row=2, sticky='w', padx=3, pady=3)
        self.fps_max_entry.grid(column=5, row=2, sticky='nes', padx=3, pady=3)
        self.fps_disable_cbox.grid(column=6, row=2, sticky='nes', padx=3, pady=3)

        self.res_w_help_btn.grid(column=0, row=3, sticky='w', padx=3, pady=3)
        self.res_w_lbl.grid(column=1, row=3, sticky='w', padx=3, pady=3)
        self.res_w_min_lbl.grid(column=2, row=3, sticky='w', padx=3, pady=3)
        self.res_w_min_entry.grid(column=3, row=3, sticky='nes', padx=3, pady=3)
        self.res_w_max_lbl.grid(column=4, row=3, sticky='w', padx=3, pady=3)
        self.res_w_max_entry.grid(column=5, row=3, sticky='nes', padx=3, pady=3)
        self.res_w_disable_cbox.grid(column=6, row=3, sticky='nes', padx=3, pady=3)

        self.res_h_help_btn.grid(column=0, row=4, sticky='w', padx=3, pady=3)
        self.res_h_lbl.grid(column=1, row=4, sticky='w', padx=3, pady=3)
        self.res_h_min_lbl.grid(column=2, row=4, sticky='w', padx=3, pady=3)
        self.res_h_min_entry.grid(column=3, row=4, sticky='nes', padx=3, pady=3)
        self.res_h_max_lbl.grid(column=4, row=4, sticky='w', padx=3, pady=3)
        self.res_h_max_entry.grid(column=5, row=4, sticky='nes', padx=3, pady=3)
        self.res_h_disable_cbox.grid(column=6, row=4, sticky='nes', padx=3, pady=3)

        self.quality_help_btn.grid(column=0, row=5, sticky='w', padx=3, pady=3)
        self.quality_lbl.grid(column=1, row=5, sticky='w', padx=3, pady=3)
        self.quality_min_lbl.grid(column=2, row=5, sticky='w', padx=3, pady=3)
        self.quality_min_entry.grid(column=3, row=5, sticky='nes', padx=3, pady=3)
        self.quality_max_lbl.grid(column=4, row=5, sticky='w', padx=3, pady=3)
        self.quality_max_entry.grid(column=5, row=5, sticky='nes', padx=3, pady=3)
        self.quality_disable_cbox.grid(column=6, row=5, sticky='nes', padx=3, pady=3)

        self.color_help_btn.grid(column=0, row=6, sticky='w', padx=3, pady=3)
        self.color_lbl.grid(column=1, row=6, sticky='w', padx=3, pady=3)
        self.color_min_lbl.grid(column=2, row=6, sticky='w', padx=3, pady=3)
        self.color_min_entry.grid(column=3, row=6, sticky='nes', padx=3, pady=3)
        self.color_max_lbl.grid(column=4, row=6, sticky='w', padx=3, pady=3)
        self.color_max_entry.grid(column=5, row=6, sticky='nes', padx=3, pady=3)
        self.color_disable_cbox.grid(column=6, row=6, sticky='nes', padx=3, pady=3)

        self.duration_help_btn.grid(column=0, row=7, sticky='w', padx=3, pady=3)
        self.duration_lbl.grid(column=1, row=7, sticky='w', padx=3, pady=3)
        self.duration_min_lbl.grid(column=2, row=7, sticky='w', padx=3, pady=3)
        self.duration_min_entry.grid(column=3, row=7, sticky='nes', padx=3, pady=3)
        self.duration_max_lbl.grid(column=4, row=7, sticky='w', padx=3, pady=3)
        self.duration_max_entry.grid(column=5, row=7, sticky='nes', padx=3, pady=3)
        self.duration_disable_cbox.grid(column=6, row=7, sticky='nes', padx=3, pady=3)

        self.size_help_btn.grid(column=0, row=8, sticky='w', padx=3, pady=3)
        self.size_lbl.grid(column=1, row=8, sticky='w', padx=3, pady=3)
        self.img_size_max_lbl.grid(column=2, row=8, sticky='w', padx=3, pady=3)
        self.img_size_max_entry.grid(column=3, row=8, sticky='nes', padx=3, pady=3)
        self.vid_size_max_lbl.grid(column=4, row=8, sticky='w', padx=3, pady=3)
        self.vid_size_max_entry.grid(column=5, row=8, sticky='nes', padx=3, pady=3)
        self.size_disable_cbox.grid(column=6, row=8, sticky='nes', padx=3, pady=3)

        self.format_help_btn.grid(column=0, row=9, sticky='w', padx=3, pady=3)
        self.format_lbl.grid(column=1, row=9, sticky='w', padx=3, pady=3)
        self.img_format_lbl.grid(column=2, row=9, sticky='w', padx=3, pady=3)
        self.img_format_entry.grid(column=3, row=9, sticky='nes', padx=3, pady=3)
        self.vid_format_lbl.grid(column=4, row=9, sticky='w', padx=3, pady=3)
        self.vid_format_entry.grid(column=5, row=9, sticky='nes', padx=3, pady=3)

        self.fake_vid_help_btn.grid(column=0, row=10, sticky='w', padx=3, pady=3)
        self.fake_vid_lbl.grid(column=1, row=10, sticky='w', padx=3, pady=3)
        self.fake_vid_cbox.grid(column=6, row=10, sticky='nes', padx=3, pady=3)

        self.cache_dir_help_btn.grid(column=0, row=11, sticky='w', padx=3, pady=3)
        self.cache_dir_lbl.grid(column=1, row=11, sticky='w', padx=3, pady=3)
        self.cache_dir_entry.grid(column=2, row=11, columnspan=4, sticky='nes', padx=3, pady=3)

        self.default_emoji_help_btn.grid(column=0, row=12, sticky='w', padx=3, pady=3)
        self.default_emoji_lbl.grid(column=1, row=12, sticky='w', padx=3, pady=3)
        self.default_emoji_dsp.grid(column=6, row=12, sticky='nes', padx=3, pady=3)

        # https://stackoverflow.com/questions/43731784/tkinter-canvas-scrollbar-with-grid
        # Create a frame for the canvas with non-zero row&column weights
        self.frame_emoji_canvas.grid_rowconfigure(0, weight=1)
        self.frame_emoji_canvas.grid_columnconfigure(0, weight=1)
        # Set grid_propagate to False to allow buttons resizing later
        self.frame_emoji_canvas.grid_propagate(False)

        self.frame_advcomp.grid(column=0, row=0, sticky='news', padx=3, pady=3)
        self.frame_emoji_search.grid(column=0, row=1, sticky='news', padx=3, pady=3)
        self.frame_emoji_canvas.grid(column=0, row=2, sticky='news', padx=3, pady=3)

        self.categories_lbl = Label(self.frame_emoji_search, text='Category', width=15, justify='left', anchor='w')
        self.categories_var = StringVar(self.scrollable_frame)
        self.categories_var.set('Smileys & Emotion')
        self.categories_opt = OptionMenu(self.frame_emoji_search, self.categories_var, 'Smileys & Emotion', *self.categories, command=self.render_emoji_list, bootstyle='secondary')
        self.categories_opt.config(width=30)

        self.search_lbl = Label(self.frame_emoji_search, text='Search')
        self.search_var = StringVar(self.frame_emoji_search)
        self.search_var.trace("w", self.render_emoji_list)
        self.search_entry = Entry(self.frame_emoji_search, textvariable=self.search_var)
        self.search_entry.bind('<Button-3><ButtonRelease-3>', RightClicker)

        self.categories_lbl.grid(column=0, row=0, sticky='nsw', padx=3, pady=3)
        self.categories_opt.grid(column=1, row=0, sticky='news', padx=3, pady=3)
        self.search_lbl.grid(column=0, row=1, sticky='nsw', padx=3, pady=3)
        self.search_entry.grid(column=1, row=1, sticky='news', padx=3, pady=3)

        # Add a canvas in frame_emoji_canvas
        self.emoji_canvas = Canvas(self.frame_emoji_canvas)
        self.emoji_canvas.grid(row=0, column=0, sticky='news')

        # Link a scrollbar to the canvas
        self.vsb = Scrollbar(self.frame_emoji_canvas, orient="vertical", command=self.emoji_canvas.yview)
        self.vsb.grid(row=0, column=1, sticky='ns')
        self.emoji_canvas.configure(yscrollcommand=self.vsb.set)

        self.frame_buttons = Frame(self.emoji_canvas)
        self.emoji_canvas.create_window((0, 0), window=self.frame_buttons, anchor='nw')

        self.render_emoji_list()

        self.set_emoji_btn()
        self.cb_disable_fps()
        self.cb_disable_res_w()
        self.cb_disable_res_h()
        self.cb_disable_quality()
        self.cb_disable_color()
        self.cb_disable_duration()
        self.cb_disable_size()
        self.resize_window()
    
    def create_scrollable_frame(self):
        self.main_frame = Frame(self.adv_comp_win)
        self.main_frame.pack(fill='both', expand=1)

        self.horizontal_scrollbar_frame = Frame(self.main_frame)
        self.horizontal_scrollbar_frame.pack(fill='x', side='bottom')

        self.canvas = Canvas(self.main_frame)
        self.canvas.pack(side='left', fill='both', expand=1)

        self.x_scrollbar = Scrollbar(self.horizontal_scrollbar_frame, orient='horizontal', command=self.canvas.xview)
        self.x_scrollbar.pack(side='bottom', fill='x')

        self.y_scrollbar = Scrollbar(self.main_frame, orient='vertical', command=self.canvas.yview)
        self.y_scrollbar.pack(side='right', fill='y')

        self.canvas.configure(xscrollcommand=self.x_scrollbar.set)
        self.canvas.configure(yscrollcommand=self.y_scrollbar.set)
        self.canvas.bind("<Configure>",lambda e: self.canvas.config(scrollregion= self.canvas.bbox('all'))) 

        self.scrollable_frame = Frame(self.canvas)
        self.canvas.create_window((0,0),window= self.scrollable_frame, anchor="nw")
    
    def resize_window(self):
        self.scrollable_frame.update_idletasks()
        width = self.scrollable_frame.winfo_width()
        height = self.scrollable_frame.winfo_height()

        screen_width = self.gui.root.winfo_screenwidth()
        screen_height = self.gui.root.winfo_screenwidth()

        if width > screen_width * 0.8:
            width = int(screen_width * 0.8)
        if height > screen_height * 0.8:
            height = int(screen_height * 0.8)

        self.canvas.configure(width=width, height=height)
    
    def cb_disable_fps(self, *args):
        if self.gui.fps_disable_var.get() == True:
            state = 'disabled'
        else:
            state = 'normal'

        self.fps_min_entry.config(state=state)
        self.fps_max_entry.config(state=state)

    def cb_disable_res_w(self, *args):
        if self.gui.res_w_disable_var.get() == True:
            state = 'disabled'
        else:
            state = 'normal'

        self.res_w_min_entry.config(state=state)
        self.res_w_max_entry.config(state=state)

    def cb_disable_res_h(self, *args):
        if self.gui.res_h_disable_var.get() == True:
            state = 'disabled'
        else:
            state = 'normal'

        self.res_h_min_entry.config(state=state)
        self.res_h_max_entry.config(state=state)

    def cb_disable_quality(self, *args):
        if self.gui.quality_disable_var.get() == True:
            state = 'disabled'
        else:
            state = 'normal'

        self.quality_min_entry.config(state=state)
        self.quality_max_entry.config(state=state)

    def cb_disable_color(self, *args):
        if self.gui.color_disable_var.get() == True:
            state = 'disabled'
        else:
            state = 'normal'

        self.color_min_entry.config(state=state)
        self.color_max_entry.config(state=state)

    def cb_disable_duration(self, *args):
        if self.gui.duration_disable_var.get() == True:
            state = 'disabled'
        else:
            state = 'normal'

        self.duration_min_entry.config(state=state)
        self.duration_max_entry.config(state=state)

    def cb_disable_size(self, *args):
        if self.gui.size_disable_var.get() == True:
            state = 'disabled'
        else:
            state = 'normal'

        self.img_size_max_entry.config(state=state)
        self.vid_size_max_entry.config(state=state)
    
    def set_emoji_btn(self):
        self.im = Image.new("RGBA", (128, 128), (255,255,255,0))
        ImageDraw.Draw(self.im).text((0, 0), self.gui.default_emoji_var.get(), embedded_color=True, font=self.gui.emoji_font)
        self.im = self.im.resize((32, 32))
        self.ph_im = ImageTk.PhotoImage(self.im)
        self.default_emoji_dsp.config(image=self.ph_im)
    
    def render_emoji_list(self, *args):
        category = self.categories_var.get()
        
        for emoji_btn, ph_im in self.emoji_btns:
            emoji_btn.destroy()
            del ph_im
        
        column = 0
        row = 0

        self.emoji_btns = []
        for entry in self.gui.emoji_list:
            # Filtering
            search_term = self.search_var.get().lower()
            emoji = entry['emoji']
            keywords = entry['aliases'] + entry['tags'] + [emoji]
            if search_term == '':
                if entry['category'] != category:
                    continue
            else:
                ok = False

                if search_term in keywords:
                    ok = True
                elif len(search_term) >= 3:
                    for i in keywords:
                        if search_term in i:
                            ok = True

                if ok == False:
                    continue
    
            im = Image.new("RGBA", (196, 196), (255,255,255,0))
            ImageDraw.Draw(im).text((16, 16), emoji, embedded_color=True, font=self.gui.emoji_font)
            im = im.resize((32, 32))
            ph_im = ImageTk.PhotoImage(im)

            button = Button(self.frame_buttons, command=lambda i=emoji: self.cb_set_emoji(i), bootstyle='dark')
            button.config(image=ph_im)
            button.grid(column=column, row=row)

            column += 1

            if column == self.emoji_column_per_row:
                column = 0
                row += 1

            self.emoji_btns.append((button, ph_im))
        
        # Update buttons frames idle tasks to let tkinter calculate buttons sizes
        self.frame_buttons.update_idletasks()

        # Resize the canvas frame to show specified number of buttons and the scrollbar
        if len(self.emoji_btns) > 0:
            in_view_columns_width = self.emoji_btns[0][0].winfo_width() * self.emoji_column_per_row
            in_view_rows_height = self.emoji_btns[0][0].winfo_height() * self.emoji_visible_rows
            self.frame_emoji_canvas.config(width=in_view_columns_width + self.vsb.winfo_width(),
                                height=in_view_rows_height)

        # Set the canvas scrolling region
        self.emoji_canvas.config(scrollregion=self.emoji_canvas.bbox("all"))

        # https://stackoverflow.com/questions/17355902/tkinter-binding-mousewheel-to-scrollbar
        self.emoji_canvas.bind('<Enter>', self.cb_bound_to_mousewheel)
        self.emoji_canvas.bind('<Leave>', self.cb_unbound_to_mousewheel)
    
    def cb_bound_to_mousewheel(self, event):
        for i in self.mousewheel:
            self.emoji_canvas.bind_all(i, self.cb_on_mousewheel)
    
    def cb_unbound_to_mousewheel(self, event):
        for i in self.mousewheel:
            self.emoji_canvas.unbind_all(i)
    
    def cb_on_mousewheel(self, event):
        self.emoji_canvas.yview_scroll(int(-1*(event.delta/self.delta_divide)), "units")

    def cb_set_emoji(self, emoji):
        self.gui.default_emoji_var.set(emoji)
        self.set_emoji_btn()
