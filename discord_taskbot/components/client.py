"""
Custom subclass of discord.Client.
"""

from typing import Any, Type

import discord
from discord import app_commands
from discord import ui

from discord_taskbot.components.exceptions import DiscordTBException, TaskDoesNotExist
from discord_taskbot.components.models import Task
from discord_taskbot.utils.constants import DEFAULT_TASK_EMOJI_MAPPING, TASK_STATUS_MAPPING
from .persistence import PersistenceAPI


class TaskBot(discord.Client):
    def __init__(self, *, intents: discord.Intents, **options: Any) -> None:
        """
        A subclass of discord.Client.
        
        Primarily to add custom application commands, but it also provides method for modal generation
        and other higher-level methods for data manipulation.
        
        """
        super().__init__(intents=intents, **options)

        self.tree = app_commands.CommandTree(self)

        # start and initialize the database
        self.db = PersistenceAPI()
        self.db.startup()

    async def setup_hook(self):
        await self.tree.sync()

    async def send_new_task(self, channel: discord.TextChannel, task: Task) -> discord.Message:
        """Send a new task into the specified channel. Return the message if successfull."""

        # TODO check if channel id is actually a project
        message: discord.Message = await channel.send(self.generate_task_string(task))

        task_emojis = self.db.get_task_action_emoji_mapping()

        # add task actions to sent task; task actions are represented with reactions
        for id, emoji in task_emojis.items():
            try:
                await message.add_reaction(emoji)
            except Exception as e:

                # use default emoji in case of an exception
                # the most possible exception is that the emoji stored in the database has been deleted on the server
                print("ERROR! {e} Using fallback emoji from default list.")
                await message.add_reaction(DEFAULT_TASK_EMOJI_MAPPING[id])

        return message

    def generate_create_task_modal(self, project: str, function) -> Type[ui.Modal]:
        """Generate a modal that creates a new task."""

        class CreateTaskModal(ui.Modal, title=f"Create new Task for '{project}'"):
            task_title = ui.TextInput(label="Title", style=discord.TextStyle.short, max_length=150, required=True,
                                      min_length=1)
            task_description = ui.TextInput(label="Description", style=discord.TextStyle.long, max_length=1000,
                                            min_length=1)

            async def on_submit(self, interaction: discord.Interaction) -> None:
                await function(interaction, self.task_title, self.task_description)

        return CreateTaskModal

    def generate_edit_project_modal(self, tag: str, displayname: str, description: str, function) -> Type[ui.Modal]:
        """Generate a modal that edits a project's title and description."""

        class EditProjectModal(ui.Modal, title=f"Edit Project '{tag}'"):
            project_displayname = ui.TextInput(label="Display Name", placeholder=displayname,
                                               style=discord.TextStyle.short, max_length=50, min_length=1,
                                               required=False)
            project_description = ui.TextInput(label="Description", placeholder=description,
                                               style=discord.TextStyle.long, max_length=800, required=False)

            async def on_submit(self, interaction: discord.Interaction) -> None:
                await function(interaction, self.project_displayname, self.project_description)

        return EditProjectModal

    def generate_edit_task_modal(self, title: str, description: str, function) -> Type[ui.Modal]:
        """Generate a modal that edits a task's title and description."""

        class EditTaskModal(ui.Modal, title=f"Edit Task '{title}'"):
            project_displayname = ui.TextInput(label="Title", placeholder=title, style=discord.TextStyle.short,
                                               max_length=150, min_length=1, required=False)
            project_description = ui.TextInput(label="Description", placeholder=description,
                                               style=discord.TextStyle.long, max_length=1000, required=False)

            async def on_submit(self, interaction: discord.Interaction) -> None:
                await function(interaction, self.project_displayname, self.project_description)

        return EditTaskModal

    async def update_task_status(self, task_id, status_id) -> None:
        """Update a task's status and update the message accordingly."""

        if status_id not in TASK_STATUS_MAPPING:
            return

        try:
            t = self.db.update_task(task_id, status=status_id)
        except DiscordTBException:
            return

        c = self.db.get_project_to_id(t.related_project)
        c: discord.TextChannel = await self.fetch_channel(c.channel_id)

        if t.message_id != -1:
            m = await c.fetch_message(t.message_id)
            await m.edit(content=self.generate_task_string(t))

        if t.thread_id != -1:
            thread = await self.fetch_channel(t.thread_id)
            await thread.edit(name=self.generate_task_thread_title(t))

            if status_id != 'done':
                if thread.archived or thread.locked:
                    await self.set_thread_read_only_status(thread, False)

            else:
                if not thread.archived or not thread.locked:
                    await self.set_thread_read_only_status(thread, True)

    async def set_thread_read_only_status(self, thread: discord.Thread, read_only: bool = False) -> None:
        """Lock/Unlock a thread for further interaction."""
        await thread.edit(archived=read_only, locked=read_only)

    def generate_task_string(self, task: Task) -> str:
        """Generate a markdown formatted string to display in a discord chat."""

        number_formatting = f"[#{task.number}]"
        title_formatting = f"**{task.title}**"

        status_formatting = f"`{TASK_STATUS_MAPPING[task.status]}`" if task.status else ""
        assign_formatting = f"> <@{task.assigned_to}>" if task.assigned_to and task.assigned_to != -1 else ""

        description_formatting = f"{task.description}"

        parts = [
            number_formatting + (
                (' ' * 3 + status_formatting) if status_formatting else '') + ' ' * 3 + title_formatting,
            ('\n' + assign_formatting + '\n') if assign_formatting else '',
            description_formatting,
        ]

        print(parts)

        return '\n'.join(parts)

    def generate_task_thread_title(self, task: Task) -> str:
        """Generate a string to use as a Discord thread title."""
        return f"[{task.number}{(', ' + TASK_STATUS_MAPPING[task.status]) if task.status else ''}] {task.title}"

    async def update_task(self, task_id: int, name: str = "", description: str = "", status: str = "",
                          assigned_to: int = "") -> None:
        """Update a task and it's connected message content."""

        if not name and not description and not status and not assigned_to:
            return

        try:
            self.db.update_task(task_id, name, description, status, assigned_to)
        except TaskDoesNotExist:
            return

        t = self.db.get_task_to_task_id(task_id)

        c = self.db.get_project_to_id(t.related_project)
        c: discord.TextChannel = await self.fetch_channel(c.channel_id)

        if t.message_id != -1:
            m = await c.fetch_message(t.message_id)
            await m.edit(content=self.generate_task_string(t))
