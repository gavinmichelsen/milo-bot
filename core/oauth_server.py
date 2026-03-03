"""
Lightweight aiohttp web server for OAuth callbacks.

Runs alongside the Telegram polling bot to receive
OAuth redirects from Whoop (and later Withings).
"""

import os
import socket
from typing import Optional

import aiohttp
from aiohttp import web

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
    from core.oauth_state import validate_state

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

    # Validate state from in-memory store
    telegram_id = validate_state(state)
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
        from core.database import store_whoop_tokens
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


async def debug_dns(request):
    """Diagnostic endpoint to test DNS and outbound connectivity."""
    results = {}

    # Test 1: Raw DNS resolution
    supabase_url = os.getenv("SUPABASE_URL", "")
    hostname = supabase_url.replace("https://", "").replace("http://", "").strip("/")
    try:
        ips = socket.getaddrinfo(hostname, 443)
        results["dns_resolve"] = f"OK — {hostname} -> {ips[0][4][0]}"
    except Exception as e:
        results["dns_resolve"] = f"FAIL — {hostname}: {e}"

    # Test 2: Can we resolve api.telegram.org (known working)?
    try:
        ips = socket.getaddrinfo("api.telegram.org", 443)
        results["dns_telegram"] = f"OK — api.telegram.org -> {ips[0][4][0]}"
    except Exception as e:
        results["dns_telegram"] = f"FAIL — {e}"

    # Test 3: Can we resolve google.com?
    try:
        ips = socket.getaddrinfo("google.com", 443)
        results["dns_google"] = f"OK — google.com -> {ips[0][4][0]}"
    except Exception as e:
        results["dns_google"] = f"FAIL — {e}"

    # Test 4: Actual HTTP request to Supabase
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{supabase_url}/rest/v1/", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                results["http_supabase"] = f"OK — status {resp.status}"
    except Exception as e:
        results["http_supabase"] = f"FAIL — {type(e).__name__}: {e}"

    # Test 5: Check /etc/resolv.conf
    try:
        with open("/etc/resolv.conf") as f:
            results["resolv_conf"] = f.read().strip()
    except Exception as e:
        results["resolv_conf"] = f"Cannot read: {e}"

    text = "\n".join(f"{k}: {v}" for k, v in results.items())
    logger.info(f"DNS diagnostic results:\n{text}")
    return web.Response(text=text, content_type="text/plain")


async def health(request):
    """Health check endpoint for Railway."""
    return web.Response(text="ok")


async def withings_callback(request):
    """Handle the Withings OAuth callback."""
    from core.oauth_state import validate_state
    from integrations.withings import exchange_token as withings_exchange_token

    error = request.query.get("error")
    if error:
        logger.warning(f"Withings OAuth error: {error}")
        return web.Response(
            text="Authorization denied. You can close this window and try /connectwithings again in Telegram.",
            content_type="text/html",
            status=400,
        )

    code = request.query.get("code")
    state = request.query.get("state")

    if not code or not state:
        return web.Response(text="Missing code or state parameter.", status=400)

    telegram_id = validate_state(state)
    if telegram_id is None:
        logger.warning(f"Invalid or expired Withings OAuth state: {state}")
        return web.Response(
            text="This link has expired. Please run /connectwithings again in Telegram.",
            content_type="text/html",
            status=400,
        )

    # Exchange code immediately — Withings codes expire in 30 seconds
    try:
        token_data = await withings_exchange_token(code)
    except Exception as e:
        logger.error(f"Withings token exchange failed: {e}")
        return web.Response(
            text="Something went wrong connecting your Withings. Please try /connectwithings again.",
            content_type="text/html",
            status=500,
        )

    try:
        from core.database import store_withings_tokens
        store_withings_tokens(telegram_id, token_data)
    except Exception as e:
        logger.error(f"Failed to store Withings tokens for {telegram_id}: {e}")
        return web.Response(
            text="Failed to save your connection. Please try again.",
            content_type="text/html",
            status=500,
        )

    if _bot:
        try:
            await _bot.send_message(
                chat_id=telegram_id,
                text=(
                    "Your Withings scale is now connected!\n\n"
                    "I can see your weight and body composition data. "
                    "Try /stats to see your latest metrics."
                ),
            )
        except Exception as e:
            logger.error(f"Failed to send Telegram confirmation to {telegram_id}: {e}")

    return web.Response(
        text=(
            "<html><body style='font-family:sans-serif;text-align:center;padding:60px;'>"
            "<h2>Withings Connected!</h2>"
            "<p>You can close this window and return to Telegram.</p>"
            "</body></html>"
        ),
        content_type="text/html",
    )


def create_web_app():
    """Create and configure the aiohttp web application."""
    app = web.Application()
    app.router.add_get("/auth/whoop/callback", whoop_callback)
    app.router.add_get("/auth/withings/callback", withings_callback)
    app.router.add_get("/health", health)
    app.router.add_get("/debug/dns", debug_dns)
    return app
