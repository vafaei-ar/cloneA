"""Telegram message handlers."""
import os
import asyncio
import tempfile
import logging

from telegram import Update
from telegram.ext import ContextTypes

import config
from llm import ollama_client
from memory import rag
from bot.utils import split_message

logger = logging.getLogger(__name__)

# Per-user in-memory conversation history (cleared on restart)
_histories: dict[int, list[dict]] = {}


def _history(user_id: int) -> list[dict]:
    if user_id not in _histories:
        _histories[user_id] = []
    return _histories[user_id]


def _build_messages(user_id: int, user_text: str) -> list[dict]:
    mem_ctx = rag.build_memory_context(user_text, user_id=user_id)
    system = config.SYSTEM_PROMPT
    if mem_ctx:
        system = system + "\n\n" + mem_ctx

    messages = [{"role": "system", "content": system}]
    messages.extend(_history(user_id))
    messages.append({"role": "user", "content": user_text})
    return messages


async def _reply_chunked(update: Update, text: str) -> None:
    """Send `text` respecting Telegram's 4096-character message limit."""
    for chunk in split_message(text):
        await update.message.reply_text(chunk)


async def _respond(update: Update, user_id: int, user_text: str) -> None:
    """Shared reply pipeline used by both text and (transcribed) voice messages."""
    await update.message.chat.send_action("typing")
    messages = _build_messages(user_id, user_text)

    try:
        # ollama_client.chat is blocking (requests); keep it off the event loop.
        reply = await asyncio.to_thread(ollama_client.chat, messages)
    except Exception as e:
        logger.error("Ollama error: %s", e)
        await update.message.reply_text("Sorry, I couldn't reach the LLM. Is Ollama running?")
        return

    hist = _history(user_id)
    hist.append({"role": "user", "content": user_text})
    hist.append({"role": "assistant", "content": reply})
    # Keep last 20 turns to avoid unbounded growth
    _histories[user_id] = hist[-40:]

    # Persist to long-term memory (blocking: embeddings + disk write).
    try:
        await asyncio.to_thread(
            rag.store,
            f"User: {user_text}\nAssistant: {reply}",
            {"user_id": str(user_id), "type": "conversation"},
        )
    except Exception as e:
        logger.warning("Memory store skipped: %s", e)

    await _reply_chunked(update, reply)

    # If voice replies are enabled and a voice sample exists, also send a voice note.
    if config.TTS_ENABLED and os.path.exists(config.VOICE_SAMPLE_PATH):
        await _send_voice(update, reply)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = (update.message.text or "").strip()
    if not user_text:
        return
    await _respond(update, update.effective_user.id, user_text)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.chat.send_action("typing")

    voice_file = await update.message.voice.get_file()
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        ogg_path = tmp.name
    await voice_file.download_to_drive(ogg_path)

    try:
        from stt import whisper_client
        # Whisper transcription is blocking; run it in a worker thread.
        user_text = await asyncio.to_thread(whisper_client.transcribe, ogg_path)
    except Exception as e:
        logger.error("Whisper error: %s", e)
        await update.message.reply_text("Sorry, I couldn't transcribe your voice message.")
        return
    finally:
        os.unlink(ogg_path)

    user_text = (user_text or "").strip()
    if not user_text:
        await update.message.reply_text("I couldn't make out what you said.")
        return

    await update.message.reply_text(f"_Transcribed:_ {user_text}", parse_mode="Markdown")

    # Telegram Update/Message objects are immutable, so we can't reassign
    # update.message.text. Instead we route the transcribed text through the
    # same reply pipeline directly.
    await _respond(update, update.effective_user.id, user_text)


async def _send_voice(update: Update, text: str) -> None:
    try:
        from tts import xtts_client
        # Speech synthesis is heavy and blocking; keep it off the event loop.
        wav_path = await asyncio.to_thread(xtts_client.synthesize, text)
        with open(wav_path, "rb") as f:
            await update.message.reply_voice(f)
        os.unlink(wav_path)
    except Exception as e:
        # e.g. Farsi text (unsupported by XTTS v2) or missing voice sample.
        logger.warning("TTS skipped: %s", e)


async def handle_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _histories.pop(update.effective_user.id, None)
    await update.message.reply_text(
        "Conversation history cleared. (Long-term memory is kept.)"
    )


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I'm your personal AI clone. Send me a text or voice message.\n\n"
        "Commands:\n"
        "/reset — clear the current conversation history"
    )
