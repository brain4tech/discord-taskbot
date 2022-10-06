"""
Persistence cache for faster data access.
"""

from typing import Any


class PersistenceCache:

    def __init__(self) -> None:
        """
        Add and update cache variables to speed up data access times.
        
        It's the programmer's responsibility to synchronize cache and persistent storage.

        Methods:
            add
            get
            update
            remove
        
        See the method docstrings for more explanation.
        """

    def add(self, name: str, value: Any) -> None:
        """Add a new value to the cache."""

        # ensure name of cache item is type string
        # checks in other methods are not needed, as all of them check if the name (== string) exists
        if not isinstance(name, str):
            raise TypeError(f"Parameter type for 'name' is {type(name)} not str.")

        if name in vars(self):
            raise AttributeError(
                f"Attribute '{name}' already exists in cache. If you want to update it use .update(name, value).")
        self.__setattr__(name, value)

    def get(self, name: str) -> Any | None:
        """Get a value from the cache. If it does not exist None is returned."""
        try:
            return self.__getattribute__(name)
        except AttributeError:
            return None

    def update(self, name: str, value: Any) -> None:
        """Update a value in the cache."""

        if name not in vars(self):
            raise AttributeError(
                f"Attribute '{name}' does not exist in cache. Add new values with add() before updating them.")
        self.__setattr__(name, value)

    def remove(self, name: str) -> None:
        """Remove a value from the cache."""
        if name in vars(self):
            self.__delattr__(name)
