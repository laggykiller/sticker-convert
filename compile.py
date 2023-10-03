#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import shutil

sys.path.append('./src')
from sticker_convert.__init__ import __version__

def osx_run_in_venv(cmd, get_stdout=False):
    if os.path.isfile('/bin/zsh'):
        sh_cmd = ['/bin/zsh', '-c']
    else:
        sh_cmd = ['/bin/bash', '-c']
    venv_cmd = 'source venv/bin/activate && '

    if get_stdout:
        return subprocess.run(sh_cmd + [venv_cmd + cmd], stdout=subprocess.PIPE).stdout.decode()
    else:
        return subprocess.run(sh_cmd + [venv_cmd + cmd])

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

def create_universal_wheels(in_dir1, in_dir2, out_dir):
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
        print(f'Created universal wheel {wheel_path_1} {wheel_path_2}')

    for wheel_name in os.listdir(out_dir):
        wheel_name_new = wheel_name.replace('x86_64', 'universal2').replace('arm64', 'universal2')

        src_path = os.path.join(out_dir, wheel_name)
        dst_path = os.path.join(out_dir, wheel_name_new)

        os.rename(src_path, dst_path)
        print(f'Renamed universal wheel {dst_path}')

def osx_install_universal2_dep():
    shutil.rmtree('wheel_arm', ignore_errors=True)
    shutil.rmtree('wheel_x64', ignore_errors=True)
    shutil.rmtree('wheel_universal2', ignore_errors=True)

    os.mkdir('wheel_arm')
    os.mkdir('wheel_x64')
    os.mkdir('wheel_universal2')

    osx_run_in_venv('python -m pip download --require-virtualenv -r requirements.txt --platform macosx_11_0_arm64 --only-binary=:all: -d wheel_arm')
    osx_run_in_venv('python -m pip download --require-virtualenv -r requirements.txt --platform macosx_11_0_x86_64 --only-binary=:all: -d wheel_x64')

    create_universal_wheels('./wheel_arm', './wheel_x64', 'wheel_universal2')
    osx_run_in_venv('python -m pip install --require-virtualenv ./wheel_universal2/*')

def nuitka(python_bin, arch):
    cmd_list = [
        python_bin,
        '-m',
        'nuitka',
        '--standalone',
        '--follow-imports',
        '--assume-yes-for-downloads',
        '--include-data-files=src/sticker_convert/ios-message-stickers-template.zip=ios-message-stickers-template.zip',
        '--include-data-dir=src/sticker_convert/resources=resources',
        '--enable-plugin=tk-inter',
        '--enable-plugin=multiprocessing',
        '--include-package-data=signalstickers_client',
        '--include-package=imageio',
        '--noinclude-data-file=tcl/opt0.4',
        '--noinclude-data-file=tcl/http1.0'
    ]

    if platform.system() == 'Windows':
        cmd_list.append('--windows-icon-from-ico=src/sticker_convert/resources/appicon.ico')
    elif platform.system() == 'Darwin' and arch:
        cmd_list.append('--disable-console')
        cmd_list.append('--macos-create-app-bundle')
        cmd_list.append('--macos-app-icon=src/sticker_convert/resources/appicon.icns')
        cmd_list.append(f'--macos-target-arch={arch}')
        cmd_list.append(f'--macos-app-version={__version__}')
    else:
        cmd_list.append('--linux-icon=src/sticker_convert/resources/appicon.png')

    cmd_list.append('src/sticker-convert.py')
    if platform.system() == 'Darwin':
        osx_run_in_venv(' '.join(cmd_list))
    else:
        subprocess.run(cmd_list, shell=True)

def win_patch():
    for i in os.listdir('sticker-convert.dist/av.libs'):
        file_path = os.path.join('sticker-convert.dist', i)
        if os.path.isfile(file_path):
            os.remove(file_path)

def osx_patch():
    # https://github.com/pyinstaller/pyinstaller/issues/5154#issuecomment-1567603461
    os.rename('sticker-convert.app/Contents/MacOS/sticker-convert', 'sticker-convert.app/Contents/MacOS/sticker-convert-cli')
    with open('sticker-convert.app/Contents/MacOS/sticker-convert', 'w+') as f:
        f.write('#!/bin/bash\n')
        f.write('cd "$(dirname "$0")"\n')
        f.write('open ./sticker-convert-cli')
    os.chmod('sticker-convert.app/Contents/MacOS/sticker-convert', 0o744)

    osx_run_in_venv('codesign --force --deep -s - sticker-convert.app')

def compile():
    arch = os.environ.get('SC_COMPILE_ARCH')
    python_bin = os.path.abspath(sys.executable)

    ios_stickers_path = 'src/sticker_convert/ios-message-stickers-template'
    ios_stickers_zip = ios_stickers_path + '.zip'
    if os.path.isfile(ios_stickers_zip):
        os.remove(ios_stickers_zip)
    shutil.make_archive(ios_stickers_path, 'zip', ios_stickers_path)

    if platform.system() == 'Windows':
        subprocess.run(f'{python_bin} -m pip install --upgrade pip'.split(' '), shell=True)
        subprocess.run(f'{python_bin} -m pip install -r requirements-build.txt'.split(' '), shell=True)
        subprocess.run(f'{python_bin} -m pip install -r requirements.txt'.split(' '), shell=True)
    elif platform.system() == 'Darwin':
        shutil.rmtree('venv', ignore_errors=True)
        subprocess.run(f'{python_bin} -m pip install --upgrade pip delocate'.split(' '))
        subprocess.run(f'{python_bin} -m venv venv'.split(' '))
        python_bin = 'python'
        osx_run_in_venv('python -m pip install -r requirements-build.txt')
        if not arch:
            osx_run_in_venv('python -m pip install --require-virtualenv -r requirements.txt')
        else:
            osx_install_universal2_dep()

    nuitka(python_bin, arch)

    if platform.system() == 'Windows':
        win_patch()
    elif platform.system() == 'Darwin':
        osx_patch()

if __name__ == '__main__':
    compile()