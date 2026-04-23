"""
conversation.py — Chameha conversation router
ADR-009 enforced: Tier 1 default, Tier 3 explicit /cloud only
"""
import datetime
import os
from tier1 import Tier1
from tier2 import Tier2
from tier3 import Tier3

LOG_PATH = os.path.expanduser("~/sorabbyngo-os/chameha/chameha.log")

def _log(entry: str):
    ts = datetime.datetime.now().isoformat()
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(f"[{ts}] {entry}\n")
    except Exception:
        pass

class Conversation:
    def __init__(self):
        self.tier1 = Tier1()
        self.tier2 = Tier2()
        self.tier3 = Tier3()

    def respond(self, user_input: str) -> str:
        user_input = user_input.strip()

        # Tier 3 — explicit /cloud command only
        if user_input.startswith("/cloud "):
            query = user_input[7:].strip()
            if not query:
                return "Usage: /cloud <your question>"
            _log(f"TIER3_REQUEST: {query[:80]}")
            response = self.tier3.respond(query)
            _log(f"TIER3_RESPONSE: {(response or '')[:80]}")
            return response or "[No response from Tier 3]"

        if user_input == "/cloud":
            return "Usage: /cloud <your question>"

        # Tier 2 — for complex queries when available
            _log(f"TIER2_QUERY: {user_input[:80]}")
            response = self.tier2.respond(user_input)
            if response:
                _log(f"TIER2_RESPONSE: {response[:80]}")
                return response
            _log("TIER2_MISS — falling back to Tier 1")

        # Tier 1 — default, always offline
        _log(f"TIER1_QUERY: {user_input[:80]}")
        response = self.tier1.chat(user_input)

        if response:
            _log(f"TIER1_RESPONSE: {response[:80]}")
            return response

        # Tier 1 unavailable — try Tier 2 as fallback
        if self.tier2.available:
            _log("TIER1_UNAVAILABLE — trying Tier 2")
            response = self.tier2.respond(user_input)
            if response:
                return response

        _log("ALL_LOCAL_UNAVAILABLE")
        return (
            "[Local model unavailable]\n"
            "  Use /cloud <query> for external intelligence."
        )

    def status(self) -> dict:
        return {
            "tier1": self.tier1.status(),
            "tier2": self.tier2.status(),
            "tier3": "active (Byngox Prime)" if self.tier3.available else "unavailable (Prime cluster unreachable)",
        }
