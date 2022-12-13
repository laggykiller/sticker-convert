FROM alpine:latest

WORKDIR /app

COPY ./sticker_convert /app/

RUN apk add alpine-sdk python3 py3-pip ffmpeg imagemagick optipng pngquant zip unzip cmake libpng-dev boost-dev tar sed python3-tkinter

RUN mkdir /app/apngdis && \
    cd /app/apngdis && \
    curl -O -L https://sourceforge.net/projects/apngdis/files/2.9/apngdis-2.9-src.zip && \
    unzip apngdis-2.9-src.zip
WORKDIR /app/apngdis
RUN make && cp /app/apngdis/apngdis /usr/local/bin && rm -rf /app/apngdis

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

RUN pip3 install requests ffmpeg-python lottie argparse signalstickers_client python-telegram-bot anyio

CMD ["python3", "/app/main.py", "--help"]
