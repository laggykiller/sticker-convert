FROM arm64v8/ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive
ENV SC_COMPILE_ARCH aarch64

RUN apt update -y && \
    apt-get install -y fuse libfuse2