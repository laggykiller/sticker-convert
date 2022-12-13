# -*- mode: python ; coding: utf-8 -*-
import os
import shutil

block_cipher = None

def get_bin(bin):
    which_result = shutil.which(bin)
    if which_result != None:
        return os.path.abspath(which_result)
    elif bin in os.listdir('./sticker_convert/bin'):
        return os.path.abspath('./sticker_convert/bin/{bin}')

bin_list = ['optipng', 'pngnq-s9', 'pngquant', 'apngdis', 'apngasm', 'ffmpeg', 'ffprobe', 'zip']

binaries = [('./sticker_convert/bin/*', './bin')]
for bin in bin_list:
    bin_path = get_bin(bin + '.exe')
    if bin_path:
        binaries.append((bin_path, './bin'))

apngasm_dir = os.path.split(shutil.which("apngasm"))[0]
magick_dir = os.path.split(shutil.which("magick"))[0]

a = Analysis(
    ['sticker_convert\\sticker_convert_gui.py'],
    pathex=[],
    binaries=binaries,
    datas=[('./sticker_convert/preset.json', './'), ('./sticker_convert/icon/*', './icon'), (f'{magick_dir}/*.exe', './magick'), (f'{magick_dir}/*.dll', './magick'), (f'{magick_dir}/modules/coders', './magick/coders'), (f'{apngasm_dir}/*', './')],
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
    name='sticker_convert_gui',
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
    name='sticker_convert_gui',
)
