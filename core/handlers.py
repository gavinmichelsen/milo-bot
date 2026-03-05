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
from core.database import upsert_user, get_whoop_tokens, get_withings_tokens, store_whoop_tokens
from core.oauth_state import create_state
from core.user_context import build_user_context
from integrations.whoop import WhoopClient, refresh_whoop_token, kilojoules_to_calories
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
/stats — Full health dashboard (recovery, sleep, strain, body)
/sleep — Detailed sleep breakdown
/strain — Daily strain and calorie burn
/workout — Latest workout details
/body — Body measurements
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
        whoop_state = create_state(telegram_id)
        withings_state = create_state(telegram_id)

        whoop = WhoopClient()
        whoop_url = whoop.get_auth_url(
            os.getenv(
                "WHOOP_REDIRECT_URI",
                "https://worker-production-526b.up.railway.app/auth/whoop/callback",
            ),
            whoop_state,
        )
        withings_url = withings_auth_url(withings_state)

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
    """Handle the /stats command — full health dashboard."""
    from integrations.withings import get_latest_measurements, refresh_withings_token
    from core.database import store_withings_tokens

    telegram_id = update.effective_user.id
    logger.info(f"/stats from user {telegram_id}")

    lines = ["\U0001f4ca *Health Dashboard*", ""]

    # --- Whoop data ---
    try:
        whoop_tokens = get_whoop_tokens(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch Whoop tokens for {telegram_id}: {e}")
        whoop_tokens = None

    if whoop_tokens and whoop_tokens.get("access_token"):
        whoop = WhoopClient()
        access_token = whoop_tokens["access_token"]

        try:
            # Recovery
            try:
                recovery_data = await _whoop_api_call(whoop, access_token, telegram_id, whoop.get_recovery)
                records = recovery_data.get("records", [])
                if records:
                    score = records[0].get("score", {})
                    recovery_score = score.get("recovery_score")
                    hrv = score.get("hrv_rmssd_milli")
                    resting_hr = score.get("resting_heart_rate")

                    lines.append("*Recovery*")
                    if recovery_score is not None:
                        lines.append(f"  \U0001f7e2 Score: {recovery_score:.0f}%")
                    if hrv is not None:
                        lines.append(f"  \u2764\ufe0f HRV: {hrv:.0f}ms")
                    if resting_hr is not None:
                        lines.append(f"  \U0001f4a4 Resting HR: {resting_hr:.0f}bpm")
                    lines.append("")
            except Exception as e:
                logger.error(f"Stats recovery fetch failed for {telegram_id}: {e}")

            # Sleep summary
            try:
                sleep_data = await _whoop_api_call(whoop, access_token, telegram_id, whoop.get_sleep)
                records = sleep_data.get("records", [])
                if records:
                    score = records[0].get("score", {})
                    perf = score.get("sleep_performance_percentage")
                    stages = score.get("stage_summary", {})
                    total_bed = stages.get("total_in_bed_time_milli")

                    lines.append("*Sleep*")
                    if perf is not None:
                        lines.append(f"  Performance: {perf:.0f}%")
                    if total_bed is not None:
                        lines.append(f"  Time in bed: {_ms_to_hours_mins(total_bed)}")
                    lines.append("")
            except Exception as e:
                logger.error(f"Stats sleep fetch failed for {telegram_id}: {e}")

            # Strain summary
            try:
                cycles_data = await _whoop_api_call(whoop, access_token, telegram_id, whoop.get_cycles)
                records = cycles_data.get("records", [])
                if records:
                    score = records[0].get("score", {})
                    strain = score.get("strain")
                    kj = score.get("kilojoule")
                    calories = kilojoules_to_calories(kj) if kj else None

                    lines.append("*Strain*")
                    if strain is not None:
                        lines.append(f"  \U0001f525 Score: {strain:.1f}")
                    if calories is not None:
                        lines.append(f"  Calories: {calories:.0f} cal")
                    lines.append("")
            except Exception as e:
                logger.error(f"Stats strain fetch failed for {telegram_id}: {e}")

        except Exception as e:
            logger.error(f"Whoop API failed for {telegram_id}: {e}")
        finally:
            await whoop.close()

    # --- Withings body data ---
    try:
        withings_tokens = get_withings_tokens(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch Withings tokens for {telegram_id}: {e}")
        withings_tokens = None

    if withings_tokens and withings_tokens.get("access_token"):
        try:
            try:
                measurements = await get_latest_measurements(withings_tokens["access_token"])
            except Exception as e:
                if "invalid_token" in str(e) or "401" in str(e):
                    logger.info(f"Withings token expired for {telegram_id}, refreshing...")
                    new_tokens = await refresh_withings_token(withings_tokens["refresh_token"])
                    store_withings_tokens(telegram_id, new_tokens)
                    measurements = await get_latest_measurements(new_tokens["access_token"])
                else:
                    raise

            weight = measurements.get("weight_lbs")
            fat = measurements.get("fat_ratio")

            if weight is not None or fat is not None:
                lines.append("*Body*")
                if weight is not None:
                    lines.append(f"  \u2696\ufe0f Weight: {weight} lbs")
                if fat is not None:
                    lines.append(f"  Body fat: {fat}%")
        except Exception as e:
            logger.error(f"Withings API call failed for {telegram_id}: {e}")

    # --- Send response ---
    if len(lines) > 2:
        lines.append("\n_Use /sleep /strain /workout /body for details_")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    elif not whoop_tokens and not withings_tokens:
        await update.message.reply_text(
            "You haven't connected any devices yet. Use /connect to get started."
        )
    else:
        await update.message.reply_text(
            "No data available yet. Make sure you're wearing your devices."
        )


def _ms_to_hours_mins(ms: int | None) -> str:
    """Convert milliseconds to 'Xh Ym' format."""
    if ms is None:
        return "N/A"
    total_mins = ms // 60000
    hours = total_mins // 60
    mins = total_mins % 60
    return f"{hours}h {mins}m"


async def _get_whoop_access(telegram_id: int, update: Update) -> tuple[WhoopClient, str] | None:
    """Get a WhoopClient with a valid access token, refreshing if needed.

    Returns (whoop_client, access_token) or None if not connected.
    """
    try:
        whoop_tokens = get_whoop_tokens(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch Whoop tokens for {telegram_id}: {e}")
        return None

    if not whoop_tokens or not whoop_tokens.get("access_token"):
        await update.message.reply_text(
            "Whoop not connected. Use /connect to link your Whoop."
        )
        return None

    return WhoopClient(), whoop_tokens["access_token"]


async def _whoop_api_call(whoop: WhoopClient, access_token: str, telegram_id: int, api_method, *args):
    """Call a Whoop API method with automatic token refresh on 401."""
    try:
        return await api_method(access_token, *args)
    except httpx.HTTPStatusError as e:
        if e.response.status_code != 401:
            raise
        logger.info(f"Whoop 401 for {telegram_id}, refreshing token...")
        whoop_tokens = get_whoop_tokens(telegram_id)
        new_tokens = await refresh_whoop_token(whoop_tokens["refresh_token"])
        store_whoop_tokens(telegram_id, new_tokens)
        return await api_method(new_tokens["access_token"], *args)


async def sleep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /sleep command — show detailed Whoop sleep data."""
    telegram_id = update.effective_user.id
    logger.info(f"/sleep from user {telegram_id}")

    result = await _get_whoop_access(telegram_id, update)
    if not result:
        return
    whoop, access_token = result

    try:
        sleep_data = await _whoop_api_call(whoop, access_token, telegram_id, whoop.get_sleep)
        await whoop.close()

        records = sleep_data.get("records", [])
        if not records:
            await update.message.reply_text("No sleep data available yet.")
            return

        score = records[0].get("score", {})
        stages = score.get("stage_summary", {})
        sleep_needed = score.get("sleep_needed", {})

        perf = score.get("sleep_performance_percentage")
        eff = score.get("sleep_efficiency_percentage")
        resp_rate = score.get("respiratory_rate")

        total_bed = stages.get("total_in_bed_time_milli")
        awake = stages.get("total_awake_time_milli")
        light = stages.get("total_light_sleep_time_milli")
        deep = stages.get("total_slow_wave_sleep_time_milli")
        rem = stages.get("total_rem_sleep_time_milli")
        cycles = stages.get("sleep_cycle_count")
        disturbances = stages.get("disturbance_count")

        debt = sleep_needed.get("need_from_sleep_debt_milli")

        lines = ["\U0001f4a4 *Sleep Report*", ""]
        if perf is not None:
            lines.append(f"Performance: *{perf:.0f}%*")
        if eff is not None:
            lines.append(f"Efficiency: *{eff:.0f}%*")
        if total_bed is not None:
            lines.append(f"Time in bed: {_ms_to_hours_mins(total_bed)}")
        if awake is not None:
            lines.append(f"Awake: {_ms_to_hours_mins(awake)}")

        lines.append("")
        lines.append("*Sleep Stages*")
        if light is not None:
            lines.append(f"  Light: {_ms_to_hours_mins(light)}")
        if deep is not None:
            lines.append(f"  Deep (SWS): {_ms_to_hours_mins(deep)}")
        if rem is not None:
            lines.append(f"  REM: {_ms_to_hours_mins(rem)}")
        if cycles is not None:
            lines.append(f"  Cycles: {cycles}")
        if disturbances is not None:
            lines.append(f"  Disturbances: {disturbances}")

        if resp_rate is not None:
            lines.append(f"\nRespiratory rate: {resp_rate:.1f} rpm")
        if debt is not None and debt > 0:
            lines.append(f"Sleep debt: {_ms_to_hours_mins(debt)}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"/sleep failed for {telegram_id}: {e}")
        await update.message.reply_text("Failed to fetch sleep data. Try again later.")


async def strain_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /strain command — show daily strain and calorie data."""
    telegram_id = update.effective_user.id
    logger.info(f"/strain from user {telegram_id}")

    result = await _get_whoop_access(telegram_id, update)
    if not result:
        return
    whoop, access_token = result

    try:
        cycles_data = await _whoop_api_call(whoop, access_token, telegram_id, whoop.get_cycles)
        await whoop.close()

        records = cycles_data.get("records", [])
        if not records:
            await update.message.reply_text("No strain data available yet.")
            return

        score = records[0].get("score", {})
        strain = score.get("strain")
        kj = score.get("kilojoule")
        calories = kilojoules_to_calories(kj) if kj else None
        avg_hr = score.get("average_heart_rate")
        max_hr = score.get("max_heart_rate")

        lines = ["\U0001f525 *Daily Strain*", ""]
        if strain is not None:
            lines.append(f"Strain: *{strain:.1f}*")
        if calories is not None:
            lines.append(f"Calories burned: {calories:.0f} cal")
        if kj is not None:
            lines.append(f"Kilojoules: {kj:.0f} kJ")
        if avg_hr is not None:
            lines.append(f"Avg heart rate: {avg_hr:.0f} bpm")
        if max_hr is not None:
            lines.append(f"Max heart rate: {max_hr:.0f} bpm")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"/strain failed for {telegram_id}: {e}")
        await update.message.reply_text("Failed to fetch strain data. Try again later.")


async def workout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /workout command — show latest Whoop workout details."""
    telegram_id = update.effective_user.id
    logger.info(f"/workout from user {telegram_id}")

    result = await _get_whoop_access(telegram_id, update)
    if not result:
        return
    whoop, access_token = result

    try:
        workout_data = await _whoop_api_call(whoop, access_token, telegram_id, whoop.get_workouts)
        await whoop.close()

        records = workout_data.get("records", [])
        if not records:
            await update.message.reply_text("No workout data available yet.")
            return

        record = records[0]
        score = record.get("score", {})
        strain = score.get("strain")
        kj = score.get("kilojoule")
        calories = kilojoules_to_calories(kj) if kj else None
        avg_hr = score.get("average_heart_rate")
        max_hr = score.get("max_heart_rate")
        distance = score.get("distance_meter")
        altitude = score.get("altitude_gain_meter")
        zone_durations = score.get("zone_duration_milliseconds", {})

        lines = ["\U0001f3cb\ufe0f *Latest Workout*", ""]
        if strain is not None:
            lines.append(f"Strain: *{strain:.1f}*")
        if calories is not None:
            lines.append(f"Calories: {calories:.0f} cal")
        if avg_hr is not None:
            lines.append(f"Avg HR: {avg_hr:.0f} bpm")
        if max_hr is not None:
            lines.append(f"Max HR: {max_hr:.0f} bpm")
        if distance is not None and distance > 0:
            lines.append(f"Distance: {distance:.0f}m")
        if altitude is not None and altitude > 0:
            lines.append(f"Altitude gain: {altitude:.0f}m")

        if zone_durations:
            lines.append("")
            lines.append("*HR Zones*")
            zone_names = ["Zone 1 (rest)", "Zone 2 (light)", "Zone 3 (moderate)", "Zone 4 (hard)", "Zone 5 (max)"]
            for i, name in enumerate(zone_names):
                zone_ms = zone_durations.get(str(i)) or zone_durations.get(i)
                if zone_ms and zone_ms > 0:
                    lines.append(f"  {name}: {_ms_to_hours_mins(zone_ms)}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"/workout failed for {telegram_id}: {e}")
        await update.message.reply_text("Failed to fetch workout data. Try again later.")


async def body_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /body command — show Whoop body measurements."""
    telegram_id = update.effective_user.id
    logger.info(f"/body from user {telegram_id}")

    result = await _get_whoop_access(telegram_id, update)
    if not result:
        return
    whoop, access_token = result

    try:
        body_data = await _whoop_api_call(whoop, access_token, telegram_id, whoop.get_body_measurements)
        await whoop.close()

        height_m = body_data.get("height_meter")
        weight_kg = body_data.get("weight_kilogram")
        max_hr = body_data.get("max_heart_rate")

        lines = ["\U0001f4cf *Body Measurements*", ""]
        if height_m is not None:
            feet = round(height_m * 3.28084, 1)
            lines.append(f"Height: {feet} ft ({height_m:.2f}m)")
        if weight_kg is not None:
            lbs = round(weight_kg * 2.20462, 1)
            lines.append(f"Weight: {lbs} lbs ({weight_kg:.1f} kg)")
        if max_hr is not None:
            lines.append(f"Max heart rate: {max_hr:.0f} bpm")

        if len(lines) == 2:
            await update.message.reply_text("No body measurement data available.")
        else:
            await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"/body failed for {telegram_id}: {e}")
        await update.message.reply_text("Failed to fetch body data. Try again later.")


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

    # Build live user context for the coaching agent
    user_context = await build_user_context(
        telegram_id=user.id,
        username=user.username or user.first_name,
    )

    response = await get_coaching_response(user_message, user_context)

    # Try Markdown first, fall back to plain text if Telegram rejects the formatting
    try:
        await update.message.reply_text(response, parse_mode="Markdown")
    except BadRequest:
        await update.message.reply_text(response)
