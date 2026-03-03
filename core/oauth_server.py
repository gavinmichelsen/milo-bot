"""
Lightweight aiohttp web server for OAuth callbacks.

Runs alongside the Telegram polling bot to receive
OAuth redirects from Whoop (and later Withings).
"""

import os
from typing import Optional

from aiohttp import web

from core.database import validate_oauth_state, store_whoop_tokens
from integrations.whoop import WhoopClient
from utils.logger import setup_logger

logger = setup_logger("milo.oauth")

REDIRECT_URI = os.getenv(
    "WHOOP_REDIRECT_URI",
    "https://worker-production-526b.up.railway.app/auth/whoop/callback",
)

# Reference to the Telegram bot, set during startup
_bot = None


def set_bot(bot):
    """Store a reference to the Telegram Bot instance for sending messages."""
    global _bot
    _bot = bot


async def whoop_callback(request):
    """Handle the Whoop OAuth callback.

    Validates the state parameter, exchanges the auth code for tokens,
    stores them in Supabase, and sends a confirmation to the user in Telegram.
    """
    error = request.query.get("error")
    if error:
        logger.warning(f"Whoop OAuth error: {error}")
        return web.Response(
            text="Authorization denied. You can close this window and try /connect again in Telegram.",
            content_type="text/html",
            status=400,
        )

    code = request.query.get("code")
    state = request.query.get("state")

    if not code or not state:
        return web.Response(text="Missing code or state parameter.", status=400)

    # Validate state and get telegram_id
    telegram_id = validate_oauth_state(state)
    if telegram_id is None:
        logger.warning(f"Invalid or expired OAuth state: {state}")
        return web.Response(
            text="This link has expired. Please run /connect again in Telegram.",
            content_type="text/html",
            status=400,
        )

    # Exchange code for tokens
    try:
        whoop = WhoopClient()
        token_data = await whoop.exchange_token(code, REDIRECT_URI)
        await whoop.close()
    except Exception as e:
        logger.error(f"Whoop token exchange failed: {e}")
        return web.Response(
            text="Something went wrong connecting your Whoop. Please try /connect again.",
            content_type="text/html",
            status=500,
        )

    # Store tokens in Supabase
    try:
        store_whoop_tokens(telegram_id, token_data)
    except Exception as e:
        logger.error(f"Failed to store Whoop tokens for {telegram_id}: {e}")
        return web.Response(
            text="Failed to save your connection. Please try again.",
            content_type="text/html",
            status=500,
        )

    # Send confirmation to the user in Telegram
    if _bot:
        try:
            await _bot.send_message(
                chat_id=telegram_id,
                text=(
                    "Your Whoop is now connected!\n\n"
                    "I can see your recovery, sleep, and strain data. "
                    "Try /stats to see your latest metrics, or just ask me "
                    "how your recovery is looking today."
                ),
            )
        except Exception as e:
            logger.error(f"Failed to send Telegram confirmation to {telegram_id}: {e}")

    return web.Response(
        text=(
            "<html><body style='font-family:sans-serif;text-align:center;padding:60px;'>"
            "<h2>Whoop Connected!</h2>"
            "<p>You can close this window and return to Telegram.</p>"
            "</body></html>"
        ),
        content_type="text/html",
    )


async def health(request):
    """Health check endpoint for Railway."""
    return web.Response(text="ok")


def create_web_app():
    """Create and configure the aiohttp web application."""
    app = web.Application()
    app.router.add_get("/auth/whoop/callback", whoop_callback)
    app.router.add_get("/health", health)
    return app
