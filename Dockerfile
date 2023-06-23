FROM python:3-alpine
LABEL maintainer="Danny Rehelis <autogun@gmail.com>"

ARG APP_NAME=sammy_ofer

WORKDIR /usr/src/$APP_NAME/

RUN apk add --update \
    gcc \
    libc-dev \
    libffi-dev \
    openssl-dev \
    musl-locales \
    && rm -rf /var/cache/apk/*

COPY html_templates ./html_templates
COPY requirements.txt \
    cron.py \
    spectators.py \
    web_scrape.py \
    web.py ./

RUN pip install --no-cache-dir -r requirements.txt

COPY docker-entrypoint.sh ./

EXPOSE 5000

ENTRYPOINT ["./docker-entrypoint.sh"]
