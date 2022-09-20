"""
Custom subclass of discord.Client.
"""

import discord
from discord import app_commands
from typing import Any
from discord_taskbot.components.persistence import PersistenceAPI
from discord import ui

class TaskBot(discord.Client):
    def __init__(self, *, intents: discord.Intents, **options: Any) -> None:
        super().__init__(intents=intents, **options)

        self.tree = app_commands.CommandTree(self)

        self.db = PersistenceAPI()
        self.db.startup()
    
    async def setup_hook(self):
        await self.tree.sync()

    def generate_edit_project_modal(self, tag: str, displayname: str, description: str, function) -> ui.Modal:
        class EditProjectModal(ui.Modal, title=f"Edit Project '{tag}'"):
            project_displayname = ui.TextInput(label="Display Name", placeholder=displayname, style=discord.TextStyle.short, max_length=50, min_length=1, required=False)
            project_description = ui.TextInput(label="Description", placeholder=description, style=discord.TextStyle.long, max_length=800, required=False)

            async def on_submit(self, interaction: discord.Interaction) -> None:
                await function(interaction, self.project_displayname, self.project_description)
        
        return EditProjectModal
