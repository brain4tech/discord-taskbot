"""
Database component.
"""

import copy

from collections.abc import Iterable

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from discord_taskbot.utils.constants import TASK_EMOJI_IDS, DEFAULT_TASK_EMOJI_MAPPING, TASK_STATUS_IDS
from .cache import PersistenceCache
from .exceptions import ChannelAlreadyInUse, EmojiDoesNotExist, CannotBeUpdated, ProjectDoesNotExist, TaskDoesNotExist
from .models import ORM_Project, ORM_Task, ORM_Value, ORM_Emoji, ORM_BASE
from .data_classes import Project, Task, Emoji, Value

__all__ = ['PersistenceAPI']


class PersistenceAPI:

    def __init__(self) -> None:
        """Class that provides an api for accessing and modifying the persistence layer."""

        self._engine: Engine
        self._cache: PersistenceCache = PersistenceCache()

        self._engine = None

    def startup(self) -> None:
        """Create the database and do some startup things."""

        # create engine and tables
        self._engine = create_engine("sqlite:///data.db", echo=True)
        ORM_BASE.metadata.create_all(self._engine)

        # execute specialized database startup functions
        self._startup_create_runtime_vals()
        self._startup_project_id_value()
        self._startup_task_action_emojis()

    def _startup_create_runtime_vals(self) -> None:
        """Create and store runtime values in database and cache."""

        # define static runtime values
        values = [
            ORM_Value(name="PROJECT_ID_COUNT", value="0")
        ]
        val_dict = {k.name: k for k in values}

        for v in val_dict.values():
            self._cache.add(v.name, v.value)

        with Session(self._engine) as session:
            db_vals: list[ORM_Value] = session.query(ORM_Value).all()

            # update existing env vars in cache
            for var in list(filter(lambda x: x.name in val_dict, db_vals)):
                self._cache.update(var.name, var.value)

            # remove all values that exist in db
            for var in db_vals:
                val_dict.pop(var.name, None)

            # add non-existing env vars to db
            for var in val_dict.values():
                session.add(var)

            session.commit()

    def _startup_project_id_value(self) -> None:
        """Add project ids to Values table"""

        def is_int_value(x: ORM_Value) -> bool:
            """Small function to check if both name and value of a Value can be cast to an int."""
            try:
                int(x.name)
                int(x.value)
            except ValueError:
                return False

            return True

        with Session(self._engine) as session:
            # get existing projects from database
            existing_projects: Iterable[int] = map(lambda x: int(x[0]), session.query(ORM_Project.id).all())

            # map all valid (see function above) values from database into a dict
            existing_values: dict[int, int] = {int(v.name): int(v.value)
                                               for v in filter(is_int_value, session.query(ORM_Value).all())}

            for p in existing_projects:
                if p not in existing_values:
                    self._cache.add(str(p), 0)
                    session.add(ORM_Value(name=p, value=0))
                else:
                    self._cache.add(str(p), existing_values[p])

            session.commit()

    def _startup_task_action_emojis(self) -> None:
        """Update and ensure correct task action emoji order and values in database."""
        existing_emojis = self.get_task_action_emoji_mapping()

        # if query result and emoji_ids have equivalent ids, return
        if DEFAULT_TASK_EMOJI_MAPPING.keys() == existing_emojis.keys():
            return

        # only keep those emojis with valid ids
        valid_existing_emoji_ids = filter(lambda x: x in TASK_EMOJI_IDS, existing_emojis.keys())

        # use stored emojis for existing ids, use default emojis for new ids
        emoji_mapping = DEFAULT_TASK_EMOJI_MAPPING.copy()
        for e_id in valid_existing_emoji_ids:
            emoji_mapping[e_id] = existing_emojis[e_id]

        position_count = 1
        with Session(self._engine) as session:

            # delete all existing emojis in table
            session.query(ORM_Emoji).delete()

            # (re) add emojis while considering their order
            for e_id, emoji in emoji_mapping.items():
                session.add(ORM_Emoji(id=e_id, emoji=emoji, position=position_count))
                position_count += 1

            session.commit()

    def add_project(self, tag: str, display_name: str, description: str, channel_id: int) -> Project:
        """Create a new project."""

        display_name = str(display_name).strip()
        description = str(description).strip()

        # check if channel is already a project
        # although channel_id is unique, check and raise custom exception for better ux
        if self.is_channel_in_use(channel_id):
            raise ChannelAlreadyInUse("This channel is already in use for another project.")

        with Session(self._engine) as session:
            # add project
            p = ORM_Project(
                tag=tag,
                id=self._generate_project_id(),
                display_name=display_name,
                description=description,
                channel_id=int(channel_id),
            )
            session.add(p)

            # add project task counter to cache and static values
            v = ORM_Value(name=p.id, value=0)
            self._cache.add(str(v.name), v.value)
            session.add(v)

            session.commit()

            return Project.from_orm(p)

    def update_project(self, tag: str, display_name: str = None, description: str = None) -> Project:
        """Update a project's display name and description."""
        display_name = str(display_name).strip() if display_name is not None else None
        description = str(description).strip() if description is not None else None

        with Session(self._engine) as session:
            p: ORM_Project = session.get(ORM_Project, tag)

            if not p:
                raise ProjectDoesNotExist(f"Project with tag '{tag}' does not exist.")

            if display_name:
                p.display_name = display_name

            if description:
                p.description = description

            session.commit()

            return Project.from_orm(p)

    def add_task(self, related_project_id: int, name: str, description: str) -> Task:
        """Create a new task for a project."""

        related_project_id = int(related_project_id)
        name = str(name).strip()
        description = str(description).strip()

        # TODO check if related project exists

        with Session(self._engine) as session:
            # add task
            t = ORM_Task(
                related_project_id=related_project_id,
                number=self._generate_task_number(related_project_id),
                title=name,
                description=description,
                status='pending',
            )
            session.add(t)

            session.commit()

            return Task.from_orm(t)

    def update_task(self, task_id: int, title: str = None, description: str = None, status: str = None,
                    assigned_to: int = None, message_id: int = None, has_thread: bool = None) -> Task:
        """Update a task."""

        title = str(title).strip() if title is not None else None
        description = str(description).strip() if description is not None else None
        status = str(status).strip() if status is not None else None
        assigned_to = int(assigned_to) if assigned_to is not None else None
        message_id = int(message_id) if message_id is not None else None
        has_thread = bool(has_thread) if has_thread is not None else None

        with Session(self._engine) as session:

            t: ORM_Task = session.get(ORM_Task, task_id)
            if not t:
                raise TaskDoesNotExist(f"Task with id '{task_id}' does not exist.")

            if title:
                t.title = title

            if description:
                t.description = description

            if status and status in TASK_STATUS_IDS:
                t.status = status

            if assigned_to:
                t.assigned_to = int(assigned_to)

            if message_id:
                if t.message_id != -1:
                    raise CannotBeUpdated(f"Message id of {task_id} cannot be updated because it already has a valid value.")

                t.message_id = message_id

            if has_thread:
                if t.has_thread:
                    raise CannotBeUpdated(f"Thread status of {task_id} cannot be updated because it already has a valid value.")

                t.has_thread = True

            session.commit()

            return Task.from_orm(t)

    def get_project(self, tag: str = None, project_id: int = None, channel_id: int = None) -> Project | None:
        """Get a project from a unique project value. Returns the Project or None if no results."""

        # ensure values have correct types
        try:
            tag = str(tag) if tag is not None else None
            project_id = int(project_id) if project_id is not None else None
            channel_id = int(channel_id) if channel_id is not None else None
        except TypeError:
            raise
        except ValueError:
            raise

        p: ORM_Project

        with Session(self._engine) as session:

            if tag:
                p = session.get(ORM_Project, tag)
                if p:
                    return Project.from_orm(p)

            if project_id:
                p = session.query(ORM_Project).filter(ORM_Project.id == project_id).first()
                if p:
                    return Project.from_orm(p)

            if channel_id:
                p = session.query(ORM_Project).filter(ORM_Project.channel_id == channel_id).first()
                if p:
                    return Project.from_orm(p)

        return None

    def get_task(self, task_id: int = None, message_id: int = None, thread_id: int = None) -> Task | None:
        """
        Get a task from a unique task value. Returns the Task or None if no results.
        thread_id is a synonym for message_id.
        """

        try:
            task_id = int(task_id) if task_id is not None else None
            message_id = int(message_id) if message_id is not None else None

            if thread_id is not None:
                message_id = int(thread_id)

        except TypeError:
            raise
        except ValueError:
            raise

        t: ORM_Task

        with Session(self._engine) as session:

            if task_id:
                t = session.get(ORM_Task, task_id)
                if t:
                    return Task.from_orm(t)

            if message_id and message_id != -1:
                t = session.query(ORM_Task).filter(ORM_Task.message_id == message_id).first()
                if t:
                    return Task.from_orm(t)

        return None

    def is_channel_in_use(self, channel_id) -> bool:
        """Check if passed channel id is already taken (== a project)."""

        with Session(self._engine) as session:
            p: ORM_Project = session.query(ORM_Project).filter(ORM_Project.channel_id == channel_id).first()

        # the query returns either something or None, and bool(None) -> False
        return bool(p)

    def _generate_project_id(self) -> int:
        """Calculates, stores and returns a new project id integer from existing counters."""

        # retrieve counter from cache
        # no need to check if the value exists in cache.
        # it is in the cache UNLESS some other unknown code manipulates the cache.
        id_count = int(self._cache.get("PROJECT_ID_COUNT"))

        # increase counter
        id_count += 1

        # update value in database
        with Session(self._engine) as session:
            v: ORM_Value = session.query(ORM_Value).filter(ORM_Value.name == "PROJECT_ID_COUNT").first()
            v.value = str(id_count)

            session.commit()

        # update value in cache if database storing was successful
        self._cache.update("PROJECT_ID_COUNT", str(id_count))

        # return generated id
        return id_count

    def _generate_task_number(self, related_project_id: int) -> int:
        """Calculates, stores and returns a task number integer for the related project from existing counters."""

        # cast project id to string
        related_project_id = str(related_project_id)

        # retrieve counter from cache
        # no need to check if the value exists in cache.
        # it is in the cache UNLESS some other unknown code manipulates the cache.
        task_number = int(self._cache.get(related_project_id))

        # increase counter
        task_number += 1

        # update value in database
        with Session(self._engine) as session:
            v: ORM_Value = session.query(ORM_Value).filter(ORM_Value.name == related_project_id).first()
            v.value = str(task_number)

            session.commit()

        # update value in cache if database storing was successful
        self._cache.update(related_project_id, str(task_number))

        # return generated number
        return task_number

    def get_emojis(self) -> list[Emoji]:
        """Get all emojis."""
        with Session(self._engine) as session:
            e_list: list[ORM_Emoji] = session.query(ORM_Emoji).all()
            return [Emoji.from_orm(e) for e in e_list]

    def get_emoji(self, emoji_id: str = None, emoji: str = None) -> Emoji | None:
        """Get the emoji to the id."""

        emoji_id = str(emoji_id).strip()
        emoji = str(emoji).strip()

        with Session(self._engine) as session:

            if emoji_id:
                e: ORM_Emoji = session.get(ORM_Emoji, emoji_id)
                if e :
                    return Emoji.from_orm(e)

            if emoji:
                e: ORM_Emoji = session.query(ORM_Emoji).filter(ORM_Emoji.emoji == emoji).first()
                if e:
                    return Emoji.from_orm(e)

        return None

    def update_task_action_emoji(self, task_id: str, emoji: str) -> None:
        """Update a task action emoji."""
        with Session(self._engine) as session:
            e: ORM_Emoji = session.query(ORM_Emoji).filter(ORM_Emoji.id == task_id).first()
            if not e:
                raise EmojiDoesNotExist(f"Emoji '{task_id}' cannot be updated because it does not exist.")

            e.emoji = emoji

            # TODO check if unique constrain of emoji column has been violated (catch exception)

            session.commit()

    def get_task_action_emoji_mapping(self) -> dict[str, str]:
        """Get all task action emoji in a map {id: emoji}."""
        with Session(self._engine) as session:
            emojis: list[ORM_Emoji] = session.query(ORM_Emoji).order_by(ORM_Emoji.position).all()

        return {e.id: e.emoji for e in emojis}
