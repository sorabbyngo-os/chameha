# Engine Registry

The Engine Registry is the central directory of every runtime engine inside Chameha.

Instead of importing engines directly, every subsystem discovers engines through the registry.

---

## Purpose

Provide loose coupling.

Support dependency injection.

Enable runtime replacement.

Allow engine discovery.

---

## Architecture

```
Application

↓

Engine Registry

↓

Memory

↓

Cognition

↓

Orchestration

↓

Twin

↓

ACP

↓

Runtime

↓

Voice
```

---

## Responsibilities

Register engines.

Remove engines.

Retrieve engines.

Enumerate engines.

Verify engine existence.

---

The registry becomes the backbone of Chameha's runtime.
