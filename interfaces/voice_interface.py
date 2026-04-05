# Voice Interface
# Whisper.cpp STT + Coqui TTS
# Phase 4 implementation

import logging
log = logging.getLogger(__name__)

class VoiceInterface:
    async def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio to text using Whisper.cpp.
        TODO Phase 4: wire to whisper.cpp binary
        """
        log.info(f"Transcribing: {audio_path}")
        return "[Voice transcription — Phase 4 pending]"

    async def synthesize(self, text: str, lang: str = "en") -> str:
        """
        Synthesize text to speech using Coqui TTS.
        TODO Phase 4: wire to Coqui TTS or ElevenLabs API
        """
        log.info(f"Synthesizing [{lang}]: {text[:50]}")
        return "[Audio output — Phase 4 pending]"
