# Chameha Core

The Core package provides the shared infrastructure used by every engine inside Chameha.

No cognitive subsystem should reimplement lifecycle management, events, exceptions or engine registration.

Instead every subsystem inherits from Core.

---

## Responsibilities

Core provides

- base engine classes
- common data models
- event definitions
- lifecycle management
- engine registry
- shared exceptions
- common type definitions

---

## Architecture

```
Core

├── BaseObject
├── BaseEngine
├── Events
├── Registry
├── Lifecycle
├── Exceptions
└── Types
```

---

## Purpose

Core guarantees that every engine behaves consistently regardless of whether it belongs to

- Cognition
- Memory
- Digital Twin
- Runtime
- Plugins
- Orchestration

---

## Design Principles

Core is

- lightweight
- dependency-free
- deterministic
- reusable
- extensible

Every engine builds upon this package.
