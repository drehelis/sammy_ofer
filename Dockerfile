FROM python:3-alpine
LABEL maintainer="Danny Rehelis <autogun@gmail.com>"

ARG APP_NAME=sammy_ofer

WORKDIR /usr/src/$APP_NAME/

RUN apk add --update \
    gcc \
    libc-dev \
    libffi-dev \
    openssl-dev \
    git \
    && rm -rf /var/cache/apk/*

VOLUME ./assets

COPY assets/. ./assets
COPY static/. ./static
COPY html_templates ./html_templates

COPY requirements.txt \
    docker-entrypoint.sh \
    *.py ./

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["./docker-entrypoint.sh"]
