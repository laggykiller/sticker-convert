FROM ubuntu:20.04

ARG PYVER=3.12.8-1+focal1_amd64

RUN apt update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential curl tzdata software-properties-common patchelf libz-dev && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt update -y && \
    # apt install python3.12 python3.12-tk python3.12-dev -y
    curl -O -L "https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa/+files/libpython3.12-stdlib_${PYVER}.deb" && \
    curl -O -L "https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa/+files/libpython3.12_${PYVER}.deb" && \
    curl -O -L "https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa/+files/libpython3.12-dev_${PYVER}.deb" && \
    curl -O -L "https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa/+files/python3.12_${PYVER}.deb" && \
    curl -O -L "https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa/+files/python3.12-tk_${PYVER}.deb" && \
    apt -f install -y "./libpython3.12-stdlib_${PYVER}.deb" \
    "./libpython3.12_${PYVER}.deb" \
    "./libpython3.12-dev_${PYVER}.deb" \
    "./python3.12_${PYVER}.deb" \
    "./python3.12-tk_${PYVER}.deb"