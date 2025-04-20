FROM ubuntu:20.04

RUN apt update -y && \
    apt-get install -y fuse libfuse2 curl