"""
Runtime Engine Registry.
"""

from .exceptions import (
    EngineAlreadyRegistered,
    EngineNotFound,
)


class EngineRegistry:

    def __init__(self):

        self._engines = {}

    def register(self, name, engine):

        if name in self._engines:
            raise EngineAlreadyRegistered(name)

        self._engines[name] = engine

    def unregister(self, name):

        if name not in self._engines:
            raise EngineNotFound(name)

        del self._engines[name]

    def get(self, name):

        if name not in self._engines:
            raise EngineNotFound(name)

        return self._engines[name]

    def exists(self, name):

        return name in self._engines

    def names(self):

        return sorted(self._engines.keys())

    def all(self):

        return dict(self._engines)
