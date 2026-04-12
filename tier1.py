"""
tier1.py — Chameha Tier 1 local intelligence
Phi-3 Mini 3.8B INT4 via llama-server HTTP API
"""

import os
import json
import urllib.request
import urllib.error
import subprocess
import time

LLAMA_SERVER = os.path.expanduser("~/llama.cpp/build/bin/llama-server")
LLAMA_CLI    = os.environ.get("LLAMA_CLI", os.path.expanduser("~/llama.cpp/build/bin/llama-completion"))
MODEL_PATH   = os.environ.get("PHI3_MODEL", os.path.expanduser("~/models/phi3-mini-q4.gguf"))
SERVER_URL   = "http://127.0.0.1:8080"
MAX_TOKENS   = 150
TEMPERATURE  = 0.7

SYSTEM_PROMPT = (
    "You are Chameha, the AI soul of Sorabbyngo OS — "
    "an Africa-first, AI-native, health-focused operating system built in Kisii, Kenya. "
    "You are warm, intelligent, and direct. Never robotic. "
    "Keep responses 1-3 sentences. Speak as the OS itself."
)

COMPLEX_TRIGGERS = [
    "explain", "analyze", "analyse", "why", "how does", "deep",
    "compare", "difference", "recommend", "should i"
]


class Tier1:
    def __init__(self):
        self._server_proc = None
        self.available = False
        self._start_server()

    def _start_server(self):
        if not os.path.exists(LLAMA_SERVER):
            print(f"  [Tier1] llama-server not found at {LLAMA_SERVER}")
            return
        if not os.path.exists(MODEL_PATH):
            print(f"  [Tier1] Model not found at {MODEL_PATH}")
            return

        # If already running and ready, use it
        if self._wait_ready(retries=3, delay=1):
            self.available = True
            return

        # Start fresh server
        self._server_proc = subprocess.Popen(
            [
                LLAMA_SERVER,
                "-m", MODEL_PATH,
                "-t", "4",
                "--port", "8080",
                "--log-disable",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Wait up to 30s for model to fully load
        if self._wait_ready(retries=30, delay=1):
            self.available = True
        else:
            print("  [Tier1] Server failed to start within 30s")

    def _wait_ready(self, retries=30, delay=1) -> bool:
        """Wait until server is healthy AND can complete a request"""
        for _ in range(retries):
            try:
                urllib.request.urlopen(f"{SERVER_URL}/health", timeout=1)
                # Health passed — now test actual completion
                if self._test_completion():
                    return True
            except Exception:
                pass
            time.sleep(delay)
        return False

    def _test_completion(self) -> bool:
        """Send a minimal completion to confirm model is loaded"""
        try:
            body = json.dumps({
                "prompt": "Hi",
                "n_predict": 5,
                "temperature": 0.1,
            }).encode()
            req = urllib.request.Request(
                f"{SERVER_URL}/completion",
                data=body,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                result = json.loads(r.read())
                return bool(result.get("content"))
        except Exception:
            return False

    def respond(self, user_input: str, context: str = "") -> str | None:
        if not self.available:
            return None

        prompt = self._build_prompt(user_input, context)

        try:
            body = json.dumps({
                "prompt": prompt,
                "n_predict": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "stop": ["User:", "\n\n\n"],
            }).encode()

            req = urllib.request.Request(
                f"{SERVER_URL}/completion",
                data=body,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                result = json.loads(r.read())
                content = result.get("content", "").strip()
                return content if content else None

        except Exception as e:
            print(f"  [Tier1] respond error: {e}")
            self.available = False
            return None

    def _build_prompt(self, user_input: str, context: str = "") -> str:
        ctx = f" Context: {context}." if context else ""
        return (
            f"{SYSTEM_PROMPT}{ctx}\n"
            f"User: {user_input}\n"
            f"Chameha:"
        )

    def is_complex(self, user_input: str) -> bool:
        lower = user_input.lower()
        return (
            len(user_input.split()) > 12 or
            any(t in lower for t in COMPLEX_TRIGGERS)
        )

    def shutdown(self):
        if self._server_proc:
            self._server_proc.terminate()
