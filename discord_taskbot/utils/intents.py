"""
Manage the bot's intents.
"""

import discord

INTENTS = discord.Intents.none()
INTENTS.messages = True
INTENTS.message_content = True
INTENTS.reactions = True
INTENTS.guilds = True
