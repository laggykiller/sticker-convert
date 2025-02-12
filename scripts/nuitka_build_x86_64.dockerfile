FROM ubuntu:20.04

RUN apt update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential tzdata software-properties-common patchelf libz-dev && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt update -y && \
    apt install python3.12-full=3.12.8-1 python3.12-dev=3.12.8-1 -y