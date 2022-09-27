"""
Database component.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from .models import Project, Task, Env, Emoji, ORM_BASE
from .cache import PersistenceCache
from sqlalchemy.engine import Engine
from .exceptions import ChannelAlreadyInUse, EmojiDoesNotExist, CannotBeUpdated
import copy

from discord_taskbot.utils.constants import TASK_EMOJI_IDS, DEFAULT_TASK_EMOJI_MAPPING

__all__ = ['PersistenceAPI']

class PersistenceAPI:

    def __init__(self) -> None:
        """Class that provides an api for accessing and modifying the persistance layer."""

        self._engine: Engine
        self._cache: PersistenceCache = PersistenceCache()

    def startup(self) -> None:
        """Create the database and do some startup things."""

        print("Starting db.")

        ### create engine and tables
        self._engine = create_engine("sqlite:///data.db", echo=True)
        ORM_BASE.metadata.create_all(self._engine)

        ### create env variables
        env_vars = [
            Env(name="PROJECT_ID_COUNT", value="0")
        ]
        env_dict = {k.name : k for k in env_vars}

        for v in env_dict.values():
            self._cache.add(v.name, v.value)

        with Session(self._engine) as session:
            existing_envs: list[Env] = session.query(Env).all()

            # update existing env vars in cache
            for var in list(filter(lambda x : x.name in env_dict, existing_envs)):
                self._cache.update(var.name, var.value)

            # add non-existing env vars to db
            env_dict_copy = env_dict.copy()
            for var in existing_envs:
                env_dict_copy.pop(var.name, None)
            
            for var in env_dict_copy.values():
                session.add(var)

            session.flush(); session.commit()

        ### check if existing project ids are in env and load in cache

        def is_two_tuple_int(x: Env) -> bool:
            try:
                int(x.name)
                int(x.value)
            except:
                return False
            
            return True

        with Session(self._engine) as session:
            existing_projects: list[int] = list(map(lambda x : int(x[0]), session.query(Project.id).all()))
            existing_envs: list[Env] = list(filter(is_two_tuple_int, session.query(Env).all()))
            existing_envs: dict[int, int] = dict(map(lambda x : (int(x.name), int(x.value)), existing_envs))

            for p in existing_projects:
                if p not in existing_envs:
                    self._cache.add(str(p), 0)
                    session.add(Env(name=p, value=0))
                else:
                    self._cache.add(str(p), existing_envs[p])
            
            session.flush(); session.commit()

        ### create task action emojis
        existing_emojis = self.get_task_action_emoji_mapping()

        # if query result and emoji_ids have equivalent ids, return
        if DEFAULT_TASK_EMOJI_MAPPING.keys() == existing_emojis.keys():
            return

        # only keep those emojis which id's are valid
        valid_existing_emoji_ids = list(filter(lambda x : x in TASK_EMOJI_IDS, existing_emojis.keys()))
        
        # use in-db empjis for existing ones, use default emojis for new ones
        new_emoji_mapping = DEFAULT_TASK_EMOJI_MAPPING.copy()
        for e in valid_existing_emoji_ids:
            new_emoji_mapping[e] = existing_emojis[e]
        
        position_count = 1
        with Session(self._engine) as session:

            for e in existing_emojis:
                session.delete(session.get(Emoji, e))

            for id, emoji in new_emoji_mapping.items():
                session.add(Emoji(id=id, emoji=emoji, position=position_count))
                position_count += 1

            session.flush(); session.commit()

    def add_project(self, tag: str, displayname: str, description: str, channel_id: int) -> None:
        """Create a new project."""

        # check if channel is already a project
        channel_ids = self.get_assigned_project_channels()
        if channel_id in channel_ids:
            raise ChannelAlreadyInUse("This channel is already in use for another project.")

        with Session(self._engine) as session:
            
            # add project
            p = Project(tag=tag, display_name=displayname, description=description, channel_id=channel_id)
            p.id = int(self._cache.get("PROJECT_ID_COUNT")) + 1
            session.query(Env).filter(Env.name == "PROJECT_ID_COUNT").first().value = str(p.id)
            self._cache.update("PROJECT_ID_COUNT", str(p.id))
            self._cache.add(str(p.id), "0")

            # add projectid to env for task counting
            e = Env(name=p.id, value=0)
            
            session.add(p)
            session.add(e)
            session.flush()

            session.commit()
    
    def update_project(self, tag: str, displayname: str = "", description: str = "") -> None:
        """Update a project's display name and description."""
        displayname = str(displayname).strip()
        description = str(description).strip()
        
        with Session(self._engine) as session:
            p: Project = session.query(Project).filter(Project.tag == tag).first()

            if displayname:
                p.display_name = displayname

            if description:
                p.description = description
            
            session.flush(); session.commit()

    def add_task(self, projectid, name: str, description: str) -> int:
        """Create a new task for a project."""

        name = str(name).strip()
        description = str(description).strip()

        t = Task(related_project=projectid, title=name, description=description, message_id=-1)

        with Session(self._engine) as session:

            # set task number and update values
            t.number = int(self._cache.get(str(projectid))) + 1
            session.query(Env).filter(Env.name == projectid).first().value = str(t.number)
            self._cache.update(str(projectid), t.number)

            session.add(t)
            session.flush(); session.commit()
        
            return t.id

    def update_task(self, id: int, name: str = "", description: str = "", status: str = "", assigned_to: int = "") -> None:
        """Update a task."""

    def update_task_message_id(self, task_id: int, message_id: int) -> None:
        """Update a task's message id."""

        with Session(self._engine) as session:
            t: Task = session.query(Task).filter(Task.id == task_id).first()

            if t.message_id != -1:
                raise CannotBeUpdated(f"Message id of {task_id} cannot be updated because it already has a valid value.")
            
            t.message_id = message_id
            session.flush(); session.commit()
    
    def update_task_thread_id(self, task_id: int, thread_id: int) -> None:
        """Update a task's thread id."""

        # TODO technically, we don't need any checks. According to the docs, the thread-id is the same
        # as the thread's origin message

        with Session(self._engine) as session:
            t: Task = session.query(Task).filter(Task.id == task_id).first()

            if t.thread_id != -1:
                raise CannotBeUpdated(f"Thread id of {task_id} cannot be updated because it already has a valid value.")
            
            t.thread_id = thread_id
            session.flush(); session.commit()
    
    def get_number_to_task(self, task_id: int) -> int | None:
        """Get a task number to a given task id. This is independent from the project as each task has a unique id."""
        with Session(self._engine) as session:
            t: Task = session.query(Task).filter(Task.id == task_id).first()
            return t.number if t else None
    
    def get_task_to_message_id(self, message_id: int) -> Task | None:
        """Get a task through a message id."""
        with Session(self._engine) as session:
            t: Task = session.query(Task).filter(Task.message_id == message_id).first()
            return copy.copy(t) if t else None

    def get_project_to_channel(self, channel_id: int) -> Project | None:
        """Get a project to a given channel. Returns the project or None if none found."""
        with Session(self._engine) as session:
            p: Project = session.query(Project).filter(Project.channel_id == channel_id).first()
            return p
    
    def get_assigned_project_channels(self) -> list[int]:
        """Get all assigned project channel ids."""

        channels = set()

        with Session(self._engine) as session:
            result = session.query(Project.channel_id).all()
        
            for r in result:
                channels.add(r[0])
        
        return channels
    
    def get_emoji_id_to_emoji(self, emoji: str) -> str | None:
        """Get the emoji id of an emoji."""
        with Session(self._engine) as session:
            e: Emoji = session.query(Emoji).filter(Emoji.emoji == emoji).first()
            return e.id if e else None

    def update_task_action_emoji(self, id: str, emoji: str) -> None:
        """Update a task action emoji."""
        with Session(self._engine) as session:
            e: Emoji = session.query(Emoji).filter(Emoji.id == id).first()
            if not e:
                raise EmojiDoesNotExist(f"Emoji '{id}' cannot be updated because it does not exist.")
            
            e.emoji = emoji

            session.flush(); session.commit()

    def get_task_action_emoji_mapping(self) -> dict[str, str]:
        """Get all task action emoji in a map {id: emoji}."""
        with Session(self._engine) as session:
            emojis: list[Emoji] = session.query(Emoji).order_by(Emoji.position).all()
        
        return {e.id: e.emoji for e in emojis}
