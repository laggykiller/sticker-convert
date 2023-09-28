#!/usr/bin/env python3
# A script for creating universal2 wheels from x86_64 and arm64 wheels
# Used for creating macOS application

import sys
import os
import shutil
import subprocess

in_dir1 = sys.argv[1]
in_dir2 = sys.argv[2]
out_dir = sys.argv[3]

def search_wheel_in_dir(package: str, dir: str):
    for i in os.listdir(dir):
        if i.startswith(package):
            return i

def copy_if_universal(wheel_name: str, in_dir: str, out_dir: str):
    if wheel_name.endswith('universal2.whl') or wheel_name.endswith('any.whl'):
        src_path = os.path.join(in_dir, wheel_name)
        dst_path = os.path.join(
            out_dir, 
            wheel_name
            .replace('x86_64', 'universal2')
            .replace('arm64', 'universal2')
            )

        shutil.copy(src_path, dst_path)
        return True
    else:
        return False

for wheel_name_1 in os.listdir(in_dir1):
    package = wheel_name_1.split('-')[0]
    wheel_name_2 = search_wheel_in_dir(package, in_dir2)
    if copy_if_universal(wheel_name_1, in_dir1, out_dir):
        continue
    if copy_if_universal(wheel_name_2, in_dir2, out_dir):
        continue
    
    wheel_path_1 = os.path.join(in_dir1, wheel_name_1)
    wheel_path_2 = os.path.join(in_dir2, wheel_name_2)
    subprocess.run(['delocate-fuse', wheel_path_1, wheel_path_2, '-w', out_dir])

for wheel_name in os.listdir(out_dir):
    wheel_name_new = wheel_name.replace('x86_64', 'universal2').replace('arm64', 'universal2')

    src_path = os.path.join(out_dir, wheel_name)
    dst_path = os.path.join(out_dir, wheel_name_new)

    os.rename(src_path, dst_path)