"""
Core event model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from .types import Payload, Metadata


@dataclass(slots=True)
class Event:
    """
    Base event shared by every subsystem.
    """

    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = ""
    source: str = ""
    payload: Payload = field(default_factory=dict)
    metadata: Metadata = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
