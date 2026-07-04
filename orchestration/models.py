"""
Shared orchestration models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class Task:

    id: str = field(default_factory=lambda: str(uuid4()))

    name: str = ""

    capability: str = ""

    parameters: dict[str, Any] = field(default_factory=dict)

    status: TaskStatus = TaskStatus.PENDING


@dataclass(slots=True)
class ExecutionPlan:

    id: str = field(default_factory=lambda: str(uuid4()))

    objective: str = ""

    tasks: list[Task] = field(default_factory=list)
