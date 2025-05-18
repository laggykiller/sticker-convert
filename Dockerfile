FROM debian:11 AS min-cli

WORKDIR /app

RUN apt update -y && \
    apt install --no-install-recommends -y python3 python3-pip

COPY ./requirements.txt /app/
RUN cat requirements.txt | grep -v 'ttkbootstrap' > requirements-cli.txt &&\
    rm requirements.txt &&\
    pip3 install --no-cache-dir -r requirements-cli.txt

COPY ./src /app/

RUN apt purge -y python3-pip && \
    apt clean autoclean && \
    apt autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

RUN useradd --create-home app
USER app

VOLUME ["/app/sticker_convert/stickers_input", "/app/sticker_convert/stickers_output"]

ENTRYPOINT ["/app/sticker-convert.py"]

FROM jlesage/baseimage-gui:debian-11-v4 AS base-gui

WORKDIR /app

# Install dependency
RUN apt update -y && \
    apt install --no-install-recommends -y python3 python3-pip python3-opencv python3-tk \
    curl wget gpg zip unzip sed locales binutils psmisc git \
    libfribidi-dev libharfbuzz-dev libx11-6 libfontconfig

# Set locales
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen

# Set application name displayed in Webpage
RUN set-cont-env APP_NAME "sticker-convert"

# Generate and install favicons.
COPY ./src/sticker_convert/resources/appicon.png /app/
RUN APP_ICON_URL=/app/appicon.png && \
    install_app_icon.sh "$APP_ICON_URL"

ENV DISPLAY_WIDTH=1920
ENV DISPLAY_HEIGHT=1080

RUN mkdir /etc/openbox && \
    printf '<Type>normal</Type>\n<Name>sticker-convert</Name>' >> /etc/openbox/main-window-selection.xml

COPY ./requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

COPY ./scripts/startapp.sh /startapp.sh

ENV HOME=/home/app

VOLUME ["/app/sticker_convert/stickers_input", "/app/sticker_convert/stickers_output"]

FROM base-gui AS min-gui
RUN apt purge -y curl wget gpg git && \
    apt clean autoclean && \
    apt autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

COPY ./src /app/

FROM base-gui AS full
RUN mkdir -p '/home/app' && \
    chmod -R 777 '/home/app'

# Install signal-desktop
RUN wget -O- https://updates.signal.org/desktop/apt/keys.asc | gpg --dearmor > signal-desktop-keyring.gpg && \
    cat signal-desktop-keyring.gpg | tee -a /usr/share/keyrings/signal-desktop-keyring.gpg > /dev/null && \
    echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/signal-desktop-keyring.gpg] https://updates.signal.org/desktop/apt xenial main' |\
    tee -a /etc/apt/sources.list.d/signal-xenial.list && \
    apt update -y && \
    apt install --no-install-recommends -y signal-desktop

# Install Viber Desktop
RUN curl -o /tmp/viber.deb -L https://download.cdn.viber.com/cdn/desktop/Linux/viber.deb && \
    apt install --no-install-recommends -y /tmp/viber.deb libgl1 libevent-2.1-7 libwebpdemux2 libxslt1.1 libxkbfile1 libegl1 libopengl0 libqt5gui5 && \
    rm /tmp/viber.deb

# Install Chromium
RUN apt install --no-install-recommends -y chromium xvfb

ENV QT_QUICK_BACKEND="software"

# Install KakaoTalk Desktop
ENV WINEPREFIX=/home/app/.wine
RUN dpkg --add-architecture i386 && \
    mkdir -pm755 /etc/apt/keyrings && \
    wget -O- https://dl.winehq.org/wine-builds/winehq.key | gpg --dearmor -o /etc/apt/keyrings/winehq-archive.key && \
    wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/debian/dists/bullseye/winehq-bullseye.sources && \
    apt update && \
    apt install -y winehq-stable=10.0.0.0~bullseye-1 && \
    # msi=$(strings -e l "/opt/wine-stable/lib64/wine/x86_64-windows/appwiz.cpl" | grep -o "wine-mono-.*msi") && \
    # pkgver="${msi##wine-mono-}" && \
    # pkgver="${pkgver%%-*}" && \
    # curl -o /tmp/wine-mono-${pkgver}-x86.msi https://dl.winehq.org/wine/wine-mono/${pkgver}/wine-mono-${pkgver}-x86.msi && \
    curl -o /tmp/wine-mono-10.0.0-x86.msi https://dl.winehq.org/wine/wine-mono/10.0.0/wine-mono-10.0.0-x86.msi && \
    curl -o /tmp/KakaoTalk_Setup.exe -L https://app-pc.kakaocdn.net/talk/win32/KakaoTalk_Setup.exe && \
    winecfg -v win10 && \
    # wine msiexec /i /tmp/wine-mono-${pkgver}-x86.msi && \
    wine msiexec /i /tmp/wine-mono-10.0.0-x86.msi && \
    wine "/tmp/KakaoTalk_Setup.exe" "/S" && \
    rm /tmp/KakaoTalk_Setup.exe && \
    # rm /tmp/wine-mono-${pkgver}-x86.msi
    rm /tmp/wine-mono-10.0.0-x86.msi

RUN apt purge -y curl wget gpg git && \
    apt clean autoclean && \
    apt autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/ && \
    chmod -R 777 '/home/app' && \
    chown -R 1000 '/home/app'

COPY ./src /app/