"""
ORM models.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

ORM_BASE = declarative_base()

__all__ = ['Project', 'Task', 'Value', 'Emoji', 'ORM_BASE']


# TODO add table constructors

class Project(ORM_BASE):
    """Database table to store all projects."""
    __tablename__ = 'projects'

    tag = Column(String, primary_key=True)
    id = Column(Integer, nullable=False)
    display_name = Column(String, nullable=False)
    description = Column(String, nullable=False, default='')
    channel_id = Column(Integer, nullable=False, unique=True)


class Task(ORM_BASE):
    """Database table to store all tasks."""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    related_project = Column(Integer, nullable=False)
    number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False, default='')
    status = Column(String, nullable=False)
    assigned_to = Column(Integer)
    message_id = Column(Integer, nullable=False, default=-1)
    thread_id = Column(Integer)


class Value(ORM_BASE):
    """Database table to store bot states."""
    __tablename__ = 'values'

    name = Column(String, primary_key=True)
    value = Column(String, nullable=False)


class Emoji(ORM_BASE):
    """Database table to store task action emojis."""
    __tablename__ = 'emojis'

    id = Column(String, primary_key=True)
    emoji = Column(String, nullable=False, unique=True)
    position = Column(Integer, nullable=False)
