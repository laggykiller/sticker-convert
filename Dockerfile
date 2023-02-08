FROM jlesage/baseimage-gui:debian-11-v4.3.4

WORKDIR /app

RUN apt update -y
RUN apt install --no-install-recommends -y python3 python3-pip python3-opencv python3-tk \
    curl wget gpg zip unzip cmake tar sed build-essential pkg-config locales binutils psmisc \
    libpng-dev libboost-program-options-dev libboost-regex-dev libboost-system-dev libboost-filesystem-dev \
    ffmpeg imagemagick optipng pngquant apngdis

WORKDIR /app
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
RUN apt install -y signal-desktop-beta

RUN apt purge -y build-essential cmake libpng-dev libboost-program-options-dev libboost-regex-dev libboost-system-dev libboost-filesystem-dev

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en 
ENV LC_ALL en_US.UTF-8
ENV LC_TIME en_US.UTF-8

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

COPY ./requirements.txt /app/
RUN pip3 install -r requirements.txt
COPY ./sticker_convert /app/

COPY startapp.sh /startapp.sh

RUN chmod -R 777 /app

Volume ["/app/stickers_input", "/app/stickers_output"]