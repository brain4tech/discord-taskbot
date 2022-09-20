"""
Custom subclass of discord.Client.
"""

import discord
from discord import app_commands
from typing import Any
from discord_taskbot.components.persistence import PersistenceAPI

class TaskBot(discord.Client):
    def __init__(self, *, intents: discord.Intents, **options: Any) -> None:
        super().__init__(intents=intents, **options)

        self.tree = app_commands.CommandTree(self)

        self.db = PersistenceAPI()
        self.db.startup()
    
    async def setup_hook(self):
        await self.tree.sync()