# Dispatcher Engine

The Dispatcher performs execution.

It receives an ExecutionPlan from the Planner and executes every node.

Responsibilities

- sequential execution
- parallel execution
- retries
- rollback
- cancellation
- fallback handling

Execution modes

Sequential

Task A
↓

Task B
↓

Task C

Parallel

Task A

Task B

Task C

↓

Merge Results

Dispatcher owns execution.

Planner owns planning.
