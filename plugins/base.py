"""
Base plugin implementation.
"""

from .interface import Plugin


class BasePlugin(Plugin):

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def description(self) -> str:
        return ""

    def execute(self, **kwargs):
        raise NotImplementedError

