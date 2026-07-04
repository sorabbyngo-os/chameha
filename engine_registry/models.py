"""
Engine Registry models.
"""

from dataclasses import dataclass


@dataclass(slots=True)
class Engine:

    name: str

    instance: object

    description: str = ""

