import json
from persona import ingest


def _capture(monkeypatch):
    stored = []
    monkeypatch.setattr(
        ingest.rag, "store",
        lambda text, metadata=None: stored.append((text, metadata or {})),
    )
    return stored


def test_txt_ingest_parses_name_and_skips_timestamps(tmp_path, monkeypatch):
    stored = _capture(monkeypatch)
    f = tmp_path / "chat.txt"
    f.write_text(
        "[2024-01-02 10:30] Ali: Hello there\n"
        "10:31 Sara: Hi Ali\n"
        "Ali: How are you?\n"
        "not a message line\n",
        encoding="utf-8",
    )
    n = ingest._ingest_txt(str(f))
    texts = [t for t, _ in stored]
    assert "Hello there" in texts
    assert "Hi Ali" in texts
    assert "How are you?" in texts
    # A bare timestamp shouldn't be captured as its own message text.
    assert "10:30" not in texts
    assert n == 3
    assert all(meta.get("type") == "persona" for _, meta in stored)


def test_json_ingest_handles_plain_and_entity_text(tmp_path, monkeypatch):
    stored = _capture(monkeypatch)
    data = {
        "messages": [
            {"from": "Ali", "date": "2024-01-02", "text": "plain message"},
            {"from": "Ali", "date": "2024-01-02",
             "text": ["mixed ", {"type": "link", "text": "https://x"}, " end"]},
            {"from": "Ali", "date": "2024-01-02", "text": ""},  # skipped
        ]
    }
    f = tmp_path / "export.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    n = ingest._ingest_json(str(f))
    texts = [t for t, _ in stored]
    assert "plain message" in texts
    assert "mixed https://x end" in texts
    assert n == 2
    assert all(meta.get("type") == "persona" for _, meta in stored)
