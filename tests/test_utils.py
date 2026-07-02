from bot.utils import split_message, TELEGRAM_MAX_CHARS


def test_short_message_is_single_chunk():
    assert split_message("hello") == ["hello"]


def test_empty_message_is_empty_list():
    assert split_message("") == []


def test_long_message_is_split_within_limit():
    text = "word " * 3000  # ~15000 chars
    chunks = split_message(text)
    assert len(chunks) > 1
    assert all(len(c) <= TELEGRAM_MAX_CHARS for c in chunks)


def test_split_prefers_boundaries_and_preserves_content():
    text = "a" * 4000 + "\n\n" + "b" * 4000
    chunks = split_message(text)
    assert len(chunks) == 2
    # Reassembled content keeps every character (ignoring split whitespace).
    assert "".join(chunks).replace("\n", "") == text.replace("\n", "")


def test_hard_cut_for_unbroken_text():
    text = "x" * 10000  # no spaces/newlines to break on
    chunks = split_message(text)
    assert all(len(c) <= TELEGRAM_MAX_CHARS for c in chunks)
    assert "".join(chunks) == text
