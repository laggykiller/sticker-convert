# Running python script directly
## 1. Install python3
Install python3 from https://www.python.org/

## 2. Install python modules
Install the required python modules with `pip3 install requests ffmpeg-python lottie argparse signalstickers_client python-telegram-bot anyio`

## 3.1 Executables / Binaries (Windows)
For Windows, the following executables are required:
- `ffmpeg.exe` and `ffprobe.exe`
    - Both can be found in https://ffmpeg.org/download.html
    - Direct link (May break): https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z
- `magick.exe`
    - Download page for ImageMagick: https://imagemagick.org/script/download.php#windows
    - Note that you should choose one that ends with '-dll' and NOT portable version
    - Direct link (May break): https://imagemagick.org/archive/binaries/ImageMagick-7.1.0-54-Q16-HDRI-x64-dll.exe
- `zip.exe`
    - Download page: https://gnuwin32.sourceforge.net/packages/zip.htm
    - Direct link: http://downloads.sourceforge.net/gnuwin32/zip-3.0-bin.zip
    - All files in `bin` directory are needed
- `bzip2.exe`
    - Download page: https://gnuwin32.sourceforge.net/packages/bzip2.htm
    - Direct link: https://sourceforge.net/projects/gnuwin32/files/bzip2/1.0.5/bzip2-1.0.5-bin.zip
    - All files in `bin` directory are needed
- `optipng.exe`
    - Download page: https://sourceforge.net/projects/optipng/files/OptiPNG/
    - Direct link: https://sourceforge.net/projects/optipng/files/OptiPNG/optipng-0.7.7/optipng-0.7.7-win32.zip
- `pngnq-s9.exe`
    - Download page: https://sourceforge.net/projects/pngnqs9/files/
    - Direct link: https://sourceforge.net/projects/pngnqs9/files/pngnq-s9-2.0.1-win32.zip/download
- `pngquant.exe`
    - Download page: https://pngquant.org/
    - Direct link: https://pngquant.org/pngquant-windows.zip
- `apngdis.exe`
    - Download page: https://sourceforge.net/projects/apngdis/files/
    - Direct link: https://sourceforge.net/projects/apngdis/files/2.9/apngdis-2.9-bin-win64.zip
- `apngasm.exe`
    - Note that version 3 is required. Sourceforge only provides up to version 2.
    - Download page: https://github.com/apngasm/apngasm/releases
    - Direct link: https://github.com/apngasm/apngasm/releases/download/3.1.1/apngasm_3.1-0_AMD64.exe

Place executables inside `sticker_convert/bin`

## 3.2 Executables / Binaries (MacOS)
For MacOS, the following binaries are required:
- `ffmpeg` and `ffprobe`
    - Eaisest method is download from Homebrew `brew install ffmpeg`
- `magick`
    - Eaisest method is download from Homebrew `brew install imagemagick`
- `optipng`
    - Easiest method is download from Homebrew `brew install optipng`
- `pngnq-s9`
    - Compilation is required: https://github.com/ImageProcessing-ElectronicPublications/pngnq-s9
    - Compilation instructions are in https://github.com/ImageProcessing-ElectronicPublications/pngnq-s9/blob/master/INSTALL
    - Note that you should add `#include <string.h>` to `src/rwpng.c` or else compilation fails
- `pngquant`
    - Easiest method is download from Homebrew `brew install pngquant`
- `apngdis`
    - Note that version 2.9 is required. Some homebrew-extra provides apngdis but it is version 2.8
    - Download page: https://apngdis.sourceforge.net/
    - Direct link: https://sourceforge.net/projects/apngdis/files/2.9/apngdis-2.9-bin-macos.zip
    - Place the binary file inside `sticker_convert/bin`
- `apngasm`
    - Easiest method is download from Homebrew `brew install apngasm`
    - Note that version 3 is required. Sourceforge only provides up to version 2.

## 3.3 Executables / Binaries (Linux) (Tested with Ubuntu 20.04)
Some packages are usually not available in repo. To compile them, install these packages:

`sudo apt install gcc make cmake libpng-dev libboost-program-options-dev libboost-regex-dev libboost-system-dev libboost-filesystem-dev build-essential curl unzip pkg-config`

You may also need to install `tkinter` with `sudo apt install python3-tk`

For Linux, the following binaries are required:
- `ffmpeg` and `ffprobe`
    - Available in many distro's package manager (`sudo apt install ffmpeg`)
- `magick`
    - Available in many distro's package manager (`sudo apt install imagemagick`)
- `optipng`
    - Available in many distro's package manager (`sudo apt install optipng`)
- `pngnq-s9`
    - Many distro do not provide such package.
    - Compilation instructions:
    ```
    mkdir ~/pngnq-s9
    cd ~/pngnq-s9
    curl -O -L https://github.com/ImageProcessing-ElectronicPublications/pngnq-s9/archive/refs/tags/2.0.2.tar.gz
    tar xvzf 2.0.2.tar.gz
    cd ~/pngnq-s9/pngnq-s9-2.0.2
    # Fix bug that causes compilation to fail
    sed -i '1i#include <string.h>' src/rwpng.c
    ./configure
    make
    sudo make install
    cd
    rm -rf ~/pngnq-s9
    ```
- `pngquant`
    - Available in many distro's package manager (`sudo apt install pngquant`)
- `apngdis`
    - Note that version 2.9 is required. Ubuntu 20.04 and later provides this.
    - Compilation instructions in case you need it:
    ```
    mkdir ~/apngdis
    cd ~/apngdis
    curl -O -L https://sourceforge.net/projects/apngdis/files/2.9/apngdis-2.9-src.zip
    unzip apngdis-2.9-src.zip
    make
    sudo cp ~/apngdis/apngdis /usr/local/bin
    cd
    rm -rf ~/apngdis
    ```
- `apngasm`
    - Note that version 3 is required. Many distro provide version 2 in official repository.
    - For ubuntu, you may use this ppa repository: https://launchpad.net/~zero-tsuki/+archive/ubuntu/ppa/+packages
- `zip`
    - Available in many distro's package manager (`sudo apt install zip`)

Note that Arch Linux have all of the required packages in official repository and AUR.

## 4 Running the script
Change directory into `sticker_convert` directory and run `python ./main.py`

# Compiling
This repository uses `pyinstaller` for compiling. Install with `pip3 install pyinstaller`

## Compiling on windows
1. Refer to the instructions in running python script directly for installing python modules and executables
2. Run `pyinstaller sticker_convert.spec`
3. Compilation result in `dist` directory

##  Compiling on MacOS
1. Refer to the instructions in running python script directly for installing python modules and binaries (Except imagemagick, ffmpeg and ffprobe)
2. `ImageMagick` precompiled portable version is broken in newer releases of MacOS. You need to compile ImageMagick. Run `magick-compile-macos.sh` first
    - Ref1: https://stackoverflow.com/questions/55754551/how-to-install-imagemagick-portably-on-macos-when-i-cant-set-dyld-library-path
    - Ref2: https://github.com/ImageMagick/ImageMagick/issues/3129
3. Get static build of `ffmpeg` and `ffprobe` from: https://evermeet.cx/ffmpeg/ (If down, then go to https://ffmpeg.org/download.html). 
4. Place `ffmpeg`, `ffprobe` and `apngdis` inside `sticker_convert/bin`
5. Run `pyinstaller sticker_convert.spec`
6. Compilation result in `dist` directory