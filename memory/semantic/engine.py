"""
Semantic Memory Engine.
"""

from .models import Concept


class SemanticMemoryEngine:

    def __init__(self):

        self._knowledge: list[Concept] = []

    def store(self, concept: Concept):

        self._knowledge.append(concept)

    def retrieve(self):

        return self._knowledge

    def update(self, index: int, concept: Concept):

        self._knowledge[index] = concept

    def delete(self, index: int):

        self._knowledge.pop(index)

    def clear(self):

        self._knowledge.clear()
