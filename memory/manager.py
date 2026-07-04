"""
Memory Manager.
"""

from memory.working.engine import WorkingMemoryEngine
from memory.episodic.engine import EpisodicMemoryEngine
from memory.semantic.engine import SemanticMemoryEngine
from memory.procedural.engine import ProceduralMemoryEngine
from memory.autobiographical.engine import AutobiographicalMemoryEngine
from memory.sensory.engine import SensoryMemoryEngine
from memory.retrieval.engine import RetrievalEngine
from memory.consolidation.engine import ConsolidationEngine
from memory.storage.engine import StorageEngine


class MemoryManager:

    """
    Coordinates the complete memory system.
    """

    def __init__(self):

        self.working = WorkingMemoryEngine()

        self.episodic = EpisodicMemoryEngine()

        self.semantic = SemanticMemoryEngine()

        self.procedural = ProceduralMemoryEngine()

        self.autobiographical = AutobiographicalMemoryEngine()

        self.sensory = SensoryMemoryEngine()

        self.retrieval = RetrievalEngine()

        self.consolidation = ConsolidationEngine()

        self.storage = StorageEngine()
