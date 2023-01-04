import os
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
import json
import shutil
import multiprocessing
import argparse

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
        preset_present = os.path.isfile('preset.json')
        if preset_present == False:
            print('Warning: preset.json cannot be found')
            return
        else:
            with open('preset.json', encoding='utf-8') as f:
                presets_dict = json.load(f)

        parser = argparse.ArgumentParser(description='CLI for stickers-convert')
        parser.add_argument('--no-confirm', dest='no_confirm', action='store_true', help='Do not ask any questions')
        parser.add_argument('--input-dir', dest='input_dir', default='./stickers_input', help='Specify input directory')
        parser.add_argument('--output-dir', dest='output_dir', default='./stickers_output', help='Specify output directory')
        parser.add_argument('--download-signal', dest='download_signal', help='Download signal stickers from a URL as input (e.g. https://signal.art/addstickers/#pack_id=xxxxx&pack_key=xxxxx)')
        parser.add_argument('--download-telegram', dest='download_telegram', help='Download telegram stickers from a URL as input (e.g. https://telegram.me/addstickers/xxxxx)')
        parser.add_argument('--download-line', dest='download_line', help='Download line stickers from a URL / ID as input (e.g. https://store.line.me/stickershop/product/1234/en OR line://shop/detail/1234 OR 1234)')
        parser.add_argument('--download-kakao', dest='download_kakao', help='Download kakao stickers from a URL / ID as input (e.g. https://e.kakao.com/t/xxxxx)')

        parser.add_argument('--export-wastickers', dest='export_wastickers', action='store_true', help='Create a .wastickers file for uploading to WhatsApp')
        parser.add_argument('--export-signal', dest='export_signal', action='store_true', help='Upload to Signal')
        parser.add_argument('--export-telegram', dest='export_telegram', action='store_true', help='Upload to Telegram')
        parser.add_argument('--export-imessage', dest='export_imessage', action='store_true', help='Create Xcode project for importing to iMessage')

        parser.add_argument('--no-compress', dest='no_compress', action='store_true', help='Do not compress files. Useful for only downloading stickers')
        parser.add_argument('--preset', dest='preset', default='custom', choices=presets_dict.keys(), help='Apply preset for compression')
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
        parser.add_argument('--duration-min', dest='duration', type=int, default=None, help='Set minimum output duration in miliseconds. Will change play speed if source is longer than duration. 0 will disable limit.')
        parser.add_argument('--duration-max', dest='duration', type=int, default=None, help='Set maximum output duration in miliseconds. Will change play speed if source is longer than duration. 0 will disable limit.')
        parser.add_argument('--steps', dest='steps', type=int, default=None, help='Set number of divisions between min and max settings. Higher value is slower but yields file more closer to the specified file size limit')
        parser.add_argument('--vid-size-max', dest='vid_size_max', type=int, default=None, help='Set maximum file size limit for animated stickers')
        parser.add_argument('--img-size-max', dest='img_size_max', type=int, default=None, help='Set maximum file size limit for static stickers')
        parser.add_argument('--vid-format', dest='vid_format', default=None, help='Set file format if input is a animated')
        parser.add_argument('--img-format', dest='img_format', default=None, help='Set file format if input is a static image')
        parser.add_argument('--fake-vid', dest='fake_vid', action='store_true', help='Convert (faking) image to video. Useful if (1) Size limit for video is larger than image; (2) Mix image and video into same pack')
        parser.add_argument('--default-emoji', dest='default_emoji', default=presets_dict['custom']['default_emoji'], help='Set the default emoji for uploading signal and telegram sticker packs')
        parser.add_argument('--processes', dest='processes', type=int, help='Set number of processes. Default to number of logical processors in system')

        parser.add_argument('--author', dest='author', default='Me', help='Set author of created sticker pack')
        parser.add_argument('--title', dest='title', default='My sticker pack', help='Set name of created sticker pack')

        parser.add_argument('--signal-uuid', dest='signal_uuid', help='Set signal uuid. Required for uploading signal stickers')
        parser.add_argument('--signal-password', dest='signal_password', help='Set signal password. Required for uploading signal stickers')
        parser.add_argument('--telegram-token', dest='telegram_token', help='Set telegram token. Required for uploading and downloading telegram stickers')
        parser.add_argument('--telegram-userid', dest='telegram_userid', help='Set telegram user_id (From real account, not bot account). Required for uploading telegram stickers')
        parser.add_argument('--save-cred', dest='save_cred', action="store_true", help='Save signal and telegram credentials')

        args = parser.parse_args()

        signal_uuid = args.signal_uuid
        signal_password = args.signal_password
        telegram_token = args.telegram_token
        telegram_userid = args.telegram_userid

        if os.path.isfile('creds.json'):
            with open('creds.json', encoding='utf-8') as f:
                creds = json.load(f)

            signal_uuid = creds['signal_uuid'] if signal_uuid == None else signal_uuid
            signal_password = creds['signal_password'] if signal_password == None else signal_password
            telegram_token = creds['telegram_token'] if telegram_token == None else telegram_token
            telegram_userid = creds['telegram_userid'] if telegram_userid == None else telegram_userid

            print('Loaded credentials from creds.json')
        
        if args.save_cred:
            creds = {
                'signal_uuid': signal_uuid,
                'signal_password': signal_password,
                'telegram_token': telegram_token,
                'telegram_userid': telegram_userid
            }
            with open('creds.json', 'w+', encoding='utf-8') as f:
                json.dump(creds, f, indent=4)
            print('Saved credentials to creds.json')
        
        input_dir = args.input_dir
        if os.path.isdir(input_dir) == False:
            print('Warning: Cannot find the specified input directory. Creating for you...')
            os.makedirs(input_dir)

        output_dir = args.output_dir
        if os.path.isdir(output_dir) == False:
            print('Info: Cannot find the specified output directory. Creating for you...')
            os.makedirs(output_dir)
        
        download_signal = args.download_signal
        download_line = args.download_line
        download_telegram = args.download_telegram
        download_kakao = args.download_kakao

        export_wastickers = args.export_wastickers
        export_signal = args.export_signal
        export_telegram = args.export_telegram
        export_imessage = args.export_imessage

        no_compress = args.no_compress
        no_confirm = args.no_confirm
        
        # Check if input and ouput directories have files and prompt for deletion
        # It is possible to help the user to delete files but this is dangerous
        

        if (download_signal or download_line or download_telegram or download_kakao) and no_compress == False and os.listdir(input_dir) != []:
            print('Input directory is not empty (e.g. Files from previous run?)')
            print(f'Input directory is set to {input_dir}')
            print('You may continue at risk of contaminating the resulting sticker pack')
            print()

            if no_confirm:
                print('"--no-confirm" flag is set. Continue with this run without asking questions')
            else:
                print('If you do not want to get asked by this question, add "--no-confirm" flag')
                print()
                result = input('Continue? [y/N] > ')
                if result.lower() != 'y':
                    print('Cancelled this run')
                    return

        if (export_wastickers or export_signal or export_telegram or export_imessage) and no_compress == False and os.listdir(output_dir) != []:
            print('Output directory is not empty (e.g. Files from previous run?)')
            print(f'Output directory is set to {output_dir}')
            print('Hint: If you just want to upload files that you had compressed before, please choose "n" and add "--no-compress" flag')
            print('You may continue at risk of contaminating the resulting sticker pack')
            print()

            if no_confirm:
                print('"--no-confirm" flag is set. Continue with this run without asking questions')
            else:
                print('If you do not want to get asked by this question, add "--no-confirm" flag')
                print()
                result = input('Continue? [y/N] > ')
                if result.lower() != 'y':
                    print('Cancelled this run')
                    return
        
        processes = args.processes if args.processes else multiprocessing.cpu_count()
        
        preset = args.preset
        if preset == 'custom':
            if sum((export_wastickers, export_signal, export_telegram, export_imessage)) > 1:
                # Let the verify functions in export do the compression
                no_compress = True
            elif export_wastickers:
                preset = 'whatsapp'
            elif export_signal:
                preset = 'signal'
            elif export_telegram:
                preset = 'telegram'
            elif export_imessage:
                preset = 'imessage_small'

        vid_size_max = presets_dict[preset]['vid_size_max'] if args.vid_size_max == None else args.vid_size_max
        img_size_max = presets_dict[preset]['img_size_max'] if args.img_size_max == None else args.img_size_max
        vid_format = presets_dict[preset]['vid_format'] if args.vid_format == None else args.vid_format
        img_format = presets_dict[preset]['img_format'] if args.img_format == None else args.img_format
        fake_vid = presets_dict[preset]['fake_vid'] if args.fake_vid == None else args.fake_vid
        fps_min = presets_dict[preset]['fps_min'] if args.fps_min == None else args.fps_min
        fps_max = presets_dict[preset]['fps_max'] if args.fps_max == None else args.fps_max
        if args.res_min:
            res_w_min = args.res_min
            res_h_min = args.res_min
        else:
            res_w_min = presets_dict[preset]['res_w_min'] if args.res_w_min == None else args.res_w_min
            res_h_min = presets_dict[preset]['res_h_min'] if args.res_h_min == None else args.res_h_min

        if args.res_max:
            res_w_max = args.res_max
            res_h_max = args.res_max
        else:
            res_w_max = presets_dict[preset]['res_w_max'] if args.res_w_max == None else args.res_w_max    
            res_h_max = presets_dict[preset]['res_h_max'] if args.res_h_max == None else args.res_h_max
        quality_max = presets_dict[preset]['quality_max'] if args.quality_max == None else args.quality_max
        quality_min = presets_dict[preset]['quality_min'] if args.quality_min == None else args.quality_min
        color_min = presets_dict[preset]['color_min'] if args.color_min == None else args.color_min
        color_max = presets_dict[preset]['color_max'] if args.color_max == None else args.color_max
        duration_min = presets_dict[preset]['duration_min'] if args.duration_min == None else args.duration_min
        duration_max = presets_dict[preset]['duration_max'] if args.duration_max == None else args.duration_max
        steps = presets_dict[preset]['steps'] if args.steps == None else args.steps

        title = args.title
        author = args.author
        default_emoji = args.default_emoji
        
        if download_signal:
            DownloadSignal.download_stickers_signal(download_signal, out_dir=input_dir)
        if download_line:
            DownloadLine.download_stickers_line(download_line, out_dir=input_dir)
        if download_telegram:
            DownloadTelegram.download_stickers_telegram(download_telegram, out_dir=input_dir, token=telegram_token)
        if download_kakao:
            DownloadKakao.download_stickers_kakao(download_kakao, out_dir=input_dir)
        
        if fake_vid:
            img_format = vid_format

        if no_compress == False:
            if vid_format == '.png' or vid_format == '.apng':
                print('Tips: Compressing .apng takes long time. Consider using another format or lowering "--steps"')

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
                
                pool.apply_async(StickerConvert.convert_and_compress_to_size, kwds={'in_f': in_f, 'out_f': out_f, 'vid_size_max': vid_size_max, 'img_size_max': img_size_max, 'res_w_min': res_w_min, 'res_w_max': res_w_max, 'res_h_min': res_h_min, 'res_h_max': res_h_max, 'quality_max': quality_max, 'quality_min': quality_min, 'fps_max': fps_max, 'fps_min': fps_min, 'color_min': color_min, 'color_max': color_max, 'duration_min': duration_min, 'duration_max': duration_max, 'fake_vid': fake_vid, 'steps': steps})

            pool.close()
            pool.join()

        urls = []
        if export_wastickers:
            urls += CompressWastickers.compress_wastickers(in_dir=output_dir, out_dir=output_dir, author=author, title=title, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, fake_vid=fake_vid, steps=steps, default_emoji=default_emoji)
        if export_signal:
            urls += UploadSignal.upload_stickers_signal(uuid=signal_uuid, password=signal_password, in_dir=output_dir, author=author, title=title, res_w_min=res_w_min, res_w_max=res_w_max, res_h_max=res_h_max, res_h_min=res_h_min, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, color_min=color_min, color_max=color_max, fake_vid=fake_vid, steps=steps, default_emoji=default_emoji)
        if export_telegram:
            urls += UploadTelegram.upload_stickers_telegram(token=telegram_token, user_id=telegram_userid, in_dir=output_dir, author=author, title=title, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, fake_vid=fake_vid, steps=steps, default_emoji=default_emoji)
        if export_imessage:
            urls += XcodeImessage.create_imessage_xcode(in_dir=output_dir, out_dir=output_dir, author=author, title=title, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, steps=steps, default_emoji=default_emoji)
        
        if urls != []:
            print(urls)