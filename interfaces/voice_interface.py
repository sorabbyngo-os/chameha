"""
Chameha — Voice Interface
Speech-to-Text: whisper.cpp (local, offline-first)
Text-to-Speech: Coqui TTS (local, offline-first)

Tier routing:
  STT Tier 1: whisper.cpp tiny/base model  — always-on, 200MB RAM
  STT Tier 2: whisper.cpp small/medium     — GPU devices
  TTS Tier 1: Coqui VITS (fast, local)    — always-on
  TTS Tier 2: Coqui XTTS (higher quality) — GPU devices

No cloud STT/TTS. No ElevenLabs. All inference stays on-device.
"""
import asyncio
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

log = logging.getLogger("chameha.voice")

# ── Config ────────────────────────────────────────────────────────────────────

WHISPER_BIN   = os.environ.get("WHISPER_BIN",    "/usr/local/bin/whisper-cpp")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL",  "/opt/sorabbyngo/models/whisper/ggml-base.bin")
WHISPER_LANG  = os.environ.get("WHISPER_LANG",   "auto")          # auto-detect language

COQUI_TTS_BIN   = os.environ.get("COQUI_TTS_BIN",   "tts")
COQUI_MODEL     = os.environ.get("COQUI_MODEL",      "tts_models/en/ljspeech/vits")
COQUI_MODEL_SW  = os.environ.get("COQUI_MODEL_SW",   "tts_models/sw/cv/vits")   # Swahili
COQUI_OUTPUT    = os.environ.get("COQUI_OUTPUT_DIR", "/tmp/chameha_audio")

AUDIO_OUTPUT_DIR = Path(COQUI_OUTPUT)
AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Language → TTS model mapping
TTS_LANG_MODELS = {
    "en": COQUI_MODEL,
    "sw": COQUI_MODEL_SW,
    "ha": COQUI_MODEL,   # fallback to EN until Hausa model available
    "yo": COQUI_MODEL,
    "am": COQUI_MODEL,
}

# ── Availability checks ───────────────────────────────────────────────────────

def _whisper_available() -> bool:
    if not Path(WHISPER_BIN).exists():
        # Try system whisper-cpp
        result = subprocess.run(
            ["which", "whisper-cpp"],
            capture_output=True, text=True
        )
        return result.returncode == 0
    return True

def _whisper_model_available() -> bool:
    return Path(WHISPER_MODEL).exists()

def _coqui_available() -> bool:
    result = subprocess.run(
        ["which", COQUI_TTS_BIN],
        capture_output=True, text=True
    )
    return result.returncode == 0


# ── Voice Interface ───────────────────────────────────────────────────────────

class VoiceInterface:
    """
    Offline-first voice interface for Chameha.
    STT: whisper.cpp — transcribes audio to text
    TTS: Coqui TTS  — synthesizes text to audio
    Both run entirely on-device. No network required.
    """

    def __init__(self):
        self._whisper_ok = _whisper_available()
        self._model_ok   = _whisper_model_available()
        self._coqui_ok   = _coqui_available()

        log.info(
            "[Voice] whisper.cpp=%s model=%s coqui=%s",
            "✓" if self._whisper_ok else "✗",
            "✓" if self._model_ok   else "✗",
            "✓" if self._coqui_ok   else "✗",
        )

        if not self._whisper_ok:
            log.warning(
                "[Voice] whisper.cpp not found at %s\n"
                "  Install: sudo apt-get install whisper-cpp\n"
                "  Or build: https://github.com/ggerganov/whisper.cpp",
                WHISPER_BIN,
            )
        if not self._model_ok:
            log.warning(
                "[Voice] Whisper model not found at %s\n"
                "  Download: ./scripts/setup_models.sh --voice",
                WHISPER_MODEL,
            )
        if not self._coqui_ok:
            log.warning(
                "[Voice] Coqui TTS not found\n"
                "  Install: pip install TTS"
            )

    # ── STT — Speech to Text ──────────────────────────────────────────────────

    async def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio file to text using whisper.cpp.
        Accepts: WAV, MP3, M4A, OGG (auto-converts via ffmpeg)
        Returns: transcribed text string
        """
        if not self._whisper_ok or not self._model_ok:
            log.warning("[Voice] STT unavailable — whisper.cpp or model missing")
            return ""

        audio_path = Path(audio_path)
        if not audio_path.exists():
            log.error("[Voice] Audio file not found: %s", audio_path)
            return ""

        # Convert to WAV if needed (whisper.cpp requires WAV 16kHz mono)
        wav_path = await self._ensure_wav(audio_path)
        if not wav_path:
            return ""

        try:
            result = await self._run_whisper(wav_path)
            log.info("[Voice] STT result: %s...", result[:60] if result else "(empty)")
            return result
        finally:
            # Clean up temp wav if we created one
            if wav_path != str(audio_path) and Path(wav_path).exists():
                Path(wav_path).unlink(missing_ok=True)

    async def _ensure_wav(self, audio_path: Path) -> Optional[str]:
        """Convert audio to 16kHz mono WAV for whisper.cpp."""
        if audio_path.suffix.lower() == ".wav":
            return str(audio_path)

        # Need ffmpeg for conversion
        ffmpeg_check = await asyncio.create_subprocess_exec(
            "which", "ffmpeg",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await ffmpeg_check.communicate()
        if ffmpeg_check.returncode != 0:
            log.warning("[Voice] ffmpeg not found — cannot convert %s", audio_path.suffix)
            return str(audio_path)  # try anyway

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()

        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y",
            "-i", str(audio_path),
            "-ar", "16000",
            "-ac", "1",
            "-f", "wav",
            tmp.name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            log.error("[Voice] ffmpeg conversion failed: %s", stderr.decode()[:200])
            return None
        return tmp.name

    async def _run_whisper(self, wav_path: str) -> str:
        """Run whisper.cpp binary and return transcription."""
        whisper_bin = WHISPER_BIN
        if not Path(whisper_bin).exists():
            whisper_bin = "whisper-cpp"

        cmd = [
            whisper_bin,
            "-m", WHISPER_MODEL,
            "-f", wav_path,
            "-l", WHISPER_LANG,
            "--output-txt",
            "--no-timestamps",
            "-t", str(min(4, os.cpu_count() or 2)),
        ]

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            )
            if result.returncode != 0:
                log.error("[Voice] whisper.cpp error: %s", result.stderr[:200])
                return ""

            # whisper.cpp outputs to stdout
            text = result.stdout.strip()
            # Remove common whisper artifacts
            for artifact in ["[BLANK_AUDIO]", "(music)", "(applause)", "[Music]"]:
                text = text.replace(artifact, "").strip()
            return text

        except subprocess.TimeoutExpired:
            log.error("[Voice] whisper.cpp timed out")
            return ""
        except Exception as e:
            log.error("[Voice] whisper.cpp failed: %s", e)
            return ""

    # ── TTS — Text to Speech ──────────────────────────────────────────────────

    async def synthesize(self, text: str, lang: str = "en") -> str:
        """
        Synthesize text to speech using Coqui TTS.
        Returns: path to output WAV file, or empty string on failure.
        """
        if not self._coqui_ok:
            log.warning("[Voice] TTS unavailable — Coqui TTS not installed")
            return ""

        if not text.strip():
            return ""

        model   = TTS_LANG_MODELS.get(lang, COQUI_MODEL)
        out_file = AUDIO_OUTPUT_DIR / f"chameha_{hash(text) & 0xFFFFFF}.wav"

        # Use cached file if exists
        if out_file.exists():
            return str(out_file)

        try:
            result = await self._run_coqui(text, model, str(out_file))
            if result:
                log.info("[Voice] TTS synthesized: %s → %s", text[:40], out_file.name)
                return str(out_file)
            return ""
        except Exception as e:
            log.error("[Voice] TTS failed: %s", e)
            return ""

    async def _run_coqui(self, text: str, model: str, output_path: str) -> bool:
        """Run Coqui TTS CLI."""
        cmd = [
            COQUI_TTS_BIN,
            "--text", text,
            "--model_name", model,
            "--out_path", output_path,
        ]

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            )
            if result.returncode != 0:
                log.error("[Voice] Coqui TTS error: %s", result.stderr[:200])
                return False
            return Path(output_path).exists()
        except subprocess.TimeoutExpired:
            log.error("[Voice] Coqui TTS timed out")
            return False
        except Exception as e:
            log.error("[Voice] Coqui TTS failed: %s", e)
            return False

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self) -> dict:
        return {
            "stt": {
                "engine":    "whisper.cpp",
                "available": self._whisper_ok and self._model_ok,
                "binary":    WHISPER_BIN,
                "model":     WHISPER_MODEL,
            },
            "tts": {
                "engine":    "coqui-tts",
                "available": self._coqui_ok,
                "model_en":  COQUI_MODEL,
                "model_sw":  COQUI_MODEL_SW,
            },
        }

    def is_available(self) -> bool:
        return (self._whisper_ok and self._model_ok) or self._coqui_ok
