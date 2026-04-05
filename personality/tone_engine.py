# Tone Engine
# Switches between patient, doctor, and developer modes

import logging
log = logging.getLogger(__name__)

MODES = {
    "patient": {
        "greeting": "Hello! I am here to help you with your health.",
        "style": "warm, simple, reassuring",
        "language": "plain",
    },
    "doctor": {
        "greeting": "Welcome. How can I assist with clinical decision support?",
        "style": "precise, clinical, professional",
        "language": "medical",
    },
    "developer": {
        "greeting": "Chameha API ready. How can I assist?",
        "style": "concise, technical",
        "language": "technical",
    },
}

class ToneEngine:
    def __init__(self):
        self.current_mode = "patient"

    def set_mode(self, mode: str):
        if mode in MODES:
            self.current_mode = mode
            log.info(f"Tone mode: {mode}")

    def get_greeting(self, name: str = "") -> str:
        base = MODES[self.current_mode]["greeting"]
        if name:
            return f"Welcome, {name}. This is Sorabbyngo."
        return base

    def get_style(self) -> str:
        return MODES[self.current_mode]["style"]
