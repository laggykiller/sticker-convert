FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive
ENV SC_COMPILE_ARCH x86_64

RUN apt update -y && \
    apt-get install -y fuse libfuse2 curl