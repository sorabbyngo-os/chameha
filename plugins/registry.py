"""
Plugin registry.
"""

from .interface import Plugin


class PluginRegistry:
    """
    Stores available plugins.
    """

    def __init__(self):
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin):
        self._plugins[plugin.name] = plugin

    def unregister(self, name: str):
        self._plugins.pop(name, None)

    def get(self, name: str):
        return self._plugins.get(name)

    def all(self):
        return self._plugins.values()

    def names(self):
        return list(self._plugins.keys())
