from tkinter import LabelFrame, Frame, OptionMenu, Button, Tk, StringVar, BooleanVar, IntVar, filedialog, Entry, Label, messagebox, scrolledtext, Checkbutton, END
from tkinter.ttk import Progressbar
import json
import os
import sys
import shutil
import multiprocessing
from threading import Thread
import webbrowser
from utils.converter import StickerConvert
from utils.format_verify import FormatVerify
from downloaders.download_line import DownloadLine
from downloaders.download_signal import DownloadSignal
from downloaders.download_telegram import DownloadTelegram
from downloaders.download_kakao import DownloadKakao
from uploaders.upload_signal import UploadSignal
from uploaders.upload_telegram import UploadTelegram
from uploaders.compress_wastickers import CompressWastickers

class GUI:
    default_input_mode = 'signal'
    default_output_mode = 'telegram'

    input_tips = {
        'signal': 'Example: https://signal.art/addstickers/#pack_id=xxxxx&pack_key=xxxxx',
        'telegram': 'Example: https://telegram.me/addstickers/xxxxx',
        'line': 'Example: https://store.line.me/stickershop/product/1234/en OR line://shop/detail/1234 OR 1234',
        'kakao': 'Example: https://e.kakao.com/t/xxxxx',
        'local': 'Example: C:/Users/username/Downloads/dir_with_stickers'
    }

    input_options = {
        'signal': 'Download from Signal',
        'telegram': 'Download from Telegram',
        'line': 'Download from Line',
        'kakao': 'Download from Kakao',
        'local': 'From local directory'
    }

    input_address_lbls = {
        'signal': 'URL address',
        'telegram': 'URL address',
        'line': 'URL address / ID',
        'kakao': 'URL address / ID',
        'local': 'URL address'
    }

    output_options = {
        'signal': 'Upload to Signal',
        'telegram': 'Upload to Telegram',
        'whatsapp': 'Compress to .wastickers (WhatsApp)',
        'local': 'Save to local directory only'
    }

    exec_pool = None

    def __init__(self):
        self.load_preset()
        self.initialized = False

        self.root = Tk()
        self.root.eval('tk::PlaceWindow . center')
        self.root.iconbitmap('icon/appicon.ico')
        self.root.title('sticker-convert')

        # Create frames
        self.frame_input = LabelFrame(self.root, borderwidth=1, text='Input')
        self.frame_comp = LabelFrame(self.root, borderwidth=1, text='Compression options')
        self.frame_output = LabelFrame(self.root, borderwidth=1, text='Output')
        self.frame_cred = LabelFrame(self.root, borderwidth=1, text='Credentials')
        self.frame_progress = LabelFrame(self.root, borderwidth=1, text='Progress')
        self.frame_controls = Frame(self.root, borderwidth=1)

        self.frame_input.pack()
        self.frame_comp.pack()
        self.frame_output.pack()
        self.frame_cred.pack()
        self.frame_progress.pack()
        self.frame_controls.pack()

        # Input frame
        self.input_option_lbl = Label(self.frame_input, text='Input source', width=15, justify='left', anchor='w')
        self.input_option_var = StringVar(self.root)
        self.input_option_var.set(self.input_options[self.default_input_mode])
        self.input_option_opt = OptionMenu(self.frame_input, self.input_option_var, *self.input_options.values(), command=self.callback_input_option)
        self.input_option_opt.config(width=32)

        self.input_address_lbl = Label(self.frame_input, text=self.input_address_lbls[self.default_input_mode], width=15, justify='left', anchor='w')
        self.input_address_var = StringVar(self.root)
        self.input_address_var.set('')
        self.input_address_entry = Entry(self.frame_input, textvariable=self.input_address_var, width=60)
        self.input_address_tip = Label(self.frame_input, text=self.input_tips[self.default_input_mode], width=50, height=2, wraplength=350, justify='left', anchor='w')

        self.input_setdir_lbl = Label(self.frame_input, text='Input directory', width=15, justify='left', anchor='w')
        self.input_setdir_var = StringVar(self.root)
        self.input_setdir_var.set('./stickers_input')
        self.input_setdir_entry = Entry(self.frame_input, textvariable=self.input_setdir_var, width=40)
        self.input_setdir_btn = Button(self.frame_input, text='Choose directory...', command=self.callback_set_indir)

        self.input_option_lbl.grid(column=0, row=0, sticky='w')
        self.input_option_opt.grid(column=1, row=0, columnspan=2, sticky='w')
        self.input_address_lbl.grid(column=0, row=1, sticky='w')
        self.input_address_entry.grid(column=1, row=1, columnspan=2, sticky='w')
        self.input_setdir_lbl.grid(column=0, row=2, columnspan=2, sticky='w')
        self.input_setdir_entry.grid(column=1, row=2, sticky='w')
        self.input_setdir_btn.grid(column=2, row=2, sticky='e')
        self.input_address_tip.grid(column=0, row=3, columnspan=3, sticky='w')

        # Compression options frame
        self.comp_preset_var = StringVar(self.root)
        self.comp_preset_var.set(list(self.presets_dict.keys())[0])
        self.comp_preset_opt = OptionMenu(self.frame_comp, self.comp_preset_var, *self.presets_dict.keys(), command=self.callback_comp_apply_preset)
        self.comp_preset_opt.config(width=10)

        self.no_compress_var = BooleanVar()
        self.no_compress_cbox = Checkbutton(self.frame_comp, text="No compression", variable=self.no_compress_var, command=self.callback_nocompress)

        self.fps_min_lbl = Label(self.frame_comp, text='Output FPS (Minimum)')
        self.fps_min_var = IntVar(self.root)
        self.fps_min_entry = Entry(self.frame_comp, textvariable=self.fps_min_var, width=8)
        self.fps_max_lbl = Label(self.frame_comp, text='Output FPS (Maximum)')
        self.fps_max_var = IntVar(self.root)
        self.fps_max_entry = Entry(self.frame_comp, textvariable=self.fps_max_var, width=8)

        self.res_min_lbl = Label(self.frame_comp, text='Output resolution (Minimum)')
        self.res_min_var = IntVar(self.root)
        self.res_min_entry = Entry(self.frame_comp, textvariable=self.res_min_var, width=8)
        self.res_max_lbl = Label(self.frame_comp, text='Output resolution (Maximum)')
        self.res_max_var = IntVar(self.root)
        self.res_max_entry = Entry(self.frame_comp, textvariable=self.res_max_var, width=8)

        self.quality_min_lbl = Label(self.frame_comp, text='Output quality (Minimum)')
        self.quality_min_var = IntVar(self.root)
        self.quality_min_entry = Entry(self.frame_comp, textvariable=self.quality_min_var, width=8)
        self.quality_max_lbl = Label(self.frame_comp, text='Output quality (Maximum)')
        self.quality_max_var = IntVar(self.root)
        self.quality_max_entry = Entry(self.frame_comp, textvariable=self.quality_max_var, width=8)

        self.color_min_lbl = Label(self.frame_comp, text='Colors [apng only] (Minimum)')
        self.color_min_var = IntVar(self.root)
        self.color_min_entry = Entry(self.frame_comp, textvariable=self.color_min_var, width=8)
        self.color_max_lbl = Label(self.frame_comp, text='Colors [apng only] (Maximum)')
        self.color_max_var = IntVar(self.root)
        self.color_max_entry = Entry(self.frame_comp, textvariable=self.color_max_var, width=8)

        self.img_size_max_lbl = Label(self.frame_comp, text='Maximum file size (Static)')
        self.img_size_max_var = IntVar(self.root)
        self.img_size_max_entry = Entry(self.frame_comp, textvariable=self.img_size_max_var, width=8)
        self.vid_size_max_lbl = Label(self.frame_comp, text='Maximum file size (Animated)')
        self.vid_size_max_var = IntVar(self.root)
        self.vid_size_max_entry = Entry(self.frame_comp, textvariable=self.vid_size_max_var, width=8)

        self.img_format_lbl = Label(self.frame_comp, text='File format (Static)')
        self.img_format_var = StringVar(self.root)
        self.img_format_entry = Entry(self.frame_comp, textvariable=self.img_format_var, width=8)
        self.vid_format_lbl = Label(self.frame_comp, text='File format (Animated)')
        self.vid_format_var = StringVar(self.root)
        self.vid_format_entry = Entry(self.frame_comp, textvariable=self.vid_format_var, width=8)

        self.default_emoji_lbl = Label(self.frame_comp, text='Default emoji')
        self.default_emoji_var = StringVar(self.root)
        self.default_emoji_entry = Entry(self.frame_comp, textvariable=self.default_emoji_var, width=8)

        self.steps_lbl = Label(self.frame_comp, text='Number of steps (Higher = Slower but closer to target size)')
        self.steps_var = IntVar(self.root)        
        self.steps_entry = Entry(self.frame_comp, textvariable=self.steps_var, width=8)

        self.processes_lbl = Label(self.frame_comp, text='Number of processes (Higher = Compress faster but consume more resources)')
        self.processes_var = IntVar(self.root)
        self.processes_var.set(multiprocessing.cpu_count())
        self.processes_entry = Entry(self.frame_comp, textvariable=self.processes_var, width=8)

        self.comp_preset_opt.grid(column=0, row=0, columnspan=2, sticky='w')
        self.no_compress_cbox.grid(column=2, row=0, sticky='w')
        self.fps_min_lbl.grid(column=0, row=1, sticky='w')
        self.fps_min_entry.grid(column=1, row=1, sticky='w')
        self.fps_max_lbl.grid(column=2, row=1, sticky='w')
        self.fps_max_entry.grid(column=3, row=1, sticky='w')
        self.res_min_lbl.grid(column=0, row=2, sticky='w')
        self.res_min_entry.grid(column=1, row=2, sticky='w')
        self.res_max_lbl.grid(column=2, row=2, sticky='w')
        self.res_max_entry.grid(column=3, row=2, sticky='w')
        self.quality_min_lbl.grid(column=0, row=3, sticky='w')
        self.quality_min_entry.grid(column=1, row=3, sticky='w')
        self.quality_max_lbl.grid(column=2, row=3, sticky='w')
        self.quality_max_entry.grid(column=3, row=3, sticky='w')
        self.color_min_lbl.grid(column=0, row=4, sticky='w')
        self.color_min_entry.grid(column=1, row=4, sticky='w')
        self.color_max_lbl.grid(column=2, row=4, sticky='w')
        self.color_max_entry.grid(column=3, row=4, sticky='w')
        self.img_size_max_lbl.grid(column=0, row=5, sticky='w')
        self.img_size_max_entry.grid(column=1, row=5, sticky='w')
        self.vid_size_max_lbl.grid(column=2, row=5, sticky='w')
        self.vid_size_max_entry.grid(column=3, row=5, sticky='w')
        self.img_format_lbl.grid(column=0, row=6, sticky='w')
        self.img_format_entry.grid(column=1, row=6, sticky='w')
        self.vid_format_lbl.grid(column=2, row=6, sticky='w')
        self.vid_format_entry.grid(column=3, row=6, sticky='w')
        self.default_emoji_lbl.grid(column=0, row=7, sticky='w')
        self.default_emoji_entry.grid(column=1, row=7, sticky='w')
        self.steps_lbl.grid(column=0, row=8, columnspan=3, sticky='w')
        self.steps_entry.grid(column=3, row=8, sticky='w')
        self.processes_lbl.grid(column=0, row=9, columnspan=3, sticky='w')
        self.processes_entry.grid(column=3, row=9, sticky='w')

        # Output frame
        self.output_options_lbl = Label(self.frame_output, text='Output options', width=15, justify='left', anchor='w')
        self.output_options_var = StringVar(self.root)
        self.output_options_var.set(self.output_options[self.default_output_mode])
        self.output_options_opt = OptionMenu(self.frame_output, self.output_options_var, *self.output_options.values())
        self.output_options_opt.config(width=32)

        self.output_setdir_lbl = Label(self.frame_output, text='Output directory', width=15, justify='left', anchor='w')
        self.output_setdir_var = StringVar(self.root)
        self.output_setdir_var.set('./stickers_output')
        self.output_setdir_entry = Entry(self.frame_output, textvariable=self.output_setdir_var, width=40)
        self.output_setdir_btn = Button(self.frame_output, text='Choose directory...', command=self.callback_set_outdir)

        self.title_lbl = Label(self.frame_output, text='Title')
        self.title_var = StringVar(self.root)
        self.title_entry = Entry(self.frame_output, textvariable=self.title_var, width=60)
        
        self.author_lbl = Label(self.frame_output, text='Author')
        self.author_var = StringVar(self.root)
        self.author_entry = Entry(self.frame_output, textvariable=self.author_var, width=60)

        self.output_options_lbl.grid(column=0, row=0, sticky='w')
        self.output_options_opt.grid(column=1, row=0, columnspan=2, sticky='w')
        self.output_setdir_lbl.grid(column=0, row=1, columnspan=2, sticky='w')
        self.output_setdir_entry.grid(column=1, row=1, sticky='w')
        self.output_setdir_btn.grid(column=2, row=1, sticky='e')
        self.title_lbl.grid(column=0, row=2, sticky='w')
        self.title_entry.grid(column=1, columnspan=2, row=2, sticky='w')
        self.author_lbl.grid(column=0, row=3, sticky='w')
        self.author_entry.grid(column=1, columnspan=2, row=3, sticky='w')

        # Credentials frame
        self.signal_uuid_lbl = Label(self.frame_cred, text='Signal uuid', width=15, justify='left', anchor='w')
        self.signal_uuid_var = StringVar(self.root)
        self.signal_uuid_entry = Entry(self.frame_cred, textvariable=self.signal_uuid_var, width=60)

        self.signal_password_lbl = Label(self.frame_cred, text='Signal password', width=15, justify='left', anchor='w')
        self.signal_password_var = StringVar(self.root)
        self.signal_password_entry = Entry(self.frame_cred, textvariable=self.signal_password_var, width=60)

        self.telegram_token_lbl = Label(self.frame_cred, text='Telegram token', width=15, justify='left', anchor='w')
        self.telegram_token_var = StringVar(self.root)
        self.telegram_token_entry = Entry(self.frame_cred, textvariable=self.telegram_token_var, width=60)

        self.telegram_userid_lbl = Label(self.frame_cred, text='Telegram user_id', width=15, justify='left', anchor='w')
        self.telegram_userid_var = StringVar(self.root)
        self.telegram_userid_entry = Entry(self.frame_cred, textvariable=self.telegram_userid_var, width=60)

        self.cred_help = Button(self.frame_cred, text='Get help', command=self.callback_cred_help)

        self.signal_uuid_lbl.grid(column=0, row=0, sticky='w')
        self.signal_uuid_entry.grid(column=1, row=0, columnspan=2, sticky='w')
        self.signal_password_lbl.grid(column=0, row=1, sticky='w')
        self.signal_password_entry.grid(column=1, row=1, columnspan=2, sticky='w')
        self.telegram_token_lbl.grid(column=0, row=2, sticky='w')
        self.telegram_token_entry.grid(column=1, row=2, columnspan=2, sticky='w')
        self.telegram_userid_lbl.grid(column=0, row=3, sticky='w')
        self.telegram_userid_entry.grid(column=1, row=3, columnspan=2, sticky='w')
        self.cred_help.grid(column=0, row=4, columnspan=2, sticky='w')

        # Progress frame
        self.progress_box = scrolledtext.ScrolledText(self.frame_progress, width=60, height=10, wrap='word')
        self.progress_bar = Progressbar(self.frame_progress, orient='horizontal', mode='determinate', length=500)

        self.progress_box.pack()
        self.progress_bar.pack()

        # Controls frame
        # self.stop_btn = Button(self.frame_controls, text='Stop', width=30, command=self.stop, state='disabled')
        self.start_btn = Button(self.frame_controls, text='Start', width=70, command=self.start)
        
        # self.stop_btn.grid(column=0, row=0)
        # self.start_btn.grid(column=1, row=0)
        self.start_btn.pack()

        self.callback_comp_apply_preset()

        self.initialized = True
        self.load_creds()
        self.callback_nocompress()

        self.root.mainloop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save_creds()
        if self.exec_pool:
            self.exec_pool.terminate()

    def load_preset(self):
        preset_present = os.path.isfile('preset.json')
        if preset_present == False:
            messagebox.showerror(title='sticker-convert', message='Warning: preset.json cannot be found')
            sys.exit()
        else:
            with open('preset.json', encoding='utf-8') as f:
                self.presets_dict = json.load(f)
    
    def load_creds(self):
        if not os.path.isfile('creds.json'):
            self.signal_uuid = ''
            self.signal_password = ''
            self.telegram_token = ''
            self.telegram_userid = ''
            return

        with open('creds.json', encoding='utf-8') as f:
            creds = json.load(f)

        self.signal_uuid_var.set(creds['signal_uuid'])
        self.signal_password_var.set(creds['signal_password'])
        self.telegram_token_var.set(creds['telegram_token'])
        self.telegram_userid_var.set(creds['telegram_userid'])
        
    def save_creds(self):
        creds = {
            'signal_uuid': self.signal_uuid_var.get(),
            'signal_password': self.signal_password_var.get(),
            'telegram_token': self.telegram_token_var.get(),
            'telegram_userid': self.telegram_userid_var.get()
        }
        with open('creds.json', 'w+', encoding='utf-8') as f:
            json.dump(creds, f, indent=4)

    def callback_set_indir(self, *args):
        input_dir = filedialog.askdirectory()
        self.input_setdir_var.set(input_dir)
    
    def callback_set_outdir(self, *args):
        output_dir = filedialog.askdirectory()
        self.output_setdir_var.set(output_dir)
    
    def callback_input_option(self, *args):
        if self.input_option_var.get() == self.input_options['local']:
            self.input_address_entry.config(state='disabled')
            self.input_address_lbl.config(text=self.input_address_lbls['local'])
            self.input_address_tip.config(text=self.input_tips['local'])
        else:
            self.input_address_entry.config(state='normal')
            if self.input_option_var.get() == self.input_options['signal']:
                self.input_address_tip.config(text=self.input_tips['signal'])
                self.input_address_lbl.config(text=self.input_address_lbls['signal'])
            elif self.input_option_var.get() == self.input_options['telegram']:
                self.input_address_tip.config(text=self.input_tips['telegram'])
                self.input_address_lbl.config(text=self.input_address_lbls['telegram'])
            elif self.input_option_var.get() == self.input_options['line']:
                self.input_address_tip.config(text=self.input_tips['line'])
                self.input_address_lbl.config(text=self.input_address_lbls['line'])
            elif self.input_option_var.get() == self.input_options['kakao']:
                self.input_address_tip.config(text=self.input_tips['kakao'])
                self.input_address_lbl.config(text=self.input_address_lbls['kakao'])
    
    def callback_comp_apply_preset(self, *args):
        selection = self.comp_preset_var.get()
        self.fps_min_var.set(self.presets_dict[selection]['fps_min'])
        self.fps_max_var.set(self.presets_dict[selection]['fps_max'])
        self.res_min_var.set(self.presets_dict[selection]['res_min'])
        self.res_max_var.set(self.presets_dict[selection]['res_max'])
        self.quality_min_var.set(self.presets_dict[selection]['quality_min'])
        self.quality_max_var.set(self.presets_dict[selection]['quality_max'])
        self.color_min_var.set(self.presets_dict[selection]['color_min'])
        self.color_max_var.set(self.presets_dict[selection]['color_max'])
        self.img_size_max_var.set(self.presets_dict[selection]['img_size_max'])
        self.vid_size_max_var.set(self.presets_dict[selection]['vid_size_max'])
        self.img_format_var.set(self.presets_dict[selection]['img_format'])
        self.vid_format_var.set(self.presets_dict[selection]['vid_format'])
        self.default_emoji_var.set(self.presets_dict[selection]['default_emoji'])
        self.steps_var.set(self.presets_dict[selection]['steps'])
    
    def callback_nocompress(self, *args):
        if self.no_compress_var.get() == True:
            self.disable_inputs_comp()
        else:
            self.enable_inputs_comp()
        
    def callback_update_progress_bar(self, *args):
        self.progress_bar['value'] += 100 / self.items
    
    def callback_cred_help(self, *args):
        webbrowser.open('https://github.com/laggykiller/sticker-convert#faq')

    def update_progress_box(self, message):
        self.progress_box.config(state='normal')
        self.progress_box.delete(1.0, END)
        self.progress_box.insert(1.0, message)
        self.progress_box.config(state='disabled')
    
    def start(self):
        Thread(target=self.start_process).start()

    def start_process(self):
        self.save_creds()
        self.disable_inputs()
        # self.stop_btn.config(state='normal')
        self.start_btn.config(state='disabled')

        # Sanity checks
        try:
            input_option = self.input_option_var.get()
            output_option = self.output_options_var.get()

            url = self.input_address_var.get()
            input_dir = self.input_setdir_var.get()
            output_dir = self.output_setdir_var.get()

            no_compress = self.no_compress_var.get()
            vid_size_max = self.vid_size_max_var.get()
            img_size_max = self.img_size_max_var.get()
            vid_format = self.vid_format_var.get()
            img_format = self.img_format_var.get()
            fps_min = self.fps_min_var.get()
            fps_max = self.fps_max_var.get()
            res_min = self.res_min_var.get()
            res_max = self.res_max_var.get()
            quality_max = self.quality_max_var.get()
            quality_min = self.quality_min_var.get()
            color_min = self.color_min_var.get()
            color_max = self.color_max_var.get()
            steps = self.steps_var.get()
            default_emoji = self.default_emoji_var.get()
            title = self.title_var.get()
            author = self.author_var.get()
            processes = self.processes_var.get()

            signal_uuid = self.signal_uuid_var.get()
            signal_password = self.signal_password_var.get()
            telegram_token = self.telegram_token_var.get()
            telegram_userid = self.telegram_userid_var.get()
        except:
            self.update_progress_box('Non-numbers found in field(s). Check your input and try again.')
            self.stop()
            return
        
        if input_option != self.input_options['local'] and url == '':
            self.update_progress_box('URL address cannot be empty. If you only want to use local files, choose "Save to local directory only" in "Input source"')
            self.stop()
            return
        
        if (input_option == self.input_options['telegram'] or output_option == self.output_options['telegram']) and telegram_token == '':
            self.update_progress_box('Downloading from and uploading to telegram requires user_id (From real account, not bot account)')
            self.stop()
            return
        
        if output_option == self.output_options['telegram'] and telegram_userid == '':
            self.update_progress_box('Uploading to telegram requires bot token')
            self.stop()
            return
        
        if output_option == self.output_options['signal'] and (signal_uuid == '' or signal_password == ''):
            self.update_progress_box('Uploading to signal requires uuid and password')
            self.stop()
            return
        
        if output_option == self.output_options['telegram'] and title == '':
            self.update_progress_box('Uploading to telegram requires title')
            self.stop()
            return
        
        if output_option == self.output_options['signal'] and (title == '' or author == ''):
            self.update_progress_box('Uploading to signal requires title and author')
            self.stop()
            return
        
        if output_option == self.output_options['whatsapp'] and (title == '' or author == ''):
            self.update_progress_box('Compressing to .wastickers requires title and author')
            self.stop()
            return
        
        if os.path.isdir(input_dir) == False:
            os.makedirs(input_dir)
        
        if os.path.isdir(output_dir) == False:
            os.makedirs(output_dir)
        
        # Download
        self.update_progress_box('Downloading...')
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(50)

        if input_option == self.input_options['signal']:
            DownloadSignal.download_stickers_signal(url, out_dir=input_dir)
        elif input_option == self.input_options['line']:
            DownloadLine.download_stickers_line(url, out_dir=input_dir)
        elif input_option == self.input_options['telegram']:
            DownloadTelegram.download_stickers_telegram(url, out_dir=input_dir, token=telegram_token)
        elif input_option == self.input_options['kakao']:
            DownloadKakao.download_stickers_kakao(url, out_dir=input_dir)

        # Compress
        if vid_format == '.apng':
            self.update_progress_box('Compressing...\nTips: Compressing .apng takes long time. Consider using another format or lowering "--steps"')
        else:
            self.update_progress_box('Compressing...')
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
        self.progress_bar['value'] = 0
        self.items = len(os.listdir(input_dir))
        
        if no_compress == False:
            pool = multiprocessing.Pool(processes=processes)
            for i in os.listdir(input_dir):
                in_f = os.path.join(input_dir, i)

                if os.path.splitext(i)[1] == '.txt':
                    shutil.copy(in_f, os.path.join(output_dir, i))
                    continue

                if FormatVerify.is_anim(in_f):
                    format = vid_format
                else:
                    format = img_format

                out_f = os.path.join(output_dir, os.path.splitext(i)[0] + format)
                
                pool.apply_async(StickerConvert.convert_and_compress_to_size, kwds={'in_f': in_f, 'out_f': out_f, 'vid_size_max': vid_size_max, 'img_size_max': img_size_max, 'res_max': res_max, 'res_min': res_min, 'quality_max': quality_max, 'quality_min': quality_min, 'fps_max': fps_max, 'fps_min': fps_min, 'color_min': color_min, 'color_max': color_max, 'steps': steps}, callback=self.callback_update_progress_bar)

            pool.close()
            pool.join()

        # Export
        self.update_progress_box('Exporting...')
        self.progress_bar['value'] = 0
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(50)
        urls = []
        if output_option == self.output_options['whatsapp']:
            CompressWastickers.compress_wastickers(in_dir=output_dir, out_dir=output_dir, author=author, title=title, res_max=res_max, res_min=res_min, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, steps=steps, default_emoji=default_emoji)
        elif output_option == self.output_options['signal']:
            urls += UploadSignal.upload_stickers_signal(uuid=signal_uuid, password=signal_password, in_dir=output_dir, author=author, title=title, res_max=res_max, res_min=res_min, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, color_min=color_min, color_max=color_max, steps=steps, default_emoji=default_emoji)
        elif output_option == self.output_options['telegram']:
            urls += UploadTelegram.upload_stickers_telegram(token=telegram_token, user_id=telegram_userid, in_dir=output_dir, author=author, title=title, res_max=res_max, res_min=res_min, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, steps=steps, default_emoji=default_emoji)
        
        if urls != []:
            urls_str = 'All done. Stickers uploaded to:\n' + '\n'.join(urls)
            self.update_progress_box(urls_str)
        else:
            self.update_progress_box('All done.')
        
        self.stop()
    
    def stop(self):
        self.progress_bar.stop()
        self.enable_inputs()
        # self.stop_btn.config(state='disabled')
        self.start_btn.config(state='normal')
    
    def disable_inputs_comp(self):
        self.comp_preset_opt.config(state='disabled')
        self.fps_min_entry.config(state='disabled')
        self.fps_max_entry.config(state='disabled')
        self.res_min_entry.config(state='disabled')
        self.res_max_entry.config(state='disabled')
        self.quality_min_entry.config(state='disabled')
        self.quality_max_entry.config(state='disabled')
        self.color_min_entry.config(state='disabled')
        self.color_max_entry.config(state='disabled')
        self.img_size_max_entry.config(state='disabled')
        self.vid_size_max_entry.config(state='disabled')
        self.img_format_entry.config(state='disabled')
        self.vid_format_entry.config(state='disabled')
        self.default_emoji_entry.config(state='disabled')
        self.steps_entry.config(state='disabled')
        self.processes_entry.config(state='disabled')

    def disable_inputs(self):
        self.input_option_opt.config(state='disabled')
        self.input_address_entry.config(state='disabled')
        self.input_setdir_entry.config(state='disabled')
        self.input_setdir_btn.config(state='disabled')
        self.no_compress_cbox.config(state='disabled')
        self.disable_inputs_comp()
        self.title_entry.config(state='disabled')
        self.author_entry.config(state='disabled')
        self.output_options_opt.config(state='disabled')
        self.output_setdir_entry.config(state='disabled')
        self.output_setdir_btn.config(state='disabled')
        self.signal_uuid_entry.config(state='disabled')
        self.signal_password_entry.config(state='disabled')
        self.telegram_token_entry.config(state='disabled')
        self.telegram_userid_entry.config(state='disabled')

    def enable_inputs_comp(self):
        self.comp_preset_opt.config(state='normal')
        self.fps_min_entry.config(state='normal')
        self.fps_max_entry.config(state='normal')
        self.res_min_entry.config(state='normal')
        self.res_max_entry.config(state='normal')
        self.quality_min_entry.config(state='normal')
        self.quality_max_entry.config(state='normal')
        self.color_min_entry.config(state='normal')
        self.color_max_entry.config(state='normal')
        self.img_size_max_entry.config(state='normal')
        self.vid_size_max_entry.config(state='normal')
        self.img_format_entry.config(state='normal')
        self.vid_format_entry.config(state='normal')
        self.default_emoji_entry.config(state='normal')
        self.steps_entry.config(state='normal')
        self.processes_entry.config(state='normal')

    def enable_inputs(self):
        self.input_option_opt.config(state='normal')
        self.input_address_entry.config(state='normal')
        self.input_setdir_entry.config(state='normal')
        self.input_setdir_btn.config(state='normal')
        self.no_compress_cbox.config(state='normal')
        self.enable_inputs_comp()
        self.title_entry.config(state='normal')
        self.author_entry.config(state='normal')
        self.output_options_opt.config(state='normal')
        self.output_setdir_entry.config(state='normal')
        self.output_setdir_btn.config(state='normal')
        self.signal_uuid_entry.config(state='normal')
        self.signal_password_entry.config(state='normal')
        self.telegram_token_entry.config(state='normal')
        self.telegram_userid_entry.config(state='normal')

        self.callback_input_option()
        self.callback_nocompress()