<p align="center">
  <img src="./assets/banner.svg" alt="Chameha" width="900"/>
</p>

<p align="center">
  <strong>Chameha — AI Personality, Interface & AION Execution Engine</strong><br/>
  The User-Facing Intelligence of SORABBYNGO OS
</p>

<p align="center">
  <img src="https://img.shields.io/badge/AI-AION-purple?style=flat-square"/>
  <img src="https://img.shields.io/badge/Voice-English%20%2B%20Swahili-purple?style=flat-square"/>
  <img src="https://img.shields.io/badge/Offline-First-darkviolet?style=flat-square"/>
  <img src="https://img.shields.io/badge/Automation-Hardware%20Aware-purple?style=flat-square"/>
  <img src="https://img.shields.io/badge/CML-Integrated-purple?style=flat-square"/>
</p>

---

# Chameha

**Chameha** is the voice, personality, conversation engine, and execution interface of **SORABBYNGO OS**.

It is the first intelligence users interact with. Every request—spoken, typed, touched, or automated—passes through Chameha.

Chameha understands user intent, manages conversations, plans tasks through **AION**, delegates reasoning to **Byngox**, communicates through **Byngonet**, and safely executes operations on the operating system.

Unlike traditional voice assistants, Chameha is a core operating system component rather than an application.

---

# Core Responsibilities

- Voice interaction
- Text interaction
- Conversation management
- Intent recognition
- Natural language understanding
- Personality and tone adaptation
- Memory integration
- Task planning
- Automation
- Hardware-aware execution
- Remote device control
- Secure capability-based execution

---

# System Architecture

```text
                    User
                      │
      Voice • Text • Touch • CLI
                      │
             Conversation Engine
                      │
               Intent Engine
                      │
                    AION
      Planning • Scheduling • Execution
                      │
      ┌───────────────┼─────────────────┐
      │               │                 │
      ▼               ▼                 ▼
   Byngox        Byngonet             HAL
 Reasoning      Networking      Hardware Layer
      │               │                 │
      └───────────────┼─────────────────┘
                      │
          Capability Broker
                      │
              Linux System APIs
                      │
             Sorabbyngo Kernel
```








---

# AION

AION is the autonomous execution engine integrated into Chameha.

Its responsibilities include:

- Intent planning
- Task decomposition
- Action graph generation
- Scheduling
- Confirmation workflow
- Automation
- Execution monitoring
- Rollback and recovery
- Multi-device orchestration

AION never communicates directly with users.

All user interaction is handled by Chameha.

---

# Execution Pipeline

```text
User
  │
  ▼
Conversation Engine
  │
  ▼
Intent Recognition
  │
  ▼
AION Planner
  │
  ▼
Capability Selection
  │
  ▼
Hardware Profile (HAL)
  │
  ▼
Execution
  │
  ▼
Monitoring
  │
  ▼
Natural Language Response
```

---

# Repository Structure

```text
aion/
├── planner.py
├── executor.py
├── scheduler.py
├── action_graph.py
├── confirmation.py
├── policies.py
└── intents/

brain/
├── context.py
├── dialogue_manager.py
└── intent_engine.py

interfaces/
├── chat_interface.py
└── voice_interface.py

personality/

architecture/

docs/

tests/
```

---

# Hardware-Aware Intelligence

Before executing any task, Chameha requests a hardware profile from the Hardware Abstraction Layer (HAL).

This allows Chameha to:

- Select the appropriate AI model.
- Respect available RAM and storage.
- Detect CPU, GPU, and NPU capabilities.
- Monitor battery level and health.
- Adapt to thermal conditions.
- Optimize performance for desktops and phones.
- Prevent workloads that could degrade device performance.

---

# Remote Device Control

Remote control is orchestrated by AION using capability-based permissions.

Supported operations include:

- Application launching
- File management
- Power management
- Desktop automation
- Mobile automation
- Notification delivery
- Clipboard synchronization
- Screen control
- Workflow execution

Every privileged operation is validated through the Capability Broker before execution.

---

# Features

- Offline-first AI
- Voice-first interaction
- English and Swahili support
- Context-aware conversations
- Hardware-aware execution
- Intelligent task automation
- Cross-device orchestration
- Modular architecture
- Kernel-integrated intelligence
- Secure capability-based execution
- Multi-agent reasoning through Byngox

---

# Quick Start

```bash
# Chat mode
python3 main.py --mode chat

# Voice mode
python3 main.py --mode voice

# Run tests
pytest tests/ -v
```

---

# Development Status

## Completed

- Chameha architecture
- AION architecture
- Conversation engine
- Intent engine
- Execution framework
- Hardware-aware architecture
- Remote control architecture
- Repository organization

## Next

- Planner implementation
- Executor implementation
- Scheduler
- Confirmation engine
- Voice improvements
- Desktop integration
- Mobile integration
- Continuous memory

---

# Sorabbyngo Ecosystem

| Repository | Responsibility |
|------------|----------------|
| **Sorabbyngo Base** | Immutable operating system foundation |
| **Chameha** | User interaction and orchestration |
| **Byngox** | Specialized reasoning engine |
| **Byngonet** | Networking and synchronization |
| **HAL** | Hardware abstraction |
| **CML** | Safety, policy, and alignment |

---

## Design Philosophy

Chameha is designed to make the operating system feel like an intelligent companion rather than a collection of applications.

It serves as the conversational layer of SORABBYNGO OS while AION performs planning and execution, Byngox provides advanced reasoning, Byngonet enables secure communication, HAL exposes hardware capabilities, and CML ensures every action remains safe, secure, and policy-compliant.

---

<p align="center">
  <strong>Sorabbyngo Company</strong><br/>
  <em>The Rhythm of Digital Life</em>
</p>
