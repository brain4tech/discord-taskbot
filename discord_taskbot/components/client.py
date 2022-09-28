"""
Custom subclass of discord.Client.
"""

import discord
from discord import app_commands
from typing import Any
from discord_taskbot.components.exceptions import DiscordTBException

from discord_taskbot.components.models import Emoji
from .persistence import PersistenceAPI
from discord import ui
from discord_taskbot.utils.constants import DEFAULT_TASK_EMOJI_MAPPING, TASK_STATUS_MAPPING

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

    def generate_edit_task_modal(self, title: str, description: str, status: str, assigned_to: discord.Member, function, users: list[discord.Member], emojis: list[Emoji]) -> ui.Modal:
        class EditTaskModal(ui.Modal, title=f"Edit Task '{title}'"):
            project_displayname = ui.TextInput(label="Title", placeholder=title, style=discord.TextStyle.short, max_length=150, min_length=1, required=False)
            project_description = ui.TextInput(label="Description", placeholder=description, style=discord.TextStyle.long, max_length=1000, required=False)

            """
            project_status_pending = ui.Button(style=discord.ButtonStyle.green, label="Pending")
            project_status_progress = ui.Button(label="In Progress")
            project_status_merge = ui.Button(label="Pending Merge")
            project_status_done = ui.Button(label="Done")

            match status:
                case 'pending': project_status_pending.disabled = True
                case 'in_progress': project_status_progress.disabled = True
                case 'pending_merge': project_status_merge.disabled = True
                case 'done': project_status_done.disabled = True"""

            # project_assigned_to = ui.Select(placeholder=assigned_to.display_name if assigned_to else None, options=list(map(lambda u : discord.SelectOption(label=u.display_name, value=u.id), users)))

            async def on_submit(self, interaction: discord.Interaction) -> None:
                await function(interaction, self.project_displayname, self.project_description)
        
        return EditTaskModal
    
    async def update_task_status(self, task_id, status_id) -> None:
        """Update a task's status and update the message accordingly."""

        if status_id not in TASK_STATUS_MAPPING:
            return

        try:
            self.db.update_task(task_id, status=status_id)
        except DiscordTBException:
            return
        
        t = self.db.get_task_to_task_id(task_id)
        if not t:
            return
        
        c = self.db.get_project_to_id(t.related_project)
        c: discord.TextChannel = await self.fetch_channel(c.channel_id)
        
        m = await c.fetch_message(t.message_id)
        await m.edit(content=f"**Task #{t.number} ({TASK_STATUS_MAPPING[status_id]}):** {t.title}\n{t.description}")

        if t.thread_id == -1:
            return

        thread = await self.fetch_channel(t.thread_id)
        await thread.edit(name=f"Task {t.number} - {t.title} ({TASK_STATUS_MAPPING[status_id]})")
        
        await self.set_thread_read_only(t.id, status_id == 'done')
    
    async def set_thread_read_only(self, task_id: int, read_only: bool = False) -> None:
        """Lock a thread for further interaction."""

        t = self.db.get_task_to_task_id(task_id)
        if not t:
            return

        if t.thread_id == -1:
            return

        thread = await self.fetch_channel(t.thread_id)
        await thread.edit(locked=read_only)        
