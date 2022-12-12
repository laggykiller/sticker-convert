# -*- mode: python ; coding: utf-8 -*-
import os
import shutil

block_cipher = None

# optipng_path = shutil.which("optipng")
# pngnqs9_path = shutil.which("pngnq-s9")
# pngquant_path = shutil.which("pngquant")
# apngdis_path = shutil.which("apngdis")
apngasm_dir = os.path.split(shutil.which("apngasm"))[0]
# ffmpeg_path = shutil.which("ffmpeg")
# ffprobe_path = shutil.which("ffprobe")
# zip_path = shutil.which("zip")
# bzip2_path = shutil.which("bzip2")
magick_dir = os.path.split(shutil.which("magick"))[0]

a = Analysis(
    ['sticker_convert\\sticker_convert_cli.py'],
    pathex=[],
    binaries=[('./bin/*', './'), (f'{magick_dir}/magick.exe', './magick')],
    datas=[('preset.json', './'), (f'{magick_dir}/*.dll', './magick'), (f'{magick_dir}/modules/coders', './magick/coders'), (f'{apngasm_dir}/*', './'), ('icon/*', './icon')],
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
    name='sticker_convert_cli',
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
    icon='icon/appicon.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='sticker_convert_cli',
)
