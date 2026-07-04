"""
Engine registry.
"""

from .engine import BaseEngine


class EngineRegistry:
    """
    Registers all engines available to Chameha.
    """

    def __init__(self):
        self._engines: dict[str, BaseEngine] = {}

    def register(self, engine: BaseEngine):
        self._engines[engine.name] = engine

    def get(self, name: str):
        return self._engines.get(name)

    def all(self):
        return self._engines.values()
