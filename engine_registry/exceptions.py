"""
Registry exceptions.
"""


class RegistryError(Exception):
    ...


class EngineAlreadyRegistered(RegistryError):
    ...


class EngineNotFound(RegistryError):
    ...

