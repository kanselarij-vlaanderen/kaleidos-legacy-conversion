FROM alpine:3.10

RUN apk update \
    && apk add musl-utils \
    && apk add git
RUN git config --global color.diff always

RUN mkdir /app

COPY fix_encoding.sh /app
RUN chmod +x /app/fix_encoding.sh

ENTRYPOINT ["/app/fix_encoding.sh"]