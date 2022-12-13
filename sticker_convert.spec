# -*- mode: python ; coding: utf-8 -*-
import os
import shutil
import sys

block_cipher = None

def get_bin(bin):
    which_result = shutil.which(bin)
    if which_result != None:
        return os.path.abspath(which_result)

binaries = [('./sticker_convert/bin/*', './bin')]
datas = [('./sticker_convert/preset.json', './'), ('./sticker_convert/icon/*', './icon')]

bin_list = ['optipng', 'pngnq-s9', 'pngquant', 'apngdis', 'apngasm', 'ffmpeg', 'ffprobe', 'zip']
if sys.platform == 'win32':
    apngasm_dir = os.path.split(shutil.which("apngasm"))[0]
    magick_dir = os.path.split(shutil.which("magick"))[0]
    datas += [(f'{magick_dir}/*.exe', './ImageMagick'), (f'{magick_dir}/*.dll', './ImageMagick'), (f'{magick_dir}/modules/coders', './ImageMagick/coders'), (f'{apngasm_dir}/*', './')]
elif sys.platform == 'darwin':
    datas += [(f'ImageMagick/bin/*', f'./ImageMagick/bin'), (f'ImageMagick/lib/*', f'./ImageMagick/lib')]
elif sys.platform == 'linux':
    datas += [(f'ImageMagick/bin/*', f'./ImageMagick/bin'), (f'ImageMagick/lib/*', f'./ImageMagick/lib')]

if (sys.platform == 'linux' or sys.platform == 'darwin') and os.path.isdir('ImageMagick') == False:
    print('Warning: ImageMagick directory not found. You may run magick-compile.sh')
    sys.exit()

for bin in bin_list:
    bin_path = get_bin(bin)
    if bin_path:
        binaries.append((bin_path, './bin'))

a = Analysis(
    ['sticker_convert/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
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
    name=f'sticker-convert-{sys.platform}',
)
