import os
import sys
from utils.sticker_convert import StickerConvert
from utils.format_verify import FormatVerify
from downloaders.download_line import DownloadLine
from downloaders.download_signal import DownloadSignal
from downloaders.download_telegram import DownloadTelegram
from downloaders.download_kakao import DownloadKakao
from uploaders.upload_signal import UploadSignal
from uploaders.upload_telegram import UploadTelegram
from uploaders.compress_wastickers import CompressWastickers
import argparse
import json
import shutil
import multiprocessing

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

if sys.platform == 'darwin' and getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    script_path = os.path.join(os.path.split(__file__)[0], '../')
else:
    script_path = os.path.split(__file__)[0]
os.chdir(os.path.abspath(script_path))

def main():
    preset_present = os.path.isfile('preset.json')
    if preset_present == False:
        print('Warning: preset.json cannot be found')
        return
    else:
        with open('preset.json') as f:
            presets_dict = json.load(f)

    parser = argparse.ArgumentParser(description='CLI for stickers-convert')
    parser.add_argument('--input-dir', dest='input_dir', default='./stickers_input', help='Specify input directory')
    parser.add_argument('--output-dir', dest='output_dir', default='./stickers_output', help='Specify output directory')
    parser.add_argument('--download-signal', dest='download_signal', help='Download signal stickers from a URL as input (e.g. https://signal.art/addstickers/#pack_id=xxxxx&pack_key=xxxxx)')
    parser.add_argument('--download-telegram', dest='download_telegram', help='Download telegram stickers from a URL as input (e.g. https://telegram.me/addstickers/xxxxx)')
    parser.add_argument('--download-line', dest='download_line', help='Download line stickers from a URL / ID as input (e.g. https://store.line.me/stickershop/product/1234/en OR line://shop/detail/1234 OR 1234)')
    parser.add_argument('--download-kakao', dest='download_kakao', help='Download kakao stickers from a URL / ID as input (e.g. https://e.kakao.com/t/xxxxx)')

    parser.add_argument('--export-wastickers', dest='export_wastickers', action='store_true', help='Create a .wastickers file for uploading to whatsapp')
    parser.add_argument('--export-signal', dest='export_signal', action='store_true', help='Upload to signal')
    parser.add_argument('--export-telegram', dest='export_telegram', action='store_true', help='Upload to telegram')

    parser.add_argument('--no-compress', dest='no_compress', action='store_true', help='Do not compress files. Useful for only downloading stickers')
    parser.add_argument('--preset', dest='preset', default='custom', choices=presets_dict.keys(), help='Use preset')
    parser.add_argument('--fps-min', dest='fps_min', type=int, default=None, help='Set minimum output fps')
    parser.add_argument('--fps-max', dest='fps_max', type=int, default=None, help='Set maximum output fps')
    parser.add_argument('--res-min', dest='res_min', type=int, default=None, help='Set minimum output resolution')
    parser.add_argument('--res-max', dest='res_max', type=int, default=None, help='Set maximum output resolution')
    parser.add_argument('--quality-min', dest='quality_min', type=int, default=None, help='Set minimum quality')
    parser.add_argument('--quality-max', dest='quality_max', type=int, default=None, help='Set maximum quality')
    parser.add_argument('--color-min', dest='color_min', type=int, default=None, help='Set minimum number of colors (For converting to apng)')
    parser.add_argument('--color-max', dest='color_max', type=int, default=None, help='Set maximum number of colors (For converting to apng)')
    parser.add_argument('--steps', dest='steps', type=int, default=None, help='Set number of divisions between min and max settings. Higher value is slower but yields file more closer to the specified file size limit')
    parser.add_argument('--vid-size-max', dest='vid_size_max', type=int, default=None, help='Set maximum file size limit for animated stickers')
    parser.add_argument('--img-size-max', dest='img_size_max', type=int, default=None, help='Set maximum file size limit for static stickers')
    parser.add_argument('--vid-format', dest='vid_format', default=None, help='Set file format if input is a animated')
    parser.add_argument('--img-format', dest='img_format', default=None, help='Set file format if input is a static image')
    parser.add_argument('--default-emoji', dest='default_emoji', default=presets_dict['custom']['default_emoji'], help='Set the default emoji for uploading signal and telegram sticker packs')
    parser.add_argument('--processes', dest='processes', type=int, help='Set number of processes. Default to cpus in system')

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
        with open('creds.json') as f:
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
        with open('creds.json', 'w+') as f:
            json.dump(creds, f, indent=4)
        print('Saved credentials to creds.json')
    
    if os.path.isdir(args.input_dir) == False:
        print('Warning: Cannot find the specified input directory. Creating for you...')
        os.makedirs(args.input_dir)
    if os.path.isdir(args.output_dir) == False:
        print('Info: Cannot find the specified output directory. Creating for you...')
        os.makedirs(args.output_dir)
    
    processes = args.processes if args.processes else multiprocessing.cpu_count()
    
    if args.preset == 'custom':
        if sum((args.export_wastickers, args.export_signal, args.export_telegram)) > 1:
            # Let the verify functions in export do the compression
            args.no_compress = True
        elif args.export_wastickers:
            args.preset = 'whatsapp'
        elif args.export_signal:
            args.preset = 'signal'
        elif args.export_telegram:
            args.preset = 'telegram'

    vid_size_max = presets_dict[args.preset]['vid_size_max'] if args.vid_size_max == None else args.vid_size_max
    img_size_max = presets_dict[args.preset]['img_size_max'] if args.img_size_max == None else args.img_size_max
    vid_format = presets_dict[args.preset]['vid_format'] if args.vid_format == None else args.vid_format
    img_format = presets_dict[args.preset]['img_format'] if args.img_format == None else args.img_format
    fps_min = presets_dict[args.preset]['fps_min'] if args.fps_min == None else args.fps_min
    fps_max = presets_dict[args.preset]['fps_max'] if args.fps_max == None else args.fps_max
    res_min = presets_dict[args.preset]['res_min'] if args.res_min == None else args.res_min
    res_max = presets_dict[args.preset]['res_max'] if args.res_max == None else args.res_max
    quality_max = presets_dict[args.preset]['quality_max'] if args.quality_max == None else args.quality_max
    quality_min = presets_dict[args.preset]['quality_min'] if args.quality_min == None else args.quality_min
    color_min = presets_dict[args.preset]['color_min'] if args.color_min == None else args.color_min
    color_max = presets_dict[args.preset]['color_max'] if args.color_max == None else args.color_max
    steps = presets_dict[args.preset]['steps'] if args.steps == None else args.steps
    
    if args.download_signal:
        DownloadSignal.download_stickers_signal(args.download_signal, out_dir=args.input_dir)
    if args.download_line:
        DownloadLine.download_stickers_line(args.download_line, out_dir=args.input_dir)
    if args.download_telegram:
        DownloadTelegram.download_stickers_telegram(args.download_telegram, out_dir=args.input_dir, token=telegram_token)
    if args.download_kakao:
        DownloadKakao.download_stickers_kakao(args.download_kakao, out_dir=args.input_dir)

    if args.no_compress == False:
        if vid_format == '.apng':
            print('Tips: Compressing .apng takes long time. Consider using another format or lowering "--steps"')

        pool = multiprocessing.Pool(processes=processes)
        for i in os.listdir(args.input_dir):
            in_f = os.path.join(args.input_dir, i)

            if os.path.splitext(i)[1] == '.txt':
                shutil.copy(in_f, os.path.join(args.output_dir, i))
                continue

            if FormatVerify.is_anim(in_f):
                format = vid_format
            else:
                format = img_format

            out_f = os.path.join(args.output_dir, os.path.splitext(i)[0] + format)
            
            pool.apply_async(StickerConvert.convert_and_compress_to_size, kwds={'in_f': in_f, 'out_f': out_f, 'vid_size_max': vid_size_max, 'img_size_max': img_size_max, 'res_max': res_max, 'res_min': res_min, 'quality_max': quality_max, 'quality_min': quality_min, 'fps_max': fps_max, 'fps_min': fps_min, 'color_min': color_min, 'color_max': color_max, 'steps': steps})

        pool.close()
        pool.join()

    urls = []
    if args.export_wastickers:
        CompressWastickers.compress_wastickers(in_dir=args.output_dir, out_dir=args.output_dir, author=args.author, title=args.title, res_max=res_max, res_min=res_min, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, steps=steps, default_emoji=args.default_emoji)
    if args.export_signal:
        urls += UploadSignal.upload_stickers_signal(uuid=signal_uuid, password=signal_password, in_dir=args.output_dir, author=args.author, title=args.title, res_max=res_max, res_min=res_min, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, color_min=color_min, color_max=color_max, steps=steps, default_emoji=args.default_emoji)
    if args.export_telegram:
        urls += UploadTelegram.upload_stickers_telegram(token=telegram_token, user_id=telegram_userid, in_dir=args.output_dir, author=args.author, title=args.title, res_max=res_max, res_min=res_min, quality_max=quality_max, quality_min=quality_min, fps_max=fps_max, fps_min=fps_min, steps=steps, default_emoji=args.default_emoji)
    
    if urls != []:
        print(urls)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
