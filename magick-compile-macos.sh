#!/bin/sh
# https://github.com/ImageMagick/ImageMagick/discussions/5215#discussioncomment-2949450

export MAGICK_HOME=$(pwd)/ImageMagick

mkdir magick-src
cd magick-src

git clone https://github.com/ImageMagick/ImageMagick.git
cd ImageMagick

curl -O https://download.imagemagick.org/archive/delegates/jpegsrc.v9b.tar.gz
tar xvzf jpegsrc.v9b.tar.gz
cd jpeg-9b
./configure --enable-static --disable-shared --prefix=$MAGICK_HOME/lib/libjpeg
cd ..

curl -O https://download.imagemagick.org/archive/delegates/libwebp-0.6.0.tar.gz
tar xvzf libwebp-0.6.0.tar.gz
cd libwebp-0.6.0
./configure --enable-static --disable-shared --prefix=$MAGICK_HOME/lib/libwebp
cd ..

curl -O https://download.imagemagick.org/archive/delegates/libpng-1.6.31.tar.gz
tar xvzf libpng-1.6.31.tar.gz
cd libpng-1.6.31
./configure --enable-static --disable-shared --prefix=$MAGICK_HOME/lib/libpng
cd ..

rm config.status config.log
./configure --prefix=$MAGICK_HOME --with-quantum-depth=32 --with-xml --disable-installed --enable-delegate-build --disable-shared --enable-static --with-modules=no \
    --enable-hdri=no --with-heic=no --without-magick-plus-plus --with-quantum-depth=32 --without-frozenpaths --disable-silent-rules --disable-dependency-tracking \
    --enable-zero-configuration --without-gslib --with-png=yes --with-jpeg=yes --without-jp2 --disable-osx-universal-binary --without-x --without-lcms \
    --without-freetype --without-pango --without-bzlib --with-webp --without-perl --without-gvc --without-zip --with-fontconfig=no

make clean
make
make install