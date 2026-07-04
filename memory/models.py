"""
Shared memory models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class Memory:

    id: str = field(default_factory=lambda: str(uuid4()))

    category: str = ""

    content: Any = None

    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)

    importance: float = 0.5
