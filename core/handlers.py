"""
Telegram command handlers for Milo bot.

Each handler corresponds to a bot command (/start, /help, etc.)
and is registered in bot.py. Conversational messages are routed
to the Claude agent for AI coaching responses.
"""

import os

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from agent import get_coaching_response
from core.database import upsert_user, get_whoop_tokens, get_withings_tokens
from core.oauth_state import create_state
from integrations.whoop import WhoopClient
from utils.logger import setup_logger

logger = setup_logger("milo.handlers")

# --- Welcome message inspired by Milo of Croton ---
WELCOME_MESSAGE = """
Welcome to *Milo* — your AI physique and health coach.

_In ancient Greece, Milo of Croton built legendary strength by carrying a calf on his shoulders every single day. As the calf grew into a bull, so did Milo's strength. This is the principle of progressive overload — small, consistent effort that compounds into extraordinary results._

That's exactly how I coach. I help you build your best physique and optimize your health through:

- *Resistance Training* — progressive overload, program design, and load management
- *Sleep* — recovery optimization using your Whoop data
- *Nutrition* — body composition focused eating, protein targets, and meal timing
- *Lifestyle* — stress management, HRV trends, and daily habits

Connect your *Whoop* and *Withings* devices so I can coach you with real data. Every recommendation I make is backed by your numbers.

Type /connect to link your devices, or just start chatting — I'm here to coach you.
"""

HELP_MESSAGE = """
*Milo Commands*

/start — Meet Milo and get started
/connect — Connect Whoop and Withings devices
/stats — View your latest health and body metrics
/progress — See your progress over time
/log — Log a workout (e.g. `bench press 3x5 185lbs`)
/help — Show this help message

You can also just *send me a message* and I'll coach you on training, nutrition, sleep, or lifestyle.
"""


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command — save the user to Supabase and send welcome message."""
    user = update.effective_user
    logger.info(f"/start from user {user.id}")

    # Save or update the user in Supabase
    try:
        upsert_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
    except Exception as e:
        logger.error(f"Failed to save user {user.id} to Supabase: {e}")

    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")


async def connect_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /connect command — show buttons for Whoop and Withings."""
    from integrations.whoop import WhoopClient
    from integrations.withings import get_auth_url as withings_auth_url

    telegram_id = update.effective_user.id
    logger.info(f"/connect from user {telegram_id}")

    try:
        state = create_state(telegram_id)

        whoop = WhoopClient()
        whoop_url = whoop.get_auth_url(
            os.getenv(
                "WHOOP_REDIRECT_URI",
                "https://worker-production-526b.up.railway.app/auth/whoop/callback",
            ),
            state,
        )
        withings_url = withings_auth_url(state)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Connect Whoop", url=whoop_url)],
            [InlineKeyboardButton("Connect Withings", url=withings_url)],
        ])

        await update.message.reply_text(
            "Connect your health devices to Milo:",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"/connect failed for {telegram_id}: {e}")
        await update.message.reply_text(
            "Something went wrong. Please try /connect again in a moment."
        )


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /stats command — fetch and display Whoop + Withings data."""
    from integrations.withings import get_latest_measurements

    telegram_id = update.effective_user.id
    logger.info(f"/stats from user {telegram_id}")

    lines = []

    # --- Whoop recovery data ---
    try:
        whoop_tokens = get_whoop_tokens(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch Whoop tokens for {telegram_id}: {e}")
        whoop_tokens = None

    if whoop_tokens and whoop_tokens.get("access_token"):
        try:
            whoop = WhoopClient()
            try:
                recovery_data = await whoop.get_recovery(whoop_tokens["access_token"])
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    # Token expired — refresh and retry once
                    logger.info(f"Whoop 401 for {telegram_id}, refreshing token...")
                    from integrations.whoop import refresh_whoop_token
                    from core.database import store_whoop_tokens
                    new_tokens = await refresh_whoop_token(whoop_tokens["refresh_token"])
                    store_whoop_tokens(telegram_id, new_tokens)
                    recovery_data = await whoop.get_recovery(new_tokens["access_token"])
                else:
                    raise
            await whoop.close()

            records = recovery_data.get("records", [])
            if records:
                score = records[0].get("score", {})
                recovery_score = score.get("recovery_score")
                hrv = score.get("hrv_rmssd_milli")
                resting_hr = score.get("resting_heart_rate")

                if recovery_score is not None:
                    lines.append(f"\U0001f7e2 Recovery Score: {recovery_score:.0f}%")
                if hrv is not None:
                    lines.append(f"\u2764\ufe0f HRV: {hrv:.0f}ms")
                if resting_hr is not None:
                    lines.append(f"\U0001f4a4 Resting HR: {resting_hr:.0f}bpm")
        except Exception as e:
            logger.error(f"Whoop API call failed for {telegram_id}: {e}")

    # --- Withings body data ---
    try:
        withings_tokens = get_withings_tokens(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch Withings tokens for {telegram_id}: {e}")
        withings_tokens = None

    if withings_tokens and withings_tokens.get("access_token"):
        try:
            measurements = await get_latest_measurements(withings_tokens["access_token"])
            weight = measurements.get("weight_lbs")
            fat = measurements.get("fat_ratio")

            if weight is not None:
                lines.append(f"\u2696\ufe0f Weight: {weight} lbs")
            if fat is not None:
                lines.append(f"\U0001f4ca Body Fat: {fat}%")
        except Exception as e:
            logger.error(f"Withings API call failed for {telegram_id}: {e}")

    # --- Send response ---
    if lines:
        await update.message.reply_text("\n".join(lines))
    elif not whoop_tokens and not withings_tokens:
        await update.message.reply_text(
            "You haven't connected any devices yet. Use /connect to get started."
        )
    else:
        await update.message.reply_text(
            "No data available yet. Make sure you're wearing your devices."
        )


async def progress_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /progress command to show trends over time."""
    logger.info(f"/progress from user {update.effective_user.id}")
    await update.message.reply_text(
        "Progress tracking coming soon.\n\n"
        "This will show your trends over time — strength PRs, "
        "body composition changes, sleep improvements, and recovery patterns.",
        parse_mode="Markdown",
    )


async def log_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /log command to record a workout."""
    logger.info(f"/log from user {update.effective_user.id}")
    await update.message.reply_text(
        "To log a workout, send a message like:\n\n"
        "`/log bench press 3x5 185lbs`\n"
        "`/log squat 5x5 225lbs`\n"
        "`/log deadlift 1x5 315lbs`\n\n"
        "I'll track your lifts and monitor your progressive overload over time.",
        parse_mode="Markdown",
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command with a list of all commands."""
    logger.info(f"/help from user {update.effective_user.id}")
    await update.message.reply_text(HELP_MESSAGE, parse_mode="Markdown")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle free-form text messages by routing them to the Claude agent."""
    user = update.effective_user
    user_message = update.message.text
    logger.info(f"Message from {user.id}: {user_message[:50]}...")

    # Build user context for the coaching agent
    user_context = {
        "telegram_id": user.id,
        "username": user.username or user.first_name,
        "whoop_data": None,     # TODO: Fetch from Supabase
        "withings_data": None,  # TODO: Fetch from Supabase
        "workout_history": [],  # TODO: Fetch from Supabase
    }

    response = await get_coaching_response(user_message, user_context)

    # Try Markdown first, fall back to plain text if Telegram rejects the formatting
    try:
        await update.message.reply_text(response, parse_mode="Markdown")
    except BadRequest:
        await update.message.reply_text(response)
