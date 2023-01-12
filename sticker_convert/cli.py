#!/usr/bin/env python3
import sys
import multiprocessing
import argparse

from flow import Flow
from utils.json_manager import JsonManager

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
    def cli(self):
        self.input_presets = JsonManager.load_json('resources/input.json')
        self.compression_presets = JsonManager.load_json('resources/compression.json')
        self.output_presets = JsonManager.load_json('resources/output.json')

        if not (self.compression_presets and self.input_presets and self.output_presets):
            self.callback_msg('Warning: preset json(s) cannot be found')
            return

        parser = argparse.ArgumentParser(description='CLI for stickers-convert')
        parser.add_argument('--no-confirm', dest='no_confirm', action='store_true', help='Do not ask any questions')
        parser.add_argument('--input-dir', dest='input_dir', default='./stickers_input', help='Specify input directory')
        parser.add_argument('--output-dir', dest='output_dir', default='./stickers_output', help='Specify output directory')
        parser.add_argument('--download-signal', dest='download_signal', help=f'{self.input_presets["signal"]["help"]} ({self.input_presets["signal"]["example"]})')
        parser.add_argument('--download-telegram', dest='download_telegram', help=f'{self.input_presets["telegram"]["help"]} ({self.input_presets["telegram"]["example"]})')
        parser.add_argument('--download-line', dest='download_line', help=f'{self.input_presets["line"]["help"]} ({self.input_presets["line"]["example"]})')
        parser.add_argument('--download-kakao', dest='download_kakao', help=f'{self.input_presets["kakao"]["help"]} ({self.input_presets["kakao"]["example"]})')

        parser.add_argument('--export-wastickers', dest='export_wastickers', action='store_true', help=self.output_presets['whatsapp']['help'])
        parser.add_argument('--export-signal', dest='export_signal', action='store_true', help=self.output_presets['signal']['help'])
        parser.add_argument('--export-telegram', dest='export_telegram', action='store_true', help=self.output_presets['telegram']['help'])
        parser.add_argument('--export-imessage', dest='export_imessage', action='store_true', help=self.output_presets['imessage']['help'])

        parser.add_argument('--no-compress', dest='no_compress', action='store_true', help='Do not compress files. Useful for only downloading stickers')
        parser.add_argument('--preset', dest='preset', default='custom', choices=self.compression_presets.keys(), help='Apply preset for compression')
        parser.add_argument('--fps-min', dest='fps_min', type=int, default=None, help='Set minimum output fps')
        parser.add_argument('--fps-max', dest='fps_max', type=int, default=None, help='Set maximum output fps')
        parser.add_argument('--res-min', dest='res_min', type=int, default=None, help='Set minimum output resolution (width and height)')
        parser.add_argument('--res-max', dest='res_max', type=int, default=None, help='Set maximum output resolution (width and height)')
        parser.add_argument('--res-w-min', dest='res_w_min', type=int, default=None, help='Set minimum output resolution (width)')
        parser.add_argument('--res-w-max', dest='res_w_max', type=int, default=None, help='Set maximum output resolution (width)')
        parser.add_argument('--res-h-min', dest='res_h_min', type=int, default=None, help='Set minimum output resolution (height)')
        parser.add_argument('--res-h-max', dest='res_h_max', type=int, default=None, help='Set maximum output resolution (height)')
        parser.add_argument('--quality-min', dest='quality_min', type=int, default=None, help='Set minimum quality')
        parser.add_argument('--quality-max', dest='quality_max', type=int, default=None, help='Set maximum quality')
        parser.add_argument('--color-min', dest='color_min', type=int, default=None, help='Set minimum number of colors (For converting to apng). >256 will disable it.')
        parser.add_argument('--color-max', dest='color_max', type=int, default=None, help='Set maximum number of colors (For converting to apng). >256 will disable it.')
        parser.add_argument('--duration-min', dest='duration_min', type=int, default=None, help='Set minimum output duration in miliseconds. Will change play speed if source is longer than duration. 0 will disable limit.')
        parser.add_argument('--duration-max', dest='duration_max', type=int, default=None, help='Set maximum output duration in miliseconds. Will change play speed if source is longer than duration. 0 will disable limit.')
        parser.add_argument('--steps', dest='steps', type=int, default=None, help='Set number of divisions between min and max settings. Higher value is slower but yields file more closer to the specified file size limit')
        parser.add_argument('--vid-size-max', dest='vid_size_max', type=int, default=None, help='Set maximum file size limit for animated stickers')
        parser.add_argument('--img-size-max', dest='img_size_max', type=int, default=None, help='Set maximum file size limit for static stickers')
        parser.add_argument('--vid-format', dest='vid_format', default=None, help='Set file format if input is a animated')
        parser.add_argument('--img-format', dest='img_format', default=None, help='Set file format if input is a static image')
        parser.add_argument('--fake-vid', dest='fake_vid', action='store_true', help='Convert (faking) image to video. Useful if (1) Size limit for video is larger than image; (2) Mix image and video into same pack')
        parser.add_argument('--default-emoji', dest='default_emoji', default=self.compression_presets['custom']['default_emoji'], help='Set the default emoji for uploading signal and telegram sticker packs')
        parser.add_argument('--processes', dest='processes', type=int, help='Set number of processes. Default to number of logical processors in system')

        parser.add_argument('--author', dest='author', default='Me', help='Set author of created sticker pack')
        parser.add_argument('--title', dest='title', default='My sticker pack', help='Set name of created sticker pack')

        parser.add_argument('--signal-uuid', dest='signal_uuid', help='Set signal uuid. Required for uploading signal stickers')
        parser.add_argument('--signal-password', dest='signal_password', help='Set signal password. Required for uploading signal stickers')
        parser.add_argument('--telegram-token', dest='telegram_token', help='Set telegram token. Required for uploading and downloading telegram stickers')
        parser.add_argument('--telegram-userid', dest='telegram_userid', help='Set telegram user_id (From real account, not bot account). Required for uploading telegram stickers')
        parser.add_argument('--save-cred', dest='save_cred', action="store_true", help='Save signal and telegram credentials')

        args = parser.parse_args()
        
        self.no_confirm = args.no_confirm

        self.get_opt_input(args)
        self.get_opt_output(args)
        self.get_opt_comp(args)
        self.get_opt_cred(args)

        flow = Flow(
            self.opt_input, self.opt_comp, self.opt_output, self.opt_cred, 
            self.input_presets, self.output_presets,
            self.callback_msg, self.callback_bar, self.callback_ask
        )
    
        success = flow.start()

        if not success:
            self.callback_msg(msg='An error occured during this run.')

    def get_opt_input(self, args):
        download_options = {
            'signal': args.download_signal, 
            'line': args.download_line, 
            'telegram': args.download_telegram, 
            'kakao': args.download_kakao
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
            'dir': args.input_dir
        }

    def get_opt_output(self, args):
        if args.export_wastickers:
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
            'dir': args.output_dir,
            'title': args.title,
            'author': args.author
        }

    def get_opt_comp(self, args):
        preset = args.preset
        if args.preset == 'custom':
            if sum((args.export_wastickers, args.export_signal, args.export_telegram, args.export_imessage)) > 1:
                # Let the verify functions in export do the compression
                args.no_compress = True
            elif args.export_wastickers:
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
            'default_emoji': args.default_emoji,
            'no_compress': args.no_compress,
            'processes': args.processes if args.processes else multiprocessing.cpu_count()
        }

    def get_opt_cred(self, args):
        creds = JsonManager.load_json('creds.json')
        if creds:
            self.callback_msg('Loaded credentials from creds.json')
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
            }
        }        
        
        if args.save_cred:
            JsonManager.save_json('creds.json', self.opt_cred)
            self.callback_msg('Saved credentials to creds.json')

    def callback_ask(self, question):
        self.callback_msg(question)

        if self.no_confirm:
            self.callback_msg('"--no-confirm" flag is set. Continue with this run without asking questions')
            return True
        else:
            self.callback_msg('If you do not want to get asked by this question, add "--no-confirm" flag')
            self.callback_msg()
            result = input('Continue? [y/N] > ')
            if result.lower() != 'y':
                self.callback_msg('Cancelling this run')
                return False
            else:
                return True

    def callback_msg(self, msg: str=None, cls: bool=True, *args):
        if msg:
            sys.stdout.write(msg)
        elif len(args) > 0:
            msg = ' '.join(str(i) for i in args)
            sys.stdout.write(msg)
    
    def callback_bar(self, set_progress_mode: str=None, steps: int=None, update_bar: bool=False):
        # Progressbar could be implemented here
        pass
