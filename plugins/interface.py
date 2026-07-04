"""
Plugin interface.
"""

from abc import ABC, abstractmethod


class Plugin(ABC):
    """
    Base interface implemented by every plugin.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @abstractmethod
    def execute(self, **kwargs):
        ...
