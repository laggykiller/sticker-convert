@echo off

cd ./sticker_convert

:: Preparing bin and ImageMagick directory
rmdir -r ./sticker_convert/bin
rmdir -r ./sticker_convert/ImageMagick

:: Get ImageMagick
mkdir ImageMagick
cd ./ImageMagick
curl -O -L "https://imagemagick.org/archive/binaries/ImageMagick-7.1.0-54-portable-Q16-x64.zip"
tar -xf ImageMagick-7.1.0-54-portable-Q16-x64.zip
del ImageMagick-7.1.0-54-portable-Q16-x64.zip
cd ..

:: Get apngasm
curl -O -L "https://github.com/laggykiller/apngasm/releases/download/3.1.3/apngasm_3.1-3_AMD64.zip"
tar -xf apngasm_3.1-3_AMD64.zip
del apngasm_3.1-3_AMD64.zip

:: Get apngdis
cd ./bin
curl -O -L "https://sourceforge.net/projects/apngdis/files/2.8/apngdis-2.8-bin-win32.zip"
tar -xf apngdis-2.8-bin-win32.zip
del apngdis-2.8-bin-win32.zip

:: Get ffmpeg
curl -O -L "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
tar -xf ffmpeg-master-latest-win64-gpl.zip
move ./ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe ./
move ./ffmpeg-master-latest-win64-gpl/bin/ffprobe.exe ./
del ./ffmpeg-master-latest-win64-gpl.zip
rmdir -r ./ffmpeg-master-latest-win64-gpl

:: Get bzip2
mkdir bzip2
cd ./bzip2
curl -O -L "https://sourceforge.net/projects/gnuwin32/files/bzip2/1.0.5/bzip2-1.0.5-bin.zip"
tar -xf bzip2-1.0.5-bin.zip
cd ..
move ./bzip2/bin/* ./
rmdir -r ./bzip2

:: Get zip
mkdir zip
cd ./zip
curl -O -L "http://downloads.sourceforge.net/gnuwin32/zip-3.0-bin.zip"
tar -xf zip-3.0-bin.zip
cd ..
move ./zip/bin/* ./
rmdir -r ./zip
