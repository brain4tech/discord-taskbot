#! /usr/bin/env bash

# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")

# Absolute path this script is in, thus /home/user/bin
PROJECTPATH=$(dirname "$SCRIPT")

# build wheel
mkdir wheels &> /dev/null
python3 -m pip wheel $PROJECTPATH -w wheels

# copy wheel to docker dir and build docker image
cp -r $PROJECTPATH/wheels/discord_taskbot* "$PROJECTPATH/docker"
docker build -t discord_taskbot "$PROJECTPATH/docker"

# cleanup
rm $PROJECTPATH/docker/*.whl
rm -r "$PROJECTPATH/wheels"
rm -r "$PROJECTPATH/build"
rm -r "$PROJECTPATH/discord_taskbot.egg-info"
