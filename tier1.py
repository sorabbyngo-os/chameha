"""
tier1.py — Chameha Tier 1 local intelligence
Phi-3 Mini 3.8B INT4 via llama.cpp
Always-on, offline, no network required
"""
import subprocess
import os

LLAMA_CLI    = os.environ.get("LLAMA_CLI", os.path.expanduser("~/llama.cpp/build/bin/llama-completion"))
MODEL_PATH   = os.environ.get("PHI3_MODEL", os.path.expanduser("~/models/phi3-mini-q4.gguf"))
MAX_TOKENS   = 150
TEMPERATURE  = 0.7
TIMEOUT_SECS = 30

SYSTEM_PROMPT = (
    "You are Chameha, the AI soul of Sorabbyngo OS — "
    "an Africa-first, AI-native, health-focused operating system built in Kisii, Kenya. "
    "You are warm, intelligent, and direct. Never robotic. "
    "You are aware of: Sentinel (security), Byngox (health agents), "
    "Byngonet (mesh network), Novela (health platform). "
    "Keep responses 1-3 sentences unless more is needed. "
    "You speak as the OS itself."
)

COMPLEX_TRIGGERS = [
    "explain", "analyze", "analyse", "why", "how does", "deep",
    "compare", "difference", "recommend", "should i"
]

class Tier1:
    def __init__(self):
        self.available = self._check()

    def _check(self) -> bool:
        cli_ok = os.path.exists(LLAMA_CLI)
        model_ok = os.path.exists(MODEL_PATH)
        if not cli_ok:
            print(f"  [Tier1] llama-completion not found at {LLAMA_CLI}")
        if not model_ok:
            print(f"  [Tier1] Model not found at {MODEL_PATH}")
        return cli_ok and model_ok

    def respond(self, user_input: str, context: str = "") -> str | None:
        if not self.available:
            return None
        prompt = self._build_prompt(user_input, context)
        try:
            result = subprocess.run(
                [
                    LLAMA_CLI,
                    "-m", MODEL_PATH,
                    "-p", prompt,
                    "-n", str(MAX_TOKENS),
                    "--temp", str(TEMPERATURE),
                    "-t", "4",
                    "--log-disable",
                ],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECS
            )
            output = result.stdout.strip()
            return self._clean(output) if output else None
        except subprocess.TimeoutExpired:
            return "[Chameha] Processing took too long. Try a shorter query."
        except FileNotFoundError:
            self.available = False
            return None

    def _build_prompt(self, user_input: str, context: str = "") -> str:
        parts = [f"<|system|>\n{SYSTEM_PROMPT}"]
        if context:
            parts.append(f"System context: {context}")
        parts.append(f"<|end|>\n<|user|>\n{user_input}<|end|>\n<|assistant|>")
        return "\n".join(parts)

    def _clean(self, text: str) -> str:
        for tag in ["<|end|>", "<|user|>", "<|assistant|>", "<|system|>"]:
            text = text.split(tag)[0]
        return text.strip()

    def is_complex(self, user_input: str) -> bool:
        """Heuristic — should we suggest Tier 3 for deeper analysis"""
        lower = user_input.lower()
        word_count = len(user_input.split())
        return (
            word_count > 12 or
            any(trigger in lower for trigger in COMPLEX_TRIGGERS)
        )
