"""
Base objects used throughout Chameha.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass(slots=True)
class BaseObject:
    """
    Base object inherited by all major entities.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def touch(self) -> None:
        """Update modification timestamp."""
        self.updated_at = datetime.utcnow()
