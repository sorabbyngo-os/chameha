# Plugin System

The Plugin System provides Chameha with extensible capabilities.

Every capability is implemented as a plugin.

Plugins may represent

- tools
- reasoning engines
- runtime providers
- ACP agents
- external APIs
- operating system functions

---

## Philosophy

Everything is a capability.

Capabilities are plugins.

The orchestration kernel decides which plugin should execute.

---

## Architecture

```
User

↓

Intent

↓

Planner

↓

Plugin Manager

↓

Plugin

↓

Execution
```

---

## Responsibilities

The Plugin System

- discovers plugins
- loads plugins
- validates plugins
- executes plugins
- manages lifecycle
- exposes capabilities

---

## Examples

Memory Plugin

Twin Plugin

Reasoning Plugin

Shell Plugin

Browser Plugin

Git Plugin

Runtime Plugin

ACP Plugin

Novela Plugin

---

## Design Principles

Plugins are

- isolated
- discoverable
- replaceable
- secure
- reusable
