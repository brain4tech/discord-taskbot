#! /usr/bin/env bash

# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")

# Absolute path this script is in, thus /home/user/bin
PROJECTPATH=$(dirname "$SCRIPT")

# build docker image
docker build -t discord_taskbot "$PROJECTPATH/docker"
