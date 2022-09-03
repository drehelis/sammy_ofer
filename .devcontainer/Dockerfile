FROM python:3

ARG USER_NAME="user"
ARG USER_UID=1000
ARG GROUP_NAME="user"
ARG USER_GID=1000

RUN groupadd --gid $USER_GID ${GROUP_NAME} && useradd --uid $USER_UID --gid $USER_GID -m ${USER_NAME} -s /bin/bash

COPY requirements.dev.txt /tmp/
RUN pip install -r /tmp/requirements.dev.txt

COPY requirements.prod.txt /tmp/
RUN pip install -r /tmp/requirements.prod.txt
