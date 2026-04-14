"""
Chameha — Tier 1 Intelligence
Sorabbyngo AI-OS | sorabbyngo-Labs/chameha

Always-on, offline-first. Runs on 2GB RAM edge devices.
No binary launching. Pure Ollama HTTP API.

Models:
  phi4-mini          — Primary conversation and reasoning
  smollm2:360m       — Device control commands (JSON output)
  aya23:8b           — African language routing (sw/ha/yo/am/ig)
"""

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Optional

log = logging.getLogger(__name__)

OLLAMA_URL   = os.environ.get("OLLAMA_URL", "http://localhost:11434")
TIMEOUT      = int(os.environ.get("TIER1_TIMEOUT", "30"))

# Tier 1 model roster
MODELS = {
    "conversation":     os.environ.get("TIER1_CHAT_MODEL",   "phi4-mini"),
    "device_control":   os.environ.get("TIER1_DEVICE_MODEL", "smollm2:360m"),
    "language_routing": os.environ.get("TIER1_LANG_MODEL",   "aya23:8b"),
}

# Language → model routing
LANGUAGE_MODELS = {
    "sw": MODELS["language_routing"],   # Swahili
    "ha": MODELS["language_routing"],   # Hausa
    "yo": MODELS["language_routing"],   # Yoruba
    "am": MODELS["language_routing"],   # Amharic
    "ig": MODELS["language_routing"],   # Igbo
}

CHAMEHA_SYSTEM = (
    "You are Chameha, the AI personality of SORABBYNGO OS. "
    "Warm, intelligent, offline-first. You speak English and Swahili fluently. "
    "You assist with health guidance, medication questions, and OS tasks. "
    "You never diagnose — you guide, support, and connect users to care. "
    "Always greet new sessions: 'Welcome. This is Sorabbyngo.'"
)


def _ollama_generate(model: str, prompt: str, system: Optional[str] = None) -> str:
    """
    Call Ollama /api/generate endpoint.
    Returns response text or raises RuntimeError on failure.
    """
    payload = {
        "model":  model,
        "prompt": f"{system}\n\n{prompt}" if system else prompt,
        "stream": False,
        "options": {
            "temperature":  0.7,
            "top_p":        0.9,
            "num_predict":  512,
        },
    }
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            result = json.loads(r.read())
            return result.get("response", "").strip()
    except urllib.error.URLError as e:
        raise RuntimeError(f"Ollama unreachable: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Tier 1 inference failed: {e}") from e


def _detect_language(text: str) -> str:
    """
    Simple heuristic language detection.
    Returns ISO 639-1 code. Defaults to 'en'.
    """
    swahili_markers  = ["habari", "karibu", "asante", "ndiyo", "hapana", "dawa", "mgonjwa"]
    hausa_markers    = ["yauwa", "lafiya", "magani", "asuba"]
    yoruba_markers   = ["bawo", "ẹ jọ", "egbogi"]

    text_lower = text.lower()
    if any(m in text_lower for m in swahili_markers):
        return "sw"
    if any(m in text_lower for m in hausa_markers):
        return "ha"
    if any(m in text_lower for m in yoruba_markers):
        return "yo"
    return "en"


class Tier1:
    """
    Tier 1 inference handler.
    Always available. No internet. No GPU required.
    """

    def __init__(self):
        self.available = self._check_ollama()
        if not self.available:
            log.warning("[Tier1] Ollama not reachable at %s — running in fallback mode", OLLAMA_URL)

    def _check_ollama(self) -> bool:
        try:
            req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=3) as r:
                tags = json.loads(r.read())
                available = {m["name"].split(":")[0] for m in tags.get("models", [])}
                log.info("[Tier1] Ollama online. Models available: %s", available)
                return True
        except Exception:
            return False

    def chat(self, user_input: str) -> str:
        """Primary conversation — Phi-4 Mini or Aya 23 based on language."""
        if not self.available:
            return "Welcome. This is Sorabbyngo. Local intelligence warming up — please wait a moment."

        lang  = _detect_language(user_input)
        model = LANGUAGE_MODELS.get(lang, MODELS["conversation"])

        log.info("[Tier1] chat · lang=%s model=%s", lang, model)
        try:
            return _ollama_generate(model, user_input, CHAMEHA_SYSTEM)
        except RuntimeError as e:
            log.error("[Tier1] chat failed: %s", e)
            return "I am here. Local model is initializing — please try again in a moment."

    def device_command(self, instruction: str) -> dict:
        """
        Device control — SmolLM2 360M.
        Returns structured JSON command for OS execution layer.
        """
        if not self.available:
            return {"error": "local model unavailable", "command": None}

        system = (
            "You are a device control agent for Sorabbyngo OS. "
            "Respond ONLY with valid JSON. No prose. No explanation. "
            "Format: {\"action\": \"<action>\", \"target\": \"<device>\", \"params\": {}}"
        )
        log.info("[Tier1] device_command · model=%s", MODELS["device_control"])
        try:
            raw = _ollama_generate(MODELS["device_control"], instruction, system)
            # Strip any accidental markdown fences
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)
        except (RuntimeError, json.JSONDecodeError) as e:
            log.error("[Tier1] device_command failed: %s", e)
            return {"error": str(e), "command": None}

    def status(self) -> str:
        if not self.available:
            return "Tier 1 offline — Ollama not reachable"
        return f"Tier 1 online · models: {', '.join(MODELS.values())}"


# Module-level singleton
_tier1 = None

def get_tier1() -> Tier1:
    global _tier1
    if _tier1 is None:
        _tier1 = Tier1()
    return _tier1
