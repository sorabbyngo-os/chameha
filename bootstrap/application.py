"""
Main Chameha application.
"""

from bootstrap.container import Container

from orchestration.pipeline.engine import Pipeline


class Chameha:

    """
    Main application object.
    """

    def __init__(self):

        self.container = Container()
        self.memory = self.container.memory
        self.pipeline = Pipeline()

    def start(self):

        print("Starting Chameha...")

    def execute(self, objective: str):

        return self.pipeline.execute(objective)
