#!/usr/bin/env python3
import os
import multiprocessing
import argparse

from tqdm import tqdm

from .flow import Flow
from .utils.json_manager import JsonManager
from .utils.get_kakao_auth import GetKakaoAuth
from .utils.get_signal_auth import GetSignalAuth
from .utils.get_line_auth import GetLineAuth
from .utils.curr_dir import CurrDir
from .__init__ import __version__

# Only download from a source
# sticker_convert_cli.py --download-signal <url> --no-compress

# Convert local files to signal compatible stickers
# sticker_convert_cli.py --input-dir ./custom-input --output-dir ./custom-output --preset signal
# sticker_convert_cli.py --preset signal

# Convert signal to telegram stickers
# sticker_convert_cli.py --download-signal <url> --export-telegram

# Convert local files to multiple formats
# sticker_convert_cli.py --export-telegram --export-signal

# Convert local files to a custom format
# sticker_convert_cli.py --fps-min 3 --fps-max 30 --quality-min 30 --quality-max 90 --res-min 512 --res-max 512 --steps 10 --vid-size-max 500000 --img-size-max 500000 --vid-format .apng --img-format .png

class CLI:
    def __init__(self):
        self.no_confirm = False
        self.progress_bar = None

    def cli(self):
        self.help = JsonManager.load_json('resources/help.json')
        self.input_presets = JsonManager.load_json('resources/input.json')
        self.compression_presets = JsonManager.load_json('resources/compression.json')
        self.output_presets = JsonManager.load_json('resources/output.json')

        if not (self.help and self.compression_presets and self.input_presets and self.output_presets):
            self.cb_msg('Warning: preset json(s) cannot be found')
            return

        parser = argparse.ArgumentParser(description='CLI for stickers-convert', formatter_class=argparse.RawTextHelpFormatter)

        parser.add_argument('--version', action='version', version=__version__)
        parser.add_argument(f'--no-confirm', dest='no_confirm', action='store_true', help=self.help['global']['no_confirm'])
        
        parser_input = parser.add_argument_group('Input options')
        for k, v in self.help['input'].items():
            parser_input.add_argument(f'--{k.replace("_", "-")}', dest=k, help=v)
        parser_input_src = parser_input.add_mutually_exclusive_group()
        for k, v in self.input_presets.items():
            if k == 'local':
                continue
            parser_input_src.add_argument(f'--download-{k.replace("_", "-")}', dest=f'download_{k}', help=f'{v["help"]}\n({v["example"]})')

        parser_output = parser.add_argument_group('Output options')
        for k, v in self.help['output'].items():
            parser_output.add_argument(f'--{k.replace("_", "-")}', dest=k, help=v)
        parser_output_dst = parser_output.add_mutually_exclusive_group()
        for k, v in self.output_presets.items():
            if k == 'local':
                continue
            parser_output_dst.add_argument(f'--export-{k.replace("_", "-")}', dest=f'export_{k}', action='store_true', help=v['help'])

        parser_comp = parser.add_argument_group('Compression options')
        parser_comp.add_argument('--no-compress', dest='no_compress', action='store_true', help=self.help['comp']['no_compress'])
        parser_comp.add_argument('--preset', dest='preset', default='custom', choices=self.compression_presets.keys(), help=self.help['comp']['preset'])
        flags_int = ('steps', 'processes', 
                    'fps_min', 'fps_max', 
                    'res_min', 'res_max', 
                    'res_w_min', 'res_w_max', 
                    'res_h_min', 'res_h_max',
                    'quality_min', 'quality_max',
                    'color_min', 'color_max',
                    'duration_min', 'duration_max',
                    'vid_size_max', 'img_size_max')
        flags_str = ('vid_format', 'img_format', 'cache_dir')
        flags_bool = ('fake_vid')
        for k, v in self.help['comp'].items():
            if k in flags_int:
                keyword_args = {'type': int, 'default': None}
            elif k in flags_str:
                keyword_args = {'default': None}
            elif k in flags_bool:
                keyword_args = {'action': 'store_true', 'default': None}
            else:
                continue
            parser_comp.add_argument(f'--{k.replace("_", "-")}', **keyword_args, dest=k, help=v)
        parser_comp.add_argument('--default-emoji', dest='default_emoji', default=self.compression_presets['custom']['default_emoji'], help=self.help['comp']['default_emoji'])

        parser_cred = parser.add_argument_group('Credentials options')
        flags_bool = ('signal_get_auth', 'kakao_get_auth', 'line_get_auth')
        for k, v in self.help['cred'].items():
            keyword_args = {}
            if k in flags_bool:
                keyword_args = {'action': 'store_true'}
            parser_cred.add_argument(f'--{k.replace("_", "-")}', **keyword_args, dest=k, help=v)

        args = parser.parse_args()
        
        self.no_confirm = args.no_confirm

        self.get_opt_input(args)
        self.get_opt_output(args)
        self.get_opt_comp(args)
        self.get_opt_cred(args)

        flow = Flow(
            self.opt_input, self.opt_comp, self.opt_output, self.opt_cred, 
            self.input_presets, self.output_presets,
            self.cb_msg, self.cb_msg_block, self.cb_bar, self.cb_ask_bool
        )

        success = flow.start()

        if not success:
            self.cb_msg(msg='An error occured during this run.')

    def get_opt_input(self, args):
        download_options = {
            'signal': args.download_signal, 
            'line': args.download_line, 
            'telegram': args.download_telegram, 
            'kakao': args.download_kakao,
        }

        download_option = 'local'
        url = None
        for k, v in download_options.items():
            if v:
                download_option = k
                url = v
                break

        self.opt_input = {
            'option': download_option,
            'url': url,
            'dir': args.input_dir if args.input_dir else os.path.join(CurrDir.get_curr_dir(), 'stickers_input')
        }

    def get_opt_output(self, args):
        if args.export_whatsapp:
            export_option = 'whatsapp'
        elif args.export_signal:
            export_option = 'signal'
        elif args.export_telegram:
            export_option = 'telegram'
        elif args.export_imessage:
            export_option = 'imessage'
        else:
            export_option = 'local'
        
        self.opt_output = {
            'option': export_option,
            'dir': args.output_dir if args.output_dir else os.path.join(CurrDir.get_curr_dir(), 'stickers_output'),
            'title': args.title,
            'author': args.author
        }

    def get_opt_comp(self, args):
        preset = args.preset
        if args.preset == 'custom':
            if sum((args.export_whatsapp, args.export_signal, args.export_telegram, args.export_imessage)) > 1:
                # Let the verify functions in export do the compression
                args.no_compress = True
            elif args.export_whatsapp:
                preset = 'whatsapp'
            elif args.export_signal:
                preset = 'signal'
            elif args.export_telegram:
                preset = 'telegram'
            elif args.export_imessage:
                preset = 'imessage_small'

        self.opt_comp = {
            'preset': preset,
            'size_max': {
                'img': self.compression_presets[preset]['size_max']['img'] if args.img_size_max == None else args.img_size_max,
                'vid': self.compression_presets[preset]['size_max']['vid'] if args.vid_size_max == None else args.vid_size_max
            },
            'format': {
                'img': self.compression_presets[preset]['format']['img'] if args.img_format == None else args.img_format,
                'vid': self.compression_presets[preset]['format']['vid'] if args.vid_format == None else args.vid_format
            },
            'fps': {
                'min': self.compression_presets[preset]['fps']['min'] if args.fps_min == None else args.fps_min,
                'max': self.compression_presets[preset]['fps']['max'] if args.fps_max == None else args.fps_max
            },
            'res': {
                'w': {
                    'min': self.compression_presets[preset]['res']['w']['min'] if args.res_w_min == None else args.res_w_min,
                    'max': self.compression_presets[preset]['res']['w']['max'] if args.res_w_max == None else args.res_w_max
                },
                'h': {
                    'min': self.compression_presets[preset]['res']['h']['min'] if args.res_h_min == None else args.res_h_min,
                    'max': self.compression_presets[preset]['res']['h']['max'] if args.res_h_max == None else args.res_h_max
                }
            },
            'quality': {
                'min': self.compression_presets[preset]['quality']['min'] if args.quality_min == None else args.quality_min,
                'max': self.compression_presets[preset]['quality']['max'] if args.quality_max == None else args.quality_max
            },
            'color': {
                'min': self.compression_presets[preset]['color']['min'] if args.color_min == None else args.color_min,
                'max': self.compression_presets[preset]['color']['max'] if args.color_max == None else args.color_max
            },
            'duration': {
                'min': self.compression_presets[preset]['duration']['min'] if args.duration_min == None else args.duration_min,
                'max': self.compression_presets[preset]['duration']['max'] if args.duration_max == None else args.duration_max
            },
            'steps': self.compression_presets[preset]['steps'] if args.steps == None else args.steps,
            'fake_vid': self.compression_presets[preset]['fake_vid'] if args.fake_vid == None else args.fake_vid,
            'cache_dir': args.cache_dir,
            'default_emoji': args.default_emoji,
            'no_compress': args.no_compress,
            'processes': args.processes if args.processes else multiprocessing.cpu_count()
        }

    def get_opt_cred(self, args):
        creds_path = os.path.join(CurrDir.get_creds_dir(), 'creds.json')
        creds = JsonManager.load_json(creds_path)
        if creds:
            self.cb_msg('Loaded credentials from creds.json')
        else:
            creds = {}

        self.opt_cred = {
            'signal': {
                'uuid': args.signal_uuid if args.signal_uuid else creds.get('signal', {}).get('uuid'),
                'password': args.signal_password if args.signal_password else creds.get('signal', {}).get('password')
            },
            'telegram': {
                'token': args.telegram_token if args.telegram_token else creds.get('telegram', {}).get('token'),
                'userid': args.telegram_userid if args.telegram_userid else creds.get('telegram', {}).get('userid')
            },
            'kakao': {
                'auth_token': args.kakao_auth_token if args.kakao_auth_token else creds.get('kakao', {}).get('auth_token'),
                'username': args.kakao_username if args.kakao_username else creds.get('kakao', {}).get('username'),
                'password': args.kakao_password if args.kakao_password else creds.get('kakao', {}).get('password'),
                'country_code': args.kakao_country_code if args.kakao_country_code else creds.get('kakao', {}).get('country_code'),
                'phone_number': args.kakao_phone_number if args.kakao_phone_number else creds.get('kakao', {}).get('phone_number')
            },
            'line': {
                'cookies': args.line_cookies if args.line_cookies else creds.get('line', {}).get('cookies')
            }
        }

        if args.kakao_get_auth:
            m = GetKakaoAuth(opt_cred=creds, cb_msg=self.cb_msg, cb_msg_block=self.cb_msg_block, cb_ask_str=self.cb_ask_str)
            auth_token = m.get_cred()

            if auth_token:
                self.opt_cred['kakao']['auth_token'] = auth_token
                
                self.cb_msg(f'Got auth_token successfully: {auth_token}')
        
        if args.signal_get_auth:
            m = GetSignalAuth(cb_msg=self.cb_msg, cb_ask_str=self.cb_ask_str)

            uuid, password = None, None
            while True:
                uuid, password = m.get_cred()

                if uuid and password:
                    self.opt_cred['signal']['uuid'] = uuid
                    self.opt_cred['signal']['password'] = password
                
                    self.cb_msg(f'Got uuid and password successfully: {uuid}, {password}')
                    break
        
        if args.line_get_auth:
            m = GetLineAuth(cb_msg=self.cb_msg, cb_ask_str=self.cb_ask_str)

            line_cookies = m.get_cred()

            if line_cookies:
                self.opt_cred['line']['cookies'] = line_cookies
            
                self.cb_msg(f'Got Line cookies successfully')
            else:
                self.cb_msg(f'Failed to get Line cookies. Have you logged in the web browser?')
        
        if args.save_cred:
            creds_path = os.path.join(CurrDir.get_creds_dir(), 'creds.json')
            JsonManager.save_json(creds_path, self.opt_cred)
            self.cb_msg('Saved credentials to creds.json')
    
    def cb_ask_str(self, msg: str=None, initialvalue: str=None, cli_show_initialvalue: bool=True):
        self.cb_msg(msg)

        hint = ''
        if cli_show_initialvalue and initialvalue:
            hint = f' [Default: {initialvalue}]'

        response = input(f'Enter your response and press enter{hint} > ')

        if initialvalue and not response:
            response = initialvalue
        
        return response

    def cb_ask_bool(self, question, parent=None):
        self.cb_msg(question)

        if self.no_confirm:
            self.cb_msg('"--no-confirm" flag is set. Continue with this run without asking questions')
            return True
        else:
            self.cb_msg('If you do not want to get asked by this question, add "--no-confirm" flag')
            self.cb_msg()
            result = input('Continue? [y/N] > ')
            if result.lower() != 'y':
                self.cb_msg('Cancelling this run')
                return False
            else:
                return True
    
    def cb_msg(self, *args, **kwargs):
        msg = kwargs.get('msg')

        if not msg and len(args) == 1:
            msg = str(args[0])

        if msg:
            if self.progress_bar:
                self.progress_bar.write(msg)
            else:
                print(msg)

    def cb_msg_block(self, *args, **kwargs):
        if len(args) > 0:
            msg = ' '.join(str(i) for i in args)
            self.cb_msg(msg)
        if not self.no_confirm:
            input('Press Enter to continue...')
    
    def cb_bar(self, set_progress_mode: str=None, steps: int=None, update_bar: bool=False):
        if update_bar:
            self.progress_bar.update()
        elif set_progress_mode == 'determinate':
            self.progress_bar = tqdm(total=steps)
        elif set_progress_mode == 'indeterminate':
            if self.progress_bar:
                self.progress_bar.close()
                self.progress_bar = None
        elif set_progress_mode == 'clear':
            if self.progress_bar:
                self.progress_bar.reset()