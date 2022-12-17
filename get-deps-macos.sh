#!/bin/sh
# To remove all homebrew packages for testing portability: brew remove --force $(brew list --formula)

NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

cd ./sticker_convert

# Preparing bin directory
rm -rf ./bin
mkdir ./bin
cd ./bin

# Get pkg-config (For compiling pngnq-s9)
brew install pkg-config

# Get apngasm (Also gets libpng)
brew install apngasm
cp /usr/local/bin/apngasm ./

# Get apngdis
curl --retry 5 -O -L https://sourceforge.net/projects/apngdis/files/2.9/apngdis-2.9-bin-macos.zip
unzip apngdis-2.9-bin-macos.zip
rm readme.txt
rm apngdis-2.9-bin-macos.zip

# Get ImageMagick
brew install imagemagick
rm -rf ../ImageMagick
mkdir ../ImageMagick
cp -r /usr/local/opt/imagemagick/bin ../ImageMagick
cp -r /usr/local/opt/imagemagick/lib ../ImageMagick
cp -r /usr/local/opt/imagemagick/etc ../ImageMagick

# Compiling pngnq-s9
mkdir ./pngnq-s9-dl
cd ./pngnq-s9-dl
curl --retry 5 -O -L https://github.com/ImageProcessing-ElectronicPublications/pngnq-s9/archive/refs/tags/2.0.2.tar.gz
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
cp ./pngnq-s9-dl/pngnq-s9-2.0.2/src/pngnq-s9 ./
rm -rf ./pngnq-s9-dl

# Get pngquant
brew install pngquant
cp /usr/local/bin/pngquant ./

# Get optipng
brew install optipng
cp /usr/local/opt/optipng/bin/* ./

# Get ffmpeg
curl --retry 5 -O -L https://evermeet.cx/ffmpeg/ffmpeg-5.1.2.zip
unzip ffmpeg-5.1.2.zip
rm ffmpeg-5.1.2.zip

# Get ffprobe
curl --retry 5 -O -L https://evermeet.cx/ffmpeg/ffprobe-5.1.2.zip
unzip ffprobe-5.1.2.zip
rm ffprobe-5.1.2.zip

# Get libwebm
brew install libwebm

# Copy library
mkdir ../lib
cp /usr/local/opt/aom/lib/* ../lib
cp /usr/local/opt/apngasm/lib/* ../lib
cp /usr/local/opt/boost/lib/* ../lib
cp /usr/local/opt/brotli/lib/* ../lib
# cp /usr/local/opt/docbook-xsl/lib/* ../lib
# cp /usr/local/opt/docbook/lib/* ../lib
cp /usr/local/opt/fontconfig/lib/* ../lib
cp /usr/local/opt/freetype/lib/* ../lib
cp /usr/local/opt/gettext/lib/* ../lib
cp /usr/local/opt/ghostscript/lib/* ../lib
cp /usr/local/opt/giflib/lib/* ../lib
cp /usr/local/opt/glib/lib/* ../lib
# cp /usr/local/opt/gnu-getopt/lib/* ../lib
cp /usr/local/opt/highway/lib/* ../lib
cp /usr/local/opt/icu4c/lib/* ../lib
# cp /usr/local/opt/imagemagick/lib/* ../lib
cp /usr/local/opt/imath/lib/* ../lib
cp /usr/local/opt/jasper/lib/* ../lib
cp /usr/local/opt/jbig2dec/lib/* ../lib
cp /usr/local/opt/jpeg-turbo/lib/* ../lib
cp /usr/local/opt/jpeg-xl/lib/* ../lib
cp /usr/local/opt/libde265/lib/* ../lib
cp /usr/local/opt/libheif/lib/* ../lib
cp /usr/local/opt/libidn/lib/* ../lib
cp /usr/local/opt/liblqr/lib/* ../lib
cp /usr/local/opt/libomp/lib/* ../lib
cp /usr/local/opt/libpng/lib/* ../lib
cp /usr/local/opt/libraw/lib/* ../lib
cp /usr/local/opt/libtiff/lib/* ../lib
cp /usr/local/opt/libtool/lib/* ../lib
cp /usr/local/opt/libvmaf/lib/* ../lib
cp /usr/local/opt/libwebm/lib/* ../lib
cp /usr/local/opt/little-cms/lib/* ../lib
cp /usr/local/opt/little-cms2/lib/* ../lib
cp /usr/local/opt/lz4/lib/* ../lib
# cp /usr/local/opt/lzlib/lib/* ../lib
# cp /usr/local/opt/m4/lib/* ../lib
cp /usr/local/opt/openexr/lib/* ../lib
cp /usr/local/opt/openjpeg/lib/* ../lib
cp /usr/local/opt/pcre2/lib/* ../lib
# cp /usr/local/opt/shared-mime-info/lib/* ../lib
cp /usr/local/opt/webp/lib/* ../lib
cp /usr/local/opt/x265/lib/* ../lib
# cp /usr/local/opt/xmlto/lib/* ../lib
cp /usr/local/opt/xz/lib/* ../lib
cp /usr/local/opt/zstd/lib/* ../lib

# Go back to root of repo
cd ../../