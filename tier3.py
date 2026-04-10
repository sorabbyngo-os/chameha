"""
tier3.py — Chameha Tier 3 external intelligence
Claude API — opt-in only, explicit /cloud command
Data is sanitized before sending — no NodeID, no raw telemetry
"""

import os
import re
import json
import urllib.request

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = (
    "You are Chameha, the AI soul of Sorabbyngo OS — "
    "an Africa-first, AI-native, health-focused operating system. "
    "The user has explicitly requested external intelligence. "
    "Be thorough, intelligent, and direct."
)

class Tier3:
    def __init__(self):
        self.available = bool(API_KEY)
        self._messages = []

    def respond(self, user_input: str) -> str | None:
        if not self.available:
            return "[Tier 3 unavailable — no API key set]"
        sanitized = self._sanitize(user_input)
        self._messages.append({"role": "user", "content": sanitized})
        try:
            body = json.dumps({
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "system": SYSTEM_PROMPT,
                "messages": self._messages
            }).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": API_KEY,
                    "anthropic-version": "2023-06-01"
                }
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                result = json.loads(r.read())
                response = result["content"][0]["text"]
                self._messages.append({"role": "assistant", "content": response})
                return response
        except Exception as e:
            return f"[Tier 3 error: {str(e)}]"

    def _sanitize(self, text: str) -> str:
        text = re.sub(r'[0-9a-f]{40,}', '[REDACTED]', text)
        return text

    def clear(self):
        self._messages = []
