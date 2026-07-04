"""
Lifecycle helpers.
"""

from .engine import BaseEngine


def boot(engine: BaseEngine):
    engine.initialize()
    engine.start()


def shutdown(engine: BaseEngine):
    engine.stop()
