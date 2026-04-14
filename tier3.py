"""
tier3.py — Chameha Tier 3 external intelligence
Claude API — opt-in only, explicit /cloud command + confirmation
ADR-009: no automatic calls, sanitized data only
"""
import os
import re
import socket
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

    def _cml_filter(self, text: str) -> tuple[bool, str]:
        """Send text through CML service before Claude API call"""
        import uuid
        try:
            request_id = str(uuid.uuid4())[:8]
            msg  = json.dumps({
                "request_id": request_id,
                "text":       text,
                "component":  "chameha.tier3",
                "action":     "tier3_call"
            })
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect(("127.0.0.1", 4222))
            sock.recv(1024)
            sock.sendall(b'CONNECT {"verbose":false}\r\n')
            sub = f"SUB sorabbyngo.cml.filter.response.{request_id} 99\r\n"
            sock.sendall(sub.encode())
            pub = f"PUB sorabbyngo.cml.filter.request {len(msg)}\r\n{msg}\r\n"
            sock.sendall(pub.encode())
            # Read response
            buf = ""
            sock.settimeout(5)
            for _ in range(20):
                chunk = sock.recv(4096).decode("utf-8", errors="ignore")
                buf += chunk
                if "MSG sorabbyngo.cml.filter.response" in buf and "\r\n" in buf:
                    lines = buf.split("\r\n")
                    for i, line in enumerate(lines):
                        if line.startswith("MSG ") and i+1 < len(lines):
                            payload = lines[i+1]
                            if payload:
                                result = json.loads(payload)
                                sock.close()
                                if result.get("allowed"):
                                    return True, result.get("text", text)
                                else:
                                    return False, result.get("reason", "Blocked by CML")
            sock.close()
        except Exception as e:
            pass  # CML unavailable — fall through with original sanitization
        return True, text

    def respond(self, user_input: str) -> str | None:
        if not self.available:
            return "[Tier 3 unavailable — set ANTHROPIC_API_KEY to enable]"

        sanitized = self._sanitize(user_input)

        # CML filter — privacy + safety before Claude API
        allowed, filtered = self._cml_filter(sanitized)
        if not allowed:
            return f"[CML blocked request: {filtered}]"
        sanitized = filtered

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
