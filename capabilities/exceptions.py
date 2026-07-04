"""
Capability exceptions.
"""


class CapabilityError(Exception):
    """Base capability exception."""


class CapabilityNotFound(CapabilityError):
    """Capability does not exist."""
