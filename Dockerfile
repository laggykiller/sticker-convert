FROM jlesage/baseimage-gui:debian-11-v4

WORKDIR /app

# Install dependency
RUN apt update -y && \
    apt install --no-install-recommends -y python3 python3-pip python3-opencv python3-tk \
    curl wget gpg zip unzip sed locales binutils psmisc git \
    libfribidi-dev libharfbuzz-dev libx11-6 libfontconfig

# Install signal-desktop-beta
RUN wget -O- https://updates.signal.org/desktop/apt/keys.asc | gpg --dearmor > signal-desktop-keyring.gpg && \
    cat signal-desktop-keyring.gpg | tee -a /usr/share/keyrings/signal-desktop-keyring.gpg > /dev/null && \
    echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/signal-desktop-keyring.gpg] https://updates.signal.org/desktop/apt xenial main' |\
    tee -a /etc/apt/sources.list.d/signal-xenial.list && \
    apt update -y && \
    apt install --no-install-recommends -y signal-desktop-beta

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

RUN mkdir -p '/root/.config/Signal' && \
    mkdir -p '/root/.config/Signal Beta' && \
    chmod 777 '/root/.config/Signal' && \
    chmod 777 '/root/.config/Signal Beta'

COPY ./requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

RUN apt purge -y curl wget gpg git && \
    apt clean autoclean && \
    apt autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

COPY startapp.sh /startapp.sh
COPY ./src/main.py /app/
COPY ./src/sticker_convert /app/

RUN chmod -R 777 /app

VOLUME ["/app/stickers_input", "/app/stickers_output"]
