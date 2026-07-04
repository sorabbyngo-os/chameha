"""
Memory interfaces.
"""

from abc import ABC, abstractmethod


class MemoryStore(ABC):

    @abstractmethod
    def store(self, memory):
        ...

    @abstractmethod
    def retrieve(self, query):
        ...

    @abstractmethod
    def delete(self, memory_id):
        ...
