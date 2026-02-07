#!/bin/sh

if [[ "$1" != "x86_64" && "$1" != "aarch64" ]]; then
    echo "Usage: ./scripts/nuitka_build_with_docker.sh [x86_64|aarch64]"
    exit 1
fi

docker run \
    --rm \
    -v $(dirname $(dirname "$0")):/sticker-convert \
    -w /sticker-convert \
    --platform linux/$1 \
    quay.io/pypa/manylinux2014_$1 \
    /bin/bash -c 'scl enable devtoolset-10 "
    curl -L http://prdownloads.sourceforge.net/tcl/tcl8.6.17-src.tar.gz | tar -C /opt -xz &&
    cd /opt/tcl8.6.17/unix && ./configure --prefix=/usr && make && make install &&
    curl -L http://prdownloads.sourceforge.net/tcl/tk8.6.17-src.tar.gz | tar -C /opt -xz &&
    cd /opt/tk8.6.17/unix && ./configure --prefix=/usr && make && make install &&
    cd /opt/_internal &&
    tar xf static-libs-for-embedding-only.tar.xz &&
    cd /sticker-convert &&
    python3.12 ./compile.py
    "'