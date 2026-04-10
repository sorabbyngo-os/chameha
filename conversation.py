"""
conversation.py — Chameha conversation router
ADR-009 enforced: Tier 1 default, Tier 3 explicit /cloud only
"""
import datetime
import os
from tier1 import Tier1
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

        # Tier 1 — default, always offline
        _log(f"TIER1_QUERY: {user_input[:80]}")
        response = self.tier1.respond(user_input)

        if response:
            _log(f"TIER1_RESPONSE: {response[:80]}")
            # Suggest Tier 3 for complex queries — never auto-call
            if self.tier1.is_complex(user_input):
                response += "\n\n  [Deeper analysis available — /cloud " + user_input[:30] + "...]"
            return response

        # Tier 1 unavailable
        _log("TIER1_UNAVAILABLE")
        return (
            "[Local model unavailable]\n"
            "  Use /cloud <query> for external intelligence."
        )

    def status(self) -> dict:
        return {
            "tier1": "active" if self.tier1.available else "unavailable",
            "tier3": "active" if self.tier3.available else "no API key",
        }
