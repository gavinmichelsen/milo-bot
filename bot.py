"""
Milo Bot — AI Physique and Health Coach for Telegram.

Main entry point that initializes the Telegram bot, registers
command handlers, and starts polling for messages.

Inspired by Milo of Croton, the ancient Greek wrestler who built
legendary strength through progressive overload.
"""

import os

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from core.handlers import (
    start_handler,
    connect_handler,
    stats_handler,
    progress_handler,
    log_handler,
    help_handler,
    message_handler,
)
from core.scheduler import start_scheduler
from utils.logger import setup_logger

load_dotenv()

logger = setup_logger("milo.bot")


def main():
    """Initialize and run the Milo Telegram bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set. Add it to your .env file.")
        return

    logger.info("Starting Milo bot...")

    app = ApplicationBuilder().token(token).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("connect", connect_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("progress", progress_handler))
    app.add_handler(CommandHandler("log", log_handler))
    app.add_handler(CommandHandler("help", help_handler))

    # Conversational handler — routes all other text to the Claude agent
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Start scheduled jobs once the event loop is running
    app.post_init = start_scheduler

    logger.info("Milo is live. Polling for messages...")
    app.run_polling()


if __name__ == "__main__":
    main()
