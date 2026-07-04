"""
Dispatches Events through the Event Bus.
"""

from .bus import EventBus
from .event import Event


class EventDispatcher:

    def __init__(self, bus: EventBus):
        self.bus = bus

    def dispatch(self, event: Event):
        self.bus.publish(event)
