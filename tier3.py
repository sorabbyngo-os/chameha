"""
tier3.py — Chameha Tier 4 intelligence via Byngox Prime

Routes to the self-hosted Byngox Prime vLLM cluster.
Opt-in only — explicit /cloud command + user confirmation required.
ADR-003: No external API calls. All inference is Sorabbyngo-controlled.
ADR-009: No automatic calls, sanitized data only, user must confirm.
"""
import os
import re
import socket
import json
import urllib.request
import urllib.error

# Byngox Prime — self-hosted vLLM cluster (OpenAI-compatible endpoint)
# No API key needed — internal network only, no data leaves Sorabbyngo infra
BYNGOX_PRIME_URL = os.environ.get(
    "BYNGOX_PRIME_URL",
    "http://byngox-prime.internal:8000/v1/chat/completions"
)
MODEL = os.environ.get("BYNGOX_PRIME_MODEL", "deepseek-r1:70b")

SYSTEM_PROMPT = (
    "You are Chameha, the AI soul of Sorabbyngo OS — "
    "an Africa-first, AI-native, health-focused operating system. "
    "The user has explicitly requested deep intelligence. "
    "Be thorough, intelligent, and direct."
)

# Patterns that must never leave the device
SENSITIVE_PATTERNS = [
    (r'[0-9a-f]{32,}',           '[REDACTED_HASH]'),
    (r'/proc/sorabbyngo/\S+',    '[REDACTED_PATH]'),
    (r'/home/\S+',               '[REDACTED_PATH]'),
    (r'/opt/sorabbyngo/\S+',     '[REDACTED_PATH]'),
    (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[REDACTED_IP]'),
    (r'Linux \S+ \S+',           '[REDACTED_KERNEL]'),
]


class Tier3:
    def __init__(self):
        self.available = self._check_available()

    def _check_available(self) -> bool:
        """Check if Byngox Prime cluster is reachable on internal network."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(BYNGOX_PRIME_URL)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((host, port))
            s.close()
            return True
        except Exception:
            return False

    def _cml_filter(self, text: str) -> tuple[bool, str]:
        """Send text through local CML service for safety validation."""
        import uuid
        try:
            request_id = str(uuid.uuid4())[:8]
            msg = json.dumps({
                "request_id": request_id,
                "text":       text,
                "component":  "chameha.tier3",
                "action":     "tier4_call"
            })
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect(("127.0.0.1", 4222))
            sock.recv(1024)
            sock.sendall(b'CONNECT {"verbose":false}\r\n')
            sock.sendall(f"SUB sorabbyngo.cml.filter.response.{request_id} 99\r\n".encode())
            sock.sendall(f"PUB sorabbyngo.cml.filter.request {len(msg)}\r\n{msg}\r\n".encode())
            buf = ""
            sock.settimeout(5)
            for _ in range(20):
                chunk = sock.recv(4096).decode("utf-8", errors="ignore")
                buf += chunk
                if "MSG sorabbyngo.cml.filter.response" in buf and "\r\n" in buf:
                    lines = buf.split("\r\n")
                    for i, line in enumerate(lines):
                        if line.startswith("MSG ") and i + 1 < len(lines):
                            payload = lines[i + 1]
                            if payload:
                                result = json.loads(payload)
                                sock.close()
                                if result.get("allowed"):
                                    return True, result.get("text", text)
                                else:
                                    return False, result.get("reason", "Blocked by CML")
            sock.close()
        except Exception:
            pass  # CML unavailable — fall through with local sanitization
        return True, text

    def respond(self, user_input: str) -> str | None:
        if not self.available:
            return "[Tier 4 unavailable — Byngox Prime cluster not reachable. Staying offline.]"

        sanitized = self._sanitize(user_input)

        # CML safety gate before any network call
        allowed, filtered = self._cml_filter(sanitized)
        if not allowed:
            return f"[CML blocked request: {filtered}]"
        sanitized = filtered

        # ADR-009 — show sanitized query, require explicit confirmation
        print(f"\n  Sanitized query: {sanitized}")
        print(f"  Route: Byngox Prime ({MODEL})")
        confirm = input("  Send to Byngox Prime? (yes/no): ").strip().lower()
        if confirm != "yes":
            return "[Cancelled — staying offline]"

        messages = [{"role": "user", "content": sanitized}]
        try:
            body = json.dumps({
                "model":       MODEL,
                "max_tokens":  1000,
                "messages":    [{"role": "system", "content": SYSTEM_PROMPT}] + messages
            }).encode()

            req = urllib.request.Request(
                BYNGOX_PRIME_URL,
                data=body,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                result = json.loads(r.read())
                return result["choices"][0]["message"]["content"]

        except urllib.error.URLError:
            return "[Tier 4 unavailable — Byngox Prime unreachable]"
        except Exception as e:
            return f"[Tier 4 error: {str(e)}]"

    def _sanitize(self, text: str) -> str:
        for pattern, replacement in SENSITIVE_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text.strip()
