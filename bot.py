"""
Milo Bot — AI Physique and Health Coach for Telegram.

Main entry point that initializes the Telegram bot, registers
command handlers, starts the OAuth callback web server, and
begins polling for messages.

Inspired by Milo of Croton, the ancient Greek wrestler who built
legendary strength through progressive overload.
"""

import asyncio
import os
import signal

from aiohttp import web
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
from core.oauth_server import create_web_app, set_bot
from core.scheduler import start_scheduler
from utils.logger import setup_logger

load_dotenv()

logger = setup_logger("milo.bot")


async def main():
    """Initialize and run the Milo Telegram bot with OAuth web server."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set. Add it to your .env file.")
        return

    logger.info("Starting Milo bot...")

    # Build the Telegram application
    tg_app = ApplicationBuilder().token(token).build()

    # Register command handlers
    tg_app.add_handler(CommandHandler("start", start_handler))
    tg_app.add_handler(CommandHandler("connect", connect_handler))
    tg_app.add_handler(CommandHandler("stats", stats_handler))
    tg_app.add_handler(CommandHandler("progress", progress_handler))
    tg_app.add_handler(CommandHandler("log", log_handler))
    tg_app.add_handler(CommandHandler("help", help_handler))

    # Conversational handler — routes all other text to the AI agent
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Initialize the Telegram application
    await tg_app.initialize()
    await tg_app.start()

    # Give the OAuth callback server access to the bot for sending messages
    set_bot(tg_app.bot)

    # Start scheduled jobs
    await start_scheduler(tg_app)

    # Set up the aiohttp web server for OAuth callbacks
    web_app = create_web_app()
    runner = web.AppRunner(web_app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"OAuth callback server listening on port {port}")

    # Start Telegram polling
    await tg_app.updater.start_polling(drop_pending_updates=True)
    logger.info("Milo is live. Polling for messages...")

    # Keep running until SIGINT/SIGTERM
    stop_event = asyncio.Event()

    def _signal_handler():
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    await stop_event.wait()

    # Graceful shutdown
    logger.info("Shutting down...")
    await tg_app.updater.stop()
    await tg_app.stop()
    await tg_app.shutdown()
    await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
