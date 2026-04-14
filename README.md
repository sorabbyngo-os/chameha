# Chameha

> **AI Personality and Interface Engine** — Sorabbyngo Labs

The face of SORABBYNGO OS. Voice-first from boot. Warm, intelligent, bilingual
English/Swahili. Inspired by the vision of AI as a calm, present companion.

> Welcome, Charles. This is Sorabbyngo.

---

## Intelligence Architecture

Chameha uses a tiered model stack — all inference is self-hosted or on-device.
**No external API dependencies.**

| Tier | Model | Runtime | Condition |
|---|---|---|---|
| Tier 1 | Phi-4 Mini | Ollama | Always-on, 1GB RAM |
| Tier 1 | SmolLM2 360M | Ollama | Device control tasks |
| Tier 1–2 | Aya 23 | Ollama | African language routing (Swahili, Hausa, Yoruba, Amharic) |
| Tier 2 | Phi-4 INT8 / Gemma 3 4B | Ollama | GPU/NPU devices, 3–4GB RAM |
| Tier 4 | DeepSeek-R1 70B | Byngox Prime vLLM | Self-hosted cluster, opt-in only |

**Tier 4 = Byngox Prime** — a privately operated H100/A100 inference cluster.
It is not a third-party API. Patient data never leaves Sorabbyngo infrastructure.

---

## Components

| Component | Technology | Status |
|---|---|---|
| UI Framework | Flutter cross-platform | In development |
| Speech-to-Text | Whisper.cpp on-device | In development |
| Text-to-Speech | Coqui TTS | In development |
| Dialogue Manager | ACP protocol over NATS | In development |
| Edge model | Phi-4 Mini (replaces Phi-3) | Planned Phase 4 |
| African language NLP | Aya 23 (Cohere, open weights) | Planned Phase 4 |
| Boot experience | Wayland compositor | In development |
| Languages | English + Swahili + 13 African languages | Designed |

---

## Tier Routing

```python
# config: /etc/sorabbyngo/chameha.yaml
chameha:
  edge_model:           "phi4-mini"       # Always-on Tier 1
  device_control_model: "smollm2:360m"    # Device control, JSON commands
  dialogue_model:       "phi4-mini"       # Tier 1 conversation
  language_model:       "aya23:8b"        # African language routing

  language_routing:
    swahili:  "aya23:8b"
    hausa:    "aya23:8b"
    yoruba:   "aya23:8b"
    amharic:  "aya23:8b"
    igbo:     "aya23:8b"
    default:  "phi4-mini"

  # Tier 4 — Byngox Prime (self-hosted, opt-in only)
  byngox_prime_url:   "http://byngox-prime.internal:8000/v1/chat/completions"
  byngox_prime_model: "deepseek-r1:70b"
```

---

## Boot Target

< 10 seconds from power-on to "Welcome" on Tier 2 hardware.

---

**Sorabbyngo Company** — Kisii, Kenya | 2026
