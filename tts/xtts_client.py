import os
import tempfile
import config

_tts = None


def _get_tts():
    global _tts
    if _tts is None:
        from TTS.api import TTS
        _tts = TTS(config.XTTS_MODEL)
    return _tts


def synthesize(text: str, output_path: str | None = None) -> str:
    """Synthesize text to speech using the configured voice sample.
    Returns path to the output wav file."""
    if not os.path.exists(config.VOICE_SAMPLE_PATH):
        raise FileNotFoundError(
            f"Voice sample not found: {config.VOICE_SAMPLE_PATH}\n"
            "Place a ~6-second WAV of your voice at that path."
        )

    tts = _get_tts()
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_path = tmp.name
        tmp.close()

    tts.tts_to_file(
        text=text,
        speaker_wav=config.VOICE_SAMPLE_PATH,
        language="fa" if _looks_farsi(text) else "en",
        file_path=output_path,
    )
    return output_path


def _looks_farsi(text: str) -> bool:
    farsi_range = range(0x0600, 0x06FF)
    return any(ord(c) in farsi_range for c in text)
