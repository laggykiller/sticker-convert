FROM ghcr.io/greyltc-org/archlinux-aur:yay-20221211.0.247

WORKDIR /app

COPY sticker_convert ./
COPY icon ./
COPY sticker_convert_cli_macos_linux.sh ./

RUN aur-install ffmpeg imagemagick zip optipng pngquant apng-utils pngnq-s9 python python-pip
RUN pip install requests ffmpeg-python wand lottie argparse signalstickers_client python-telegram-bot anyio

CMD ["/app/sticker_convert_cli_macos_linux.sh"]
