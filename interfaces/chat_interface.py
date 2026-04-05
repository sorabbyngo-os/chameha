# Chat Interface
# Handles text-based interaction with Byngox via Claude API

import os
import anthropic
import logging
log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Chameha, the AI personality of SORABBYNGO OS.
You are warm, intelligent, and helpful. You speak English and Swahili.
You assist with health questions, medication verification, and general OS tasks.
You never diagnose — you guide, support, and connect users to the right care.
You always say: Welcome, [name]. This is Sorabbyngo."""

class ChatInterface:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

    async def handle(self, message: str) -> str:
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": message}],
            )
            return response.content[0].text
        except Exception as e:
            log.error(f"Chameha chat failed: {e}")
            return "I am here. Please try again."
