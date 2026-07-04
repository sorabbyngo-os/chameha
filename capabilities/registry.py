"""
Capability Registry.
"""

from .models import Capability


class CapabilityRegistry:

    def __init__(self):

        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability):

        self._capabilities[capability.name] = capability

    def get(self, name: str):

        return self._capabilities.get(name)

    def names(self):

        return list(self._capabilities.keys())

    def all(self):

        return self._capabilities.values()
