"""
Working Memory Engine.
"""

from .models import WorkingMemory


class WorkingMemoryEngine:

    def __init__(self):

        self._items: list[WorkingMemory] = []

    def add(self, memory: WorkingMemory):

        self._items.append(memory)

    def all(self):

        return self._items

    def clear(self):

        self._items.clear()
