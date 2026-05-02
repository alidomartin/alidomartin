"""
Voice I/O for Jarvis.

STT  — OGG (from Telegram) → WAV → Google Speech Recognition (free, no API key)
TTS  — text → MP3 (gTTS) → OGG OPUS (Telegram's required voice format)

System dependency: ffmpeg must be installed.
  Ubuntu/Debian:  sudo apt-get install ffmpeg
  macOS:          brew install ffmpeg
"""

import io
import os
import tempfile
import logging

logger = logging.getLogger(__name__)


def _ensure_ffmpeg() -> bool:
    return os.system("ffmpeg -version > /dev/null 2>&1") == 0


# ── Speech-to-Text ─────────────────────────────────────────────────────────────

def transcribe(ogg_bytes: bytes) -> str:
    """
    Convert Telegram voice message bytes (OGG OPUS) to transcribed text.
    Uses Google's free speech recognition service via SpeechRecognition.
    Returns empty string on failure.
    """
    try:
        import speech_recognition as sr
        from pydub import AudioSegment
    except ImportError:
        logger.error("SpeechRecognition or pydub not installed.")
        return ""

    try:
        with tempfile.TemporaryDirectory() as tmp:
            ogg_path = os.path.join(tmp, "voice.ogg")
            wav_path = os.path.join(tmp, "voice.wav")

            with open(ogg_path, "wb") as f:
                f.write(ogg_bytes)

            # OGG OPUS → WAV (requires ffmpeg)
            audio = AudioSegment.from_ogg(ogg_path)
            audio.export(wav_path, format="wav")

            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)

            text = recognizer.recognize_google(audio_data)
            logger.info("Transcribed: %s", text)
            return text

    except Exception as exc:
        logger.warning("Transcription failed: %s", exc)
        return ""


# ── Text-to-Speech ─────────────────────────────────────────────────────────────

def synthesize(text: str) -> bytes | None:
    """
    Convert text to OGG OPUS bytes suitable for Telegram's sendVoice.
    Uses gTTS (Google TTS) → MP3 → OGG OPUS via pydub/ffmpeg.
    Returns None on failure.
    """
    try:
        from gtts import gTTS
        from pydub import AudioSegment
    except ImportError:
        logger.error("gTTS or pydub not installed.")
        return None

    try:
        with tempfile.TemporaryDirectory() as tmp:
            mp3_path = os.path.join(tmp, "jarvis.mp3")
            ogg_path = os.path.join(tmp, "jarvis.ogg")

            tts = gTTS(text=text, lang="en", tld="co.uk", slow=False)
            tts.save(mp3_path)

            # MP3 → OGG OPUS (Telegram's required format for voice messages)
            audio = AudioSegment.from_mp3(mp3_path)
            audio.export(ogg_path, format="ogg", codec="libopus")

            with open(ogg_path, "rb") as f:
                return f.read()

    except Exception as exc:
        logger.warning("Speech synthesis failed: %s", exc)
        return None


def strip_markdown(text: str) -> str:
    """Remove markdown symbols so TTS reads cleanly."""
    import re
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    # Remove bold/italic markers
    text = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", text)
    # Remove headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r"^[-─═]{3,}$", "", text, flags=re.MULTILINE)
    # Remove bullet characters
    text = re.sub(r"^[•\-\*]\s+", "", text, flags=re.MULTILINE)
    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
