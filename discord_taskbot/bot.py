"""
The actual discord bot.
"""

import traceback
import discord, asyncio

import discord_taskbot.components.models as models
from discord_taskbot.components.persistence import PersistenceAPI
from discord_taskbot.components.exceptions import DiscordTBException
from discord_taskbot.components.client import TaskBot

from discord_taskbot.utils import modals, functions
from discord_taskbot.utils import INTENTS

from sqlalchemy.exc import IntegrityError

BOT = TaskBot(intents=INTENTS)
tree = BOT.tree

@BOT.event
async def on_ready():
    bot_activity = discord.Activity(type=discord.ActivityType.watching, name="task completions ✅")
    await BOT.change_presence(status=discord.Status.online, activity=bot_activity)
    print(f'Successfully logged in as {BOT.user}.')

@BOT.event
async def on_message(message: discord.Message):

    channel_ids = BOT.db.get_assigned_project_channels()

    # if message is an interaction (app command, modal submission, ...), return
    if message.interaction:
        return

    # if message no interaction and channel is registered, delete message
    if message.channel.id in channel_ids:
        await message.delete()

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

    async def modal_func(interaction: discord.Interaction, title: str, description: str):
        await interaction.response.defer()
        await BOT.send_new_task(interaction.channel, title, description)

    modal = BOT.generate_create_task_modal(project="PROJECTNAME HERE!", function=modal_func)
    await interaction.response.send_modal(modal())

@tree.command(name="newtaska")
async def new_task_arguments(interaction: discord.Interaction, title: str, description: str):
    """Create a new task without a modal window."""

    await interaction.response.defer()
    await BOT.send_new_task(interaction.channel, title, description)
    await interaction.followup.send(f"Task created successfully.")
    await asyncio.sleep(1)
    await interaction.delete_original_response()

@tree.command(name="newproject")
async def new_project(interaction: discord.Interaction, id: str, displayname: str, description: str) -> None:
    """Assign a new project to this channel."""

    await interaction.response.defer()
    try:
        BOT.db.add_project(id, displayname, description, interaction.channel_id)
    except IntegrityError:
        await interaction.followup.send(f"Could not create project `{displayname}` as it already exists.")
    except DiscordTBException as e:
        await interaction.followup.send(f"Could not create project `{displayname}`: {e}")
    except Exception:
        traceback.print_exc()
        await interaction.followup.send(f"Something went wrong while creating `{displayname}`.")

    else:
        await interaction.followup.send(f"Created new project `{displayname}`. From now on, all non-command messages will be deleted.")

@tree.command(name="editproject")
async def edit_project(interaction: discord.Interaction) -> None:
    """Edit a project with a pop-up."""
    
    p = BOT.db.get_project_to_channel(interaction.channel_id)
    if not p:
        await interaction.response.send_message(f"This channel is not bound to a project.")
        return

    async def modal_func(interaction: discord.Interaction, new_displayname: str, new_description: str) -> None:
        await interaction.response.defer()

        try:
            BOT.db.update_project(p.tag, new_displayname, new_description)
        except:
            await interaction.followup.send(f"Something went wrong while updating `{p.tag}`.")
        else:
            await interaction.followup.send(f"Successfully updated `{p.tag}`.")

    modal = BOT.generate_edit_project_modal(p.tag, p.display_name, p.description, modal_func)
    await interaction.response.send_modal(modal())
     
@tree.command(name="setemoji")
async def set_emoji(interaction: discord.Interaction, emoji_id: str, emoji: str) -> None:
    """Update a task action emoji"""

    await interaction.response.defer()

    try:
        BOT.db.update_task_action_emoji(emoji_id, emoji)
    except DiscordTBException as e:
        await interaction.followup.send(f"{e} You can only choose from {' | '.join(list(BOT.db.get_task_action_emoji_mapping().keys()))}.")
    else:
        await interaction.followup.send(f"Successfully updated emoji '{emoji_id}' to '{emoji}' (\{emoji}).")