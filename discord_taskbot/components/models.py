"""
ORM models.
"""

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base

ORM_BASE = declarative_base()

__all__ = ['ORM_Project', 'ORM_Task', 'ORM_Value', 'ORM_Emoji', 'ORM_BASE']


# TODO add table constructors

class ORM_Project(ORM_BASE):
    """Database table to store all projects."""
    __tablename__ = 'projects'

    tag = Column(String, primary_key=True)
    id = Column(Integer, nullable=False)
    display_name = Column(String, nullable=False)
    description = Column(String, nullable=False, default='')
    channel_id = Column(Integer, nullable=False, unique=True)


class ORM_Task(ORM_BASE):
    """Database table to store all tasks."""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    related_project_id = Column(Integer, nullable=False)
    number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False, default='')
    status = Column(String, nullable=False)
    assigned_to = Column(Integer)
    message_id = Column(Integer, nullable=False, default=-1)
    has_thread = Column(Boolean, nullable=False, default=False)


class ORM_Value(ORM_BASE):
    """Database table to store bot states."""
    __tablename__ = 'values'

    name = Column(String, primary_key=True)
    value = Column(String, nullable=False)


class ORM_Emoji(ORM_BASE):
    """Database table to store task action emojis."""
    __tablename__ = 'emojis'

    id = Column(String, primary_key=True)
    emoji = Column(String, nullable=False, unique=True)
    position = Column(Integer, nullable=False)
