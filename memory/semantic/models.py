"""
Semantic memory models.
"""

from dataclasses import dataclass
from memory.models import Memory


@dataclass(slots=True)
class Concept(Memory):

    category: str = "semantic"

    concept: str = ""
