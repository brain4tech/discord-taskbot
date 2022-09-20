"""
Persistence cache for faster data access.
"""

from typing import Any


class PersistenceCache:
    
    def __init__(self) -> None:
        """
        Add and update cache variables to speed up data access times.
        
        It's the programmer's responsibility changes to the cache are stored in the db too.
        """

    def add(self, name: str, value: Any) -> None:
        """Add a new value to the cache."""
        if name in vars(self):
            raise AttributeError(f"Attribute '{name}' already exists. If you want to update it use .update().")
        self.__setattr__(name, value)

    def get(self, name: str) -> Any | None:
        """Get a value from the cache. If value does not exist None is returned."""
        try:
            return self.__getattribute__(name)
        except:
            return None

    
    def update(self, name: str, value: Any) -> None:
        """Update a value in the cache."""
        
        if name not in vars(self):
            raise AttributeError(f"Attribute '{name}' does not exist in cache. Please add it with .add().")
        self.__setattr__(name, value)
    
    def remove(self, name: str) -> None:
        """Remove a value from the cache."""
        self.__delattr__(name)
    