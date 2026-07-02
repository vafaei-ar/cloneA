import os
import config

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
    return _model


def transcribe(audio_path: str) -> str:
    model = _get_model()
    segments, info = model.transcribe(
        audio_path,
        language=config.WHISPER_LANGUAGE,
        beam_size=5,
    )
    text = "".join(seg.text for seg in segments).strip()
    return text
