# Chat Interface
# Handles text-based interaction for chameha_service HTTP API layer
# Routes to Byngox Prime (self-hosted vLLM) — no external API dependencies
# NOTE: This is the HTTP API layer only. Boot path uses main.py + tier1.py

import os
import json
import urllib.request
import urllib.error
import logging

log = logging.getLogger(__name__)

# Byngox Prime — self-hosted vLLM cluster (OpenAI-compatible)
# Internal network only. No data leaves Sorabbyngo infrastructure.
BYNGOX_PRIME_URL = os.getenv(
    "BYNGOX_PRIME_URL",
    "http://byngox-prime.internal:8000/v1/chat/completions"
)
MODEL = os.getenv("BYNGOX_PRIME_MODEL", "deepseek-r1:70b")

SYSTEM_PROMPT = """You are Chameha, the AI personality of SORABBYNGO OS.
You are warm, intelligent, and helpful. You speak English and Swahili.
You assist with health questions, medication verification, and general OS tasks.
You never diagnose — you guide, support, and connect users to the right care.
You always say: Welcome, [name]. This is Sorabbyngo."""


class ChatInterface:
    def __init__(self):
        self.prime_url = BYNGOX_PRIME_URL

    async def handle(self, message: str) -> str:
        try:
            body = json.dumps({
                "model":      MODEL,
                "max_tokens": 1024,
                "messages": [
                    {"role": "system",  "content": SYSTEM_PROMPT},
                    {"role": "user",    "content": message}
                ]
            }).encode()

            req = urllib.request.Request(
                self.prime_url,
                data=body,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                result = json.loads(r.read())
                return result["choices"][0]["message"]["content"]

        except urllib.error.URLError:
            # Byngox Prime unreachable — fall back to tier1 response
            return "I am here. Deep intelligence temporarily unavailable — running on local model."
        except Exception as e:
            log.error("Chameha chat failed: %s", e)
            return "I am here. Please try again."
