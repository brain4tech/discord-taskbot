# build from stable tested python version
FROM python:3.10.6-bullseye

WORKDIR /

RUN pip install --upgrade pip
RUN apt-get update

# create needed directories
RUN mkdir build
RUN mkdir data

# install discord_taskbot libary
COPY *.whl build
RUN for file in build/*.whl; do pip install --no-cache-dir $file; done;

RUN echo discord-taskbot

# set entrypoint for image
ENTRYPOINT [ "discord-taskbot", "run", "/data/.env" ]
