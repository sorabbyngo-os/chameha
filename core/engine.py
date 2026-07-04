"""
Base engine implementation for Chameha.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto


class EngineState(Enum):
    """Lifecycle states of an engine."""

    CREATED = auto()
    INITIALIZED = auto()
    RUNNING = auto()
    STOPPED = auto()
    FAILED = auto()


class BaseEngine(ABC):
    """
    Base class for every engine inside Chameha.

    Every subsystem inherits from this class.
    """

    def __init__(self, name: str):
        self.name = name
        self.state = EngineState.CREATED

    def initialize(self) -> None:
        """Prepare engine resources."""
        self.state = EngineState.INITIALIZED

    def start(self) -> None:
        """Start execution."""
        self.state = EngineState.RUNNING

    @abstractmethod
    def execute(self, *args, **kwargs):
        """
        Execute the engine's primary task.
        """
        raise NotImplementedError

    def stop(self) -> None:
        """Gracefully stop execution."""
        self.state = EngineState.STOPPED

    def fail(self) -> None:
        """Transition into failed state."""
        self.state = EngineState.FAILED

    @property
    def running(self) -> bool:
        return self.state == EngineState.RUNNING
