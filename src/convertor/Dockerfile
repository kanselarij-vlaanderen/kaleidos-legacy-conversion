FROM python:alpine3.7

COPY . /app

WORKDIR /app

RUN apk add --no-cache tzdata
ENV TZ Europe/Brussels
RUN pip install -r requirements.txt
