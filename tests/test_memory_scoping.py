from memory import rag


def test_where_filter_scopes_to_user_and_persona():
    where = rag._where_for_user("42")
    assert where == {"$or": [{"user_id": "42"}, {"type": "persona"}]}


def test_where_filter_none_when_no_user():
    assert rag._where_for_user(None) is None


def test_build_memory_context_passes_user_id(monkeypatch):
    captured = {}

    def fake_retrieve(query, n_results=5, user_id=None):
        captured["user_id"] = user_id
        return ["mem A", "mem B"]

    monkeypatch.setattr(rag, "retrieve", fake_retrieve)
    ctx = rag.build_memory_context("hi", user_id=7)
    assert captured["user_id"] == 7
    assert "mem A" in ctx and "mem B" in ctx


def test_build_memory_context_empty_when_no_docs(monkeypatch):
    monkeypatch.setattr(rag, "retrieve", lambda *a, **k: [])
    assert rag.build_memory_context("hi", user_id=1) == ""
