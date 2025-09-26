FROM openjdk:17-jdk-alpine

WORKDIR /app

COPY game.java /app/

RUN javac game.java

CMD [ "java", "game" ]

# docker build -t game-java .
# docker run -it --rm game-java