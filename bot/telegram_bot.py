import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import config
from bot.handlers import handle_text, handle_voice, handle_start, handle_reset

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def run() -> None:
    if not config.TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN is not set. Copy .env.example to .env and fill it in.")

    app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("reset", handle_reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logger.info("Bot starting — model: %s", config.OLLAMA_MODEL)
    app.run_polling(drop_pending_updates=True)
