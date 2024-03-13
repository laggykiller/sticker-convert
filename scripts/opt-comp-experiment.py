#!/usr/bin/env python3
"""
Script for finding optimal minimal compression arguments
based on compression on random pixels, which is an almost
worst case scenario for compression
"""

import copy
import csv
import itertools
import os
import sys
from math import ceil
from multiprocessing import Process, Queue, cpu_count
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from typing import Any, List, Optional, Tuple

import numpy
from apngasm_python._apngasm_python import APNGAsm, create_frame_from_rgba  # type: ignore
from PIL import Image
from tqdm import tqdm

os.chdir(Path(__file__).resolve().parent)
sys.path.append("../src")

from sticker_convert.converter import StickerConvert  # type: ignore # noqa: E402
from sticker_convert.job_option import CompOption  # type: ignore # noqa: E402
from sticker_convert.utils.callback import Callback, CallbackReturn  # type: ignore # noqa: E402

processes_max = ceil(cpu_count() / 2)

opt_comp_template = CompOption(
    size_max_img=1,
    size_max_vid=1,
    format_img=(".webp",),
    format_vid=(".apng",),
    fps_min=1,
    fps_max=1,
    res_w_min=256,
    res_w_max=256,
    res_h_min=256,
    res_h_max=256,
    steps=1,
    fake_vid=False,
)
opt_comp_template.set_quality(50)
opt_comp_template.set_color(50)
opt_comp_template.set_duration(3000)

formats = (
    ("img", ".webp"),
    ("vid", ".webp"),
    ("vidlong", ".webp"),
    ("img", ".png"),
    ("img618", ".png"),
    ("vid", ".apng"),
    ("vid618", ".apng"),
    ("vid", ".webm"),
    ("vid", ".gif"),
)


def generate_random_apng(res: int, fps: float, duration: float, out_f: str) -> None:
    apngasm = APNGAsm()  # type: ignore
    for _ in range(int(duration / 1000 * fps)):
        im = numpy.random.rand(res, res, 4) * 255
        frame = create_frame_from_rgba(im, res, res)
        frame.delay_num = int(1000 / fps)
        frame.delay_den = 1000
        apngasm.add_frame(frame)
    apngasm.assemble(out_f)


def generate_random_png(res: int, out_f: Path) -> None:
    im_numpy = numpy.random.rand(res, res, 4) * 255
    with Image.fromarray(im_numpy, "RGBA") as im:  # type: ignore
        im.save(out_f)


def compress_worker(
    work_queue: Queue[Optional[Tuple[Path, Path, CompOption]]],
    results_queue: Queue[
        Tuple[
            bool,
            int,
            Optional[int],
            Optional[int],
            Tuple[Optional[int], Optional[int]],
            Tuple[Optional[int], Optional[int]],
        ]
    ],
):
    for in_f, out_f, opt_comp in iter(work_queue.get, None):
        success, _, _, size = StickerConvert.convert(
            in_f=in_f,
            out_f=out_f,
            opt_comp=opt_comp,
            cb=Callback(),
            _cb_return=CallbackReturn(),
        )
        results_queue.put(
            (
                success,
                size,
                opt_comp.fps_max,
                opt_comp.res_w_max,
                opt_comp.get_quality(),
                opt_comp.get_color(),
            )
        )

    work_queue.put(None)


def write_result(csv_path: str, results_queue: Queue[Any], items: int) -> None:
    with open(csv_path, "w+", newline="") as f, tqdm(total=items) as progress:
        fieldnames = ["size", "fps", "res", "quality", "color"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for _, size, fps, res, quality, color in iter(results_queue.get, None):
            writer.writerow(
                {
                    "size": size,
                    "fps": fps,
                    "res": res,
                    "quality": quality,
                    "color": color,
                }
            )
            progress.update()


def main() -> None:
    os.makedirs("opt-comp-result", exist_ok=True)

    for img_or_vid, fmt in formats:
        csv_name = f'{fmt.replace(".", "")}-{img_or_vid}.csv'
        csv_path = Path("opt-comp-result", csv_name)

        if csv_path.is_file():
            with open(csv_path) as f:
                if f.read():
                    print(
                        f"Skip generating as result already exists for {fmt} ({img_or_vid})..."
                    )
                    continue
                else:
                    os.remove(csv_path)

        print(f"Generating result for compressing using preset {fmt} ({img_or_vid})...")

        with TemporaryDirectory() as tmpdir:
            random_png_path = Path(tmpdir, "random.png")
            result_path = Path("none" + fmt)

            rnd_res = 618 if "618" in img_or_vid else 512
            rnd_duration = 10000 if img_or_vid == "vidlong" else 3000

            print("Generating random png...")
            if "img" in img_or_vid:
                generate_random_png(rnd_res, random_png_path)
            else:
                generate_random_apng(rnd_res, 60, rnd_duration, str(random_png_path))
            print("Generated random png")

            if "img" in img_or_vid:
                fps_list = [1]
            else:
                fps_list = [i for i in range(10, 60, 5)]

            if "618" in img_or_vid:
                res_list = [618]  # 618 for imessage_large
            else:
                res_list = [i for i in range(256, 512, 8)]

            if fmt in (".apng", ".png"):
                quality_list = [95]
            else:
                quality_list = [i for i in range(50, 95, 5)]

            if fmt in (".apng", ".png"):
                color_list = [i for i in range(57, 257, 10)]
            else:
                color_list = [257]

            combinations = [
                i
                for i in itertools.product(fps_list, res_list, quality_list, color_list)
            ]

            work_queue: Queue[Optional[Tuple[Path, Path, CompOption]]] = Queue()
            results_queue: Queue[Any] = Queue()

            Thread(
                target=write_result, args=(csv_path, results_queue, len(combinations))
            ).start()

            processes: List[Process] = []
            for _ in range(processes_max):
                process = Process(
                    target=compress_worker, args=(work_queue, results_queue)
                )

                process.start()
                processes.append(process)

            for fps, res, quality, color in combinations:
                opt_comp = copy.deepcopy(opt_comp_template)
                opt_comp.set_size_max(None)
                opt_comp.set_format((fmt,))
                if img_or_vid == "vidlong":
                    opt_comp.set_duration(10000)
                else:
                    opt_comp.set_duration(3000)
                opt_comp.set_fps(fps)
                opt_comp.set_res(res)
                opt_comp.set_quality(quality)
                opt_comp.set_color(color)

                work_queue.put((random_png_path, result_path, opt_comp))

            work_queue.put(None)

            for process in processes:
                process.join()

            results_queue.put(None)


if __name__ == "__main__":
    main()
