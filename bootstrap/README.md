# Bootstrap

The Bootstrap package assembles Chameha.

Every subsystem is initialized here.

---

## Responsibilities

Bootstrap

- initializes Core
- creates Event Bus
- loads Plugin Manager
- creates Capability Registry
- starts Orchestration
- registers engines
- starts Chameha

---

## Startup

```
Configuration

↓

Core

↓

Capabilities

↓

Plugins

↓

Orchestration

↓

Engines

↓

Ready
```

Bootstrap guarantees that every subsystem starts in the correct order.
