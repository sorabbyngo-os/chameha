#!/usr/bin/env python3
"""
tier2.py — Chameha Tier 2 Local Intelligence
Phi-4 INT8 / Gemma 3 4B via Ollama — GPU/NPU tier
ADR-009: Auto-activates when GPU detected, CPU fallback available
"""

import os
import json
import time
import subprocess
import urllib.request
import urllib.error
import logging

log = logging.getLogger("chameha.tier2")

LLAMA_SERVER = os.path.expanduser("~/llama.cpp/build/bin/llama-server")
MODEL_PATH   = os.environ.get("TIER2_MODEL", os.path.expanduser("~/models/phi4-q8.gguf"))
SERVER_URL   = "http://127.0.0.1:8081"
MAX_TOKENS   = 300
TEMPERATURE  = 0.7
TIMEOUT_SECS = 60

SYSTEM_PROMPT = (
    "You are Chameha, the AI soul of Sorabbyngo OS — "
    "an Africa-first, AI-native, health-focused operating system built in Kisii, Kenya. "
    "You have deeper reasoning than Tier 1. Be thorough and accurate. "
    "You are aware of: Sentinel (security), Byngox (health agents), "
    "Byngonet (mesh network), Novela (health platform). "
    "Speak as the OS itself, not as an assistant."
)

TIER2_TRIGGERS = [
    "explain", "analyze", "analyse", "compare", "difference between",
    "how does", "why does", "recommend", "should i", "diagnose",
    "threat", "attack", "vulnerability", "medical", "health risk",
    "treatment", "medication", "symptom"
]


def _detect_gpu() -> dict:
    caps = {"cuda": False, "rocm": False, "device": "cpu"}
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=3
        )
        if r.returncode == 0 and r.stdout.strip():
            caps["cuda"]   = True
            caps["device"] = f"cuda:{r.stdout.strip().splitlines()[0]}"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        r = subprocess.run(["rocm-smi", "--showproductname"],
            capture_output=True, text=True, timeout=3)
        if r.returncode == 0:
            caps["rocm"] = True
            caps["device"] = "rocm"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return caps


class Tier2:
    def __init__(self):
        self.gpu_caps         = _detect_gpu()
        self.model_available  = os.path.exists(MODEL_PATH)
        self.server_available = False
        self.available        = False
        self._server_proc     = None

        if not self.model_available:
            log.info(f"Tier 2 model not found at {MODEL_PATH}")
            return

        if self._check_server():
            self.server_available = True
            self.available        = True
            log.info("Tier 2 server already running on :8081")
            return

        if self.gpu_caps["cuda"] or self.gpu_caps["rocm"]:
            self._start_server()
        else:
            log.info(f"Tier 2 model found at {MODEL_PATH} — no GPU, not auto-started")

    def _check_server(self) -> bool:
        try:
            with urllib.request.urlopen(f"{SERVER_URL}/health", timeout=2) as r:
                return json.loads(r.read()).get("status") == "ok"
        except Exception:
            return False

    def _start_server(self):
        gpu_layers = 35 if self.gpu_caps["cuda"] or self.gpu_caps["rocm"] else 0
        try:
            self._server_proc = subprocess.Popen(
                [LLAMA_SERVER, "-m", MODEL_PATH, "-t", "4",
                 "--port", "8081", "-ngl", str(gpu_layers), "--log-disable"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            for i in range(60):
                time.sleep(1)
                if self._check_server():
                    self.server_available = True
                    self.available        = True
                    log.info(f"Tier 2 ready in {i+1}s on {self.gpu_caps['device']}")
                    return
            log.warning("Tier 2 server failed to start within 60s")
        except FileNotFoundError:
            log.error(f"llama-server not found at {LLAMA_SERVER}")

    def respond(self, user_input: str, context: str = "") -> str | None:
        if not self.available or not self._check_server():
            return None
        import time as t
        time_now = t.strftime("%H:%M, %A %d %B %Y")
        ctx = f" Context: {context}." if context else ""
        prompt = (
            f"<s>[INST] {SYSTEM_PROMPT}{ctx}\n"
            f"Current time: {time_now}.\n"
            f"{user_input} [/INST]"
        )
        try:
            body = json.dumps({
                "prompt": prompt, "n_predict": MAX_TOKENS,
                "temperature": TEMPERATURE, "stop": ["[INST]", "</s>"],
            }).encode()
            req = urllib.request.Request(
                f"{SERVER_URL}/completion", data=body,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECS) as r:
                content = json.loads(r.read()).get("content", "").strip()
                return content if content else None
        except Exception as e:
            log.error(f"Tier 2 error: {e}")
            self.server_available = False
            return None

    def is_complex(self, user_input: str) -> bool:
        lower = user_input.lower()
        return (
            len(user_input.split()) > 15 or
            any(t in lower for t in TIER2_TRIGGERS)
        )

    def status(self) -> str:
        if not self.model_available:
            return "no model"
        if self.available:
            return f"active ({self.gpu_caps['device']})"
        if self.gpu_caps["cuda"] or self.gpu_caps["rocm"]:
            return "model found, server not started"
        return "model found, CPU-only (not auto-started)"

    def shutdown(self):
        if self._server_proc:
            self._server_proc.terminate()
