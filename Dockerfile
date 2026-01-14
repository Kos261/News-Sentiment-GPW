FROM ubuntu:latest
LABEL authors="koste"

ENTRYPOINT ["top", "-b"]