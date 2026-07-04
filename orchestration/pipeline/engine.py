"""
Execution Pipeline.
"""

from orchestration.planner.engine import Planner
from orchestration.scheduler.engine import Scheduler
from orchestration.dispatcher.engine import Dispatcher
from orchestration.coordinator.engine import Coordinator


class Pipeline:

    def __init__(self):

        self.planner = Planner()

        self.scheduler = Scheduler()

        self.dispatcher = Dispatcher()

        self.coordinator = Coordinator()

    def execute(self, objective: str):

        plan = self.planner.create_plan(objective)

        tasks = self.scheduler.schedule(plan.tasks)

        results = []

        for task in tasks:

            results.append(
                self.dispatcher.dispatch(task)
            )

        return self.coordinator.collect(results)
