"""
ORM models.
"""

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey

ORM_BASE = declarative_base()

__all__ = ['Project', 'Task']

class Project(ORM_BASE):
    """Database table to store all projects."""
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    tag = Column(String)
    name = Column(String)
    description = Column(String)
    channel_id = Column(Integer)


class Task(ORM_BASE):
    """Database table to store all tasks."""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    related_project = Column(Integer, ForeignKey("projects.id"), nullable = False)
    number = Column(Integer, nullable = False)
    title = Column(String, nullable = False)
    description = Column(String)
    status = Column(String)
    assigned_to = Column(Integer)
    message_id = Column(Integer, nullable = False)
    thread_id = Column(Integer)
