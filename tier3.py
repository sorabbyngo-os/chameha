"""
tier3.py — Chameha Tier 3 external intelligence
Claude API — opt-in only, explicit /cloud command + confirmation
ADR-009: no automatic calls, sanitized data only
"""
import os
import re
import json
import urllib.request
import urllib.error

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL   = "claude-sonnet-4-5"

SYSTEM_PROMPT = (
    "You are Chameha, the AI soul of Sorabbyngo OS — "
    "an Africa-first, AI-native, health-focused operating system. "
    "The user has explicitly requested external intelligence. "
    "Be thorough, intelligent, and direct."
)

# Patterns that must never leave the device
SENSITIVE_PATTERNS = [
    (r'[0-9a-f]{32,}', '[REDACTED_HASH]'),
    (r'/proc/sorabbyngo/\S+', '[REDACTED_PATH]'),
    (r'/home/\S+', '[REDACTED_PATH]'),
    (r'/opt/sorabbyngo/\S+', '[REDACTED_PATH]'),
    (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[REDACTED_IP]'),
    (r'Linux \S+ \S+', '[REDACTED_KERNEL]'),
]

class Tier3:
    def __init__(self):
        self.available = bool(API_KEY)

    def respond(self, user_input: str) -> str | None:
        if not self.available:
            return "[Tier 3 unavailable — set ANTHROPIC_API_KEY to enable]"

        sanitized = self._sanitize(user_input)

        # ADR-009 — show sanitized query, require explicit confirmation
        print(f"\n  Sanitized query: {sanitized}")
        confirm = input("  Send to Claude API? (yes/no): ").strip().lower()
        if confirm != "yes":
            return "[Cancelled — staying offline]"

        # Fresh messages per call — no session leakage
        messages = [{"role": "user", "content": sanitized}]

        try:
            body = json.dumps({
                "model": MODEL,
                "max_tokens": 1000,
                "system": SYSTEM_PROMPT,
                "messages": messages
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
                return result["content"][0]["text"]

        except urllib.error.HTTPError as e:
            return f"[Tier 3 HTTP error: {e.code}]"
        except urllib.error.URLError:
            return "[Tier 3 unavailable — no network]"
        except Exception as e:
            return f"[Tier 3 error: {str(e)}]"

    def _sanitize(self, text: str) -> str:
        for pattern, replacement in SENSITIVE_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text.strip()
