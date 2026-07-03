# Engine Interactions

Every engine owns a single responsibility.

No engine duplicates another.

---

Observation

↓

publishes observations

↓

Memory

↓

publishes memories

↓

Knowledge

↓

publishes facts

↓

Model

↓

publishes state

↓

Context

↓

publishes working context

↓

Prediction

↓

publishes forecasts

↓

Simulation

↓

publishes scenarios

↓

Planning

↓

publishes plans

↓

Decision

↓

publishes recommendations

↓

Permissions

↓

Execution

↓

Observation

---

# Event Driven

Every engine communicates through events.

No engine should directly manipulate another engine's internal state.

---

# Ownership

Observation owns observations.

Memory owns experiences.

Knowledge owns facts.

Model owns state.

Context owns working memory.

Prediction owns forecasts.

Simulation owns scenarios.

Planning owns plans.

Decision owns recommendations.

Execution owns actions.

Evolution owns learning.

Identity owns entities.

Permissions own authority.
