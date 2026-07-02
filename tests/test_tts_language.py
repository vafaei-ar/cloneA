from tts import xtts_client


def test_english_is_supported():
    assert xtts_client._detect_language("Hello, how are you?") == "en"


def test_farsi_is_unsupported():
    # Persian text -> None (XTTS v2 cannot speak Farsi).
    assert xtts_client._detect_language("سلام حال شما چطور است") is None


def test_looks_farsi_detects_arabic_script():
    assert xtts_client._looks_farsi("سلام") is True
    assert xtts_client._looks_farsi("hello") is False


def test_synthesize_rejects_farsi(tmp_path, monkeypatch):
    # Point at an existing "voice sample" so we get past the file check and
    # hit the language guard.
    sample = tmp_path / "sample.wav"
    sample.write_bytes(b"RIFF")
    monkeypatch.setattr(xtts_client.config, "VOICE_SAMPLE_PATH", str(sample))
    try:
        xtts_client.synthesize("سلام دنیا")
        assert False, "expected ValueError for Farsi text"
    except ValueError:
        pass
