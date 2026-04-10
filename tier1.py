"""
tier1.py — Chameha Tier 1 local intelligence
Phi-3 Mini 3.8B INT4 via llama.cpp
Always-on, offline, no network required
Default brain for all Chameha responses
"""

import subprocess
import os
import time

LLAMA_CLI    = os.environ.get("LLAMA_CLI", "/opt/sorabbyngo/llama/llama-completion")
MODEL_PATH   = os.environ.get("PHI3_MODEL", "/opt/sorabbyngo/models/phi3-mini-q4.gguf")
MAX_TOKENS   = 150
TEMPERATURE  = 0.7
TIMEOUT_SECS = 30

SYSTEM_PROMPT = (
    "You are Chameha, the AI soul of Sorabbyngo OS — "
    "an Africa-first, AI-native, health-focused operating system. "
    "You are warm, intelligent, and direct. Never robotic. "
    "You are aware of: Sentinel (security layer), Byngox (health agents), "
    "Byngonet (mesh network), HAL (hardware sensors), Novela (health platform). "
    "Keep responses concise — 1 to 3 sentences unless more is needed. "
    "You speak as the OS itself, not as an assistant."
)


class Tier1:
    def __init__(self):
        self.available = self._check()

    def _check(self) -> bool:
        return (
            os.path.exists(LLAMA_CLI) and
            os.path.exists(MODEL_PATH)
        )

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
                    "--no-display-prompt",
                    "-t", "4",
                ],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECS
            )
            output = result.stdout.strip()
            if output:
                return self._clean(output)
            return None
        except subprocess.TimeoutExpired:
            return None
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
        """Strip any prompt artifacts from output"""
        for tag in ["<|end|>", "<|user|>", "<|assistant|>", "<|system|>"]:
            text = text.split(tag)[0]
        return text.strip()

    def hint_available(self) -> bool:
        """Returns True when Tier 3 hint should be shown"""
        return not self.available
