"""
Task Dispatcher.
"""

from plugins import PluginManager


class Dispatcher:

    def __init__(self):

        self.plugins = PluginManager()

    def dispatch(self, task):

        return self.plugins.execute(
            task.capability,
            **task.parameters,
        )
