import os
import subprocess

cmd_list = [
    'python',
    '-m',
    'nuitka',
    '--standalone',
    '--follow-imports',
    '--assume-yes-for-downloads',
    '--include-data-dir=src/sticker_convert/ios-message-stickers-template=ios-message-stickers-template',
    '--include-data-dir=src/sticker_convert/resources=resources',
    '--windows-icon-from-ico=src/sticker_convert/resources/appicon.ico',
    '--macos-target-arch=universal',
    '--macos-create-app-bundle',
    '--macos-app-icon=src/sticker_convert/resources/appicon.icns',
    '--enable-plugin=tk-inter',
    '--enable-plugin=multiprocessing',
    '--include-package-data=signalstickers_client',
    '--include-package=av',
    '--include-module=av.audio.codeccontext',
    '--include-module=av.video.codeccontext',
    '--include-package=imageio',
    '--user-package-configuration-file=nuitka.config.yml'
]

cmd_list.append('src/sticker-convert.py')
subprocess.run(cmd_list, shell=True)

for i in os.listdir('sticker-convert.dist/av.libs'):
    file_path = os.path.join('sticker-convert.dist', i)
    if os.path.isfile(file_path):
        os.remove(file_path)

for i in os.listdir('test.dist/av.libs'):
    file_path = os.path.join('test.dist', i)
    if os.path.isfile(file_path):
        os.remove(file_path)