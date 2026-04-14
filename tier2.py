"""
Chameha — Tier 2 Intelligence
Sorabbyngo AI-OS | sorabbyngo-Labs/chameha

GPU/NPU-accelerated local inference via Ollama.
Activates automatically when GPU is detected.
Falls back to Tier 1 if unavailable.

Models:
  phi4:14b-q8        — Primary Tier 2 conversation (Phi-4 full, INT8)
  gemma3:4b          — Lightweight GPU conversation fallback
  qwen2.5:7b         — Multilingual reasoning
  aya23:35b          — Full African language model (GPU required)
"""

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Optional

log = logging.getLogger(__name__)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
TIMEOUT    = int(os.environ.get("TIER2_TIMEOUT", "120"))

# Tier 2 model roster
MODELS = {
    "primary":      os.environ.get("TIER2_PRIMARY_MODEL",   "phi4:14b-q8"),
    "multilingual": os.environ.get("TIER2_LANG_MODEL",      "qwen2.5:7b"),
    "fallback":     os.environ.get("TIER2_FALLBACK_MODEL",  "gemma3:4b"),
    "language":     os.environ.get("TIER2_AFRICAN_MODEL",   "aya23:35b"),
}

# Minimum VRAM (GB) required to run Tier 2
MIN_VRAM_GB = float(os.environ.get("TIER2_MIN_VRAM_GB", "3.0"))

CHAMEHA_SYSTEM = (
    "You are Chameha, the AI personality of SORABBYNGO OS. "
    "Warm, intelligent, deeply knowledgeable. You speak English and Swahili fluently. "
    "You assist with health guidance, medication questions, clinical support, and OS tasks. "
    "You never diagnose — you guide, support, and connect users to care. "
    "Responses at Tier 2 should be more detailed and thorough than Tier 1."
)


def _ollama_generate(model: str, prompt: str, system: Optional[str] = None,
                     max_tokens: int = 1024) -> str:
    payload = {
        "model":  model,
        "prompt": f"{system}\n\n{prompt}" if system else prompt,
        "stream": False,
        "options": {
            "temperature":  0.5,
            "top_p":        0.95,
            "num_predict":  max_tokens,
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
        raise RuntimeError(f"Tier 2 inference failed: {e}") from e


def _check_gpu() -> bool:
    """
    Check if GPU is available via nvidia-smi or ollama ps.
    Returns True if GPU with sufficient VRAM is present.
    """
    import subprocess
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            vram_mb = float(result.stdout.strip().split("\n")[0])
            vram_gb = vram_mb / 1024
            log.info("[Tier2] GPU detected: %.1f GB VRAM", vram_gb)
            return vram_gb >= MIN_VRAM_GB
    except Exception:
        pass
    return False


def _get_available_models() -> set:
    """Return set of model base names available in Ollama."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as r:
            tags = json.loads(r.read())
            return {m["name"] for m in tags.get("models", [])}
    except Exception:
        return set()


class Tier2:
    """
    Tier 2 inference handler.
    GPU/NPU accelerated. Falls back to Tier 1 on failure.
    """

    def __init__(self):
        self.gpu_available      = _check_gpu()
        self.available_models   = _get_available_models()
        self.available          = self.gpu_available and bool(self.available_models)

        if self.available:
            log.info("[Tier2] Online · GPU=True · models=%s", self.available_models)
        else:
            log.info("[Tier2] Offline · GPU=%s", self.gpu_available)

    def _best_model(self, preferred: str) -> str:
        """Return preferred model if available, else fallback."""
        if preferred in self.available_models:
            return preferred
        fallback = MODELS["fallback"]
        if fallback in self.available_models:
            log.warning("[Tier2] %s not available, using fallback %s", preferred, fallback)
            return fallback
        # Return any available model
        if self.available_models:
            return next(iter(self.available_models))
        return preferred

    def chat(self, user_input: str, language: str = "en") -> str:
        """
        Tier 2 conversation.
        Uses Aya 23 35B for African languages, Phi-4 14B for English.
        """
        if not self.available:
            raise RuntimeError("Tier 2 unavailable")

        if language in ("sw", "ha", "yo", "am", "ig"):
            model = self._best_model(MODELS["language"])
        else:
            model = self._best_model(MODELS["primary"])

        log.info("[Tier2] chat · lang=%s model=%s", language, model)
        return _ollama_generate(model, user_input, CHAMEHA_SYSTEM, max_tokens=1024)

    def reason(self, prompt: str) -> str:
        """
        Deep reasoning task — Qwen 2.5 7B multilingual.
        Used for complex health queries requiring structured thinking.
        """
        if not self.available:
            raise RuntimeError("Tier 2 unavailable")

        model = self._best_model(MODELS["multilingual"])
        system = (
            "You are a reasoning engine for Sorabbyngo OS. "
            "Think step by step. Be precise. Flag uncertainty clearly. "
            "For health topics: never diagnose, always recommend professional consultation."
        )
        log.info("[Tier2] reason · model=%s", model)
        return _ollama_generate(model, prompt, system, max_tokens=2048)

    def status(self) -> str:
        if not self.gpu_available:
            return "Tier 2 offline — no GPU detected"
        if not self.available:
            return "Tier 2 offline — no models available"
        return f"Tier 2 online · GPU=True · models: {', '.join(self.available_models)}"


# Module-level singleton
_tier2 = None

def get_tier2() -> Tier2:
    global _tier2
    if _tier2 is None:
        _tier2 = Tier2()
    return _tier2
