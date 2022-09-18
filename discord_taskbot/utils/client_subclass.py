"""
Custom subclass of discord.Client.
"""

import discord
from discord import app_commands
from typing import Any

class TaskBot(discord.Client):
    def __init__(self, *, intents: discord.Intents, **options: Any) -> None:
        super().__init__(intents=intents, **options)

        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        await self.tree.sync()