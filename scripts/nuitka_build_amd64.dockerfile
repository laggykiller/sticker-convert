FROM ubuntu:20.04

ENV PYTHON_VERSION 3.12
ENV PYENV_ROOT=/root/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
ENV PYTHON_CONFIGURE_OPTS "--enable-shared"
ENV DEBIAN_FRONTEND noninteractive

RUN apt update -y && \
    apt-get install -y \
        make \
        build-essential \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        wget \
        ca-certificates \
        curl \
        llvm \
        libncurses5-dev \
        xz-utils \
        tk-dev \
        libxml2-dev \
        libxmlsec1-dev \
        libffi-dev \
        liblzma-dev \
        mecab-ipadic-utf8 \
        git \
        tzdata \
        software-properties-common \
        patchelf \
        python-openssl \
        python3-tk \
        libz-dev && \
    curl -fsSL https://pyenv.run | bash && \
    set -ex && \
    pyenv update && \
    pyenv install ${PYTHON_VERSION} && \
    pyenv global ${PYTHON_VERSION} && \
    pyenv rehash