FROM openjdk:17-jdk-alpine

WORKDIR /app

COPY calc.java /app/

RUN javac calc.java

CMD [ "java", "calc" ]

# docker build -t java-calc . 
# docker run -it --rm java-calc
