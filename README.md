# Chameha

**The voice of Sorabbyngo OS**

> Not an assistant trapped in a browser tab —  
> the conversational presence of the machine itself.

Chameha is how people *speak with* Sorabbyngo.  
It lives inside **Vanta**, from first setup through daily work and across devices.

It is personality and dialogue.  
It is not the planner, the executor, or the model.

---

## Vision

Most systems bolt speech onto an app.

Chameha is closer to a continuous companion: present at install, present in the desktop, able to continue a conversation when work moves to another machine — without the user managing IPs or SSH.

```text
User speaks or types
        ↓
    Chameha          ← understanding, tone, turn-taking, continuity of dialogue
        ↓ clean intent
    AION             ← planning, backend choice, mediation
        ↓
    ObjectSpace / system
        ↓
    Vanta renders the result
Inspiration: an OS you can talk to.
Discipline: Chameha never becomes a second system runtime.
What Chameha is
Is
Is not
Voice in / voice out
The model that “thinks” for the OS
Personality and conversational style
AION (planning & tool execution)
Intent capture and dialogue state
ObjectSpace (world model)
Guide for setup and navigation
A standalone product outside Vanta
Client of AION
Owner of filesystem or kernel control
Chameha makes the system feel approachable.
AION makes the system act safely.
Architecture
┌─────────────────────────────────────────────┐
│  VANTA                                      │
│  ┌───────────────────────────────────────┐  │
│  │  Chameha                              │  │
│  │  · capture (mic / text)               │  │
│  │  · STT / TTS (local-first where possible)│
│  │  · dialogue manager                   │  │
│  │  · personality / tone                 │  │
│  │  · session continuity (with memory svc)│ │
│  └───────────────────┬───────────────────┘  │
│                      │ intent + metadata      │
│                      ▼                        │
│                 vanta-intent → AION           │
└─────────────────────────────────────────────┘
Concern
Owner
Microphone, playback, barge-in
Chameha + PipeWire stack
Speech-to-text / text-to-speech
Chameha (pluggable engines)
“What did the user mean?” at dialogue level
Chameha
“What should the system do?”
AION
Long-term project memory
Context/Memory service (queried via AION)
Cross-device conversation handoff
Chameha + Byngonet + AION
Design principles
Present from the beginning — usable during installation and first-boot, not only after a full desktop session.
Personality without power — warmth and continuity; no bypass of AION mediation.
Local-first speech — basic listen/respond paths work offline; cloud STT/TTS optional.
Same companion across devices — identity and dialogue can continue via Byngonet when the user opts in.
Clear boundaries — Chameha does not absorb planning, package management, or init-system duties.
Graceful degradation — if voice fails, text remains; if AION is limited, Chameha still explains and guides within safe bounds.
Technical direction
Area
Approach
Language
Prefer Rust for integration with Vanta; Python acceptable for speech experiments early
Audio
PipeWire
STT / TTS
Pluggable (e.g. Whisper-class local, system TTS, optional cloud)
IPC
Same intent contracts as vanta-intent / AION
Config
User-visible in Vanta settings; no mandatory config files
Older prototypes embedded planning inside Chameha and treated multi-agent swarms as the core.
That path is superseded. Planning and tools belong to AION; Chameha is the face and voice.
Status
Pre-alpha / realignment.
Historical research: conversation, personality, bilingual experiments
Current mandate: voice + personality + dialogue only, inside Vanta
Implementation priority tracks Vanta Phase 5+ (intent path), with lighter stubs earlier
Related
Project
Relationship
vanta
Home of Chameha
aion
Receives intent; returns speakable results
byngonet
Multi-device continuity
sorabbyngo-os
OS umbrella
License
To be decided. All rights reserved until a license is published.
Sorabbyngo · The Rhythm of Digital Life
