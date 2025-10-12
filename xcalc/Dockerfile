FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
    x11-apps \
    xauth \
    && rm -rf /var/lib/apt/lists/*

ENV DISPLAY=host.docker.internal:0

CMD ["xcalc"] 

# docker build -t xcalc-p1 .
# docker run --rm xcalc-p1