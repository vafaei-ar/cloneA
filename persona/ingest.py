"""Ingest exported chat history to build persona memory."""
import os
import re
import glob
import config
from memory import rag


def ingest_directory(directory: str | None = None) -> int:
    directory = directory or config.PERSONA_CHATS_DIR
    files = glob.glob(os.path.join(directory, "**/*.txt"), recursive=True)
    files += glob.glob(os.path.join(directory, "**/*.json"), recursive=True)

    count = 0
    for path in files:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".txt":
            count += _ingest_txt(path)
        elif ext == ".json":
            count += _ingest_json(path)

    print(f"Ingested {count} messages from {len(files)} files in {directory}")
    return count


# Matches "Name: message", tolerating an optional leading "[date]" bracket,
# a leading date (2024-01-02 or 02/01/2024) and/or a time (10:30 / 10:30:45)
# so those are not mistaken for the sender or a message.
_TXT_LINE = re.compile(
    r"^\s*"
    r"(?:\[[^\]]+\]\s*)?"                      # optional [timestamp]
    r"(?:\d{1,4}[/.\-]\d{1,2}[/.\-]\d{1,4}[, ]+)?"  # optional date
    r"(?:\d{1,2}:\d{2}(?::\d{2})?\s*[-–]?\s*)?"      # optional time
    r"(?P<sender>[^:\n]{1,40}?):\s+"          # sender name
    r"(?P<text>.+?)\s*$"
)


def _ingest_txt(path: str) -> int:
    """Parse plain-text chat export (lines like "[date] Name: message")."""
    count = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = _TXT_LINE.match(line)
            if not m:
                continue
            sender = m.group("sender").strip()
            text = m.group("text").strip()
            if text:
                rag.store(
                    text,
                    metadata={
                        "source": os.path.basename(path),
                        "sender": sender,
                        "type": "persona",
                    },
                )
                count += 1
    return count


def _ingest_json(path: str) -> int:
    """Parse Telegram JSON export (result.messages list)."""
    import json
    count = 0
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    messages = data if isinstance(data, list) else data.get("messages", [])
    for msg in messages:
        text = msg.get("text", "")
        if isinstance(text, list):
            text = "".join(p if isinstance(p, str) else p.get("text", "") for p in text)
        text = text.strip()
        if text:
            rag.store(
                text,
                metadata={
                    "source": os.path.basename(path),
                    "sender": str(msg.get("from", "unknown")),
                    "date": str(msg.get("date", "")),
                    "type": "persona",
                },
            )
            count += 1
    return count
