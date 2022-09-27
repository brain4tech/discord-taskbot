"""
Functions to summarize repeatable processes.
"""

import discord
from .constants import DEFAULT_TASK_EMOJIS

async def send_new_task(channel: discord.TextChannel, title: str, description: str):

    message: discord.Message = await channel.send(f"**Task #{0}:** {title}\n{description}")
    for emoji in DEFAULT_TASK_EMOJIS:
        await message.add_reaction(emoji)