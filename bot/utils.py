"""Small pure helpers with no Telegram/network dependencies (easy to unit-test)."""

TELEGRAM_MAX_CHARS = 4096


def split_message(text: str, limit: int = TELEGRAM_MAX_CHARS) -> list[str]:
    """Split a reply into Telegram-sized chunks.

    Tries to break on paragraph, then line, then space boundaries so words
    aren't cut in half; falls back to a hard cut for very long unbroken text.
    """
    text = text or ""
    if len(text) <= limit:
        return [text] if text else []

    chunks: list[str] = []
    remaining = text
    while len(remaining) > limit:
        window = remaining[:limit]
        # Prefer the latest natural boundary inside the window.
        cut = max(window.rfind("\n\n"), window.rfind("\n"), window.rfind(" "))
        if cut <= 0:
            cut = limit  # no boundary found — hard cut
        chunks.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks
