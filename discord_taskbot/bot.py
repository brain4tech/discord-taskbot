"""
The actual discord bot.
"""

import traceback
import discord, asyncio

import discord_taskbot.components.models as models
from discord_taskbot.components.persistence import PersistenceAPI
from discord_taskbot.components.exceptions import DiscordTBException, CannotBeUpdated
from discord_taskbot.components.client import TaskBot
from discord_taskbot.utils.constants import TASK_STATUS_IDS, TASK_STATUS_MAPPING

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
    if message.channel.id in channel_ids and message.author.id != BOT.user.id:
        await message.delete()

@BOT.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    # print(f"New reaction {reaction.emoji} to message {reaction.message.id} by {user.name}.")
    channel = await BOT.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = await BOT.fetch_user(payload.user_id)

    # check if message is a task
    task = BOT.db.get_task_to_message_id(message.id)
    if not task:
        return

    if not user.bot:
        await message.remove_reaction(payload.emoji, user)
    
    if user.bot:
        return

    emoji_id = BOT.db.get_emoji_id_to_emoji(str(payload.emoji))
    if not emoji_id:
        return

    match emoji_id:
        case 'pending':
            await BOT.update_task_status(task.id, emoji_id)
        case 'in_progress':
            await BOT.update_task_status(task.id, emoji_id)
        case 'pending_merge':
            await BOT.update_task_status(task.id, emoji_id)
        case 'self_assign':
            print (f"Task self-assigned by {user.name}")
        case 'open_discussion':
            thread_name = message.clean_content.split("\n")[0]
            thread = await message.create_thread(name=thread_name, auto_archive_duration=None)
            await thread.edit(name=f"Task {task.number} - {task.title}")
            
            try:
                BOT.db.update_task_thread_id(task.id, thread.id)
            except CannotBeUpdated:
                pass
        case 'done':
            await BOT.update_task_status(task.id, emoji_id)

@tree.command()
async def ping(interaction: discord.Interaction):
    """Play the ping pong game!"""
    await interaction.response.send_message("Pong!")
    await asyncio.sleep(3)
    await interaction.delete_original_response()

    # await interaction.channel.send("")

@tree.command(name="newtask")
async def new_task(interaction: discord.Interaction, title: str, description: str):
    """Create a new task."""

    await interaction.response.defer()

    # check if channel id is valid
    project = BOT.db.get_project_to_channel(interaction.channel_id)
    if not project:
        await interaction.followup.send(f"This channel is not assigned to a project. Try again in a valid project channel. Entered information:\n\n{title}\n{description}")
        return

    try:
        task_id = BOT.db.add_task(project.id, title, description)
    except Exception:
        print (traceback.format_exc())
        await interaction.followup.send("Something went wrong while creating a new task.")
        return
    
    message = await BOT.send_new_task(interaction.channel, BOT.db.get_number_to_task(task_id), title, description)
    BOT.db.update_task_message_id(task_id, message.id)
    await BOT.update_task_status(task_id, 'pending')

    await interaction.followup.send(f"Task created successfully.")
    await asyncio.sleep(1)
    await interaction.delete_original_response()

@tree.command(name="newtaskm")
async def new_task_modal(interaction: discord.Interaction):
    """Create a new task with a modal window."""

    async def modal_func(interaction: discord.Interaction, title: str, description: str):
        await interaction.response.send_message("Creating new task...")

        try:
            task_id = BOT.db.add_task(project.id, title, description)
        except Exception:
            print (traceback.format_exc())
            await interaction.followup.send("Something went wrong while creating a new task.")
            return
        
        message = await BOT.send_new_task(interaction.channel, BOT.db.get_number_to_task(task_id), title, description)
        BOT.db.update_task_message_id(task_id, message.id)
        await BOT.update_task_status(task_id, 'pending')
        await interaction.edit_original_response(content=f"Task created successfully.")
        await asyncio.sleep(1)
        await interaction.delete_original_response()

    project = BOT.db.get_project_to_channel(interaction.channel_id)
    if not project:
        await interaction.response.send_message(f"This channel is not assigned to a project. Try again in a valid project channel.")
        return

    modal = BOT.generate_create_task_modal(project=project.display_name, function=modal_func)
    await interaction.response.send_modal(modal())

@tree.command(name="edittask")
async def edit_task(interaction: discord.Interaction):
    """Edit a task's title and description with a modal."""

    # check if command is send in a task thread
    t = BOT.db.get_task_to_thread_id(interaction.channel_id)
    if not t:
        await interaction.followup.send("Failure. Tasks can only be edited from their discussion threads.")
        await asyncio.sleep(3)
        await interaction.delete_original_response()
        return
    
    async def modal_func(interaction: discord.Interaction, new_title: str, new_description: str) -> None:
        await interaction.response.defer()

        try:
            BOT.db.update_task(task_id=t.id, name=new_title, description=new_description)
        except:
            await interaction.followup.send(f"Something went wrong while updating task {t.number}.")
        else:
            await interaction.followup.send(f"Successfully updated task {t.number}. ")
            if str(new_title).strip() != "":
                c = await BOT.fetch_channel(interaction.channel.id)
                await c.edit(name=f"Task {t.number} - {new_title}")

    t_assigned_user = None
    if t.assigned_to:
        t_assigned_user = await BOT.get_user(t.assigned_to)
    
    emoji_dict = {e.id: e.emoji for e in BOT.db.get_emojis()}

    all_members = list(BOT.get_all_members())
        
    modal = BOT.generate_edit_task_modal(t.title, t.description, t.status, t_assigned_user, modal_func, all_members, emoji_dict)
    await interaction.response.send_modal(modal())

@tree.command(name="status")
async def set_task_status(interaction: discord.Interaction, status: str) -> None:
    """Update a task's status."""

    await interaction.response.defer()

    # check if command is send in a task thread
    t = BOT.db.get_task_to_thread_id(interaction.channel_id)
    if not t:
        await interaction.followup.send("Failure. Tasks can only be edited from their discussion threads.")
        await asyncio.sleep(3)
        await interaction.delete_original_response()
        return

    status = str(status).strip()

    if status not in TASK_STATUS_MAPPING:
        await interaction.followup.send(f"Invalid status id. You can only choose from {' | '.join(list(TASK_STATUS_MAPPING.keys()))}")
        return

    await BOT.update_task_status(t.id, status)
    await interaction.followup.send(f"Updated status to {TASK_STATUS_MAPPING[status]}.")

@tree.command(name="assign")
async def assign_task(interaction: discord.Interaction, person: str = None) -> None:
    """Update a task's developer."""

    await interaction.response.defer()

    # check if command is send in a task thread
    t = BOT.db.get_task_to_thread_id(interaction.channel_id)
    if not t:
        await interaction.followup.send("Failure. Tasks can only be edited from their discussion threads.")
        await asyncio.sleep(3)
        await interaction.delete_original_response()
        return
    
    print(person, type(person))
    # None <class 'NoneType'>
    # hi <class 'str'>
    # <@438711786225795072> <class 'str'>

    # if None: self assign
    # if string without a valid mention: reset
    # if valid mention: to mention

    print ("assignment")

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