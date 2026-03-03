"""
Telegram command handlers for Milo bot.

Each handler corresponds to a bot command (/start, /help, etc.)
and is registered in bot.py. Conversational messages are routed
to the Claude agent for AI coaching responses.
"""

import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from agent import get_coaching_response
from core.database import upsert_user
from core.oauth_state import create_state
from integrations.whoop import WhoopClient
from utils.logger import setup_logger

WHOOP_REDIRECT_URI = os.getenv(
    "WHOOP_REDIRECT_URI",
    "https://worker-production-526b.up.railway.app/auth/whoop/callback",
)

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
    """Handle the /connect command — generate Whoop OAuth link."""
    telegram_id = update.effective_user.id
    logger.info(f"/connect from user {telegram_id}")

    try:
        # Generate in-memory OAuth state (no database dependency)
        state = create_state(telegram_id)

        whoop = WhoopClient()
        auth_url = whoop.get_auth_url(WHOOP_REDIRECT_URI, state)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Connect Whoop", url=auth_url)]
        ])

        await update.message.reply_text(
            "Tap the button below to connect your Whoop account.\n\n"
            "You'll be redirected to Whoop to authorize access to your "
            "recovery, sleep, and workout data.",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"/connect failed for {telegram_id}: {e}")
        await update.message.reply_text(
            "Something went wrong. Please try /connect again in a moment."
        )


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /stats command to show latest metrics."""
    logger.info(f"/stats from user {update.effective_user.id}")
    await update.message.reply_text(
        "Stats dashboard coming soon.\n\n"
        "This will show your latest Whoop recovery, HRV, resting heart rate, "
        "Withings weight, body fat %, and recent training volume.",
        parse_mode="Markdown",
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
