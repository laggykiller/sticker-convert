#!/usr/bin/env python3
import sys
import os
import subprocess
import shutil
import zipfile
import urllib

try:
    from bs4 import BeautifulSoup
except ImportError:
    os.system('pip3 install beautifulsoup4')
    from bs4 import BeautifulSoup

def clean_dir(dir):
    shutil.rmtree(dir, ignore_errors=True)
    os.mkdir(dir)

def unzip(file):
    with zipfile.ZipFile(file, 'r') as zip_ref:
        zip_ref.extractall()

def download(url, file=None):
    if not file:
        file = url.split('/')[-1]
    for i in range(5):
        try:
            with open(file, 'wb+') as f:
                response = urllib.request.urlopen(url)
                f.write(response.read())
                break
        except Exception as e:
            print(f'Try {i}: Download failed for {url}')
            print(e)

def cp_files_in_dir(src, dst='.'):
    for i in os.listdir(src):
        src_f = os.path.join(src, i)
        dst_f = os.path.join(dst, i)
        shutil.copy(src_f, dst_f)

def win_cairo():
    print('Installing uniconvertor for getting cairo')
    url = 'https://downloads.sk1project.net/uc2/MS_Windows/uniconvertor-2.0rc5-win64_headless.msi'
    file = 'uniconvertor.msi'
    version = url.split('uniconvertor-')[1].split('-')[0]
    download(url, file)
    subprocess.run(['start', '/wait', 'msiexec.exe', '/qn', '/i', file], shell=True)
    os.remove(file)
    subprocess.run(['powershell', '-command', f"[Environment]::SetEnvironmentVariable('Path', $env:Path + ';C:\\Program Files\\UniConvertor-{version}\\dlls', 'Machine')"], shell=True)

def win_apngasm():
    print('Getting apngasm')
    url = 'https://github.com/laggykiller/apngasm/releases/download/3.1.3/apngasm_3.1-3_AMD64.zip'
    file = 'apngasm.zip'
    download(url, file)
    unzip(file)
    cp_files_in_dir('bin')
    os.remove(file)
    shutil.rmtree('bin')

    assert os.path.isfile('apngasm.exe')

def win_apngdis():
    print('Getting apngdis')
    url = 'https://sourceforge.net/projects/apngdis/files/2.9/apngdis-2.9-bin-win64.zip'
    file = 'apngdis.zip'
    download(url, file)
    unzip(file)
    os.remove(file)
    os.remove('readme.txt')

    assert os.path.isfile('apngdis.exe')

def win_pngnqs9():
    print('Getting pngnq-s9')
    url = 'https://sourceforge.net/projects/pngnqs9/files/pngnq-s9-2.0.2.zip'
    file = 'pngnq-s9.zip'
    version = url.split('pngnq-s9-')[1].split('.zip')[0]
    download(url, file)
    unzip(file)
    os.remove(file)
    shutil.move(f'pngnq-s9-{version}/pngnq-s9.exe', './')
    shutil.rmtree(f'pngnq-s9-{version}')

    assert os.path.isfile('pngnq-s9.exe')

def win_optipng():
    print('Getting optipng')
    url = 'https://sourceforge.net/projects/optipng/files/optipng-0.7.7-win32.zip'
    file = 'optipng.zip'
    version = url.split('optipng-')[-1].split('.zip')[0]
    download(url, file)
    unzip(file)
    os.remove(file)
    shutil.move(f'optipng-{version}/optipng.exe', './')
    shutil.rmtree(f'optipng-{version}')

    assert os.path.isfile('optipng.exe')

def win_pngquant():
    print('Getting pngquant')
    url = 'https://github.com/laggykiller/pngquant/releases/download/2.17.0/pngquant-windows.zip'
    file = 'pngquant.zip'
    os.mkdir('pngquant-dl')
    os.chdir('pngquant-dl')
    download(url, file)
    unzip(file)
    os.chdir('../')
    shutil.move('pngquant-dl/pngquant/pngquant.exe', './')
    shutil.rmtree('pngquant-dl')

def win_ffmpeg():
    print('Getting ffmpeg')
    url = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip'
    file = url.split('/')[-1]
    os.mkdir('ffmpeg-dl')
    os.chdir('ffmpeg-dl')
    download(url, file)
    unzip(file)
    os.chdir('../')
    shutil.move(f'ffmpeg-dl/{file.replace(".zip", "")}/bin/ffmpeg.exe', './')
    shutil.move(f'ffmpeg-dl/{file.replace(".zip", "")}/bin/ffprobe.exe', './')
    shutil.rmtree('ffmpeg-dl')

def win_bzip2():
    print('Getting bzip2')
    url = 'https://sourceforge.net/projects/gnuwin32/files/bzip2/1.0.5/bzip2-1.0.5-bin.zip'
    file = 'bzip.zip'
    os.mkdir('bzip2-dl')
    os.chdir('bzip2-dl')
    download(url, file)
    unzip(file)
    os.chdir('../')
    cp_files_in_dir('bzip2-dl/bin')
    shutil.rmtree('bzip2-dl')

def win_zip():
    print('Getting zip')
    url = 'http://downloads.sourceforge.net/gnuwin32/zip-3.0-bin.zip'
    file = 'zip.zip'
    os.mkdir('zip-dl')
    os.chdir('zip-dl')
    download(url, file)
    unzip(file)
    os.chdir('../')
    cp_files_in_dir('zip-dl/bin')
    shutil.rmtree('zip-dl')

def win_magick():
    print('Getting magick')
    soup = BeautifulSoup(urllib.request.urlopen("https://imagemagick.org/archive/binaries").read().decode(), "html.parser")

    for x in soup.find_all("a", href=True):
        file = x['href']
        if file.startswith('ImageMagick-7') and file.endswith('portable-Q16-x64.zip'):
            url = 'https://imagemagick.org/archive/binaries/' + file
            break
    download(url, file)
    unzip(file)
    os.remove(file)
    os.chdir('../')

def mac_brew():
    print('Installing packages from brew')
    download('https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh')
    subprocess.run(['NONINTERACTIVE=1', '/bin/bash', '-c', '"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'], shell=True)
    subprocess.run(['brew', 'install', 'pkg-config', 'apngasm', 'imagemagick', 'pngquant', 'optipng', 'libwebm'], shell=True)

def mac_apngasm():
    shutil.copy('/usr/local/bin/apngasm', './')

def mac_apngdis():
    print('Getting apngdis')
    url = 'https://sourceforge.net/projects/apngdis/files/2.9/apngdis-2.9-bin-macos.zip'
    file = 'apngdis.zip'
    download(url, file)
    unzip(file)
    os.remove(file)
    os.remove('readme.txt')

def mac_pngnqs9():
    print('Getting pngnq-s9')
    url = 'https://github.com/ImageProcessing-ElectronicPublications/pngnq-s9/archive/refs/tags/2.0.2.tar.gz'
    file = 'pngnqs9.zip'
    version = url.split('/')[-1].replace('.tar.gz', '')
    os.mkdir('pngnq-s9-dl')
    os.chdir('pngnq-s9-dl')
    download(url, file)
    unzip(file)
    os.chdir(f'pngnq-s9-{version}')
    with open('src/rwpng.c') as f:
        rwpng = f.read()
    with open('src/rwpng.c', 'w+') as f:
        f.write('#include <string.h>\n')
        f.write('rwpng')
    shutil.run(['./configure'])
    shutil.run(['make'])
    # shutil.run(['make', 'install'])
    shutil.run(['chmod', '+x', 'src/pngnq-s9'])
    shutil.move(f'pngnq-s9-dl/pngnq-s9-{version}/src/pngnq-s9', '.')
    shutil.rmtree('pngnq-s9-dl')

def mac_pngquant():
    print('Getting pngquant')
    shutil.copy('/usr/local/bin/pngquant', './')

def mac_optipng():
    cp_files_in_dir('/usr/local/opt/optipng/bin')

def mac_ffmpeg():
    print('Getting ffmpeg')
    url = 'https://evermeet.cx/ffmpeg/getrelease/zip'
    file = 'ffmpeg.zip'
    download(url, file)
    unzip(file)
    os.remove(file)

def mac_ffprobe():
    print('Getting ffprobe')
    url = 'https://evermeet.cx/ffprobe/getrelease/zip'
    file = 'ffprobe.zip'
    download(url, file)
    unzip(file)
    os.remove(file)

def mac_magick():
    print('Getting magick')
    shutil.copy('/usr/local/opt/imagemagick/bin', './')
    shutil.copy('/usr/local/opt/imagemagick/lib', './')
    shutil.copy('/usr/local/opt/imagemagick/etc', './')

def mac_cp_lib():
    print('Getting libraries')
    packages = (
        'aom',
        'apngasm',
        'boost',
        'brotli',
        # 'docbook-xsl',
        # 'docbook',
        'fontconfig',
        'freetype',
        'gettext',
        'ghostscript',
        'giflib',
        'glib',
        # 'gnu-getopt',
        'highway',
        'icu4c',
        # 'imagemagick',
        'imath',
        'jasper',
        'jbig2dec',
        'jpeg-turbo',
        'jpeg-xl',
        'libde265',
        'libheif',
        'libidn',
        'liblqr',
        'libomp',
        'libpng',
        'libraw',
        'libtiff',
        'libtool',
        'libvmaf',
        'libwebm',
        'little-cms',
        'little-cms2',
        'lz4',
        # 'lzlib',
        # 'm4',
        'openexr',
        'openjpeg',
        'pcre2',
        # 'shared-mime-info',
        'webp',
        'x265',
        # 'xmlto',
        'xz',
        'zstd'
    )
    for package in packages:
        cp_files_in_dir(f'/usr/local/opt/{package}/lib')

if sys.platform not in ('win32', 'darwin'):
    print(f'{sys.platform} is not supported')
    sys.exit()

# Prepare bin directory
os.chdir('sticker_convert')
clean_dir('bin')
clean_dir('lib')
clean_dir('ImageMagick')

if sys.platform == 'win32':
    print('Notice: You should run this script as Administrator!')
    os.chdir('bin')
    win_apngasm()
    win_apngdis()
    win_cairo()
    win_ffmpeg()
    win_optipng()
    win_pngnqs9()
    win_pngquant()
    win_bzip2()
    win_zip()
    os.chdir('../ImageMagick')
    win_magick()
elif sys.platform == 'darwin':
    print('Notice: You should run this script with sudo!')
    os.chdir('bin')
    mac_brew()
    mac_apngasm()
    mac_apngdis()
    mac_pngnqs9()
    mac_pngquant()
    mac_optipng()
    mac_ffmpeg()
    mac_ffprobe()
    os.chdir('../ImageMagick')
    mac_magick()
    os.chdir('../lib')
    mac_cp_lib()

os.chdir('../../')