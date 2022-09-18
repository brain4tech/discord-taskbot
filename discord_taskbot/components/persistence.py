"""
Database component.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from .models import Project, Task

__all__ = ['PersistenceAPI']

class PersistenceAPI:

    def __init__(self) -> None:
        """Class that provides an api for accessing and modifying the persistance layer."""

        self._engine: None

    def startup(self) -> None:
        """Create the database and do some startup things."""

        self._engine = create_engine("sqlite://data.db")

    def add_project(self, name: str, description: str, channel_id: int) -> None:
        """Create a new project."""

        with Session(self._engine) as session:
            pass

    def add_task(self, projectid, name: str, description: str) -> None:
        """Create a new task for a project."""

    def update_task(self, id: int, name: str = "", description: str = "", status: str = "", assigned_to: int = "", thread_id: int = "") -> None:
        """Update a task."""
