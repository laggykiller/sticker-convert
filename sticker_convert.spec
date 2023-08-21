# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import importlib

block_cipher = None

datas = [('./src/sticker_convert/resources/*', './resources')]

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

a = Analysis(
    ['src/sticker_convert/__main__.py'],
    pathex=['src/sticker_convert'],
    binaries=None,
    datas=datas,
    hiddenimports=['tkinter', 'Pillow', 'opencv-python'],
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
    icon='./src/sticker_convert/resources/appicon.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    Tree('./src/sticker_convert/ios-message-stickers-template', prefix='ios-message-stickers-template'),
    strip=False,
    upx=True,
    upx_exclude=[],
    name=f'sticker-convert',
)
app = BUNDLE(coll,
    name=f'sticker-convert.app',
    icon='./src/sticker_convert/resources/appicon.icns',
    bundle_identifier=None)