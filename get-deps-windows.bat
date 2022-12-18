@echo off

cd sticker_convert

:: Preparing bin and ImageMagick directory
rd /s /q sticker_convert\bin >nul 2>&1
rd /s /q sticker_convert\ImageMagick >nul 2>&1

:: Get ImageMagick
mkdir ImageMagick
cd .\ImageMagick
curl --retry 5 -O -L "https://imagemagick.org/archive/binaries/ImageMagick-7.1.0-55-portable-Q16-x64.zip"
tar -xf ImageMagick-7.1.0-55-portable-Q16-x64.zip
del ImageMagick-7.1.0-55-portable-Q16-x64.zip
cd ..

:: Get apngasm
curl --retry 5 -O -L "https://github.com/laggykiller/apngasm/releases/download/3.1.3/apngasm_3.1-3_AMD64.zip"
tar -xf apngasm_3.1-3_AMD64.zip
del apngasm_3.1-3_AMD64.zip

:: Get apngdis
cd bin
curl --retry 5 -O -L "https://sourceforge.net/projects/apngdis/files/2.9/apngdis-2.9-bin-win64.zip"
tar -xf apngdis-2.9-bin-win64.zip
del apngdis-2.9-bin-win64.zip
del readme.txt

:: Get pngnq-s9
curl --retry 5 -O -L "https://sourceforge.net/projects/pngnqs9/files/pngnq-s9-2.0.2.zip"
tar -xf pngnq-s9-2.0.2.zip
move pngnq-s9-2.0.2\pngnq-s9.exe .
del pngnq-s9-2.0.2.zip
rd /s /q pngnq-s9-2.0.2

:: Get optipng
curl --retry 5 -O -L "https://sourceforge.net/projects/optipng/files/OptiPNG/optipng-0.7.7/optipng-0.7.7-win32.zip"
tar -xf optipng-0.7.7-win32.zip
move optipng-0.7.7-win32\optipng.exe .
del optipng-0.7.7-win32.zip
rd /s /q optipng-0.7.7-win32

:: Get pngquant
mkdir pngquant-dl
cd pngquant-dl
curl --retry 5 -O -L "https://github.com/laggykiller/pngquant/releases/download/2.17.0/pngquant-windows.zip"
tar -xf pngquant-windows.zip
cd ..
move pngquant-dl\pngquant\pngquant.exe .
rd /s /q pngquant-dl

:: Get ffmpeg
mkdir ffmpeg-dl
cd ffmpeg-dl
curl --retry 5 -O -L "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
tar -xf ffmpeg-master-latest-win64-gpl.zip
cd ..
move ffmpeg-dl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe .
move ffmpeg-dl\ffmpeg-master-latest-win64-gpl\bin\ffprobe.exe .
rd /s /q ffmpeg-dl

:: Get bzip2
mkdir bzip2-dl
cd bzip2-dl
curl --retry 5 -O -L "https://sourceforge.net/projects/gnuwin32/files/bzip2/1.0.5/bzip2-1.0.5-bin.zip"
tar -xf bzip2-1.0.5-bin.zip
cd ..
move bzip2-dl\bin\* .
rd /s /q bzip2-dl

:: Get zip
mkdir zip-dl
cd zip-dl
curl --retry 5 -O -L "http://downloads.sourceforge.net/gnuwin32/zip-3.0-bin.zip"
tar -xf zip-3.0-bin.zip
cd ..
move zip-dl\bin\* .
rd /s /q zip-dl

:: Go back to repo root
cd ..\..\