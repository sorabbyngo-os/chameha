"""
Capability Resolver.
"""

from .exceptions import CapabilityNotFound
from .registry import CapabilityRegistry


class CapabilityResolver:

    def __init__(self):

        self.registry = CapabilityRegistry()

    def resolve(self, capability: str):

        result = self.registry.get(capability)

        if result is None:
            raise CapabilityNotFound(capability)

        return result
