"""
Episodic Memory Engine.
"""

from .models import Episode


class EpisodicMemoryEngine:

    def __init__(self):

        self._episodes: list[Episode] = []

    def store(self, episode: Episode):

        self._episodes.append(episode)

    def retrieve(self):

        return self._episodes

    def update(self, index: int, episode: Episode):

        self._episodes[index] = episode

    def delete(self, index: int):

        self._episodes.pop(index)

    def clear(self):

        self._episodes.clear()
