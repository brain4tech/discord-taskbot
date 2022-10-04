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
from .models import Project, Task, Value, Emoji, ORM_BASE

__all__ = ['PersistenceAPI']


class PersistenceAPI:

    def __init__(self) -> None:
        """Class that provides an api for accessing and modifying the persistence layer."""

        self._engine: Engine
        self._cache: PersistenceCache = PersistenceCache()

        self._engine = None

    def startup(self) -> None:
        """Create the database and do some startup things."""

        ### create engine and tables
        self._engine = create_engine("sqlite:///data.db", echo=True)
        ORM_BASE.metadata.create_all(self._engine)
        self._startup_create_runtime_vals()
        self._startup_project_id_value()
        self._startup_task_action_emojis()

    def _startup_create_runtime_vals(self) -> None:
        """Create and store runtime values in database and cache."""

        # define static runtime values
        values = [
            Value(name="PROJECT_ID_COUNT", value="0")
        ]
        val_dict = {k.name: k for k in values}

        for v in val_dict.values():
            self._cache.add(v.name, v.value)

        with Session(self._engine) as session:
            db_vals: list[Value] = session.query(Value).all()

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
        def is_int_value(x: Value) -> bool:
            """Small function to check if both name and value of a Value can be cast to an int."""
            try:
                int(x.name)
                int(x.value)
            except ValueError:
                return False

            return True

        with Session(self._engine) as session:
            # get existing projects from database
            existing_projects: Iterable[int] = map(lambda x: int(x[0]), session.query(Project.id).all())

            # map all valid (see function above) values from database into a dict
            existing_values: dict[int, int] = {int(v.name): int(v.value)
                                               for v in filter(is_int_value, session.query(Value).all())}

            for p in existing_projects:
                if p not in existing_values:
                    self._cache.add(str(p), 0)
                    session.add(Value(name=p, value=0))
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
            session.query(Emoji).delete()

            # (re) add emojis while considering their order
            for e_id, emoji in emoji_mapping.items():
                session.add(Emoji(id=e_id, emoji=emoji, position=position_count))
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
            p = Project(
                tag=tag,
                id=self._generate_project_id(),
                display_name=display_name,
                description=description,
                channel_id=int(channel_id),
            )
            session.add(p)

            # add project id to static values
            v = Value(name=p.id, value=0)
            session.add(v)

            session.commit()

        return copy.copy(p)

    def update_project(self, tag: str, display_name: str = "", description: str = "") -> Project:
        """Update a project's display name and description."""
        display_name = str(display_name).strip()
        description = str(description).strip()

        with Session(self._engine) as session:
            p: Project = session.get(Project, tag)

            if not p:
                raise ProjectDoesNotExist(f"Project with tag '{tag}' does not exist.")

            if display_name:
                p.display_name = display_name

            if description:
                p.description = description

            session.commit()

        return copy.copy(p)

    def add_task(self, related_project: int, name: str, description: str) -> Task:
        """Create a new task for a project."""

        related_project = int(related_project)
        name = str(name).strip()
        description = str(description).strip()

        # TODO check if related project exists

        with Session(self._engine) as session:
            # add task
            t = Task(
                related_project=related_project,
                number=self._generate_task_number(related_project),
                title=name,
                description=description,
                status='pending',
            )
            session.add(t)

            session.commit()

        return copy.copy(t)

    def update_task(self, task_id: int, name: str = "", description: str = "", status: str = "",
                    assigned_to: int = "") -> Task:
        """Update a task."""

        name = str(name).strip()
        description = str(description).strip()
        status = str(status).strip()

        with Session(self._engine) as session:

            t: Task = session.get(Task, task_id)
            if not t:
                raise TaskDoesNotExist(f"Task with id '{task_id}' does not exist.")

            if name:
                t.title = name

            if description:
                t.description = description

            if status and status in TASK_STATUS_IDS:
                t.status = status

            if assigned_to:
                t.assigned_to = int(assigned_to)

            session.commit()

        return copy.copy(t)

    def update_task_message_id(self, task_id: int, message_id: int) -> None:
        """Update a task's message id."""

        with Session(self._engine) as session:
            t: Task = session.query(Task).filter(Task.id == task_id).first()

            if t.message_id != -1:
                raise CannotBeUpdated(
                    f"Message id of {task_id} cannot be updated because it already has a valid value.")

            t.message_id = message_id
            
            session.commit()

    def update_task_thread_id(self, task_id: int, thread_id: int) -> None:
        """Update a task's thread id."""

        # TODO technically, we don't need any checks. According to the docs, the thread-id is the same
        # as the thread's origin message

        with Session(self._engine) as session:
            t: Task = session.query(Task).filter(Task.id == task_id).first()

            if t.thread_id != -1:
                raise CannotBeUpdated(f"Thread id of {task_id} cannot be updated because it already has a valid value.")

            t.thread_id = thread_id
            
            session.commit()

    def get_number_to_task(self, task_id: int) -> int | None:
        """Get a task number to a given task id. This is independent from the project as each task has a unique id."""
        with Session(self._engine) as session:
            t: Task = session.query(Task).filter(Task.id == task_id).first()
            return t.number if t else None

    def get_task_to_thread_id(self, thread_id: int) -> Task | None:
        """Get a task through a thread id."""
        with Session(self._engine) as session:
            t: Task = session.query(Task).filter(Task.thread_id == thread_id).first()
            return copy.copy(t) if t else None

    def get_task_to_message_id(self, message_id: int) -> Task | None:
        """Get a task through a message id."""
        with Session(self._engine) as session:
            t: Task = session.query(Task).filter(Task.message_id == message_id).first()
            return copy.copy(t) if t else None

    def get_task_to_task_id(self, task_id: int) -> Task | None:
        """Get a task through a task id."""
        with Session(self._engine) as session:
            t: Task = session.query(Task).filter(Task.id == task_id).first()
            return copy.copy(t) if t else None

    def get_project_to_channel(self, channel_id: int) -> Project | None:
        """Get a project to a given channel. Returns the project or None if none found."""
        with Session(self._engine) as session:
            p: Project = session.query(Project).filter(Project.channel_id == channel_id).first()
            return p

    def get_project_to_id(self, project_id: int) -> Project | None:
        """Get a task through a task id."""
        with Session(self._engine) as session:
            p: Task = session.query(Project).filter(Project.id == project_id).first()
            return copy.copy(p) if p else None

    def is_channel_in_use(self, channel_id) -> bool:
        """Check if passed channel id is already taken (== a project)."""

        with Session(self._engine) as session:
            p: Project = session.query(Project).filter(Project.channel_id == channel_id)

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
            v: Value = session.query(Value).filter(Value.name == "PROJECT_ID_COUNT").first()
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
            v: Value = session.query(Value).filter(Value.name == related_project_id).first()
            v.value = str(task_number)

            session.commit()

        # update value in cache if database storing was successful
        self._cache.update(related_project_id, str(task_number))

        # return generated number
        return task_number

    def get_emoji_id_to_emoji(self, emoji: str) -> str | None:
        """Get the emoji id of an emoji."""
        with Session(self._engine) as session:
            e: Emoji = session.query(Emoji).filter(Emoji.emoji == emoji).first()
            return e.id if e else None

    def get_emojis(self) -> list[Emoji]:
        """Get all emojis."""
        with Session(self._engine) as session:
            e: Emoji = session.query(Emoji).all()
            return e

    def update_task_action_emoji(self, id: str, emoji: str) -> None:
        """Update a task action emoji."""
        with Session(self._engine) as session:
            e: Emoji = session.query(Emoji).filter(Emoji.id == id).first()
            if not e:
                raise EmojiDoesNotExist(f"Emoji '{id}' cannot be updated because it does not exist.")

            e.emoji = emoji

            
            session.commit()

    def get_task_action_emoji_mapping(self) -> dict[str, str]:
        """Get all task action emoji in a map {id: emoji}."""
        with Session(self._engine) as session:
            emojis: list[Emoji] = session.query(Emoji).order_by(Emoji.position).all()

        return {e.id: e.emoji for e in emojis}
