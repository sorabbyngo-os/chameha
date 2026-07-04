# Planner Engine

The Planner is the first execution stage of Chameha's Orchestration Kernel.

Its responsibility is to transform an intention into an executable plan.

The planner never executes anything.

It answers:

- What is the user trying to achieve?
- Which engines are required?
- What dependencies exist?
- Which steps can execute in parallel?
- Which permissions are required?
- Which ACP agents are needed?

Example

User
    │
    ▼
"I want to book a hospital appointment next week."

↓

Intent

↓

Execution Plan

1. Retrieve calendar
2. Retrieve hospital schedule
3. Compare availability
4. Select recommendation
5. Ask for confirmation
6. Execute booking

Output:
ExecutionGraph
ExecutionPlan
ExecutionContext

Planner only plans.

Dispatcher executes.
