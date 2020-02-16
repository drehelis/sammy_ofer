FROM python:3-alpine
LABEL maintainer="Danny Rehelis <autogun@gmail.com>"

ARG APP_NAME=sammy_ofer

RUN apk add --update \
    gcc \
    libc-dev \
    libffi-dev \
    openssl-dev \
    && rm -rf /var/cache/apk/*

RUN adduser -g "Sammy Ofer" -D $APP_NAME

WORKDIR /usr/src/$APP_NAME/

COPY requirements.txt \
    cron.py spectators.py \
    web_scrape.py web.py html_templates ./

RUN pip install --no-cache-dir -r requirements.txt

RUN echo "0 8 * * * python /usr/src/$APP_NAME/cron.py" > /var/spool/cron/crontabs/$APP_NAME
RUN chmod 0600 /var/spool/cron/crontabs/$APP_NAME

ENV FLASK_APP web.py
ENV FLASK_ENV development

ENTRYPOINT ["flask", "run", "--host=0.0.0.0", "--port=5000"]
