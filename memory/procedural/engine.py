"""
Procedural Memory Engine.
"""

from .models import Skill


class ProceduralMemoryEngine:

    def __init__(self):

        self._skills: list[Skill] = []

    def store(self, skill: Skill):

        self._skills.append(skill)

    def retrieve(self):

        return self._skills

    def update(self, index: int, skill: Skill):

        self._skills[index] = skill

    def delete(self, index: int):

        self._skills.pop(index)

    def clear(self):

        self._skills.clear()
