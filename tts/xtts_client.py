import os
import tempfile
import config

# Languages supported by Coqui XTTS v2. Note: Persian/Farsi (fa) is NOT
# supported, so Farsi replies are sent as text only (no voice note).
XTTS_SUPPORTED_LANGS = {
    "en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru",
    "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko", "hi",
}

_tts = None


def _get_tts():
    global _tts
    if _tts is None:
        # XTTS requires agreeing to the Coqui TOS; set it non-interactively.
        os.environ.setdefault("COQUI_TOS_AGREED", "1")
        from TTS.api import TTS
        _tts = TTS(config.XTTS_MODEL)
    return _tts


def _detect_language(text: str) -> str | None:
    """Best-effort language code for XTTS. Returns None if unsupported."""
    if _looks_farsi(text):
        # Persian is written in Arabic script but is a distinct, unsupported
        # language for XTTS v2 — do not fall back to "ar".
        return None
    return "en"


def synthesize(text: str, output_path: str | None = None) -> str:
    """Synthesize text to speech using the configured voice sample.
    Returns the path to the output wav file. Raises ValueError for
    languages XTTS cannot speak (e.g. Farsi)."""
    if not os.path.exists(config.VOICE_SAMPLE_PATH):
        raise FileNotFoundError(
            f"Voice sample not found: {config.VOICE_SAMPLE_PATH}\n"
            "Place a ~6-second WAV of your voice at that path."
        )

    language = _detect_language(text)
    if language is None or language not in XTTS_SUPPORTED_LANGS:
        raise ValueError(
            "Text language is not supported by XTTS v2 (e.g. Farsi); "
            "sending text only."
        )

    tts = _get_tts()
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_path = tmp.name
        tmp.close()

    tts.tts_to_file(
        text=text,
        speaker_wav=config.VOICE_SAMPLE_PATH,
        language=language,
        file_path=output_path,
    )
    return output_path


def _looks_farsi(text: str) -> bool:
    farsi_range = range(0x0600, 0x06FF)
    return any(ord(c) in farsi_range for c in text)
