"""
Central Event Bus.

Every subsystem communicates through the Event Bus.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable

from .event import Event


class EventBus:
    """
    Publish / Subscribe Event Bus.
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Event], None]]] = defaultdict(list)

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], None],
    ) -> None:
        """
        Register a handler.
        """

        self._subscribers[event_type].append(handler)

    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Event], None],
    ) -> None:

        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    def publish(self, event: Event) -> None:
        """
        Publish an event.
        """

        for handler in self._subscribers[event.event_type]:
            handler(event)

    def clear(self) -> None:
        self._subscribers.clear()
