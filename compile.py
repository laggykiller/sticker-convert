#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

cmd_list = [
    os.path.abspath(sys.executable),
    '-m',
    'nuitka',
    '--standalone',
    '--follow-imports',
    '--assume-yes-for-downloads',
    '--include-data-dir=src/sticker_convert/ios-message-stickers-template=ios-message-stickers-template',
    '--include-data-dir=src/sticker_convert/resources=resources',
    '--enable-plugin=tk-inter',
    '--enable-plugin=multiprocessing',
    '--include-package-data=signalstickers_client',
    '--include-package=av',
    '--include-module=av.audio.codeccontext',
    '--include-module=av.video.codeccontext',
    '--include-package=imageio',
    '--user-package-configuration-file=nuitka.config.yml',
    '--macos-target-arch=universal',
    '--macos-create-app-bundle',
    '--macos-app-icon=src/sticker_convert/resources/appicon.icns',
]

if platform.system() == 'Windows':
    cmd_list.append('--windows-icon-from-ico=src/sticker_convert/resources/appicon.ico')
    use_shell = True
else:
    use_shell = False

cmd_list.append('src/sticker-convert.py')
subprocess.run(cmd_list, shell=use_shell)

for i in os.listdir('sticker-convert.dist/av.libs'):
    file_path = os.path.join('sticker-convert.dist', i)
    if os.path.isfile(file_path):
        os.remove(file_path)
