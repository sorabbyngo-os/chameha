"""
Sensory Memory Engine.
"""

from .models import SensoryInput


class SensoryMemoryEngine:

    def __init__(self):

        self._buffer: list[SensoryInput] = []

    def push(self, data: SensoryInput):

        self._buffer.append(data)

    def consume(self):

        items = self._buffer

        self._buffer = []

        return items

