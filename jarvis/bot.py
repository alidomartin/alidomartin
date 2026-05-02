"""
J.A.R.V.I.S. — Telegram Bot Entry Point
Just A Rather Very Intelligent System

Run:
    pip install -r requirements.txt
    cp .env.example .env   # fill in your tokens
    python bot.py
"""

import logging
import sys

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
from handlers import (
    cmd_start,
    cmd_help,
    cmd_status,
    cmd_clear,
    cmd_mode,
    cmd_voice,
    cmd_briefing,
    handle_text,
    handle_voice,
)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.critical(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Copy .env.example to .env and fill in your tokens."
        )
        sys.exit(1)

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # ── Command handlers ───────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("mode", cmd_mode))
    app.add_handler(CommandHandler("voice", cmd_voice))
    app.add_handler(CommandHandler("briefing", cmd_briefing))

    # ── Message handlers ───────────────────────────────────────────────────────
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("J.A.R.V.I.S. is online and standing by...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
