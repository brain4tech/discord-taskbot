"""
Custom subclass of discord.Client.
"""

import discord
from discord import app_commands
from typing import Any
from .persistence import PersistenceAPI
from discord import ui
from discord_taskbot.utils.constants import DEFAULT_TASK_EMOJI_MAPPING

class TaskBot(discord.Client):
    def __init__(self, *, intents: discord.Intents, **options: Any) -> None:
        super().__init__(intents=intents, **options)

        self.tree = app_commands.CommandTree(self)

        self.db = PersistenceAPI()
        self.db.startup()
    
    async def setup_hook(self):
        await self.tree.sync()
    
    async def send_new_task(self, channel: discord.TextChannel, number: int, title: str, description: str) -> discord.Message:
        message: discord.Message = await channel.send(f"**Task #{number}:** {title}\n{description}")

        task_emojis = self.db.get_task_action_emoji_mapping()

        for id, emoji in task_emojis.items():
            try:
                await message.add_reaction(emoji)
            except Exception as e:
                # use default emoji in case of an exception
                print("ERROR! {e} Using fallback emoji from default list.")
                await message.add_reaction(DEFAULT_TASK_EMOJI_MAPPING[id])
        
        return message

    
    def generate_create_task_modal(self, project: str, function) -> ui.Modal:
        class CreateTaskModal(ui.Modal, title=f"Create new Task for '{project}'"):
            task_title = ui.TextInput(label="Title", style=discord.TextStyle.short, max_length=150, required=True, min_length=1)
            task_description = ui.TextInput(label="Description", style=discord.TextStyle.long, max_length=1000, min_length=1)

            async def on_submit(self, interaction: discord.Interaction) -> None:
                await function(interaction, self.task_title, self.task_description)
        
        return CreateTaskModal

    def generate_edit_project_modal(self, tag: str, displayname: str, description: str, function) -> ui.Modal:
        class EditProjectModal(ui.Modal, title=f"Edit Project '{tag}'"):
            project_displayname = ui.TextInput(label="Display Name", placeholder=displayname, style=discord.TextStyle.short, max_length=50, min_length=1, required=False)
            project_description = ui.TextInput(label="Description", placeholder=description, style=discord.TextStyle.long, max_length=800, required=False)

            async def on_submit(self, interaction: discord.Interaction) -> None:
                await function(interaction, self.project_displayname, self.project_description)
        
        return EditProjectModal

    def generate_edit_task_modal(self, title: str, description: str, status: str, assigned_to: str, function) -> ui.Modal:
        class EditTaskModal(ui.Modal, title=f"Edit Project '{title}'"):
            project_displayname = ui.TextInput(label="Title", placeholder=title, style=discord.TextStyle.short, max_length=150, min_length=1, required=False)
            project_description = ui.TextInput(label="Description", placeholder=description, style=discord.TextStyle.long, max_length=1000, required=False)

            # TODO missing UI elements

            async def on_submit(self, interaction: discord.Interaction) -> None:
                await function(interaction, self.project_displayname, self.project_description)
        
        return EditTaskModal
