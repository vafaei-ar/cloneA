"""Telegram message handlers."""
import os
import tempfile
import logging

from telegram import Update
from telegram.ext import ContextTypes

import config
from llm import ollama_client
from memory import rag

logger = logging.getLogger(__name__)

# Per-user in-memory conversation history (cleared on restart)
_histories: dict[int, list[dict]] = {}


def _history(user_id: int) -> list[dict]:
    if user_id not in _histories:
        _histories[user_id] = []
    return _histories[user_id]


def _build_messages(user_id: int, user_text: str) -> list[dict]:
    mem_ctx = rag.build_memory_context(user_text)
    system = config.SYSTEM_PROMPT
    if mem_ctx:
        system = system + "\n\n" + mem_ctx

    messages = [{"role": "system", "content": system}]
    messages.extend(_history(user_id))
    messages.append({"role": "user", "content": user_text})
    return messages


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text.strip()

    await update.message.chat.send_action("typing")
    messages = _build_messages(user_id, user_text)

    try:
        reply = ollama_client.chat(messages)
    except Exception as e:
        logger.error("Ollama error: %s", e)
        await update.message.reply_text("Sorry, I couldn't reach the LLM. Is Ollama running?")
        return

    hist = _history(user_id)
    hist.append({"role": "user", "content": user_text})
    hist.append({"role": "assistant", "content": reply})
    # Keep last 20 turns to avoid unbounded growth
    _histories[user_id] = hist[-40:]

    rag.store(f"User: {user_text}\nAssistant: {reply}", metadata={"user_id": str(user_id)})

    # Send text reply
    await update.message.reply_text(reply)

    # If TTS is available and voice sample exists, also send a voice note
    if os.path.exists(config.VOICE_SAMPLE_PATH):
        await _send_voice(update, reply)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.chat.send_action("typing")

    voice_file = await update.message.voice.get_file()
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        ogg_path = tmp.name
    await voice_file.download_to_drive(ogg_path)

    try:
        from stt import whisper_client
        user_text = whisper_client.transcribe(ogg_path)
    except Exception as e:
        logger.error("Whisper error: %s", e)
        await update.message.reply_text("Sorry, I couldn't transcribe your voice message.")
        return
    finally:
        os.unlink(ogg_path)

    if not user_text:
        await update.message.reply_text("I couldn't make out what you said.")
        return

    await update.message.reply_text(f"_Transcribed:_ {user_text}", parse_mode="Markdown")

    # Re-use text handler logic
    update.message.text = user_text
    await handle_text(update, context)


async def _send_voice(update: Update, text: str) -> None:
    try:
        from tts import xtts_client
        wav_path = xtts_client.synthesize(text)
        with open(wav_path, "rb") as f:
            await update.message.reply_voice(f)
        os.unlink(wav_path)
    except Exception as e:
        logger.warning("TTS skipped: %s", e)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I'm your personal AI clone. Send me a text or voice message."
    )
