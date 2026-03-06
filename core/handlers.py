"""
Telegram command handlers for Milo bot.

Each handler corresponds to a bot command (/start, /help, etc.)
and is registered in bot.py. Conversational messages are routed
to the Claude agent for AI coaching responses.
"""

from __future__ import annotations

import os
import re

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from agent import get_coaching_response
from coaching.training import build_training_guidance, check_progressive_overload, format_workout_log
from coaching.progress import build_weekly_progress_summary
from core.database import (
    get_onboarding_state,
    get_nutrition_state,
    get_recent_body_metrics,
    get_recent_recovery_statuses,
    get_recent_whoop_snapshots,
    get_user_profile,
    get_whoop_tokens,
    get_withings_tokens,
    get_workout_history,
    log_workout,
    store_body_metrics,
    store_chat_message,
    store_whoop_snapshot,
    store_whoop_tokens,
    upsert_user,
    upsert_user_profile,
)
from core.onboarding import begin_or_resume_onboarding, needs_onboarding, process_onboarding_message
from core.oauth_state import create_state
from core.user_context import build_user_context
from integrations.whoop import WhoopClient, refresh_whoop_token, kilojoules_to_calories
from utils.helpers import parse_sets_reps
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
/profile — View or update your coaching profile
/help — Show this help message

You can also just *send me a message* and I'll coach you on training, nutrition, sleep, or lifestyle.
"""


PROFILE_FIELD_ALIASES = {
    "sex": "sex",
    "age": "age_years",
    "age_years": "age_years",
    "height": "height_cm",
    "height_cm": "height_cm",
    "weight": "body_weight_lbs",
    "weight_lbs": "body_weight_lbs",
    "bodyfat": "estimated_body_fat_pct",
    "body_fat": "estimated_body_fat_pct",
    "goal": "primary_goal",
    "experience": "experience_level",
    "experience_level": "experience_level",
    "days": "training_days_per_week",
    "training_days": "training_days_per_week",
    "activity": "activity_multiplier",
    "activity_multiplier": "activity_multiplier",
    "nutrition": "nutrition_mode",
    "wake": "target_wake_time",
    "bed": "target_bedtime",
}

PROFILE_ALLOWED_VALUES = {
    "sex": {"male", "female"},
    "primary_goal": {"fat_loss", "maintain", "muscle_gain", "recomp"},
    "experience_level": {"beginner", "intermediate", "advanced"},
    "nutrition_mode": {"tracked", "ad_libitum"},
}


_PROFILE_BOUNDS = {
    "age_years": (13, 120),
    "training_days_per_week": (1, 7),
    "height_cm": (100, 250),
    "body_weight_lbs": (50, 700),
    "estimated_body_fat_pct": (3, 60),
    "activity_multiplier": (1.0, 2.5),
}


def _coerce_profile_value(field: str, raw_value: str):
    if field in {"age_years", "training_days_per_week"}:
        val = int(raw_value)
        lo, hi = _PROFILE_BOUNDS[field]
        if not (lo <= val <= hi):
            raise ValueError(f"{field} must be between {lo} and {hi}")
        return val
    if field in {"height_cm", "body_weight_lbs", "estimated_body_fat_pct", "activity_multiplier"}:
        val = float(raw_value)
        lo, hi = _PROFILE_BOUNDS[field]
        if not (lo <= val <= hi):
            raise ValueError(f"{field} must be between {lo} and {hi}")
        return val
    value = raw_value.lower()
    allowed = PROFILE_ALLOWED_VALUES.get(field)
    if allowed and value not in allowed:
        raise ValueError(f"Invalid value for {field}: {raw_value}")
    return value if allowed else raw_value


def _format_profile(profile: dict | None) -> str:
    if not profile:
        return (
            "No coaching profile saved yet.\n\n"
            "Set one with:\n"
            "/profile sex=male age=32 height_cm=178 goal=fat_loss experience=intermediate days=4 activity=1.55"
        )

    lines = ["Your coaching profile", ""]
    lines.append(f"Sex: {profile.get('sex', 'N/A')}")
    lines.append(f"Age: {profile.get('age_years', 'N/A')}")
    lines.append(f"Height: {profile.get('height_cm', 'N/A')} cm")
    lines.append(f"Weight: {profile.get('body_weight_lbs', 'N/A')} lb")
    lines.append(f"Goal: {profile.get('primary_goal', 'N/A')}")
    lines.append(f"Experience: {profile.get('experience_level', 'N/A')}")
    lines.append(f"Training days: {profile.get('training_days_per_week', 'N/A')}")
    lines.append(f"Activity multiplier: {profile.get('activity_multiplier', 'N/A')}")
    lines.append(f"Nutrition mode: {profile.get('nutrition_mode', 'N/A')}")
    lines.append("")
    lines.append("Update fields with /profile key=value ...")
    return "\n".join(lines)


def _ensure_user_record(user) -> None:
    try:
        upsert_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
    except Exception as e:
        logger.error(f"Failed to save user {user.id} to Supabase: {e}")


async def _reply_markdown(update: Update, text: str) -> None:
    try:
        await update.message.reply_text(text, parse_mode="Markdown")
    except BadRequest:
        await update.message.reply_text(text)


async def _reply_sequence(update: Update, messages) -> None:
    from core.onboarding import OnboardingMessage
    for message in messages:
        if not message:
            continue
        if isinstance(message, OnboardingMessage):
            try:
                await update.message.reply_text(message.text, parse_mode="Markdown", reply_markup=message.reply_markup)
            except BadRequest:
                await update.message.reply_text(message.text, reply_markup=message.reply_markup)
        elif isinstance(message, str):
            await _reply_markdown(update, message)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command — save the user to Supabase and send welcome message."""
    user = update.effective_user
    logger.info(f"/start from user {user.id}")

    _ensure_user_record(user)

    try:
        user_profile = get_user_profile(user.id)
        onboarding_state = get_onboarding_state(user.id)
    except Exception as e:
        logger.error(f"Failed to fetch user onboarding context for {user.id}: {e}")
        user_profile = None
        onboarding_state = None

    if needs_onboarding(user_profile, onboarding_state):
        try:
            onboarding_messages = begin_or_resume_onboarding(user.id)
        except Exception as e:
            logger.error(f"Onboarding flow failed for {user.id}: {e}")
            await update.message.reply_text("I hit a snag while starting your onboarding. Send /start again and I'll keep going.")
            return

        await _reply_sequence(update, onboarding_messages)
        return

    await _reply_markdown(update, WELCOME_MESSAGE)


async def connect_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /connect command — show buttons for Whoop and Withings."""
    from integrations.whoop import WhoopClient
    from integrations.withings import get_auth_url as withings_auth_url

    telegram_id = update.effective_user.id
    logger.info(f"/connect from user {telegram_id}")
    _ensure_user_record(update.effective_user)

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
    has_live_recovery = False
    has_live_sleep = False
    has_live_strain = False
    has_live_body = False

    try:
        recent_whoop_snapshots = get_recent_whoop_snapshots(telegram_id, limit=1)
    except Exception as e:
        logger.error(f"Failed to fetch stored Whoop snapshots for {telegram_id}: {e}")
        recent_whoop_snapshots = []

    try:
        recent_body_metrics = get_recent_body_metrics(telegram_id, limit=1)
    except Exception as e:
        logger.error(f"Failed to fetch stored body metrics for {telegram_id}: {e}")
        recent_body_metrics = []

    try:
        recovery_statuses = get_recent_recovery_statuses(telegram_id, limit=1)
    except Exception as e:
        logger.error(f"Failed to fetch recovery status for {telegram_id}: {e}")
        recovery_statuses = []

    try:
        nutrition_state = get_nutrition_state(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch nutrition state for {telegram_id}: {e}")
        nutrition_state = None

    try:
        user_profile = get_user_profile(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch user profile for {telegram_id}: {e}")
        user_profile = None

    try:
        training_history = get_workout_history(telegram_id, limit=10)
    except Exception as e:
        logger.error(f"Failed to fetch training history for {telegram_id}: {e}")
        training_history = []

    try:
        training_guidance = build_training_guidance(
            recovery_status=recovery_statuses[0] if recovery_statuses else None,
            workout_history=training_history,
            experience_level=(user_profile or {}).get("experience_level"),
        )
    except Exception as e:
        logger.error(f"Failed to build training guidance for {telegram_id}: {e}")
        training_guidance = None

    latest_recovery_status = recovery_statuses[0] if recovery_statuses else None
    if latest_recovery_status or nutrition_state or training_guidance:
        lines.append("*Coaching State*")
        if latest_recovery_status:
            tier = str(latest_recovery_status.get("composite_tier", "N/A")).replace("_", " ")
            training_action = str(latest_recovery_status.get("training_action", "N/A")).replace("_", " ")
            lines.append(f"  Recovery tier: {tier}")
            lines.append(f"  Training action: {training_action}")
        if nutrition_state:
            phase = str(nutrition_state.get("phase", "N/A")).replace("_", " ")
            lines.append(f"  Nutrition phase: {phase}")
            lines.append(f"  Calories: {nutrition_state.get('current_calorie_target', 'N/A')} kcal")
            lines.append(f"  Protein: {nutrition_state.get('current_protein_target_g', 'N/A')} g")
        if training_guidance:
            lines.append(f"  Training phase: {training_guidance.get('phase', 'N/A')}")
            lines.append(f"  Target RIR: {training_guidance.get('target_rir', 'N/A')}")
            lines.append(f"  Session adjustment: {training_guidance.get('session_adjustment', 'N/A')}")
        lines.append("")

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
                    has_live_recovery = True

                    store_whoop_snapshot(
                        telegram_id,
                        {
                            "recovery_score": recovery_score,
                            "hrv": hrv,
                            "resting_hr": resting_hr,
                        },
                    )

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
                    eff = score.get("sleep_efficiency_percentage")
                    resp_rate = score.get("respiratory_rate")
                    has_live_sleep = True

                    total_bed = score.get("stage_summary", {}).get("total_in_bed_time_milli")
                    awake = score.get("stage_summary", {}).get("total_awake_time_milli")
                    light = score.get("stage_summary", {}).get("total_light_sleep_time_milli")
                    deep = score.get("stage_summary", {}).get("total_slow_wave_sleep_time_milli")
                    rem = score.get("stage_summary", {}).get("total_rem_sleep_time_milli")
                    cycles = score.get("stage_summary", {}).get("sleep_cycle_count")
                    disturbances = score.get("stage_summary", {}).get("disturbance_count")

                    debt = score.get("sleep_needed", {}).get("need_from_sleep_debt_milli")
                    sleep_duration_ms = None
                    if any(value is not None for value in (light, deep, rem)):
                        sleep_duration_ms = sum(value or 0 for value in (light, deep, rem))
                    elif total_bed is not None:
                        sleep_duration_ms = total_bed
                    sleep_duration_hrs = round(sleep_duration_ms / 3_600_000, 2) if sleep_duration_ms is not None else None

                    store_whoop_snapshot(
                        telegram_id,
                        {
                            "sleep_duration_hrs": sleep_duration_hrs,
                            "sleep_efficiency_pct": eff,
                            "sleep_performance_pct": perf,
                            "respiratory_rate": resp_rate,
                        },
                    )

                    lines.append("*Sleep*")
                    if perf is not None:
                        lines.append(f"Performance: {perf:.0f}%")
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
                    avg_hr = score.get("average_heart_rate")
                    max_hr = score.get("max_heart_rate")
                    has_live_strain = True

                    store_whoop_snapshot(
                        telegram_id,
                        {
                            "strain": strain,
                        },
                    )

                    lines.append("*Strain*")
                    if strain is not None:
                        lines.append(f"  \U0001f525 Score: {strain:.1f}")
                    if calories is not None:
                        lines.append(f"  Calories: {calories:.0f} cal")
                    if avg_hr is not None:
                        lines.append(f"  Avg HR: {avg_hr:.0f} bpm")
                    if max_hr is not None:
                        lines.append(f"  Max HR: {max_hr:.0f} bpm")

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
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.info(f"Withings token expired for {telegram_id}, refreshing...")
                    new_tokens = await refresh_withings_token(withings_tokens["refresh_token"])
                    store_withings_tokens(telegram_id, new_tokens)
                    measurements = await get_latest_measurements(new_tokens["access_token"])
                else:
                    raise
            except Exception as e:
                if "invalid_token" in str(e):
                    logger.info(f"Withings token expired for {telegram_id}, refreshing...")
                    new_tokens = await refresh_withings_token(withings_tokens["refresh_token"])
                    store_withings_tokens(telegram_id, new_tokens)
                    measurements = await get_latest_measurements(new_tokens["access_token"])
                else:
                    raise

            weight = measurements.get("weight_lbs")
            fat = measurements.get("fat_ratio")

            if weight is not None or fat is not None:
                has_live_body = True
                store_body_metrics(
                    telegram_id,
                    {
                        "weight_lbs": weight,
                        "body_fat_pct": fat,
                    },
                )
                lines.append("*Body*")
                if weight is not None:
                    lines.append(f"  \u2696\ufe0f Weight: {weight} lbs")
                if fat is not None:
                    lines.append(f"  Body fat: {fat}%")

        except Exception as e:
            logger.error(f"Withings API call failed for {telegram_id}: {e}")

    latest_snapshot = recent_whoop_snapshots[0] if recent_whoop_snapshots else None
    if latest_snapshot and not has_live_recovery:
        recovery_score = latest_snapshot.get("recovery_score")
        hrv = latest_snapshot.get("hrv")
        resting_hr = latest_snapshot.get("resting_hr")
        if recovery_score is not None or hrv is not None or resting_hr is not None:
            lines.append("*Recovery*")
            if recovery_score is not None:
                lines.append(f"  \U0001f7e2 Score: {float(recovery_score):.0f}%")
            if hrv is not None:
                lines.append(f"  \u2764\ufe0f HRV: {float(hrv):.0f}ms")
            if resting_hr is not None:
                lines.append(f"  \U0001f4a4 Resting HR: {float(resting_hr):.0f}bpm")
            lines.append("  Source: stored Whoop snapshot")
            lines.append("")

    if latest_snapshot and not has_live_sleep:
        performance = latest_snapshot.get("sleep_performance_pct")
        duration = latest_snapshot.get("sleep_duration_hrs")
        efficiency = latest_snapshot.get("sleep_efficiency_pct")
        if performance is not None or duration is not None or efficiency is not None:
            lines.append("*Sleep*")
            if performance is not None:
                lines.append(f"  Performance: {float(performance):.0f}%")
            if duration is not None:
                lines.append(f"  Sleep duration: {float(duration):.1f}h")
            if efficiency is not None:
                lines.append(f"  Efficiency: {float(efficiency):.0f}%")
            lines.append("  Source: stored Whoop snapshot")
            lines.append("")

    if latest_snapshot and not has_live_strain:
        strain = latest_snapshot.get("strain")
        if strain is not None:
            lines.append("*Strain*")
            lines.append(f"  \U0001f525 Score: {float(strain):.1f}")
            lines.append("  Source: stored Whoop snapshot")
            lines.append("")

    latest_body_metric = recent_body_metrics[0] if recent_body_metrics else None
    if latest_body_metric and not has_live_body:
        weight = latest_body_metric.get("weight_lbs")
        fat = latest_body_metric.get("body_fat_pct")
        if weight is not None or fat is not None:
            lines.append("*Body*")
            if weight is not None:
                lines.append(f"  \u2696\ufe0f Weight: {weight} lbs")
            if fat is not None:
                lines.append(f"  Body fat: {fat}%")
            lines.append("  Source: stored body metrics")

    # --- Send response ---
    if len(lines) > 2:
        lines.append("\n_Use /sleep /strain /workout /body for details_")
        await _reply_markdown(update, "\n".join(lines))
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

    try:
        recent_snapshots = get_recent_whoop_snapshots(telegram_id, limit=1)
    except Exception as e:
        logger.error(f"Failed to fetch stored Whoop snapshots for {telegram_id}: {e}")
        recent_snapshots = []

    result = await _get_whoop_access(telegram_id, update)
    if not result:
        return
    whoop, access_token = result

    try:
        sleep_data = await _whoop_api_call(whoop, access_token, telegram_id, whoop.get_sleep)

        records = sleep_data.get("records", [])
        if records:
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
            sleep_duration_ms = None
            if any(value is not None for value in (light, deep, rem)):
                sleep_duration_ms = sum(value or 0 for value in (light, deep, rem))
            elif total_bed is not None:
                sleep_duration_ms = total_bed
            sleep_duration_hrs = round(sleep_duration_ms / 3_600_000, 2) if sleep_duration_ms is not None else None

            store_whoop_snapshot(
                telegram_id,
                {
                    "sleep_duration_hrs": sleep_duration_hrs,
                    "sleep_efficiency_pct": eff,
                    "sleep_performance_pct": perf,
                    "respiratory_rate": resp_rate,
                },
            )

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

            await _reply_markdown(update, "\n".join(lines))
            return

    except Exception as e:
        logger.error(f"/sleep failed for {telegram_id}: {e}")
    finally:
        await whoop.close()

    if recent_snapshots:
        snapshot = recent_snapshots[0]
        lines = ["\U0001f4a4 *Sleep Report*", ""]
        duration = snapshot.get("sleep_duration_hrs")
        performance = snapshot.get("sleep_performance_pct")
        efficiency = snapshot.get("sleep_efficiency_pct")
        respiratory_rate = snapshot.get("respiratory_rate")
        if performance is not None:
            lines.append(f"Performance: *{float(performance):.0f}%*")
        if efficiency is not None:
            lines.append(f"Efficiency: *{float(efficiency):.0f}%*")
        if duration is not None:
            lines.append(f"Sleep duration: {float(duration):.1f}h")
        if respiratory_rate is not None:
            lines.append(f"Respiratory rate: {float(respiratory_rate):.1f} rpm")
        lines.append("")
        lines.append("Source: stored Whoop snapshot")
        await _reply_markdown(update, "\n".join(lines))
        return

    await update.message.reply_text("Failed to fetch sleep data. Try again later.")


async def strain_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /strain command — show daily strain and calorie data."""
    telegram_id = update.effective_user.id
    logger.info(f"/strain from user {telegram_id}")

    try:
        recent_snapshots = get_recent_whoop_snapshots(telegram_id, limit=1)
    except Exception as e:
        logger.error(f"Failed to fetch stored Whoop snapshots for {telegram_id}: {e}")
        recent_snapshots = []

    result = await _get_whoop_access(telegram_id, update)
    if not result:
        return
    whoop, access_token = result

    try:
        cycles_data = await _whoop_api_call(whoop, access_token, telegram_id, whoop.get_cycles)

        records = cycles_data.get("records", [])
        if records:
            score = records[0].get("score", {})
            strain = score.get("strain")
            kj = score.get("kilojoule")
            calories = kilojoules_to_calories(kj) if kj else None
            avg_hr = score.get("average_heart_rate")
            max_hr = score.get("max_heart_rate")

            store_whoop_snapshot(
                telegram_id,
                {
                    "strain": strain,
                },
            )

            lines = ["\U0001f525 *Daily Strain*", ""]
            if strain is not None:
                lines.append(f"Strain: *{strain:.1f}*")
            if calories is not None:
                lines.append(f"Calories burned: {calories:.0f} cal")
            if avg_hr is not None:
                lines.append(f"Avg HR: {avg_hr:.0f} bpm")
            if max_hr is not None:
                lines.append(f"Max HR: {max_hr:.0f} bpm")

            await _reply_markdown(update, "\n".join(lines))
            return

    except Exception as e:
        logger.error(f"/strain failed for {telegram_id}: {e}")
    finally:
        await whoop.close()

    if recent_snapshots:
        snapshot = recent_snapshots[0]
        strain = snapshot.get("strain")
        lines = ["\U0001f525 *Daily Strain*", ""]
        if strain is not None:
            lines.append(f"Strain: *{float(strain):.1f}*")
        lines.append("Source: stored Whoop snapshot")
        await _reply_markdown(update, "\n".join(lines))
        return

    await update.message.reply_text("Failed to fetch strain data. Try again later.")


async def workout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /workout command — show latest Whoop workout details."""
    telegram_id = update.effective_user.id
    logger.info(f"/workout from user {telegram_id}")

    try:
        logged_workouts = get_workout_history(telegram_id, limit=1) or []
    except Exception as e:
        logger.error(f"Failed to fetch logged workouts for {telegram_id}: {e}")
        logged_workouts = []

    def _manual_workout_reply():
        if not logged_workouts:
            return None
        latest = logged_workouts[0]
        weight = latest.get("weight_lbs", latest.get("weight", 0)) or 0
        lines = ["\U0001f3cb\ufe0f *Latest Workout*", ""]
        lines.append("Source: manual log")
        lines.append(format_workout_log(latest.get("exercise", "workout"), latest.get("sets", 0), latest.get("reps", 0), float(weight)))
        logged_at = latest.get("logged_at")
        if logged_at:
            lines.append(f"Logged at: {logged_at}")
        notes = latest.get("notes")
        if notes:
            lines.append(f"Notes: {notes}")
        return lines

    whoop_tokens = None
    try:
        whoop_tokens = get_whoop_tokens(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch Whoop tokens for {telegram_id}: {e}")

    if whoop_tokens and whoop_tokens.get("access_token"):
        whoop = WhoopClient()
        try:
            workout_data = await _whoop_api_call(whoop, whoop_tokens["access_token"], telegram_id, whoop.get_workouts)
            records = workout_data.get("records", [])
            if records:
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

                await _reply_markdown(update, "\n".join(lines))
                await whoop.close()
                return
        except Exception as e:
            logger.error(f"/workout Whoop fetch failed for {telegram_id}: {e}")
        finally:
            await whoop.close()

    manual_lines = _manual_workout_reply()
    if manual_lines:
        await _reply_markdown(update, "\n".join(manual_lines))
        return

    await update.message.reply_text("No workout data available yet. Use /log to record a workout.")


async def body_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /body command — show Withings body data with Whoop supplemental."""
    from integrations.withings import get_latest_measurements, refresh_withings_token
    from core.database import store_withings_tokens

    telegram_id = update.effective_user.id
    logger.info(f"/body from user {telegram_id}")

    lines = ["\U0001f4cf *Body Measurements*", ""]

    # --- Withings (primary: weight, body fat) ---
    try:
        withings_tokens = get_withings_tokens(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch Withings tokens for {telegram_id}: {e}")
        withings_tokens = None

    try:
        recent_body_metrics = get_recent_body_metrics(telegram_id, limit=1)
    except Exception as e:
        logger.error(f"Failed to fetch stored body metrics for {telegram_id}: {e}")
        recent_body_metrics = []

    if withings_tokens and withings_tokens.get("access_token"):
        try:
            try:
                measurements = await get_latest_measurements(withings_tokens["access_token"])
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.info(f"Withings token expired for {telegram_id}, refreshing...")
                    new_tokens = await refresh_withings_token(withings_tokens["refresh_token"])
                    store_withings_tokens(telegram_id, new_tokens)
                    measurements = await get_latest_measurements(new_tokens["access_token"])
                else:
                    raise
            except Exception as e:
                if "invalid_token" in str(e):
                    logger.info(f"Withings token expired for {telegram_id}, refreshing...")
                    new_tokens = await refresh_withings_token(withings_tokens["refresh_token"])
                    store_withings_tokens(telegram_id, new_tokens)
                    measurements = await get_latest_measurements(new_tokens["access_token"])
                else:
                    raise

            weight = measurements.get("weight_lbs")
            fat = measurements.get("fat_ratio")

            store_body_metrics(
                telegram_id,
                {
                    "weight_lbs": weight,
                    "body_fat_pct": fat,
                },
            )

            if weight is not None:
                lines.append(f"\u2696\ufe0f Weight: {weight} lbs")
            if fat is not None:
                lines.append(f"\U0001f4ca Body fat: {fat}%")
        except Exception as e:
            logger.error(f"Withings body fetch failed for {telegram_id}: {e}")

    if len(lines) == 2 and recent_body_metrics:
        latest_metric = recent_body_metrics[0]
        weight = latest_metric.get("weight_lbs")
        fat = latest_metric.get("body_fat_pct")
        if weight is not None:
            lines.append(f"⚖️ Weight: {weight} lbs")
        if fat is not None:
            lines.append(f"📊 Body fat: {fat}%")
        lines.append("Source: stored body metrics")

    # --- Whoop (supplemental: height, max HR) ---
    try:
        whoop_tokens = get_whoop_tokens(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch Whoop tokens for {telegram_id}: {e}")
        whoop_tokens = None

    if whoop_tokens and whoop_tokens.get("access_token"):
        whoop = WhoopClient()
        try:
            body_data = await _whoop_api_call(whoop, whoop_tokens["access_token"], telegram_id, whoop.get_body_measurements)
            height_m = body_data.get("height_meter")
            max_hr = body_data.get("max_heart_rate")

            if height_m is not None:
                feet = round(height_m * 3.28084, 1)
                lines.append(f"\U0001f4cf Height: {feet} ft ({height_m:.2f}m)")
            if max_hr is not None:
                lines.append(f"\u2764\ufe0f Max heart rate: {max_hr:.0f} bpm")
        except Exception as e:
            logger.error(f"Whoop body fetch failed for {telegram_id}: {e}")
        finally:
            await whoop.close()

    if len(lines) == 2:
        if not withings_tokens and not whoop_tokens:
            await update.message.reply_text("No devices connected. Use /connect to get started.")
        else:
            await update.message.reply_text("No body measurement data available.")
    else:
        await _reply_markdown(update, "\n".join(lines))


async def progress_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /progress command to show trends over time."""
    telegram_id = update.effective_user.id
    logger.info(f"/progress from user {telegram_id}")

    try:
        await build_user_context(
            telegram_id=telegram_id,
            username=update.effective_user.username or update.effective_user.first_name,
        )

        recovery_statuses = get_recent_recovery_statuses(telegram_id, limit=7)
        body_metrics = get_recent_body_metrics(telegram_id, limit=8)
        workouts = get_workout_history(telegram_id, limit=50)
        nutrition_state = get_nutrition_state(telegram_id)

        summary = build_weekly_progress_summary(
            recovery_statuses=recovery_statuses,
            body_metrics=body_metrics,
            workouts=workouts,
            nutrition_state=nutrition_state,
        )
    except Exception as e:
        logger.error(f"/progress failed for {telegram_id}: {e}")
        await update.message.reply_text("Failed to build your progress summary. Try again later.")
        return

    if not summary:
        await update.message.reply_text(
            "Not enough stored progress data yet. Connect your devices, log workouts, and let Milo build a week of history first."
        )
        return

    await _reply_markdown(update, summary)


async def log_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /log command to record a workout."""
    telegram_id = update.effective_user.id
    logger.info(f"/log from user {telegram_id}")
    _ensure_user_record(update.effective_user)

    if len(context.args) < 3:
        await update.message.reply_text(
            "Use /log like this:\n\n"
            "`/log bench press 3x5 185lbs`\n"
            "`/log squat 5x5 225lbs`\n"
            "`/log deadlift 1x5 315lbs`",
            parse_mode="Markdown",
        )
        return

    sets_reps = parse_sets_reps(context.args[-2])
    weight = _parse_weight_token(context.args[-1])
    exercise = " ".join(context.args[:-2]).strip()

    if not exercise or not sets_reps or weight is None:
        await update.message.reply_text(
            "I couldn't parse that workout. Try /log bench press 3x5 185lbs"
        )
        return

    try:
        log_workout(
            telegram_id=telegram_id,
            exercise=exercise,
            sets=sets_reps["sets"],
            reps=sets_reps["reps"],
            weight=weight,
        )
    except Exception as e:
        logger.error(f"Failed to log workout for {telegram_id}: {e}")
        await update.message.reply_text("Failed to save that workout. Try again in a moment.")
        return

    overload = None
    try:
        history = get_workout_history(telegram_id, limit=6) or []
        overload = check_progressive_overload(history, exercise)
    except Exception as e:
        logger.error(f"Failed to evaluate progressive overload for {telegram_id}: {e}")

    reply_lines = [
        "Logged workout:",
        "",
        format_workout_log(exercise, sets_reps["sets"], sets_reps["reps"], weight),
    ]
    if overload:
        suggested_weight = overload.get("suggested_weight")
        if suggested_weight is not None:
            suggested_weight = float(suggested_weight)
            if suggested_weight.is_integer():
                suggested_weight = int(suggested_weight)
        reply_lines.extend(
            [
                "",
                f"Next time: aim for {suggested_weight} lbs if execution stays solid.",
                overload.get("reason", ""),
            ]
        )

    await _reply_markdown(update, "\n".join(line for line in reply_lines if line != ""))


def _parse_weight_token(token: str) -> float | None:
    match = re.search(r"\d+(?:\.\d+)?", token)
    if not match:
        return None
    return float(match.group(0))


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /profile command — view or update user profile fields."""
    telegram_id = update.effective_user.id
    logger.info(f"/profile from user {telegram_id}")
    _ensure_user_record(update.effective_user)

    try:
        existing_profile = get_user_profile(telegram_id) or {}
    except Exception as e:
        logger.error(f"Failed to fetch user profile for {telegram_id}: {e}")
        existing_profile = {}

    if not context.args:
        await _reply_markdown(update, _format_profile(existing_profile))
        return

    updates = {}
    invalid_args = []
    for arg in context.args:
        if "=" not in arg:
            invalid_args.append(arg)
            continue

        raw_key, raw_value = arg.split("=", 1)
        field = PROFILE_FIELD_ALIASES.get(raw_key.lower())
        if field is None:
            invalid_args.append(arg)
            continue

        try:
            updates[field] = _coerce_profile_value(field, raw_value)
        except ValueError:
            invalid_args.append(arg)

    if invalid_args:
        await update.message.reply_text(
            "Couldn't parse these fields: "
            + ", ".join(invalid_args)
            + "\n\nUse /profile sex=male age=32 height_cm=178 goal=fat_loss experience=intermediate days=4 activity=1.55"
        )
        return

    merged_profile = {
        **existing_profile,
        **updates,
    }

    try:
        upsert_user_profile(telegram_id, merged_profile)
        refreshed_context = await build_user_context(
            telegram_id=telegram_id,
            username=update.effective_user.username or update.effective_user.first_name,
            refresh_nutrition=True,
        )
    except Exception as e:
        logger.error(f"Failed to update user profile for {telegram_id}: {e}")
        await update.message.reply_text("Failed to update your profile. Try again in a moment.")
        return

    reply_lines = ["Profile updated.", "", _format_profile(merged_profile)]
    nutrition_state = refreshed_context.get("nutrition_state")
    if nutrition_state:
        reply_lines.extend(
            [
                "",
                f"Nutrition phase: {nutrition_state.get('phase', 'N/A')}",
                f"Calorie target: {nutrition_state.get('calorie_target', nutrition_state.get('current_calorie_target', 'N/A'))} kcal",
                f"Protein target: {nutrition_state.get('protein_target_g', nutrition_state.get('current_protein_target_g', 'N/A'))} g",
            ]
        )

    await _reply_markdown(update, "\n".join(reply_lines))


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command with a list of all commands."""
    logger.info(f"/help from user {update.effective_user.id}")
    await _reply_markdown(update, HELP_MESSAGE)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle free-form text messages by routing them to the Claude agent."""
    user = update.effective_user
    user_message = update.message.text
    logger.info(f"Message from {user.id}: {user_message[:50]}...")
    _ensure_user_record(user)

    try:
        user_profile = get_user_profile(user.id)
        onboarding_state = get_onboarding_state(user.id)
    except Exception as e:
        logger.error(f"Failed to fetch user onboarding context for {user.id}: {e}")
        user_profile = None
        onboarding_state = None

    if needs_onboarding(user_profile, onboarding_state):
        try:
            onboarding_messages = await process_onboarding_message(
                telegram_id=user.id,
                username=user.username or user.first_name or "there",
                message_text=user_message,
                onboarding_state=onboarding_state,
            )
        except Exception as e:
            logger.error(f"Onboarding flow failed for {user.id}: {e}")
            await update.message.reply_text("I hit a snag while saving your onboarding. Send that again and I'll keep going.")
            return

        await _reply_sequence(update, onboarding_messages)
        return

    # Build live user context for the coaching agent
    user_context = await build_user_context(
        telegram_id=user.id,
        username=user.username or user.first_name,
    )

    response = await get_coaching_response(user_message, user_context)

    try:
        store_chat_message(user.id, "user", user_message)
    except Exception as e:
        logger.error(f"Failed to store user chat message for {user.id}: {e}")

    try:
        store_chat_message(user.id, "assistant", response)
    except Exception as e:
        logger.error(f"Failed to store assistant chat message for {user.id}: {e}")

    await _reply_markdown(update, response)


_BUTTON_LABELS = {
    "yes": "Yes, let's go", "yes_18": "Yes, 18+", "under_18": "Under 18",
    "muscle_gain": "Get bigger", "fat_loss": "Get leaner", "recomp": "Both / recomp", "maintain": "Maintain",
    "full_gym": "Full gym", "home_gym": "Home gym", "minimal": "Minimal",
    "balanced": "Balanced", "upper": "Upper body", "lower": "Lower body", "arms": "Arms",
    "tracked": "Tracked", "habit": "Habit-based",
    "whoop": "Whoop", "withings": "Withings", "both": "Both", "neither": "Neither",
    "daily": "Daily", "training_days": "Training days", "weekly": "Weekly",
    "change": "Change something",
}


async def onboarding_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses during onboarding (callback_data prefixed with 'ob:')."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    data = query.data
    if not data or not data.startswith("ob:"):
        return

    button_value = data[3:]  # strip "ob:" prefix
    button_label = _BUTTON_LABELS.get(button_value, button_value)
    logger.info(f"Onboarding button from {user.id}: {button_value}")
    _ensure_user_record(user)

    # Edit the original message to show what the user selected (remove buttons)
    try:
        original_text = query.message.text or ""
        await query.edit_message_text(
            text=f"{original_text}\n\n*You selected: {button_label}*",
            parse_mode="Markdown",
        )
    except BadRequest:
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except BadRequest:
            pass

    try:
        onboarding_state = get_onboarding_state(user.id)
    except Exception as e:
        logger.error(f"Failed to fetch onboarding state for callback {user.id}: {e}")
        await query.message.reply_text("Something went wrong. Send any message to continue.")
        return

    try:
        onboarding_messages = await process_onboarding_message(
            telegram_id=user.id,
            username=user.username or user.first_name or "there",
            message_text=button_value,
            onboarding_state=onboarding_state,
        )
    except Exception as e:
        logger.error(f"Onboarding callback failed for {user.id}: {e}")
        await query.message.reply_text("I hit a snag. Send any message to continue.")
        return

    from core.onboarding import OnboardingMessage
    for message in onboarding_messages:
        if not message:
            continue
        if isinstance(message, OnboardingMessage):
            try:
                await query.message.reply_text(message.text, parse_mode="Markdown", reply_markup=message.reply_markup)
            except BadRequest:
                await query.message.reply_text(message.text, reply_markup=message.reply_markup)
        elif isinstance(message, str):
            await _reply_markdown_msg(query.message, message)


async def _reply_markdown_msg(message, text: str) -> None:
    try:
        await message.reply_text(text, parse_mode="Markdown")
    except BadRequest:
        await message.reply_text(text)
