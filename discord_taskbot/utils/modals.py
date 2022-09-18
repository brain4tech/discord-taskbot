"""
Modal subclasses for all ui-related inputs.
"""

import discord
from discord import ui

from .functions import send_new_task

class NewTaskModal(ui.Modal, title="New Task"):
    task_title = ui.TextInput(label="Title", style=discord.TextStyle.short, max_length=150, required=True, min_length=1)
    task_description = ui.TextInput(label="Description", style=discord.TextStyle.long, max_length=3000, min_length=1)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        await send_new_task(interaction.channel, self.task_title, self.task_description)