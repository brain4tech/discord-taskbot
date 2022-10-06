"""
ORM models as normal classes.
"""

from __future__ import annotations

from .models import ORM_Project, ORM_Task, ORM_Value, ORM_Emoji

__all__ = ['Project', 'Task', 'Value', 'Emoji']


class Data:

    def __init__(self) -> None:
        """Base class for data classes."""

    def __repr__(self) -> str:
        """Generates string representation."""
        values = [f"{k[1:]}:{v}" for k, v in vars(self).items()]
        return f"{type(self).__name__} ({', '.join(values)})"


class Project(Data):
    _tag: str
    _id: int
    _display_name: str
    _description: str
    _channel_id: int

    def __init__(self, tag: str = None, project_id: int = None, display_name: str = None, description: str = None,
                 channel_id: int = None) -> None:
        """
        Project information.

        Attributes:
            tag             Project tag.
            id              Numeric project id.
            display_name    Project display name.
            description     Project description.
            channel_id      Discord channel id for this project.
        """

        self._tag = str(tag).strip() if tag is not None else None
        self._id = int(project_id) if project_id is not None else None
        self._display_name = str(display_name).strip() if display_name is not None else None
        self._description = str(description).strip() if description is not None else None
        self._channel_id = int(channel_id) if channel_id is not None else None

        super().__init__()

    @staticmethod
    def from_orm(orm_project: ORM_Project) -> Project:
        """Create an instance from an existing ORM model instance."""

        if not isinstance(orm_project, ORM_Project):
            raise TypeError(f"Passed project is type {type(orm_project)} not ORM_Project.")

        return Project(orm_project.tag, orm_project.id, orm_project.display_name, orm_project.description,
                       orm_project.channel_id)

    @property
    def tag(self) -> str:
        return self._tag

    @property
    def id(self) -> int:
        return self._id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    @property
    def channel_id(self) -> int:
        return self._channel_id


class Task(Data):
    _id: int
    _related_project_id: int
    _number: int
    _title: str
    _description: str
    _status: str
    _assigned_to: int
    _message_id: int
    _has_thread: int

    def __init__(self, task_id: int = None, related_project_id: int = None, number: int = None, title: str = None,
                 description: str = None, status: str = None, assigned_to: int = None, message_id: int = None,
                 has_thread: bool = None) -> None:
        """
        Task information.

        Attributes:
            id                  Task id.
            related_project_id  Project id this task is bound to.
            number              Task number within project.
            title               Task title.
            description         Task description.
            status              Task status. Either 'pending', 'in_progress', 'pending_merge' or 'done'.
            assigned_to         Discord user id who this task is assigned to.
            message_id          Discord message id of the task's in-discord message.
            has_thread          Whether a task's discussion thread has been opened.
                                A thread's channel id equals its origin message id
        """

        self._id = int(task_id) if task_id is not None else None
        self._related_project_id = int(related_project_id) if related_project_id is not None else None
        self._number = int(number) if number is not None else None
        self._title = str(title).strip() if title is not None else None
        self._description = str(description).strip() if description is not None else None
        self._status = str(status).strip() if status is not None else None
        self._assigned_to = int(assigned_to) if assigned_to is not None else None
        self._message_id = int(message_id) if message_id is not None else None
        self._has_thread = bool(has_thread) if has_thread is not None else None

        super().__init__()

    @staticmethod
    def from_orm(orm_task: ORM_Task) -> Task:
        """Create an instance from an existing ORM model instance."""

        if not isinstance(orm_task, ORM_Task):
            raise TypeError(f"Passed project is type {type(orm_task)} not ORM_Task.")

        return Task(orm_task.id, orm_task.related_project_id, orm_task.number, orm_task.title, orm_task.description,
                    orm_task.status, orm_task.assigned_to, orm_task.message_id, orm_task.thread_id)

    @property
    def id(self) -> int:
        return self._id

    @property
    def related_project_id(self) -> int:
        return self._related_project_id

    @property
    def number(self) -> int:
        return self._number

    @property
    def title(self) -> str:
        return self._title

    @property
    def description(self) -> str:
        return self._description

    @property
    def status(self) -> str:
        return self._status

    @property
    def assigned_to(self) -> int:
        return self._assigned_to

    @property
    def message_id(self) -> int:
        return self._message_id

    @property
    def has_thread(self) -> int:
        return self.has_thread


class Value(Data):
    _name: str
    _value: str

    def __init__(self, name: str = None, value: str = None) -> None:
        """
        Value with named identifier.

        Attributes:
            name        Value name and identifier.
            value       The value itself.
        """

        self._name = str(name).strip() if name is not None else None
        self._value = str(value).strip() if value is not None else None

        super().__init__()

    @staticmethod
    def from_orm(orm_value: ORM_Value) -> Value:
        """Create an instance from an existing ORM model instance."""

        if not isinstance(orm_value, ORM_Value):
            raise TypeError(f"Passed project is type {type(orm_value)} not ORM_Value.")

        return Value(orm_value.name, orm_value.value)

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> str:
        return self._value


class Emoji(Data):
    _id: str
    _emoji: str
    _position: int

    def __init__(self, emoji_id: str = None, emoji: str = None, position: int = None) -> None:
        """
        Task action emoji (Discord reaction emoji).

        Attributes:
            id          Reaction emoji id.
            emoji       The emoji itself. Can be emoji itself (e.g. '😏') or Discord identifier ('<:server_emoji_name:discord_emoji_identifier>').
            position    Row position of emoji.
        """

        self._id = str(emoji_id).strip() if emoji_id is not None else None
        self._emoji = str(emoji).strip() if emoji is not None else None
        self._position = int(position) if position is not None else None

        super().__init__()

    @staticmethod
    def from_orm(orm_emoji: ORM_Emoji) -> Emoji:
        """Create an instance from an existing ORM model instance."""

        if not isinstance(orm_emoji, ORM_Emoji):
            raise TypeError(f"Passed project is type {type(orm_emoji)} not ORM_Emoji.")

        return Emoji(orm_emoji.id, orm_emoji.emoji, orm_emoji.position)

    @property
    def id(self) -> str:
        return self._id

    @property
    def emoji(self) -> str:
        return self._emoji

    @property
    def position(self) -> id:
        return self._position
