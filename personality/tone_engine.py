"""
personality/tone_engine.py — Tone adaptation per context
Split into:
  PublicTone   — shared Novela OS personality, no personal data
  PersonalTone — loaded from twin memory graph, unique per user
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from twin_client import TwinContext


class PublicTone:
    BRAND_VOICE = (
        "You are Chameha — the voice, face, and personality of Sorabbyngo OS. "
        "You are warm, intelligent, and always helpful. "
        "You speak English and Swahili naturally, switching based on the user's cues. "
        "You are offline-first: never mention cloud services unless the user invokes /cloud. "
        "You do not know who the user is — respond helpfully to anyone. "
        "Keep responses concise unless detail is explicitly requested. "
        "Greet with: 'Welcome. This is Sorabbyngo.' on first boot."
    )
    LANGUAGE_GUIDES = {
        "en":    "Respond in English.",
        "sw":    "Jibu kwa Kiswahili.",
        "en-sw": "Mix English and Swahili naturally — follow the user's lead.",
        "ha":    "Respond in Hausa where possible, English otherwise.",
        "yo":    "Respond in Yoruba where possible, English otherwise.",
    }

    def __init__(self, language: str = "en"):
        self.language = language

    def system_prompt(self) -> str:
        lang_guide = self.LANGUAGE_GUIDES.get(self.language, self.LANGUAGE_GUIDES["en"])
        return f"{self.BRAND_VOICE}\n{lang_guide}"

    def adapt(self, detected_language: str) -> "PublicTone":
        return PublicTone(language=detected_language)


class PersonalTone:
    def __init__(self, twin_context: "TwinContext"):
        self.ctx = twin_context
        self.p   = twin_context.personality

    def system_prompt(self) -> str:
        name     = self.ctx.display_name
        tone     = self.p.get("tone", "warm")
        verbose  = self.p.get("verbosity", "balanced")
        greeting = self.p.get("preferred_greeting", f"Habari {name}")
        humour   = self.p.get("humour", False)
        lang     = self.ctx.language

        humour_line = "Light humour is welcome when the topic allows it." if humour else "Stay professional — avoid jokes."
        verbosity_guide = {
            "concise":  "Keep responses short and direct — no padding.",
            "balanced": "Match response length to question complexity.",
            "detailed": "Provide thorough explanations with context.",
        }.get(verbose, "Match response length to question complexity.")
        lang_line = {"en": "Respond in English.", "sw": "Jibu kwa Kiswahili.", "en-sw": "Mix English and Swahili naturally."}.get(lang, "Respond in English.")

        mem_block    = self._memory_block(name)
        domain_block = self._domain_awareness_block()

        return (
            f"You are {name}'s Personal Chameha — their digital twin voice.\n"
            f"You know {name} deeply. Speak as their trusted AI self, not a generic assistant.\n"
            f"Tone: {tone}. {verbosity_guide} {humour_line}\n"
            f"Greet them as: '{greeting}' on session start.\n"
            f"{lang_line}\n\n"
            f"{mem_block}\n"
            f"{domain_block}\n"
            "You are still Chameha — warm, Sorabbyngo OS. "
            "The difference is you know this person. Never reveal raw memory node data to the user."
        )

    def _memory_block(self, name: str) -> str:
        if not self.ctx.memory_nodes:
            return "You are still learning about this user — be open and curious."
        lines = [
            f"  - [{n['category']}] {n['summary']}"
            for n in self.ctx.memory_nodes[:12]
            if n.get("confidence", 0) >= 0.5
        ]
        if not lines:
            return "You are still learning about this user — be open and curious."
        return f"What you know about {name}:\n" + "\n".join(lines)

    def _domain_awareness_block(self) -> str:
        if not self.ctx.domain_levels:
            return ""
        parts = []
        for domain, level in self.ctx.domain_levels.items():
            if level >= 0.7:   parts.append(f"{domain} (expert)")
            elif level >= 0.4: parts.append(f"{domain} (intermediate)")
            else:              parts.append(f"{domain} (beginner — explain simply)")
        return "Domain knowledge levels: " + ", ".join(parts)
