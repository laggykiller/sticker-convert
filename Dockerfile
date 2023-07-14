FROM jlesage/baseimage-gui:debian-11-v4

WORKDIR /app

# Install dependency
RUN apt update -y && \
    apt install --no-install-recommends -y python3 python3-pip python3-opencv python3-tk \
    curl wget gpg zip unzip cmake tar sed build-essential pkg-config locales binutils psmisc git \
    libpng-dev libboost-program-options-dev libboost-regex-dev libboost-system-dev libboost-filesystem-dev \
    libfribidi-dev libharfbuzz-dev libx11-6 libfontconfig \
    ffmpeg optipng pngquant apngdis

# Install apngasm
RUN curl -O -L https://github.com/apngasm/apngasm/archive/refs/tags/3.1.10.tar.gz && \
    tar xvzf 3.1.10.tar.gz && \
    cd ./apngasm-3.1.10 && \
    mkdir build && \
    cd build && \
    cmake ../ && \
    make && \
    make install && \
    cd ../../ && \
    rm -rf ./apngasm-3.1.10 && \
    rm 3.1.10.tar.gz

# Install pngnq-s9
RUN curl -O -L https://github.com/ImageProcessing-ElectronicPublications/pngnq-s9/archive/refs/tags/2.0.2.tar.gz && \
    tar xvzf 2.0.2.tar.gz && \
    cd ./pngnq-s9-2.0.2 && \
    sed -i '1i#include <string.h>' src/rwpng.c && ./configure && make && make install && \
    cd ../ && \
    rm -rf /app/pngnq-s9-2.0.2 && \
    rm /app/2.0.2.tar.gz

# Install signal-desktop-beta
RUN wget -O- https://updates.signal.org/desktop/apt/keys.asc | gpg --dearmor > signal-desktop-keyring.gpg && \
    cat signal-desktop-keyring.gpg | tee -a /usr/share/keyrings/signal-desktop-keyring.gpg > /dev/null && \
    echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/signal-desktop-keyring.gpg] https://updates.signal.org/desktop/apt xenial main' |\
    tee -a /etc/apt/sources.list.d/signal-xenial.list && \
    apt update -y && \
    apt install --no-install-recommends -y signal-desktop-beta

# Install ImageMagick
# ImageMagick on Ubuntu repo does not have delegates (e.g. webp file conversion would not work)
# ImageMagick on Debian repo cannot convert some files for unclear reason (Because of old version?)
# Debian repo version also has small default caching set in policy.xml
# RUN sed -i 's,<policy domain="resource" name="disk" value="1GiB"/>,<policy domain="resource" name="disk" value="8GiB"/>,g' /etc/ImageMagick-6/policy.xml
# ImageMagick appimage seems to be most reliable and easiest
# However, appimage cannot be directly used on Docker due to lack of FUSE
# Quick hack is to extract appimage to root
# RUN curl -o magick -L https://github.com/ImageMagick/ImageMagick/releases/download/7.1.0-57/ImageMagick--clang-x86_64.AppImage && \
RUN curl -o magick -L https://github.com/ImageMagick/ImageMagick/releases/latest/download/ImageMagick--gcc-x86_64.AppImage && \
    chmod +x ./magick && \
    ./magick --appimage-extract && \
    rsync -av squashfs-root/ / --exclude AppRun --exclude imagemagick.desktop --exclude imagemagick.png --exclude share --exclude usr/include --exclude usr/share && \
    rm ./magick && \
    rm -rf ./squashfs-root

# Set locales
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen

# Set application name displayed in Webpage
RUN set-cont-env APP_NAME "sticker-convert"

# Generate and install favicons.
COPY ./sticker_convert/resources/appicon.png /app/
RUN APP_ICON_URL=/app/appicon.png && \
    install_app_icon.sh "$APP_ICON_URL"

ENV DISPLAY_WIDTH=1920
ENV DISPLAY_HEIGHT=1080

RUN mkdir /etc/openbox && \
    printf '<Type>normal</Type>\n<Name>sticker-convert</Name>' >> /etc/openbox/main-window-selection.xml

RUN mkdir '/root/.config' && \
    mkdir '/root/.config/Signal' && \
    mkdir '/root/.config/Signal Beta' && \
    chmod 777 '/root/.config/Signal' && \
    chmod 777 '/root/.config/Signal Beta'

COPY ./requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt
COPY startapp.sh /startapp.sh
COPY ./sticker_convert /app/

RUN chmod -R 777 /app

RUN apt clean autoclean && \
    apt autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

VOLUME ["/app/stickers_input", "/app/stickers_output"]
