#!/usr/bin/env python3
'''
Script for finding optimal minimal compression arguments
based on compression on random pixels, which is an almost
worst case scenario for compression
'''

import os
import sys
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from multiprocessing import Process, Queue, cpu_count
import itertools
import copy
import csv

import numpy
from PIL import Image
from tqdm import tqdm
from apngasm_python._apngasm_python import create_frame_from_rgba, APNGAsm

os.chdir(Path(__file__).resolve().parent)
sys.path.append('../src')

from sticker_convert.converter import StickerConvert
from sticker_convert.job_option import CompOption

processes_max = math.ceil(cpu_count() / 2)

opt_comp_template = CompOption({
    'size_max': {
        'img': 1,
        'vid': 1
    },
    'format': {
        'img': '.webp',
        'vid': '.apng'
    },
    'fps': {
        'min': 1,
        'max': 1
    },
    'res': {
        'w': {
            'min': 256,
            'max': 256
        },
        'h': {
            'min': 256,
            'max': 256
        }
    },
    'quality': 50,
    'color': 50,
    'duration': 3000,
    'steps': 1,
    'fake_vid': False
})

formats = [
    ('img', '.webp'),
    ('vid', '.webp'),
    ('vidlong', '.webp'),
    ('img', '.png'),
    ('img618', '.png'),
    ('vid', '.apng'),
    ('vid618', '.apng'),
    ('vid', '.webm'),
    ('vid', '.gif')
]

def generate_random_apng(res: int, fps: float, duration: float, out_f: str):
    apngasm = APNGAsm()
    for _ in range(int(duration/1000*fps)):
        im = numpy.random.rand(res, res, 4) * 255
        frame = create_frame_from_rgba(im, res, res)
        frame.delay_num = int(1000 / fps)
        frame.delay_den = 1000
        apngasm.add_frame(frame)
    apngasm.assemble(out_f)

def generate_random_png(res: int, out_f: Path):
    im_numpy = numpy.random.rand(res, res, 4) * 255
    with Image.fromarray(im_numpy, 'RGBA') as im:
        im.save(out_f)

def compress_worker(jobs_queue: Queue, results_queue: Queue):
    for (in_f, out_f, opt_comp) in iter(jobs_queue.get, None):
        sticker = StickerConvert(in_f=in_f, out_f=out_f, opt_comp=opt_comp, cb_msg=False)
        success, in_f, out_f, size = sticker.convert()
        del sticker
        results_queue.put((success, size, opt_comp.fps_max, opt_comp.res_w_max, opt_comp.quality, opt_comp.color))
    
    jobs_queue.put(None)

def write_result(csv_path: str, results_queue: Queue, items: int):
    with open(csv_path, 'w+', newline='') as f, tqdm(total=items) as progress:
        fieldnames = ['size', 'fps', 'res', 'quality', 'color']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for (success, size, fps, res, quality, color) in iter(results_queue.get, None):
            writer.writerow({
                'size': size,
                'fps': fps,
                'res': res,
                'quality': quality,
                'color': color
            })
            progress.update()

def main():
    os.makedirs('opt-comp-result', exist_ok=True)
    
    for (img_or_vid, fmt) in formats:
        csv_name = f'{fmt.replace(".", "")}-{img_or_vid}.csv'
        csv_path = Path('opt-comp-result', csv_name)

        if csv_path.is_file():
            with open(csv_path) as f:
                if f.read():
                    print(f'Skip generating as result already exists for {fmt} ({img_or_vid})...')
                    continue
                else:
                    os.remove(csv_path)

        print(f'Generating result for compressing using preset {fmt} ({img_or_vid})...')

        with TemporaryDirectory() as tmpdir:
            random_png_path = Path(tmpdir, 'random.png')
            result_path = 'none' + fmt

            rnd_res = 618 if '618' in img_or_vid else 512
            rnd_duration = 10000 if img_or_vid == 'vidlong' else 3000

            print('Generating random png...')
            if 'img' in img_or_vid:
                generate_random_png(rnd_res, random_png_path)
            else:
                generate_random_apng(rnd_res, 60, rnd_duration, random_png_path)    
            print('Generated random png')

            if 'img' in img_or_vid:
                fps_list = [1]
            else:
                fps_list = [i for i in range(10, 60, 5)]

            if '618' in img_or_vid:
                res_list = [618] # 618 for imessage_large
            else:
                res_list = [i for i in range(256, 512, 8)]

            if fmt in ('.apng', '.png'):
                quality_list = [95]
            else:    
                quality_list = [i for i in range(50, 95, 5)]

            if fmt in ('.apng', '.png'):
                color_list = [i for i in range(57, 257, 10)]
            else:
                color_list = [257]
            
            combinations = [i for i in itertools.product(fps_list, res_list, quality_list, color_list)]

            jobs_queue = Queue()
            results_queue = Queue()
            
            Thread(target=write_result, args=(csv_path, results_queue, len(combinations))).start()

            processes = []
            for _ in range(processes_max):
                process = Process(
                    target=compress_worker,
                    args=(jobs_queue, results_queue)
                )

                process.start()
                processes.append(process)
            
            for fps, res, quality, color in combinations:
                opt_comp = copy.deepcopy(opt_comp_template)
                opt_comp.size_max = None
                opt_comp.format = fmt
                if img_or_vid == 'vidlong':
                    opt_comp.duration = 10000
                else:
                    opt_comp.duration = 3000
                opt_comp.fps = fps
                opt_comp.res = res
                opt_comp.quality = quality
                opt_comp.color = color

                jobs_queue.put((random_png_path, result_path, opt_comp))
            
            jobs_queue.put(None)
            
            for process in processes:
                process.join()

            results_queue.put(None)

if __name__ == '__main__':
    main()