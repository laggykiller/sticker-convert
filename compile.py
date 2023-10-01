#!/usr/bin/env python3
import os
import subprocess
import platform
import shutil

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

arch = os.environ.get('SC_COMPILE_ARCH')

if platform.system() == 'Windows':
    use_shell = True
else:
    use_shell = False

if shutil.which('python3'):
    python_bin = 'python3'
else:
    python_bin = 'python'

shutil.make_archive('src/sticker_convert/ios-message-stickers-template', 'zip', 'src/sticker_convert/ios-message-stickers-template')
shutil.rmtree('venv', ignore_errors=True)

if platform.system() == 'Darwin':
    subprocess.run(f'{python_bin} -m pip install --upgrade pip delocate'.split(' '))
    subprocess.run(f'{python_bin} -m venv venv'.split(' '))
    osx_run_in_venv('python -m pip install wheel nuitka')

    if not arch:
        osx_run_in_venv('python -m pip install --require-virtualenv -r requirements-build.txt')
    else:
        shutil.rmtree('wheel_arm', ignore_errors=True)
        shutil.rmtree('wheel_x64', ignore_errors=True)
        shutil.rmtree('wheel_universal2', ignore_errors=True)

        os.mkdir('wheel_arm')
        os.mkdir('wheel_x64')
        os.mkdir('wheel_universal2')

        osx_run_in_venv('python -m pip install -r requirements-src.txt')
        osx_run_in_venv('python -m pip download --require-virtualenv -r requirements-bin.txt --platform macosx_11_0_arm64 --only-binary=:all: -d wheel_arm')
        osx_run_in_venv('python -m pip download --require-virtualenv -r requirements-bin.txt --platform macosx_11_0_x86_64 --only-binary=:all: -d wheel_x64')

        osx_run_in_venv('clang -arch arm64 -shared -undefined dynamic_lookup -o ./scripts/stub-arm64.dylib ./scripts/stub.c')
        osx_run_in_venv('clang -arch x86_64 -shared -undefined dynamic_lookup -o ./scripts/stub-x86_64.dylib ./scripts/stub.c')

        stub_x64 = './scripts/stub-x86_64.dylib'
        stub_arm = './scripts/stub-arm64.dylib'
    
        create_universal_wheels('./wheel_arm', './wheel_x64', 'wheel_universal2')
        osx_run_in_venv(f'python -m pip install --require-virtualenv ./wheel_universal2/*')
    
        for dirpath, dirnames, filenames in os.walk('venv/lib'):
            for f in filenames:
                if os.path.splitext(f)[1] == '.dylib':
                    f_path = os.path.join(dirpath, f)
                    out = osx_run_in_venv(f'lipo -info {f_path}', get_stdout=True)
                    if f_path.endswith('-x86_64.dylib') or f_path.endswith('-arm64.dylib'):
                        continue
                    if 'x86_64' in out and 'arm64' in out:
                        continue
                    if 'x86_64' in out:
                        f_bak = os.path.splitext(f)[0] + '-x86_64.dylib'
                        f_bak_path = os.path.join(dirpath, f_bak)
                        os.rename(f_path, f_bak_path)
                        osx_run_in_venv(f'lipo {f_bak_path} {stub_arm} -create -output {f_path}', get_stdout=True)
                        print(f'Created fat library {f}')
                    elif 'arm64' in out:
                        f_bak = os.path.splitext(f)[0] + '-arm64.dylib'
                        f_bak_path = os.path.join(dirpath, f_bak)
                        os.rename(f_path, f_bak_path)
                        osx_run_in_venv(f'lipo {f_bak_path} {stub_x64} -create -output {f_path}', get_stdout=True)
                        print(f'Created fat library {f}')
else:
    subprocess.run(f'{python_bin} -m venv venv'.split(' '), shell=use_shell)
    subprocess.run(f'venv/Scripts/activate.bat'.split(' '), shell=use_shell)
    subprocess.run(f'{python_bin} -m pip install --upgrade pip'.split(' '), shell=use_shell)
    subprocess.run(f'{python_bin} -m pip install -r requirements-build.txt'.split(' '), shell=use_shell)

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
    '--include-package=av',
    '--include-module=av.audio.codeccontext',
    '--include-module=av.video.codeccontext',
    '--include-package=imageio',
    '--noinclude-data-file=tcl/opt0.4',
    '--noinclude-data-file=tcl/http1.0',
    '--user-package-configuration-file=nuitka.config.yml',
    '--macos-create-app-bundle',
    '--macos-app-icon=src/sticker_convert/resources/appicon.icns',
]

if platform.system() == 'Windows':
    cmd_list.append('--windows-icon-from-ico=src/sticker_convert/resources/appicon.ico')
elif platform.system() == 'Darwin' and arch:
    cmd_list.append(f'--macos-target-arch={arch}')

cmd_list.append('src/sticker-convert.py')
if platform.system() == 'Darwin':
    osx_run_in_venv(' '.join(cmd_list))
else:
    subprocess.run(cmd_list, shell=use_shell)

if platform.system() == 'Windows':
    for i in os.listdir('sticker-convert.dist/av.libs'):
        file_path = os.path.join('sticker-convert.dist', i)
        if os.path.isfile(file_path):
            os.remove(file_path)
elif platform.system() == 'Darwin' and arch:
    # https://github.com/Nuitka/Nuitka/issues/1511#issuecomment-1113260273
    site = osx_run_in_venv("python -c 'import site; print(site.getsitepackages()[0])'", get_stdout=True).strip()
    pil_dylibs = os.path.join(site, 'PIL/.dylibs')
    for i in os.listdir(pil_dylibs):
        if 'libjpeg' in i and not i.endswith('-arm64.dylib') and not i.endswith('-x86_64.dylib'):
            libjpeg = os.path.join(pil_dylibs, i)
            break
    os.makedirs('sticker-convert.app/Contents/MacOS/PIL/.dylibs', exist_ok=True)
    shutil.copy(libjpeg, 'sticker-convert.app/Contents/MacOS')
    shutil.copy(libjpeg, 'sticker-convert.app/Contents/MacOS/PIL/.dylibs')
    subprocess.run(f'codesign --force --deep -s - sticker-convert.app'.split(' '), stdout=subprocess.PIPE).stdout.decode()