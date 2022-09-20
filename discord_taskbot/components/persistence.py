"""
Database component.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from .models import Project, Task, Env, ORM_BASE
from .cache import PersistenceCache
from sqlalchemy.engine import Engine

__all__ = ['PersistenceAPI']

class PersistenceAPI:

    def __init__(self) -> None:
        """Class that provides an api for accessing and modifying the persistance layer."""

        self._engine: Engine
        self._cache: PersistenceCache = PersistenceCache()

    def startup(self) -> None:
        """Create the database and do some startup things."""

        print("Starting db.")

        # create engine and tables
        self._engine = create_engine("sqlite:///data.db", echo=True)
        ORM_BASE.metadata.create_all(self._engine)

        # create env variables
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
                print(var)
                session.add(var)

            session.flush(); session.commit()

    def add_project(self, tag:str, displayname: str, description: str, channel_id: int) -> None:
        """Create a new project."""

        with Session(self._engine) as session:
            p = Project(tag=tag, display_name=displayname, description=description, channel_id=channel_id)
            p.id = int(self._cache.get("PROJECT_ID_COUNT")) + 1
            session.query(Env).filter(Env.name == "PROJECT_ID_COUNT").first().value = str(p.id)
            
            session.add(p)
            session.flush()

            session.commit()

    def add_task(self, projectid, name: str, description: str) -> None:
        """Create a new task for a project."""

    def update_task(self, id: int, name: str = "", description: str = "", status: str = "", assigned_to: int = "", thread_id: int = "") -> None:
        """Update a task."""
