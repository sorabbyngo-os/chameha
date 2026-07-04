"""
Autobiographical Memory Engine.
"""

from .models import LifeEvent


class AutobiographicalMemoryEngine:

    def __init__(self):

        self._events: list[LifeEvent] = []

    def store(self, event: LifeEvent):

        self._events.append(event)

    def retrieve(self):

        return self._events

    def clear(self):

        self._events.clear()
