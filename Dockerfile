FROM jlesage/baseimage-gui:debian-11-v4.3.4

WORKDIR /app

RUN apt update -y
RUN apt install --no-install-recommends -y python3 python3-pip python3-opencv python3-tk \
    curl wget gpg zip unzip cmake tar sed build-essential pkg-config locales binutils psmisc \
    libpng-dev libboost-program-options-dev libboost-regex-dev libboost-system-dev libboost-filesystem-dev \
    libfribidi-dev libharfbuzz-dev libx11-6 libfontconfig \
    ffmpeg optipng pngquant apngdis

WORKDIR /app

# ImageMagick on Ubuntu repo does not have delegates (e.g. webp file conversion would not work)
# ImageMagick on Debian repo cannot convert some files for unclear reason (Because of old version?)
# Debian repo version also has small default caching set in policy.xml
# RUN sed -i 's,<policy domain="resource" name="disk" value="1GiB"/>,<policy domain="resource" name="disk" value="8GiB"/>,g' /etc/ImageMagick-6/policy.xml
# ImageMagick appimage seems to be most reliable and easiest
# However, appimage cannot be directly used on Docker due to lack of FUSE
# Quick hack is to extract appimage to root
RUN curl -o magick -L https://github.com/ImageMagick/ImageMagick/releases/download/7.1.0-61/ImageMagick--gcc-x86_64.AppImage
RUN chmod +x ./magick
RUN ./magick --appimage-extract
RUN cp -r ./squashfs-root/* /
RUN rm ./magick
RUN rm -rf ./squashfs-root

RUN curl -O -L https://github.com/apngasm/apngasm/archive/refs/tags/3.1.10.tar.gz && \
    tar xvzf 3.1.10.tar.gz
WORKDIR /app/apngasm-3.1.10
RUN mkdir build && cd build && cmake ../ && make && make install
WORKDIR /app
RUN rm -rf /app/apngasm-3.1.10 && rm 3.1.10.tar.gz

RUN curl -O -L https://github.com/ImageProcessing-ElectronicPublications/pngnq-s9/archive/refs/tags/2.0.2.tar.gz && \
    tar xvzf 2.0.2.tar.gz
WORKDIR /app/pngnq-s9-2.0.2
RUN sed -i '1i#include <string.h>' src/rwpng.c && ./configure && make && make install
WORKDIR /app
RUN rm -rf /app/pngnq-s9-2.0.2 && \
    rm /app/2.0.2.tar.gz

RUN wget -O- https://updates.signal.org/desktop/apt/keys.asc | gpg --dearmor > signal-desktop-keyring.gpg
RUN cat signal-desktop-keyring.gpg | tee -a /usr/share/keyrings/signal-desktop-keyring.gpg > /dev/null
RUN echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/signal-desktop-keyring.gpg] https://updates.signal.org/desktop/apt xenial main' |\
    tee -a /etc/apt/sources.list.d/signal-xenial.list
RUN apt update -y
RUN apt install --no-install-recommends -y signal-desktop-beta

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen

RUN set-cont-env APP_NAME "sticker-convert"

# Generate and install favicons.
RUN APP_ICON_URL=https://github.com/laggykiller/sticker-convert/raw/master/sticker_convert/resources/appicon.png && \
    install_app_icon.sh "$APP_ICON_URL"

ENV DISPLAY_WIDTH=1920
ENV DISPLAY_HEIGHT=1080

RUN mkdir /etc/openbox
RUN printf '<Type>normal</Type>\n<Name>sticker-convert</Name>' >> /etc/openbox/main-window-selection.xml

RUN mkdir '/root/.config'
RUN mkdir '/root/.config/Signal'
RUN mkdir '/root/.config/Signal Beta'

RUN chmod 777 '/root/.config/Signal'
RUN chmod 777 '/root/.config/Signal Beta'

RUN apt clean autoclean
RUN apt autoremove --yes
RUN rm -rf /var/lib/{apt,dpkg,cache,log}/

COPY ./requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt
COPY ./sticker_convert /app/
COPY startapp.sh /startapp.sh

RUN chmod -R 777 /app

Volume ["/app/stickers_input", "/app/stickers_output"]