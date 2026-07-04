"""
Dependency Injection Container.

Creates and owns the shared services used by Chameha.
"""

from core import EventBus
from core import EngineRegistry
from engine_registry import EngineRegistry
from plugins import PluginManager

from capabilities import CapabilityRegistry

from memory import MemoryManager


class Container:
    """
    Central dependency container.
    """

    def __init__(self):

        # Core
        self.events = EventBus()
        self.engines = EngineRegistry()

        # Plugin System
        self.plugins = PluginManager()

        # Capability Layer
        self.capabilities = CapabilityRegistry()

        # Memory System
        self.memory = MemoryManager()
       
        self.registry = EngineRegistry()

        self.registry.register("memory", self.memory)
