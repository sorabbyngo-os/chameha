# Coordinator Engine

The Coordinator supervises every engine participating in execution.

It synchronizes:

- Cognition
- Memory
- Twin
- ACP Swarm
- Runtime
- External Tools
- Device Layer

Responsibilities

- lifecycle management
- synchronization
- cancellation
- retries
- timeout handling
- state consistency

The Coordinator is the conductor of the orchestration layer.

It never performs reasoning itself.

It only coordinates engines.
