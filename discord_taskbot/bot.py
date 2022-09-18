"""
The actual discord bot.
"""

import discord, asyncio

import discord_taskbot.components.models as models
from discord_taskbot.components.persistence import PersistenceAPI

from discord_taskbot.utils import TaskBot, modals, functions
from discord_taskbot.utils import INTENTS

BOT = TaskBot(intents=INTENTS)
tree = BOT.tree

@BOT.event
async def on_ready():
    bot_activity = discord.Activity(type=discord.ActivityType.watching, name="task completions ✅")
    await BOT.change_presence(status=discord.Status.online, activity=bot_activity)
    print(f'Successfully logged in as {BOT.user}.')

@BOT.event
async def on_message(message: discord.Message):
    print (message.clean_content)

@BOT.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    # print(f"New reaction {reaction.emoji} to message {reaction.message.id} by {user.name}.")
    channel = await BOT.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = await BOT.fetch_user(payload.user_id)

    if not user.bot:
        await message.remove_reaction(payload.emoji, user)
    
    if user.bot:
        return

    match str(payload.emoji):
        case '🔴':
            print ("Set status to 'pending'.")
        case '🟠':
            print ("Set status to 'in progress'.")
        case '🟣':
            print ("Set status to 'pending merge'.")
        case '🖐🏼':
            print (f"Task self-assigned by {user.name}")
        case '📰':
            thread_name = message.clean_content.split("\n")[0]
            await message.create_thread(name=thread_name, auto_archive_duration=None)
            print ("Opening discussion thread.")
        case '✅':
            print ("Marking task as done.")

@tree.command()
async def ping(interaction: discord.Interaction):
    """Play the ping pong game!"""
    await interaction.response.send_message("Pong!")
    await asyncio.sleep(3)
    await interaction.delete_original_response()

    # await interaction.channel.send("")

@tree.command(name="newtask")
async def new_task(interaction: discord.Interaction):
    """Create a new task."""
    await interaction.response.send_modal(modals.NewTaskModal())

@tree.command(name="newtaska")
async def new_task_arguments(interaction: discord.Interaction, title: str, description: str):
    """Create a new task without a modal window."""

    await functions.send_new_task(interaction.channel, title, description)