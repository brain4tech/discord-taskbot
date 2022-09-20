#! /usr/bin/env bash

source venv/bin/activate

# rm data.db

pip install .

rm -r build discord_taskbot.egg-info

discordtb run .env