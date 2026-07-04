"""
Registry interface.
"""

from abc import ABC
from abc import abstractmethod


class Registry(ABC):

    @abstractmethod
    def register(self, name, engine):
        ...

    @abstractmethod
    def get(self, name):
        ...

    @abstractmethod
    def unregister(self, name):
        ...
