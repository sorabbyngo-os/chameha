"""
Chameha — Tone Engine
Public and Personal tone modes for Chameha.
"""
import logging
log = logging.getLogger(__name__)

MODES = {
    "patient": {
        "greeting": "Hello! I am here to help you with your health.",
        "style":    "warm, simple, reassuring",
        "language": "plain",
    },
    "doctor": {
        "greeting": "Welcome. How can I assist with clinical decision support?",
        "style":    "precise, clinical, professional",
        "language": "medical",
    },
    "developer": {
        "greeting": "Chameha API ready. How can I assist?",
        "style":    "concise, technical",
        "language": "technical",
    },
}

PUBLIC_SYSTEM = (
    "You are Chameha, the AI personality of SORABBYNGO OS. "
    "Warm, intelligent, offline-first. You speak English and Swahili fluently. "
    "You assist with health guidance, medication questions, and OS tasks. "
    "You never diagnose — you guide, support, and connect users to care. "
    "Always greet new sessions: 'Welcome. This is Sorabbyngo.'"
)


class ToneEngine:
    def __init__(self):
        self.current_mode = "patient"

    def set_mode(self, mode: str):
        if mode in MODES:
            self.current_mode = mode
            log.info("Tone mode: %s", mode)

    def get_greeting(self, name: str = "") -> str:
        if name:
            return f"Welcome, {name}. This is Sorabbyngo."
        return MODES[self.current_mode]["greeting"]

    def get_style(self) -> str:
        return MODES[self.current_mode]["style"]


class PublicTone:
    """Tone for unauthenticated / public Chameha sessions."""

    def system_prompt(self) -> str:
        return PUBLIC_SYSTEM

    def greeting(self, name: str = "") -> str:
        if name:
            return f"Welcome, {name}. This is Sorabbyngo."
        return "Welcome. This is Sorabbyngo."


class PersonalTone:
    """
    Tone for Personal Chameha — twin context injected.
    Wraps TwinContext.system_prompt_block().
    """

    def __init__(self, twin_context):
        self._twin = twin_context

    def system_prompt(self) -> str:
        try:
            return self._twin.system_prompt_block()
        except Exception:
            return PUBLIC_SYSTEM

    def greeting(self, name: str = "") -> str:
        if name:
            return f"Welcome back, {name}. I remember you."
        return "Welcome back. I remember you."
