# -*- mode: python ; coding: utf-8 -*-
import os
import shutil
import sys
import importlib

block_cipher = None

def get_bin(bin):
    # Prioritize local binaries
    if sys.platform == 'win32' and os.path.isfile(f'./sticker_convert/bin/{bin}.exe'):
        return os.path.abspath(f'./sticker_convert/bin/{bin}.exe')
    elif os.path.isfile(f'./sticker_convert/bin/{bin}'):
        return os.path.abspath(f'./sticker_convert/bin/{bin}')

    which_result = shutil.which(bin)
    if which_result != None:
        return os.path.abspath(which_result)

def get_magick_dir():
    # Prioritize local binaries
    if os.path.isdir('./sticker_convert/ImageMagick'):
        return os.path.abspath(f'./sticker_convert/ImageMagick')
    else:
        magick_path = shutil.which("magick")
        if magick_path:
            return os.path.split(magick_path)[0]
        else:
            print('Error: ImageMagick directory not found.')
            if sys.platform == 'win32':
                print('You may run get-deps-windows.bat to get ImageMagick automagically')
            elif sys.platform == 'darwin':
                print('You may run get-deps-macos.sh to get ImageMagick automagically')
            sys.exit()

binaries = []
datas = [('./sticker_convert/resources/*', './resources')]

if sys.platform == 'win32':
    apngasm_path = shutil.which("apngasm")
    if apngasm_path:
        apngasm_dir = os.path.split(apngasm_path)[0]
        binaries += [(f'{apngasm_dir}/*', './bin')]
    
    magick_dir = get_magick_dir()
    binaries += [(f'{magick_dir}/*.exe', './ImageMagick'), (f'{magick_dir}/*.xml', './ImageMagick')]

    # Portable version does not have coders directory
    if os.path.isdir(f'{magick_dir}/modules/coders'):
        binaries += [(f'{magick_dir}/modules/coders', './ImageMagick/coders')]
    
    # Portable version does not have dll
    if [i for i in os.listdir(magick_dir) if os.path.splitext(i)[-1].lower() == '.dll'] != []:
        binaries += [(f'{magick_dir}/*.dll', './ImageMagick')]

    
elif sys.platform == 'darwin':
    binaries += [(f'./sticker_convert/ImageMagick/bin/*', f'./ImageMagick/bin')]
    binaries += [(f'./sticker_convert/ImageMagick/lib/*.dylib', f'./ImageMagick/lib')]
    binaries += [(f'./sticker_convert/ImageMagick/lib/*.a', f'./ImageMagick/lib')]
    binaries += [(f'./sticker_convert/ImageMagick/lib/ImageMagick/modules-Q16HDRI/coders/*.la', f'./ImageMagick/lib/ImageMagick/modules-Q16HDRI/coders')]
    binaries += [(f'./sticker_convert/ImageMagick/lib/ImageMagick/modules-Q16HDRI/coders/*.so', f'./ImageMagick/lib/ImageMagick/modules-Q16HDRI/coders')]
    binaries += [(f'./sticker_convert/ImageMagick/etc/ImageMagick-7/*.xml', f'./ImageMagick/etc/ImageMagick-7')]

bin_list = ['optipng', 'pngnq-s9', 'pngquant', 'apngdis', 'apngasm', 'ffmpeg', 'ffprobe', 'zip']
for bin in bin_list:
    bin_path = get_bin(bin)
    if bin_path:
        binaries.append((bin_path, './bin'))

# Add local binaries at last so they are not overwritten by those found in system
if os.path.isdir('./sticker_convert/bin'):
    binaries += [('./sticker_convert/bin/*', './bin')]

if os.path.isdir('./sticker_convert/lib'):
    binaries += [('./sticker_convert/lib/*', './lib')]

# signalstickers_client needs a custom cacert.pem
# https://stackoverflow.com/a/48068640
proot = os.path.dirname(importlib.import_module('signalstickers_client').__file__)
datas.append((os.path.join(proot, 'utils/ca/cacert.pem'), 'signalstickers_client/utils/ca/'))

# rlottie_python needs to copy rlottie dll
if sys.platform.startswith('win32') or sys.platform.startswith('cygwin'):
    rlottie_dll = 'rlottie.dll'
elif sys.platform.startswith('darwin'):
    rlottie_dll = 'librlottie.dylib'
else:
    rlottie_dll = 'rlottie.so'
proot = os.path.dirname(importlib.import_module('rlottie_python').__file__)
datas.append((os.path.join(proot, rlottie_dll), 'rlottie_python/'))

# Tkinter tix
# Example directory: %appdatalocal%/Programs/Python/Python310/tcl/tix8.4.3
for path in sys.path:
    tcl_path = os.path.join(path, 'tcl')
    if os.path.isdir(tcl_path):
        break

if sys.platform == 'win32':
    suffix = 'windows'
elif sys.platform == 'darwin':
    suffix = 'macos'
elif sys.platform == 'linux':
    suffix = 'linux'
else:
    suffix = 'unknown'

a = Analysis(
    ['sticker_convert/main.py'],
    pathex=['sticker_convert'],
    binaries=binaries,
    datas=datas,
    hiddenimports=['tkinter', 'Pillow', 'CairoSVG', 'opencv-python'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='sticker-convert',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='./sticker_convert/resources/appicon.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    Tree('./sticker_convert/ios-message-stickers-template', prefix='ios-message-stickers-template'),
    strip=False,
    upx=True,
    upx_exclude=[],
    name=f'sticker-convert-{suffix}',
)