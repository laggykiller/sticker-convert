@echo off

cd sticker_convert

:: Preparing bin and ImageMagick directory
rmdir -r sticker_convert\bin >nul 2>&1
rmdir -r sticker_convert\ImageMagick >nul 2>&1

:: Get ImageMagick
mkdir ImageMagick
cd .\ImageMagick
curl -O -L "https://imagemagick.org/archive/binaries/ImageMagick-7.1.0-54-portable-Q16-x64.zip"
tar -xf ImageMagick-7.1.0-54-portable-Q16-x64.zip
del ImageMagick-7.1.0-54-portable-Q16-x64.zip
cd ..

:: Get apngasm
curl -O -L "https://github.com/laggykiller/apngasm/releases/download/3.1.3/apngasm_3.1-3_AMD64.zip"
tar -xf apngasm_3.1-3_AMD64.zip
del apngasm_3.1-3_AMD64.zip

:: Get apngdis
cd bin
curl -O -L "https://sourceforge.net/projects/apngdis/files/2.8/apngdis-2.8-bin-win32.zip"
tar -xf apngdis-2.8-bin-win32.zip
del apngdis-2.8-bin-win32.zip

:: Get pngnq-s9
curl -O -L "https://sourceforge.net/projects/pngnqs9/files/pngnq-s9-2.0.1-win32.zip"
tar -xf pngnq-s9-2.0.1-win32.zip
move pngnq-s9-2.0.1-win32\pngnq-s9-2.0.1-win32.exe .\pngnq-s9.exe
del pngnq-s9-2.0.1-win32.zip
rmdir -r pngnq-s9-2.0.1-win32

:: Get optipng
curl -O -L "https://sourceforge.net/projects/optipng/files/OptiPNG/optipng-0.7.7/optipng-0.7.7-win32.zip"
tar -xf optipng-0.7.7-win32.zip
move optipng-0.7.7-win32\optipng.exe .
del optipng-0.7.7-win32.zip
rmdir -r optipng-0.7.7-win32

:: Get pngquant
curl -O -L "https://pngquant.org/pngquant-windows.zip"
tar -xf pngquant-windows.zip
move pngquant\pngquant.exe .
del pngquant-windows.zip
rmdir -r pngquant

:: Get ffmpeg
curl -O -L "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
tar -xf ffmpeg-master-latest-win64-gpl.zip
move ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe .
move ffmpeg-master-latest-win64-gpl\bin\ffprobe.exe .
del ffmpeg-master-latest-win64-gpl.zip
rmdir -r ffmpeg-master-latest-win64-gpl

:: Get bzip2
mkdir bzip2
cd .\bzip2
curl -O -L "https://sourceforge.net/projects/gnuwin32/files/bzip2/1.0.5/bzip2-1.0.5-bin.zip"
tar -xf bzip2-1.0.5-bin.zip
cd ..
move bzip2\bin\* .
rmdir -r bzip2

:: Get zip
mkdir zip
cd zip
curl -O -L "http://downloads.sourceforge.net/gnuwin32/zip-3.0-bin.zip"
tar -xf zip-3.0-bin.zip
cd ..
move zip\bin\* .
rmdir -r zip

:: Go back to repo root
cd ..\..\