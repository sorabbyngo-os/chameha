"""
Plugin exceptions.
"""


class PluginError(Exception):
    """Base plugin exception."""


class PluginNotFound(PluginError):
    """Requested plugin does not exist."""


class PluginExecutionError(PluginError):
    """Plugin execution failed."""
