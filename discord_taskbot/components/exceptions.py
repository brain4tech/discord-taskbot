"""
Collection of all Exceptions.
"""

class DiscordTBException(Exception):
    """Base exception."""

class ProjectAlreadyExists(DiscordTBException):
    """Exception thrown when a project with same id already exists."""

class ChannelAlreadyInUse(DiscordTBException):
    """Exception thrown when a project is created in a channel that is already assigned to another project."""