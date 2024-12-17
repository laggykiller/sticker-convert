#!/bin/sh

if [ -z ${SC_COMPILE_ARCH} ]; then
    echo "Please set env variable 'SC_COMPILE_ARCH' (Supported: x86_64, aarch64)"
    exit
fi

sudo apt install -y libpng-dev libxft-dev libfontconfig1-dev libfreetype6-dev

wget -O appimage-builder https://github.com/AppImageCrafters/appimage-builder/releases/download/v1.1.0/appimage-builder-1.1.0-x86_64.AppImage
wget -O appimagetool https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x ./appimage-builder
chmod +x ./appimagetool

# Creating appimage directly with appimage-builder result in xz compression
# That would be not possible to be verified by https://appimage.github.io/apps/
# Due to https://github.com/AppImage/appimage.github.io/blob/master/code/worker.sh
# runtime-fuse2-x86_64 unable to handle xz compression
./appimage-builder --skip-appimage --recipe AppImageBuilder-${SC_COMPILE_ARCH}.yml

# Add .desktop comment
sed -i 's/Comment=/Comment=Convert (animated) stickers between WhatsApp, Telegram, Signal, Line, Kakao, Viber, Discord, iMessage/g' ./AppDir/*.desktop

# Add appdata.xml
mkdir -p AppDir/usr/share/metainfo
cp ./sticker-convert.appdata.xml AppDir/usr/share/metainfo

# Bundling into appimage
wget https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-${SC_COMPILE_ARCH}
if [ ${SC_COMPILE_ARCH} = "aarch64" ]; then
    ARCH="arm_aarch64"
else
    ARCH=${SC_COMPILE_ARCH}
fi
./appimagetool --runtime-file ./runtime-${SC_COMPILE_ARCH} ./AppDir
chmod +x sticker-convert-${SC_COMPILE_ARCH}.AppImage
