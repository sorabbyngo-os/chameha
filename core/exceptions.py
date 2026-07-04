"""
Common exceptions used across Chameha.
"""


class ChamehaError(Exception):
    """Base exception."""


class EngineError(ChamehaError):
    """Generic engine failure."""


class InitializationError(EngineError):
    """Engine initialization failed."""


class ExecutionError(EngineError):
    """Execution failed."""


class ConfigurationError(ChamehaError):
    """Invalid configuration."""


class PermissionError(ChamehaError):
    """Permission denied."""
