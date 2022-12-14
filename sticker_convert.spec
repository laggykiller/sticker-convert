# -*- mode: python ; coding: utf-8 -*-
import os
import shutil
import sys
import importlib

block_cipher = None

def get_bin(bin):
    which_result = shutil.which(bin)
    if which_result != None:
        return os.path.abspath(which_result)

if os.path.isdir('./sticker_convert/bin'):
    binaries = [('./sticker_convert/bin/*', './bin')]
else:
    binaries = []

datas = [('./sticker_convert/preset.json', './'), ('./sticker_convert/icon/*', './icon')]

bin_list = ['optipng', 'pngnq-s9', 'pngquant', 'apngdis', 'apngasm', 'ffmpeg', 'ffprobe', 'zip']
if sys.platform == 'win32':
    apngasm_dir = os.path.split(shutil.which("apngasm"))[0]
    magick_dir = os.path.split(shutil.which("magick"))[0]
    binaries += [(f'{magick_dir}/*.exe', './ImageMagick'), (f'{magick_dir}/*.dll', './ImageMagick'), (f'{magick_dir}/modules/coders', './ImageMagick/coders'), (f'{apngasm_dir}/*', './')]
elif sys.platform == 'darwin':
    binaries += [(f'./sticker_convert/ImageMagick/bin/*', f'./ImageMagick/bin'), (f'./sticker_convert/ImageMagick/lib/*', f'./ImageMagick/lib')]

if os.path.isdir('./sticker_convert/ImageMagick') == False and sys.platform == 'darwin':
    print('Warning: ImageMagick directory not found. You may run magick-compile-macos.sh')
    sys.exit()

for bin in bin_list:
    bin_path = get_bin(bin)
    if bin_path:
        binaries.append((bin_path, './bin'))

# signalstickers_client needs a custom cacert.pem
# https://stackoverflow.com/a/48068640
proot = os.path.dirname(importlib.import_module('signalstickers_client').__file__)
datas.append((os.path.join(proot, 'utils/ca/cacert.pem'), 'signalstickers_client/utils/ca/'))

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
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=['tkinter'],
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
    icon='./sticker_convert/icon/appicon.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=f'sticker-convert-{suffix}',
)
