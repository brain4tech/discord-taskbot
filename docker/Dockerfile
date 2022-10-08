# build from stable tested python version
FROM python:3.10.6-bullseye

WORKDIR /

RUN apt-get update
RUN apt-get install git
RUN pip install --upgrade pip

# create needed directories
RUN mkdir data

# install discord_taskbot libary
RUN git clone --branch main https://github.com/brain4tech/discord-taskbot
WORKDIR /discord-taskbot
RUN pip install .

WORKDIR /

RUN echo discord-taskbot

# set entrypoint for image
ENTRYPOINT [ "discord-taskbot", "run", "/data/.env" ]
