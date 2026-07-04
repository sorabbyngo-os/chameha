"""
Execution Planner.
"""

from orchestration.models import ExecutionPlan


class Planner:

    """
    Converts objectives into execution plans.
    """

    def create_plan(self, objective: str) -> ExecutionPlan:

        return ExecutionPlan(
            objective=objective,
            tasks=[],
        )
