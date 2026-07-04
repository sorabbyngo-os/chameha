"""
Dependency container.
"""

from core import EventBus
from core import EngineRegistry

from plugins import PluginManager

from capabilities import CapabilityRegistry


class Container:

    """
    Central dependency container.
    """

    def __init__(self):

        self.events = EventBus()

        self.engines = EngineRegistry()

        self.plugins = PluginManager()

        self.capabilities = CapabilityRegistry()
