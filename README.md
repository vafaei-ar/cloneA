# cloneA

[![CI](https://github.com/vafaei-ar/cloneA/actions/workflows/ci.yml/badge.svg)](https://github.com/vafaei-ar/cloneA/actions/workflows/ci.yml)

A self-hosted **personal AI clone** that talks to you on Telegram — in text or
voice — using a local LLM, local speech-to-text, and voice-cloned
text-to-speech. It remembers past conversations and can adopt your persona from
your own exported chat history. English and Farsi are both supported for text
and transcription (see the note on voice output below).

Everything runs locally: no data leaves your machine except the Telegram
messages themselves.

## How it works

```
Telegram  ──►  bot/handlers  ──►  Ollama (LLM)  ──►  reply
   ▲   │                              ▲
   │   ├─ voice in ─► faster-whisper (STT) ─┘
   │   └─ reply ────► Coqui XTTS v2 (TTS, voice clone) ─► voice note
   │                              │
   └──────────────────────────────┘
                     memory/rag: ChromaDB long-term memory
                     persona/ingest: seed persona from chat exports
```

| Component | Library | Notes |
|-----------|---------|-------|
| Chat interface | `python-telegram-bot` | Long-polling bot |
| LLM | [Ollama](https://ollama.com) | Runs as a separate local server |
| Speech-to-text | `faster-whisper` | Transcribes voice messages |
| Text-to-speech | Coqui **XTTS v2** | Clones a voice from a short sample |
| Memory / RAG | `chromadb` + `sentence-transformers` | Per-user + shared persona memory |

## Prerequisites

- **Python 3.10 or 3.11** (Coqui `TTS` does **not** support 3.12+).
- **ffmpeg** on your `PATH` (audio decoding for Whisper and Telegram voice notes).
  - macOS: `brew install ffmpeg` · Debian/Ubuntu: `sudo apt install ffmpeg`
- **[Ollama](https://ollama.com)** installed and running, with a model pulled:
  ```bash
  ollama pull qwen2:7b
  ```
- A **Telegram bot token** from [@BotFather](https://t.me/BotFather).
- (Optional, for voice replies) a **~6-second WAV** recording of the voice to clone.

## Setup

```bash
# 1. Clone and enter the project
git clone https://github.com/vafaei-ar/cloneA.git
cd cloneA

# 2. Create a virtual environment (Python 3.10/3.11)
python3.11 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
#   then edit .env and set TELEGRAM_TOKEN (at minimum)

# 5. (Optional) add a voice sample for cloned voice replies
#   place a ~6s WAV at voice_samples/sample.wav
```

## Running

```bash
# Make sure Ollama is running first:  ollama serve
python main.py
```

Then open Telegram, message your bot, and send `/start`.

- Send **text** → get a text reply (and a spoken reply if a voice sample exists).
- Send a **voice note** → it's transcribed, answered, and (optionally) spoken back.
- `/reset` clears the current conversation history (long-term memory is kept).

## Giving it your persona (optional)

Seed the memory with your own chat history so the clone sounds like you:

1. Export a Telegram chat (Telegram Desktop → ⋮ → *Export chat history* →
   JSON or plain text) and drop the files into `chats/`.
   Plain-text lines like `[2024-01-02 10:30] Ali: message` and Telegram JSON
   exports are both supported.
2. Ingest them:
   ```bash
   python main.py --ingest
   ```

Ingested messages are tagged as shared `persona` memory and are retrieved
alongside each user's own conversation history.

## Configuration (`.env`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `TELEGRAM_TOKEN` | — | **Required.** Bot token from BotFather |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2:7b` | Ollama model name |
| `WHISPER_MODEL` | `base` | faster-whisper size (`tiny`…`large-v3`) |
| `WHISPER_LANGUAGE` | auto-detect | Force a language, e.g. `fa`; leave empty to auto-detect |
| `XTTS_MODEL` | `…/xtts_v2` | Coqui TTS model id |
| `VOICE_SAMPLE_PATH` | `voice_samples/sample.wav` | Voice to clone |
| `TTS_ENABLED` | `1` | Set `0` for text-only replies |
| `CHROMA_DB_PATH` | `./chroma_db` | Memory database location |
| `MEMORY_COLLECTION` | `conversations` | Chroma collection name |
| `PERSONA_CHATS_DIR` | `./chats` | Where `--ingest` reads exports |
| `SYSTEM_PROMPT` | see file | Base instruction for the LLM |

## A note on Farsi voice replies

Whisper transcribes Farsi voice input fine, and the LLM answers in Farsi. However
**Coqui XTTS v2 does not support Persian/Farsi**, so Farsi replies are sent as
**text only** — no spoken voice note. English (and the other 16 XTTS languages)
are spoken normally. This is handled gracefully; you don't need to configure
anything.

## Tests

```bash
pip install pytest
pytest -q
```

The tests cover message splitting, per-user memory scoping, TTS language
handling, and persona ingestion, and run without the heavy ML models.

## Project layout

```
main.py               entry point (python main.py [--ingest])
config.py             environment-driven configuration
bot/telegram_bot.py   builds and runs the Telegram app
bot/handlers.py       message pipeline (text + voice)
bot/utils.py          pure helpers (message splitting)
llm/ollama_client.py  Ollama chat API client
stt/whisper_client.py faster-whisper transcription
tts/xtts_client.py    XTTS v2 voice-cloned synthesis
memory/rag.py         ChromaDB long-term memory
persona/ingest.py     import chat exports as persona memory
tests/                unit tests
```

## Troubleshooting

- **"I couldn't reach the LLM. Is Ollama running?"** — start `ollama serve` and
  confirm the model in `OLLAMA_MODEL` is pulled.
- **No voice note comes back** — check a WAV exists at `VOICE_SAMPLE_PATH`, that
  `TTS_ENABLED=1`, and that the reply isn't Farsi (unsupported by XTTS).
- **`TTS` fails to install** — you're likely on Python 3.12+. Use 3.10/3.11.
- **Whisper errors on voice notes** — make sure `ffmpeg` is installed.

## License

MIT — see [LICENSE](LICENSE).
