import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2:7b")

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
# None = auto-detect. Treat an empty value as auto-detect too.
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE") or None

XTTS_MODEL = os.getenv("XTTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")
VOICE_SAMPLE_PATH = os.getenv("VOICE_SAMPLE_PATH", "voice_samples/sample.wav")
# Set TTS_ENABLED=0 to disable voice replies entirely (text only).
TTS_ENABLED = os.getenv("TTS_ENABLED", "1").lower() not in ("0", "false", "no")

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
MEMORY_COLLECTION = os.getenv("MEMORY_COLLECTION", "conversations")

PERSONA_CHATS_DIR = os.getenv("PERSONA_CHATS_DIR", "./chats")

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a helpful AI assistant. Answer in the same language the user writes in (English or Farsi).",
)
