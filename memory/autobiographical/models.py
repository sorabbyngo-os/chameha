"""
Autobiographical memory models.
"""

from dataclasses import dataclass
from memory.models import Memory


@dataclass(slots=True)
class LifeEvent(Memory):

    category = "autobiographical"

    title: str = ""

    summary: str = ""
