"""
Procedural memory models.
"""

from dataclasses import dataclass
from memory.models import Memory


@dataclass(slots=True)
class Skill(Memory):

    category: str = "procedural"

    skill: str = ""
