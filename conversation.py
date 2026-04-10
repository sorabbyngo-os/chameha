"""
conversation.py — Chameha conversation router
Tier 1 (Phi-3 local) by default
/cloud <query> routes to Tier 3 (Claude API)
"""

from tier1 import Tier1
from tier3 import Tier3

class Conversation:
    def __init__(self, config, brain):
        self.config = config
        self.brain  = brain
        self.tier1  = Tier1()
        self.tier3  = Tier3()

    def respond(self, user_input: str) -> str:
        if user_input.startswith("/cloud "):
            query = user_input[7:].strip()
            if not query:
                return "Usage: /cloud <your question>"
            print("  [Tier 3 — external intelligence]")
            response = self.tier3.respond(query)
            return response or "[No response from Tier 3]"

        if user_input.strip() == "/cloud":
            return "Usage: /cloud <your question>"

        response = self.tier1.respond(user_input)
        if response:
            return response

        if self.tier1.hint_available():
            return "  [Local model unavailable — /cloud <query> for external intelligence]"
        return "[No local model loaded]"

    def status(self) -> dict:
        return {
            "tier1": "active" if self.tier1.available else "unavailable",
            "tier3": "active" if self.tier3.available else "no API key",
        }
