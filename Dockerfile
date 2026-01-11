FROM debian:11 AS min-cli

ENV HOME=/home/app
ENV PYENV_ROOT=/home/app/.pyenv
ENV PATH="/home/app/.pyenv/shims:/home/app/.pyenv/bin:$PATH"

RUN useradd --create-home app && \
    apt update -y && \
    apt install --no-install-recommends -y git curl gettext ca-certificates \
    build-essential gdb lcov libbz2-dev libffi-dev libgdbm-dev liblzma-dev \
    libncurses5-dev libreadline6-dev libsqlite3-dev \
    libssl-dev lzma lzma-dev uuid-dev xvfb zlib1g-dev && \
    update-ca-certificates && \
    curl -fsSL https://pyenv.run | bash && \
    pyenv install 3.12 && \
    pyenv global 3.12 && \
    pyenv rehash && \
    apt purge -y build-essential curl git gdb lcov libbz2-dev libffi-dev libgdbm-dev \
    liblzma-dev libncurses5-dev libreadline6-dev libsqlite3-dev \
    libssl-dev lzma-dev uuid-dev zlib1g-dev && \
    apt clean autoclean && \
    apt autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/
WORKDIR /app

COPY ./requirements.txt /app/
RUN cat requirements.txt | grep -v 'ttkbootstrap' > requirements-cli.txt &&\
    rm requirements.txt &&\
    pip3 install --no-cache-dir -r requirements-cli.txt

COPY ./src /app/

COPY ./scripts/update-locales.sh /app/scripts/update-locales.sh
RUN /app/scripts/update-locales.sh /app

USER app
VOLUME ["/app/sticker_convert/stickers_input", "/app/sticker_convert/stickers_output"]
ENTRYPOINT ["/home/app/.pyenv/shims/python", "/app/sticker-convert.py"]

FROM jlesage/baseimage-gui:debian-11-v4 AS base-gui

WORKDIR /app

ENV HOME=/home/app
ENV PYENV_ROOT=/home/app/.pyenv
ENV PATH="/home/app/.pyenv/shims:/home/app/.pyenv/bin:$PATH"

RUN mkdir -p '/home/app' && \
    chmod -R 777 '/home/app' && \
    # Install dependency
    apt update -y && \
    apt install --no-install-recommends -y ca-certificates \
    curl gpg zip unzip sed locales binutils psmisc git libtk8.6 \
    libfribidi-dev libharfbuzz-dev libx11-6 libfontconfig gettext \
    build-essential gdb lcov libbz2-dev libffi-dev libgdbm-dev liblzma-dev \
    libncurses5-dev libreadline6-dev libsqlite3-dev \
    libssl-dev lzma lzma-dev tk-dev uuid-dev xvfb zlib1g-dev && \
    update-ca-certificates && \
    # Set locales
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen && \
    # Build python
    curl -fsSL https://pyenv.run | bash && \
    pyenv install 3.12 && \
    pyenv global 3.12 && \
    pyenv rehash && \
    # Cleanup python build requirements
    apt purge -y build-essential git gdb lcov libbz2-dev libffi-dev libgdbm-dev \
    liblzma-dev libncurses5-dev libreadline6-dev libsqlite3-dev \
    libssl-dev lzma-dev tk-dev uuid-dev zlib1g-dev && \
    apt clean autoclean && \
    apt autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

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

VOLUME ["/app/sticker_convert/stickers_input", "/app/sticker_convert/stickers_output"]

FROM base-gui AS min-gui
COPY ./src /app/
COPY ./scripts/update-locales.sh /app/scripts/update-locales.sh
RUN /app/scripts/update-locales.sh /app

FROM base-gui AS full

# Install signal-desktop
RUN curl -s https://updates.signal.org/desktop/apt/keys.asc | gpg --dearmor > signal-desktop-keyring.gpg && \
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
RUN apt install --no-install-recommends -y chromium

ENV QT_QUICK_BACKEND="software"

# Install KakaoTalk Desktop
ENV WINEPREFIX=/home/app/.wine
RUN dpkg --add-architecture i386 && \
    mkdir -pm755 /etc/apt/keyrings && \
    curl -s https://dl.winehq.org/wine-builds/winehq.key | gpg --dearmor -o /etc/apt/keyrings/winehq-archive.key && \
    curl -o /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/debian/dists/bullseye/winehq-bullseye.sources && \
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

# Additional language support
RUN sed -i -e 's/# ja_JP.UTF-8 UTF-8/ja_JP.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# zh_TW.UTF-8 UTF-8/zh_TW.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# zh_CN.UTF-8 UTF-8/zh_CN.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

RUN apt install --no-install-recommends -y fonts-noto-cjk

COPY ./src /app/
COPY ./scripts/update-locales.sh /app/scripts/update-locales.sh
RUN /app/scripts/update-locales.sh /app