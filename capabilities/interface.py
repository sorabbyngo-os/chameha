"""
Capability interface.
"""

from abc import ABC, abstractmethod


class CapabilityProvider(ABC):

    @property
    @abstractmethod
    def capability(self) -> str:
        ...

    @abstractmethod
    def execute(self, **kwargs):
        ...

