"""
Memory exceptions.
"""


class MemoryError(Exception):
    """Base memory exception."""


class MemoryNotFound(MemoryError):
    """Requested memory does not exist."""


class StorageError(MemoryError):
    """Storage backend failure."""
