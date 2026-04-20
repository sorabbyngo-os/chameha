# Chat Interface
# Handles text-based interaction for chameha_service HTTP API layer
# NOTE: This is the HTTP API layer only. Boot path uses main.py + tier1.py

import os
import json
import urllib.request
import urllib.error
import logging

log = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are Chameha, the AI personality of SORABBYNGO OS.
You are warm, intelligent, and helpful. You speak English and Swahili.
You assist with health questions, medication verification, and general OS tasks.
You never diagnose — you guide, support, and connect users to the right care.
You always say: Welcome, [name]. This is Sorabbyngo."""


class ChatInterface:
    def __init__(self):
        self.available = bool(API_KEY)

    async def handle(self, message: str) -> str:
        if not self.available:
            return "I am here. External intelligence unavailable — no API key set."
        try:
            body = json.dumps({
                "model": MODEL,
                "max_tokens": 1024,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": message}]
            }).encode()

            req = urllib.request.Request(
                data=body,
                headers={
                    "Content-Type": "application/json",
                }
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                result = json.loads(r.read())
                return result["content"][0]["text"]

        except urllib.error.URLError:
            return "I am here. Network unavailable."
        except Exception as e:
            log.error(f"Chameha chat failed: {e}")
            return "I am here. Please try again."
