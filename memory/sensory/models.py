"""
Sensory memory models.
"""

from dataclasses import dataclass
from memory.models import Memory


@dataclass(slots=True)
class SensoryInput(Memory):

    category = "sensory"

    modality: str = ""
