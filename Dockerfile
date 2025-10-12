FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
    x11-apps \
    xauth \
    openjdk-17-jdk \
    xterm \
    && rm -rf /var/lib/apt/lists/*

ENV DISPLAY=host.docker.internal:0

COPY RandomNumberGenerator.jar .

CMD xterm -hold -e "ls -la /" & java -jar RandomNumberGenerator.jar