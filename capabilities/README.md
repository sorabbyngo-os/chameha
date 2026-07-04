# Capability Registry

The Capability Registry is the abstraction layer between orchestration and implementation.

The Orchestration Kernel never executes plugins directly.

Instead it requests capabilities.

The Capability Registry determines which implementation satisfies each capability.

---

## Philosophy

Orchestration should reason about **what** must be done.

Implementations decide **how** it is done.

---

## Architecture

```
Objective

↓

Planner

↓

Capability Resolver

↓

Capability Registry

↓

Plugin

↓

Execution
```

---

## Responsibilities

The Capability Registry

- registers capabilities
- resolves implementations
- supports multiple providers
- enables runtime replacement
- isolates orchestration from implementations

---

## Examples

Capability

```
search_memory
```

↓

Implementation

```
SemanticMemoryPlugin
```

---

Capability

```
medical_reasoning
```

↓

Implementation

```
HealthAgent
```

---

Capability

```
simulation
```

↓

Implementation

```
TwinSimulationEngine
```

---

## Design Principles

Capabilities are

- abstract
- stable
- provider-independent
- discoverable
- extensible
