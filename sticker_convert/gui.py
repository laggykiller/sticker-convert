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
from utils.codec_info import CodecInfo
from downloaders.download_line import DownloadLine
from downloaders.download_signal import DownloadSignal
from downloaders.download_telegram import DownloadTelegram
from downloaders.download_kakao import DownloadKakao
from uploaders.upload_signal import UploadSignal
from uploaders.upload_telegram import UploadTelegram
from uploaders.compress_wastickers import CompressWastickers
from uploaders.xcode_imessage import XcodeImessage

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
        'imessage': 'Create Xcode project (iMessage)',
        'local': 'Save to local directory only'
    }

    exec_pool = None

    def __init__(self):
        self.load_preset()
        self.initialized = False

        self.root = Tk()
        # self.root.eval('tk::PlaceWindow . center')
        if sys.platform == 'darwin':
            self.root.iconbitmap('icon/appicon.icns')
        else:
            self.root.iconbitmap('icon/appicon.ico')
        self.root.title('sticker-convert')

        # Create frames
        self.frame_input = LabelFrame(self.root, borderwidth=1, text='Input')
        self.frame_comp = LabelFrame(self.root, borderwidth=1, text='Compression options')
        self.frame_output = LabelFrame(self.root, borderwidth=1, text='Output')
        self.frame_cred = LabelFrame(self.root, borderwidth=1, text='Credentials')
        self.frame_progress = LabelFrame(self.root, borderwidth=1, text='Progress')
        self.frame_controls = Frame(self.root, borderwidth=1)

        self.frame_input.grid(column=0, row=0, sticky='w')
        self.frame_comp.grid(column=1, row=0, rowspan=3, sticky='news')
        self.frame_output.grid(column=0, row=1, sticky='w')
        self.frame_cred.grid(column=0, row=2, sticky='w')
        self.frame_progress.grid(column=0, row=3, columnspan=2, sticky='news')
        self.frame_controls.grid(column=0, row=4, columnspan=2, sticky='news')

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
        self.input_setdir_var.set(os.path.abspath('./stickers_input'))
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
        self.no_compress_help_btn = Button(self.frame_comp, text='?', command=lambda: self.callback_compress_help('Do not compress files. Useful for only downloading stickers'))
        self.no_compress_var = BooleanVar()
        self.no_compress_cbox = Checkbutton(self.frame_comp, text="No compression", variable=self.no_compress_var, command=self.callback_nocompress)

        self.comp_preset_help_btn = Button(self.frame_comp, text='?', command=lambda: self.callback_compress_help('Apply preset for compression'))
        self.comp_preset_lbl = Label(self.frame_comp, text='Preset')
        self.comp_preset_var = StringVar(self.root)
        self.comp_preset_var.set(list(self.presets_dict.keys())[0])
        self.comp_preset_opt = OptionMenu(self.frame_comp, self.comp_preset_var, *self.presets_dict.keys(), command=self.callback_comp_apply_preset)
        self.comp_preset_opt.config(width=20)

        self.fps_help_btn = Button(self.frame_comp, text='?', command=lambda: self.callback_compress_help('FPS Higher = Smoother but larger size'))
        self.fps_lbl = Label(self.frame_comp, text='Output FPS')
        self.fps_min_lbl = Label(self.frame_comp, text='Min:')
        self.fps_min_var = IntVar(self.root)
        self.fps_min_entry = Entry(self.frame_comp, textvariable=self.fps_min_var, width=8)
        self.fps_max_lbl = Label(self.frame_comp, text='Max:')
        self.fps_max_var = IntVar(self.root)
        self.fps_max_entry = Entry(self.frame_comp, textvariable=self.fps_max_var, width=8)
        self.fps_disable_var = BooleanVar()
        self.fps_disable_cbox = Checkbutton(self.frame_comp, text="X", variable=self.fps_disable_var, command=self.callback_disable_fps)

        self.res_w_help_btn = Button(self.frame_comp, text='?', command=lambda: self.callback_compress_help('Set width.\nResolution higher = Clearer but larger size'))
        self.res_w_lbl = Label(self.frame_comp, text='Output resolution (Width)')
        self.res_w_min_lbl = Label(self.frame_comp, text='Min:')
        self.res_w_min_var = IntVar(self.root)
        self.res_w_min_entry = Entry(self.frame_comp, textvariable=self.res_w_min_var, width=8)
        self.res_w_max_lbl = Label(self.frame_comp, text='Max:')
        self.res_w_max_var = IntVar(self.root)
        self.res_w_max_entry = Entry(self.frame_comp, textvariable=self.res_w_max_var, width=8)
        self.res_w_disable_var = BooleanVar()
        self.res_w_disable_cbox = Checkbutton(self.frame_comp, text="X", variable=self.res_w_disable_var, command=self.callback_disable_res_w)
        
        self.res_h_help_btn = Button(self.frame_comp, text='?', command=lambda: self.callback_compress_help('Set height.\nResolution higher = Clearer but larger size'))
        self.res_h_lbl = Label(self.frame_comp, text='Output resolution (Height)')
        self.res_h_min_lbl = Label(self.frame_comp, text='Min:')
        self.res_h_min_var = IntVar(self.root)
        self.res_h_min_entry = Entry(self.frame_comp, textvariable=self.res_h_min_var, width=8)
        self.res_h_max_lbl = Label(self.frame_comp, text='Max:')
        self.res_h_max_var = IntVar(self.root)
        self.res_h_max_entry = Entry(self.frame_comp, textvariable=self.res_h_max_var, width=8)
        self.res_h_disable_var = BooleanVar()
        self.res_h_disable_cbox = Checkbutton(self.frame_comp, text="X", variable=self.res_h_disable_var, command=self.callback_disable_res_h)

        self.quality_help_btn = Button(self.frame_comp, text='?', command=lambda: self.callback_compress_help('Quality higher = Clearer but larger size'))
        self.quality_lbl = Label(self.frame_comp, text='Output quality (0-100)')
        self.quality_min_lbl = Label(self.frame_comp, text='Min:')
        self.quality_min_var = IntVar(self.root)
        self.quality_min_entry = Entry(self.frame_comp, textvariable=self.quality_min_var, width=8)
        self.quality_max_lbl = Label(self.frame_comp, text='Max:')
        self.quality_max_var = IntVar(self.root)
        self.quality_max_entry = Entry(self.frame_comp, textvariable=self.quality_max_var, width=8)
        self.quality_disable_var = BooleanVar()
        self.quality_disable_cbox = Checkbutton(self.frame_comp, text="X", variable=self.quality_disable_var, command=self.callback_disable_quality)

        self.color_help_btn = Button(self.frame_comp, text='?', command=lambda: self.callback_compress_help('Reduce size by limiting number of colors.\nMakes image "blocky". >256 will disable this.\nApplies to png and apng only.\nColor higher = More colors but larger size'))
        self.color_lbl = Label(self.frame_comp, text='Colors (0-256)')
        self.color_min_lbl = Label(self.frame_comp, text='Min:')
        self.color_min_var = IntVar(self.root)
        self.color_min_entry = Entry(self.frame_comp, textvariable=self.color_min_var, width=8)
        self.color_max_lbl = Label(self.frame_comp, text='Max:')
        self.color_max_var = IntVar(self.root)
        self.color_max_entry = Entry(self.frame_comp, textvariable=self.color_max_var, width=8)
        self.color_disable_var = BooleanVar()
        self.color_disable_cbox = Checkbutton(self.frame_comp, text="X", variable=self.color_disable_var, command=self.callback_disable_color)

        self.duration_help_btn = Button(self.frame_comp, text='?', command=lambda: self.callback_compress_help('Change playback speed if outside of duration limit.\nDuration set in miliseconds.\n0 will disable limit.'))
        self.duration_lbl = Label(self.frame_comp, text='Duration (Miliseconds)')
        self.duration_min_lbl = Label(self.frame_comp, text='Min:')
        self.duration_min_var = IntVar(self.root)
        self.duration_min_entry = Entry(self.frame_comp, textvariable=self.duration_min_var, width=8)
        self.duration_max_lbl = Label(self.frame_comp, text='Max:')
        self.duration_max_var = IntVar(self.root)
        self.duration_max_entry = Entry(self.frame_comp, textvariable=self.duration_max_var, width=8)
        self.duration_disable_var = BooleanVar()
        self.duration_disable_cbox = Checkbutton(self.frame_comp, text="X", variable=self.duration_disable_var, command=self.callback_disable_duration)

        self.size_help_btn = Button(self.frame_comp, text='?', command=lambda: self.callback_compress_help('Set maximum file size in bytes for video and image'))
        self.size_lbl = Label(self.frame_comp, text='Maximum file size (bytes)')
        self.img_size_max_lbl = Label(self.frame_comp, text='Img:')
        self.img_size_max_var = IntVar(self.root)
        self.img_size_max_entry = Entry(self.frame_comp, textvariable=self.img_size_max_var, width=8)
        self.vid_size_max_lbl = Label(self.frame_comp, text='Vid:')
        self.vid_size_max_var = IntVar(self.root)
        self.vid_size_max_entry = Entry(self.frame_comp, textvariable=self.vid_size_max_var, width=8)
        self.size_disable_var = BooleanVar()
        self.size_disable_cbox = Checkbutton(self.frame_comp, text="X", variable=self.size_disable_var, command=self.callback_disable_size)

        self.format_help_btn = Button(self.frame_comp, text='?', command=lambda: self.callback_compress_help('Set file format for video and image'))
        self.format_lbl = Label(self.frame_comp, text='File format')
        self.img_format_lbl = Label(self.frame_comp, text='Img:')
        self.img_format_var = StringVar(self.root)
        self.img_format_entry = Entry(self.frame_comp, textvariable=self.img_format_var, width=8)
        self.vid_format_lbl = Label(self.frame_comp, text='Vid:')
        self.vid_format_var = StringVar(self.root)
        self.vid_format_entry = Entry(self.frame_comp, textvariable=self.vid_format_var, width=8)

        self.fake_vid_help_btn = Button(self.frame_comp, text='?', command=lambda: self.callback_compress_help('Convert image to video. Useful if:\n(1) Size limit for video is larger than image\n(2) Mix image and video into same pack'))
        self.fake_vid_var = BooleanVar()
        self.fake_vid_cbox = Checkbutton(self.frame_comp, text="Convert (faking) image to video", variable=self.fake_vid_var)

        self.default_emoji_help_btn = Button(self.frame_comp, text='?', command=lambda: self.callback_compress_help('Set the default emoji for uploading signal and telegram sticker packs'))
        self.default_emoji_lbl = Label(self.frame_comp, text='Default emoji')
        self.default_emoji_var = StringVar(self.root)
        self.default_emoji_entry = Entry(self.frame_comp, textvariable=self.default_emoji_var, width=8)

        self.steps_help_btn = Button(self.frame_comp, text='?', command=lambda: self.callback_compress_help('Set number of divisions between min and max settings.\nSteps higher = Slower but yields file more closer to the specified file size limit'))
        self.steps_lbl = Label(self.frame_comp, text='Number of steps')
        self.steps_var = IntVar(self.root)        
        self.steps_entry = Entry(self.frame_comp, textvariable=self.steps_var, width=8)

        self.processes_help_btn = Button(self.frame_comp, text='?', command=lambda: self.callback_compress_help('Set number of processes. Default to number of logical processors in system.\nProcesses higher = Compress faster but consume more resources'))
        self.processes_lbl = Label(self.frame_comp, text='Number of processes')
        self.processes_var = IntVar(self.root)
        self.processes_var.set(multiprocessing.cpu_count())
        self.processes_entry = Entry(self.frame_comp, textvariable=self.processes_var, width=8)

        self.no_compress_help_btn.grid(column=0, row=0, sticky='w')
        self.no_compress_cbox.grid(column=1, row=0, columnspan=6, sticky='w')

        self.comp_preset_help_btn.grid(column=0, row=1, sticky='w')
        self.comp_preset_lbl.grid(column=1, row=1, sticky='w')
        self.comp_preset_opt.grid(column=2, row=1, columnspan=6, sticky='nes')

        self.fps_help_btn.grid(column=0, row=2, sticky='w')
        self.fps_lbl.grid(column=1, row=2, sticky='w')
        self.fps_min_lbl.grid(column=2, row=2, sticky='w')
        self.fps_min_entry.grid(column=3, row=2, sticky='nes')
        self.fps_max_lbl.grid(column=4, row=2, sticky='w')
        self.fps_max_entry.grid(column=5, row=2, sticky='nes')
        self.fps_disable_cbox.grid(column=6, row=2, sticky='nes')

        self.res_w_help_btn.grid(column=0, row=3, sticky='w')
        self.res_w_lbl.grid(column=1, row=3, sticky='w')
        self.res_w_min_lbl.grid(column=2, row=3, sticky='w')
        self.res_w_min_entry.grid(column=3, row=3, sticky='nes')
        self.res_w_max_lbl.grid(column=4, row=3, sticky='w')
        self.res_w_max_entry.grid(column=5, row=3, sticky='nes')
        self.res_w_disable_cbox.grid(column=6, row=3, sticky='nes')

        self.res_h_help_btn.grid(column=0, row=4, sticky='w')
        self.res_h_lbl.grid(column=1, row=4, sticky='w')
        self.res_h_min_lbl.grid(column=2, row=4, sticky='w')
        self.res_h_min_entry.grid(column=3, row=4, sticky='nes')
        self.res_h_max_lbl.grid(column=4, row=4, sticky='w')
        self.res_h_max_entry.grid(column=5, row=4, sticky='nes')
        self.res_h_disable_cbox.grid(column=6, row=4, sticky='nes')

        self.quality_help_btn.grid(column=0, row=5, sticky='w')
        self.quality_lbl.grid(column=1, row=5, sticky='w')
        self.quality_min_lbl.grid(column=2, row=5, sticky='w')
        self.quality_min_entry.grid(column=3, row=5, sticky='nes')
        self.quality_max_lbl.grid(column=4, row=5, sticky='w')
        self.quality_max_entry.grid(column=5, row=5, sticky='nes')
        self.quality_disable_cbox.grid(column=6, row=5, sticky='nes')

        self.color_help_btn.grid(column=0, row=6, sticky='w')
        self.color_lbl.grid(column=1, row=6, sticky='w')
        self.color_min_lbl.grid(column=2, row=6, sticky='w')
        self.color_min_entry.grid(column=3, row=6, sticky='nes')
        self.color_max_lbl.grid(column=4, row=6, sticky='w')
        self.color_max_entry.grid(column=5, row=6, sticky='nes')
        self.color_disable_cbox.grid(column=6, row=6, sticky='nes')

        self.duration_help_btn.grid(column=0, row=7, sticky='w')
        self.duration_lbl.grid(column=1, row=7, sticky='w')
        self.duration_min_lbl.grid(column=2, row=7, sticky='w')
        self.duration_min_entry.grid(column=3, row=7, sticky='nes')
        self.duration_max_lbl.grid(column=4, row=7, sticky='w')
        self.duration_max_entry.grid(column=5, row=7, sticky='nes')
        self.duration_disable_cbox.grid(column=6, row=7, sticky='nes')

        self.size_help_btn.grid(column=0, row=8, sticky='w')
        self.size_lbl.grid(column=1, row=8, sticky='w')
        self.img_size_max_lbl.grid(column=2, row=8, sticky='w')
        self.img_size_max_entry.grid(column=3, row=8, sticky='nes')
        self.vid_size_max_lbl.grid(column=4, row=8, sticky='w')
        self.vid_size_max_entry.grid(column=5, row=8, sticky='nes')
        self.size_disable_cbox.grid(column=6, row=8, sticky='nes')

        self.format_help_btn.grid(column=0, row=9, sticky='w')
        self.format_lbl.grid(column=1, row=9, sticky='w')
        self.img_format_lbl.grid(column=2, row=9, sticky='w')
        self.img_format_entry.grid(column=3, row=9, sticky='nes')
        self.vid_format_lbl.grid(column=4, row=9, sticky='w')
        self.vid_format_entry.grid(column=5, row=9, sticky='nes')

        self.fake_vid_help_btn.grid(column=0, row=10, sticky='w')
        self.fake_vid_cbox.grid(column=1, row=10, columnspan=6, sticky='w')

        self.default_emoji_help_btn.grid(column=0, row=11, sticky='w')
        self.default_emoji_lbl.grid(column=1, row=11, sticky='w')
        self.default_emoji_entry.grid(column=2, row=11, columnspan=5, sticky='nes')

        self.steps_help_btn.grid(column=0, row=12, sticky='w')
        self.steps_lbl.grid(column=1, row=12, sticky='w')
        self.steps_entry.grid(column=2, row=12, columnspan=5, sticky='nes')

        self.processes_help_btn.grid(column=0, row=13, sticky='w')
        self.processes_lbl.grid(column=1, row=13, sticky='w')
        self.processes_entry.grid(column=2, row=13, columnspan=5, sticky='nes')

        # Output frame
        self.output_options_lbl = Label(self.frame_output, text='Output options', width=15, justify='left', anchor='w')
        self.output_options_var = StringVar(self.root)
        self.output_options_var.set(self.output_options[self.default_output_mode])
        self.output_options_opt = OptionMenu(self.frame_output, self.output_options_var, *self.output_options.values())
        self.output_options_opt.config(width=32)

        self.output_setdir_lbl = Label(self.frame_output, text='Output directory', width=15, justify='left', anchor='w')
        self.output_setdir_var = StringVar(self.root)
        self.output_setdir_var.set(os.path.abspath('./stickers_output'))
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
        self.progress_box = scrolledtext.ScrolledText(self.frame_progress, height=10, wrap='word')
        self.progress_bar = Progressbar(self.frame_progress, orient='horizontal', mode='determinate')

        self.progress_box.pack(expand=True, fill='x')
        self.progress_bar.pack(expand=True, fill='x')

        # Controls frame
        # self.stop_btn = Button(self.frame_controls, text='Stop', width=30, command=self.stop, state='disabled')
        self.start_btn = Button(self.frame_controls, text='Start', command=self.start)
        
        # self.stop_btn.grid(column=0, row=0)
        # self.start_btn.grid(column=1, row=0)
        self.start_btn.pack(expand=True, fill='x')

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
        orig_input_dir = self.output_setdir_var.get()
        if not os.path.isdir(orig_input_dir):
            orig_input_dir = os.getwcd()
        input_dir = filedialog.askdirectory(initialdir=orig_input_dir)
        if input_dir != '':
            self.input_setdir_var.set(input_dir)
    
    def callback_set_outdir(self, *args):
        orig_output_dir = self.output_setdir_var.get()
        if not os.path.isdir(orig_output_dir):
            orig_output_dir = os.getwcd()
        output_dir = filedialog.askdirectory(initialdir=orig_output_dir)
        if output_dir != '':
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
        self.res_w_min_var.set(self.presets_dict[selection]['res_w_min'])
        self.res_w_max_var.set(self.presets_dict[selection]['res_w_max'])
        self.res_h_min_var.set(self.presets_dict[selection]['res_h_min'])
        self.res_h_max_var.set(self.presets_dict[selection]['res_h_max'])
        self.quality_min_var.set(self.presets_dict[selection]['quality_min'])
        self.quality_max_var.set(self.presets_dict[selection]['quality_max'])
        self.color_min_var.set(self.presets_dict[selection]['color_min'])
        self.color_max_var.set(self.presets_dict[selection]['color_max'])
        self.duration_min_var.set(self.presets_dict[selection]['duration_min'])
        self.duration_max_var.set(self.presets_dict[selection]['duration_max'])
        self.img_size_max_var.set(self.presets_dict[selection]['img_size_max'])
        self.vid_size_max_var.set(self.presets_dict[selection]['vid_size_max'])
        self.img_format_var.set(self.presets_dict[selection]['img_format'])
        self.vid_format_var.set(self.presets_dict[selection]['vid_format'])
        self.fake_vid_var.set(self.presets_dict[selection]['fake_vid'])
        self.default_emoji_var.set(self.presets_dict[selection]['default_emoji'])
        self.steps_var.set(self.presets_dict[selection]['steps'])
    
    def callback_nocompress(self, *args):
        if self.no_compress_var.get() == True:
            self.set_inputs_comp(False)
        else:
            self.set_inputs_comp(True)
    
    def callback_disable_fps(self, *args):
        if self.fps_disable_var.get() == True:
            state = 'disabled'
        else:
            state = 'normal'

        self.fps_min_entry.config(state=state)
        self.fps_max_entry.config(state=state)

    def callback_disable_res_w(self, *args):
        if self.res_w_disable_var.get() == True:
            state = 'disabled'
        else:
            state = 'normal'

        self.res_w_min_entry.config(state=state)
        self.res_w_max_entry.config(state=state)

    def callback_disable_res_h(self, *args):
        if self.res_h_disable_var.get() == True:
            state = 'disabled'
        else:
            state = 'normal'

        self.res_h_min_entry.config(state=state)
        self.res_h_max_entry.config(state=state)

    def callback_disable_quality(self, *args):
        if self.quality_disable_var.get() == True:
            state = 'disabled'
        else:
            state = 'normal'

        self.quality_min_entry.config(state=state)
        self.quality_max_entry.config(state=state)

    def callback_disable_color(self, *args):
        if self.color_disable_var.get() == True:
            state = 'disabled'
        else:
            state = 'normal'

        self.color_min_entry.config(state=state)
        self.color_max_entry.config(state=state)

    def callback_disable_duration(self, *args):
        if self.duration_disable_var.get() == True:
            state = 'disabled'
        else:
            state = 'normal'

        self.duration_min_entry.config(state=state)
        self.duration_max_entry.config(state=state)

    def callback_disable_size(self, *args):
        if self.size_disable_var.get() == True:
            state = 'disabled'
        else:
            state = 'normal'

        self.img_size_max_entry.config(state=state)
        self.vid_size_max_entry.config(state=state)

    def callback_compress_help(self, message='', *args):
        messagebox.showinfo(title='sticker-convert', message=message)
        
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
        self.set_inputs(False)
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

            size_disable = self.size_disable_var.get()
            vid_size_max = int(self.vid_size_max_var.get()) if not size_disable else None
            img_size_max = int(self.img_size_max_var.get()) if not size_disable else None

            vid_format = self.vid_format_var.get()
            img_format = self.img_format_var.get()

            fake_vid = self.fake_vid_var.get()

            fps_disable = self.fps_disable_var.get()
            fps_min = int(self.fps_min_var.get()) if not fps_disable else None
            fps_max = int(self.fps_max_var.get()) if not fps_disable else None

            res_w_disable = self.res_w_disable_var.get()
            res_w_min = int(self.res_w_min_var.get()) if not res_w_disable else None
            res_w_max = int(self.res_w_max_var.get()) if not res_w_disable else None

            res_h_disable = self.res_h_disable_var.get()
            res_h_min = int(self.res_h_min_var.get()) if not res_h_disable else None
            res_h_max = int(self.res_h_max_var.get()) if not res_h_disable else None

            quality_disable = self.quality_disable_var.get()
            quality_max = int(self.quality_max_var.get()) if not quality_disable else None
            quality_min = int(self.quality_min_var.get()) if not quality_disable else None

            color_disable = self.color_disable_var.get()
            color_min = int(self.color_min_var.get()) if not color_disable else None
            color_max = int(self.color_max_var.get()) if not color_disable else None

            duration_disable = self.duration_disable_var.get()
            duration_min = self.duration_min_var.get() if not duration_disable else None
            duration_max = self.duration_max_var.get() if not duration_disable else None

            steps = int(self.steps_var.get())
            default_emoji = self.default_emoji_var.get()
            title = self.title_var.get()
            author = self.author_var.get()
            processes = int(self.processes_var.get())

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
            self.update_progress_box('Downloading from and uploading to telegram requires bot token. If you want to upload the results by yourself, select "Save to local directory only" for output')
            self.stop()
            return
        
        if output_option == self.output_options['telegram'] and telegram_userid == '':
            self.update_progress_box('Uploading to telegram requires user_id (From real account, not bot account). If you want to upload the results by yourself, select "Save to local directory only" for output')
            self.stop()
            return
        
        if output_option == self.output_options['signal'] and (signal_uuid == '' or signal_password == ''):
            self.update_progress_box('Uploading to signal requires uuid and password. If you want to upload the results by yourself, select "Save to local directory only" for output')
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
        
        if output_option == self.output_options['imessage'] and (title == '' or author == ''):
            self.update_progress_box('Creating Xcode project (for iMessage) requires title and author')
            self.stop()
            return
        
        if os.path.isdir(input_dir) == False:
            os.makedirs(input_dir)
        
        if os.path.isdir(output_dir) == False:
            os.makedirs(output_dir)

        # Check if input and ouput directories have files and prompt for deletion
        # It is possible to help the user to delete files but this is dangerous
        if input_option != self.input_options['local'] and os.listdir(input_dir) != []:
            message = 'Input directory is not empty (e.g. Files from previous run?)\n'
            message += f'Input directory is set to {input_dir}\n'
            message += 'You may continue at risk of contaminating the resulting sticker pack. Continue?'

            result = messagebox.askyesno('sticker-convert', message)

            if result == False:
                self.stop()
                return

        if output_option != self.output_options['local'] and no_compress == False and os.listdir(output_dir) != []:
            message = 'Output directory is not empty (e.g. Files from previous run?)\n'
            message += f'Output directory is set to {output_dir}\n'
            message += 'Hint: If you just want to upload files that you had compressed before, please choose "No" and tick the "No compression" box\n'
            message += 'You may continue at risk of contaminating the resulting sticker pack. Continue?'

            result = messagebox.askyesno('sticker-convert', message)

            if result == False:
                self.stop()
                return

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
        
        if fake_vid:
            img_format = vid_format

        # Compress
        if vid_format == '.png' or vid_format == '.apng':
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

                if CodecInfo.get_file_ext(i) == '.txt':
                    shutil.copy(in_f, os.path.join(output_dir, i))
                    continue

                if CodecInfo.is_anim(in_f):
                    format = vid_format
                else:
                    format = img_format

                out_f = os.path.join(output_dir, os.path.splitext(i)[0] + format)
                
                pool.apply_async(StickerConvert.convert_and_compress_to_size, kwds={'in_f': in_f, 'out_f': out_f, 'vid_size_max': vid_size_max, 'img_size_max': img_size_max, 'res_w_min': res_w_min, 'res_w_max': res_w_max, 'res_h_min': res_h_min, 'res_h_max': res_h_max, 'quality_max': quality_max, 'quality_min': quality_min, 'fps_max': fps_max, 'fps_min': fps_min, 'color_min': color_min, 'color_max': color_max, 'duration_min': duration_min, 'duration_max': duration_max, 'fake_vid': fake_vid, 'steps': steps}, callback=self.callback_update_progress_bar)

            pool.close()
            pool.join()

        # Export
        self.update_progress_box('Exporting...')
        self.progress_bar['value'] = 0
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(50)
        urls = []
        if output_option == self.output_options['whatsapp']:
            urls += CompressWastickers.compress_wastickers(in_dir=output_dir, out_dir=output_dir, author=author, title=title, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, fake_vid=fake_vid, steps=steps, default_emoji=default_emoji)
        elif output_option == self.output_options['signal']:
            urls += UploadSignal.upload_stickers_signal(uuid=signal_uuid, password=signal_password, in_dir=output_dir, author=author, title=title, res_w_min=res_w_min, res_w_max=res_w_max, res_h_max=res_h_max, res_h_min=res_h_min, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, color_min=color_min, color_max=color_max, fake_vid=fake_vid, steps=steps, default_emoji=default_emoji)
        elif output_option == self.output_options['telegram']:
            urls += UploadTelegram.upload_stickers_telegram(token=telegram_token, user_id=telegram_userid, in_dir=output_dir, author=author, title=title, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, fake_vid=fake_vid, steps=steps, default_emoji=default_emoji)
        elif output_option == self.output_options['imessage']:
            urls += XcodeImessage.create_imessage_xcode(in_dir=output_dir, out_dir=output_dir, author=author, title=title, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, steps=steps, default_emoji=default_emoji)

        if urls != []:
            urls_str = 'All done. Stickers uploaded to:\n' + '\n'.join(urls)
            self.update_progress_box(urls_str)
        else:
            self.update_progress_box('All done.')
        
        self.stop()
    
    def stop(self):
        self.progress_bar.stop()
        self.set_inputs(True)
        # self.stop_btn.config(state='disabled')
        self.start_btn.config(state='normal')
    
    def set_inputs_comp(self, state_bool: bool):
        if state_bool:
            state = 'normal'
            self.callback_disable_fps()
            self.callback_disable_res_w()
            self.callback_disable_res_h()
            self.callback_disable_quality()
            self.callback_disable_color()
            self.callback_disable_duration()
            self.callback_disable_size()
        else:
            state = 'disabled'
            self.fps_min_entry.config(state=state)
            self.fps_max_entry.config(state=state)
            self.res_w_min_entry.config(state=state)
            self.res_w_max_entry.config(state=state)
            self.res_h_min_entry.config(state=state)
            self.res_h_max_entry.config(state=state)
            self.color_min_entry.config(state=state)
            self.color_max_entry.config(state=state)
            self.quality_min_entry.config(state=state)
            self.quality_max_entry.config(state=state)
            self.duration_min_entry.config(state=state)
            self.duration_max_entry.config(state=state)
            self.img_size_max_entry.config(state=state)
            self.vid_size_max_entry.config(state=state)

        self.comp_preset_opt.config(state=state)
        self.fps_disable_cbox.config(state=state)
        self.res_w_disable_cbox.config(state=state)
        self.res_h_disable_cbox.config(state=state)
        self.quality_disable_cbox.config(state=state)
        self.color_disable_cbox.config(state=state)
        self.duration_disable_cbox.config(state=state)
        self.size_disable_cbox.config(state=state)
        self.img_format_entry.config(state=state)
        self.vid_format_entry.config(state=state)
        self.fake_vid_cbox.config(state=state)
        self.default_emoji_entry.config(state=state)
        self.steps_entry.config(state=state)
        self.processes_entry.config(state=state)

    def set_inputs(self, state_bool: bool):
        if state_bool:
            state = 'normal'
        else:
            state = 'disabled'

        self.input_option_opt.config(state=state)
        self.input_address_entry.config(state=state)
        self.input_setdir_entry.config(state=state)
        self.input_setdir_btn.config(state=state)
        self.no_compress_cbox.config(state=state)
        self.set_inputs_comp(state_bool)
        self.title_entry.config(state=state)
        self.author_entry.config(state=state)
        self.output_options_opt.config(state=state)
        self.output_setdir_entry.config(state=state)
        self.output_setdir_btn.config(state=state)
        self.signal_uuid_entry.config(state=state)
        self.signal_password_entry.config(state=state)
        self.telegram_token_entry.config(state=state)
        self.telegram_userid_entry.config(state=state)

        if state_bool:
            self.callback_input_option()
            self.callback_nocompress()