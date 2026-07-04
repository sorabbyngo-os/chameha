"""
Working memory models.
"""

from dataclasses import dataclass
from memory.models import Memory


@dataclass(slots=True)
class WorkingMemory(Memory):

    category: str = "working"

