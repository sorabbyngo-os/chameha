"""
Episodic memory models.
"""

from dataclasses import dataclass
from memory.models import Memory


@dataclass(slots=True)
class Episode(Memory):

    category: str = "episodic"

    sequence: int = 0
