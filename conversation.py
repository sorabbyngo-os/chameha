"""
conversation.py -- Chameha conversation router (fixed v2)
ADR-009 enforced: Tier 1 default, Tier 3 explicit /cloud only

Fixes over v1:
  - Tier 2 routing block was dead code (inside bare `if` with no condition)
    Fixed: Tier 2 now properly tried for complex queries before Tier 1
  - /cloud check refactored cleanly
"""
import datetime
import os

from tier1 import Tier1, _detect_language
from tier2 import Tier2
from tier3 import Tier3

LOG_PATH = os.path.expanduser("~/.sorabbyngo/chameha/chameha.log")


def _log(entry: str):
    ts = datetime.datetime.now().isoformat()
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(f"[{ts}] {entry}\n")
    except Exception:
        pass


# Queries longer than this or containing these keywords get Tier 2 first
COMPLEX_KEYWORDS = {
    "diagnose", "diagnosis", "treatment", "dosage", "medication",
    "symptoms", "clinical", "patient", "risk", "drug interaction",
    "protocol", "guideline", "differential",
}


def _is_complex(text: str) -> bool:
    """Heuristic: long queries or clinical keywords go to Tier 2 first."""
    lower = text.lower()
    return len(text) > 120 or any(kw in lower for kw in COMPLEX_KEYWORDS)


class Conversation:
    def __init__(self):
        self.tier1 = Tier1()
        self.tier2 = Tier2()
        self.tier3 = Tier3()

    def respond(self, user_input: str) -> str:
        user_input = user_input.strip()

        # -- Tier 3: explicit /cloud command only (ADR-009) -------------------
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

        # -- Tier 2: complex queries when GPU available -----------------------
        if self.tier2.available and _is_complex(user_input):
            _log(f"TIER2_QUERY: {user_input[:80]}")
            try:
                lang     = _detect_language(user_input)
                response = self.tier2.chat(user_input, language=lang)
                if response:
                    _log(f"TIER2_RESPONSE: {response[:80]}")
                    return response
            except Exception:
                _log("TIER2_FAILED -- falling back to Tier 1")

        # -- Tier 1: default, always offline ----------------------------------
        _log(f"TIER1_QUERY: {user_input[:80]}")
        response = self.tier1.chat(user_input)
        if response:
            _log(f"TIER1_RESPONSE: {response[:80]}")
            return response

        # -- Last resort: Tier 2 fallback when Tier 1 unavailable ------------
        if self.tier2.available:
            _log("TIER1_UNAVAILABLE -- trying Tier 2 as fallback")
            try:
                response = self.tier2.chat(user_input)
                if response:
                    return response
            except Exception:
                pass

        _log("ALL_LOCAL_UNAVAILABLE")
        return (
            "[Local model unavailable]\n"
            "  Use /cloud <query> for external intelligence."
        )

    def status(self) -> dict:
        return {
            "tier1": self.tier1.status(),
            "tier2": self.tier2.status(),
            "tier3": (
                "active (Byngox Prime)"
                if self.tier3.available
                else "unavailable (Prime cluster unreachable)"
            ),
        }
