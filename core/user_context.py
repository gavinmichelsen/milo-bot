"""
User context assembly for coaching + stats flows.

Centralizes fetching biometric and workout context so handlers and
scheduled jobs can share one code path.
"""

from __future__ import annotations

import httpx

from core.database import (
    get_whoop_tokens,
    get_withings_tokens,
    get_workout_history,
    store_whoop_tokens,
    store_withings_tokens,
)
from integrations.whoop import WhoopClient, refresh_whoop_token
from integrations.withings import get_latest_measurements, refresh_withings_token
from utils.logger import setup_logger

logger = setup_logger("milo.user_context")


async def _fetch_whoop_data(telegram_id: int) -> dict | None:
    """Fetch latest Whoop recovery data with automatic token refresh."""
    whoop_tokens = get_whoop_tokens(telegram_id)
    if not whoop_tokens or not whoop_tokens.get("access_token"):
        return None

    whoop = WhoopClient()
    try:
        try:
            recovery_data = await whoop.get_recovery(whoop_tokens["access_token"])
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 401:
                raise
            logger.info(f"Whoop token expired for {telegram_id}, refreshing...")
            new_tokens = await refresh_whoop_token(whoop_tokens["refresh_token"])
            store_whoop_tokens(telegram_id, new_tokens)
            recovery_data = await whoop.get_recovery(new_tokens["access_token"])

        records = recovery_data.get("records", [])
        if not records:
            return None

        score = records[0].get("score", {})
        return {
            "recovery_score": score.get("recovery_score"),
            "hrv": score.get("hrv_rmssd_milli"),
            "resting_hr": score.get("resting_heart_rate"),
            # not currently available from this endpoint; keep key for prompt compatibility
            "sleep_score": None,
        }
    finally:
        await whoop.close()


async def _fetch_withings_data(telegram_id: int) -> dict | None:
    """Fetch latest Withings metrics with automatic token refresh."""
    withings_tokens = get_withings_tokens(telegram_id)
    if not withings_tokens or not withings_tokens.get("access_token"):
        return None

    try:
        measurements = await get_latest_measurements(withings_tokens["access_token"])
    except Exception as e:
        if "invalid_token" not in str(e) and "401" not in str(e):
            raise
        logger.info(f"Withings token expired for {telegram_id}, refreshing...")
        new_tokens = await refresh_withings_token(withings_tokens["refresh_token"])
        store_withings_tokens(telegram_id, new_tokens)
        measurements = await get_latest_measurements(new_tokens["access_token"])

    if not measurements:
        return None

    return {
        "weight": measurements.get("weight_lbs"),
        "body_fat": measurements.get("fat_ratio"),
        # not currently fetched from Withings; key kept for prompt compatibility
        "muscle_mass": None,
    }


async def build_user_context(telegram_id: int, username: str) -> dict:
    """Build complete user context for the coaching agent."""
    context = {
        "telegram_id": telegram_id,
        "username": username,
        "whoop_data": None,
        "withings_data": None,
        "workout_history": [],
    }

    # workouts are local DB reads; non-fatal on failure
    try:
        context["workout_history"] = get_workout_history(telegram_id, limit=5) or []
    except Exception as e:
        logger.error(f"Failed to fetch workout history for {telegram_id}: {e}")

    # fetch external data independently so one failure doesn't block the other
    try:
        context["whoop_data"] = await _fetch_whoop_data(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch Whoop data for {telegram_id}: {e}")

    try:
        context["withings_data"] = await _fetch_withings_data(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch Withings data for {telegram_id}: {e}")

    return context
