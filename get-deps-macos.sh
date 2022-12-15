#!/bin/sh
# https://github.com/ImageMagick/ImageMagick/discussions/5215#discussioncomment-2949450

# Compile ImageMagick
cd ./sticker_convert
export MAGICK_HOME=$(pwd)/ImageMagick
cd ..

rm -rf $MAGICK_HOME
rm -rf magick-src

mkdir magick-src
cd magick-src

curl -O -L https://github.com/ImageMagick/ImageMagick/archive/refs/tags/7.1.0-54.tar.gz
tar xvzf 7.1.0-54.tar.gz
cd ImageMagick-7.1.0-54

curl -O -L https://download.imagemagick.org/archive/delegates/jpegsrc.v9b.tar.gz
tar xvzf jpegsrc.v9b.tar.gz
cd jpeg-9b
./configure --enable-static --disable-shared --prefix=$MAGICK_HOME/lib/libjpeg
cd ..

curl -O -L https://download.imagemagick.org/archive/delegates/libwebp-0.6.0.tar.gz
tar xvzf libwebp-0.6.0.tar.gz
cd libwebp-0.6.0
./configure --enable-static --disable-shared --prefix=$MAGICK_HOME/lib/libwebp
cd ..

curl -O -L https://download.imagemagick.org/archive/delegates/libpng-1.6.31.tar.gz
tar xvzf libpng-1.6.31.tar.gz
cd libpng-1.6.31
./configure --enable-static --disable-shared --prefix=$MAGICK_HOME/lib/libpng
cd ..

rm config.status config.log

./configure --prefix=$MAGICK_HOME --with-quantum-depth=16 --with-xml --disable-installed --enable-delegate-build --disable-shared --enable-static --with-modules=no \
    --enable-hdri=no --with-heic=no --without-magick-plus-plus --without-frozenpaths --disable-silent-rules --disable-dependency-tracking \
    --enable-zero-configuration --without-gslib --with-png=yes --with-jpeg=yes --without-jp2 --disable-osx-universal-binary --without-x --without-lcms \
    --without-freetype --without-pango --without-bzlib --with-webp --without-perl --without-gvc --without-zip --with-fontconfig=no

make clean
make
make install

cd ../../
rm -rf ./magick-src

# Preparing bin directory
rm -rf ./sticker_convert/bin
mkdir ./sticker_convert/bin
cd ./sticker_convert/bin

# Compiling pngnq-s9
mkdir ./pngnqs9
cd ./pngnqs9
curl -O -L https://github.com/ImageProcessing-ElectronicPublications/pngnq-s9/archive/refs/tags/2.0.2.tar.gz
tar xvzf 2.0.2.tar.gz
cd ./pngnq-s9-2.0.2
# Fix bug that causes compilation to fail
echo '#include <string.h>' > src/rwpng.c.new
cat src/rwpng.c >> src/rwpng.c.new
mv src/rwpng.c.new src/rwpng.c
./configure
make
# make install
chmod +x src/pngnq-s9
cd ../../
cp ./pngnqs9/pngnq-s9-2.0.2/src/pngnq-s9 ./
rm -rf ./pngnqs9

# Get apngasm
curl -O -L https://sourceforge.net/projects/apngasm/files/2.91/apngasm-2.91-bin-macos.zip
unzip apngasm-2.91-bin-macos.zip
rm readme.txt
rm apngasm-2.91-bin-macos.zip

# Get apngdis
curl -O -L https://sourceforge.net/projects/apngdis/files/2.9/apngdis-2.9-bin-macos.zip
unzip apngdis-2.9-bin-macos.zip
rm readme.txt
rm apngdis-2.9-bin-macos.zip

# Get ffmpeg
curl -O -L https://evermeet.cx/ffmpeg/ffmpeg-5.1.2.zip
unzip ffmpeg-5.1.2.zip
rm ffmpeg-5.1.2.zip

# Get ffprobe
curl -O -L https://evermeet.cx/ffmpeg/ffprobe-5.1.2.zip
unzip ffprobe-5.1.2.zip
rm ffprobe-5.1.2.zip

# Go back to root of repo
cd ../../