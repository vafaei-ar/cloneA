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


def _ingest_txt(path: str) -> int:
    """Parse plain-text Telegram export format (each line: [date] Name: message)."""
    count = 0
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Rough pattern: capture lines that look like "Name: message body"
    pattern = re.compile(r"^(.+?):\s+(.+)$", re.MULTILINE)
    for match in pattern.finditer(content):
        sender, text = match.group(1).strip(), match.group(2).strip()
        if text:
            rag.store(text, metadata={"source": os.path.basename(path), "sender": sender})
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
                },
            )
            count += 1
    return count
