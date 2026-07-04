"""
Plugin Manager.
"""

from .exceptions import PluginNotFound
from .registry import PluginRegistry


class PluginManager:
    """
    Discovers and executes plugins.
    """

    def __init__(self):
        self.registry = PluginRegistry()

    def register(self, plugin):
        self.registry.register(plugin)

    def execute(self, plugin_name: str, **kwargs):
        plugin = self.registry.get(plugin_name)

        if plugin is None:
            raise PluginNotFound(plugin_name)

        return plugin.execute(**kwargs)

    def available_plugins(self):
        return self.registry.names()
