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
from integrations.whoop import (
    WhoopClient,
    kilojoules_to_calories,
    kilograms_to_pounds,
    refresh_whoop_token,
)
from integrations.withings import get_latest_measurements, refresh_withings_token
from utils.logger import setup_logger

logger = setup_logger("milo.user_context")


async def _fetch_whoop_recovery(telegram_id: int, whoop: WhoopClient, access_token: str) -> dict | None:
    """Fetch latest Whoop recovery data."""
    try:
        recovery_data = await whoop.get_recovery(access_token)
        records = recovery_data.get("records", [])
        if not records:
            return None

        score = records[0].get("score", {})
        return {
            "recovery_score": score.get("recovery_score"),
            "hrv": score.get("hrv_rmssd_milli"),
            "resting_hr": score.get("resting_heart_rate"),
            "spo2": score.get("spo2_percentage"),
            "skin_temp": score.get("skin_temp_celsius"),
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise  # token expired, let caller handle refresh
        logger.error(f"Failed to fetch Whoop recovery: {e}")
        return None


async def _fetch_whoop_sleep(telegram_id: int, whoop: WhoopClient, access_token: str) -> dict | None:
    """Fetch latest Whoop sleep data."""
    try:
        sleep_data = await whoop.get_sleep(access_token)
        records = sleep_data.get("records", [])
        if not records:
            return None

        record = records[0]
        score = record.get("score", {})
        stage_summary = score.get("stage_summary", {})
        sleep_needed = score.get("sleep_needed", {})

        return {
            "sleep_performance_pct": score.get("sleep_performance_percentage"),
            "sleep_efficiency_pct": score.get("sleep_efficiency_percentage"),
            "respiratory_rate": score.get("respiratory_rate"),
            "total_in_bed_ms": stage_summary.get("total_in_bed_time_milli"),
            "total_awake_ms": stage_summary.get("total_awake_time_milli"),
            "total_light_sleep_ms": stage_summary.get("total_light_sleep_time_milli"),
            "total_deep_sleep_ms": stage_summary.get("total_slow_wave_sleep_time_milli"),
            "total_rem_sleep_ms": stage_summary.get("total_rem_sleep_time_milli"),
            "sleep_cycles": stage_summary.get("sleep_cycle_count"),
            "disturbances": stage_summary.get("disturbance_count"),
            "sleep_need_baseline_ms": sleep_needed.get("baseline_milli"),
            "sleep_need_debt_ms": sleep_needed.get("need_from_sleep_debt_milli"),
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise
        logger.error(f"Failed to fetch Whoop sleep: {e}")
        return None


async def _fetch_whoop_cycles(telegram_id: int, whoop: WhoopClient, access_token: str) -> dict | None:
    """Fetch latest Whoop cycles (daily strain) data."""
    try:
        cycles_data = await whoop.get_cycles(access_token, limit=1)
        records = cycles_data.get("records", [])
        if not records:
            return None

        record = records[0]
        score = record.get("score", {})

        # Convert kilojoules to calories
        kj = score.get("kilojoule")
        calories = kilojoules_to_calories(kj) if kj else None

        return {
            "strain": score.get("strain"),
            "kilojoules": kj,
            "calories_burned": calories,
            "average_heart_rate": score.get("average_heart_rate"),
            "max_heart_rate": score.get("max_heart_rate"),
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise
        logger.error(f"Failed to fetch Whoop cycles: {e}")
        return None


async def _fetch_whoop_workouts(telegram_id: int, whoop: WhoopClient, access_token: str) -> dict | None:
    """Fetch latest Whoop workout data."""
    try:
        workouts_data = await whoop.get_workouts(access_token, limit=1)
        records = workouts_data.get("records", [])
        if not records:
            return None

        record = records[0]
        score = record.get("score", {})
        zone_durations = score.get("zone_durations", {})

        # Convert kilojoules to calories
        kj = score.get("kilojoule")
        calories = kilojoules_to_calories(kj) if kj else None

        return {
            "strain": score.get("strain"),
            "kilojoules": kj,
            "calories_burned": calories,
            "average_heart_rate": score.get("average_heart_rate"),
            "max_heart_rate": score.get("max_heart_rate"),
            "distance_meters": score.get("distance_meter"),
            "altitude_gain_meters": score.get("altitude_gain_meter"),
            "zone_durations_ms": zone_durations,
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise
        logger.error(f"Failed to fetch Whoop workouts: {e}")
        return None


async def _fetch_whoop_body(telegram_id: int, whoop: WhoopClient, access_token: str) -> dict | None:
    """Fetch user's body measurements from Whoop."""
    try:
        body_data = await whoop.get_body_measurements(access_token)
        # Already returns as JSON with height_meter, weight_kilogram, max_heart_rate
        height_m = body_data.get("height_meter")
        weight_kg = body_data.get("weight_kilogram")
        max_hr = body_data.get("max_heart_rate")

        return {
            "height_meters": height_m,
            "height_feet": round(height_m * 3.28084, 1) if height_m else None,
            "weight_kg": weight_kg,
            "weight_lbs": kilograms_to_pounds(weight_kg) if weight_kg else None,
            "max_heart_rate": max_hr,
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise
        logger.error(f"Failed to fetch Whoop body measurements: {e}")
        return None


async def _fetch_all_whoop_data(telegram_id: int) -> dict | None:
    """Fetch all Whoop data with automatic token refresh."""
    whoop_tokens = get_whoop_tokens(telegram_id)
    if not whoop_tokens or not whoop_tokens.get("access_token"):
        return None

    whoop = WhoopClient()
    access_token = whoop_tokens["access_token"]

    try:
        # Try initial fetch
        recovery = await _fetch_whoop_recovery(telegram_id, whoop, access_token)
        sleep = await _fetch_whoop_sleep(telegram_id, whoop, access_token)
        cycles = await _fetch_whoop_cycles(telegram_id, whoop, access_token)
        workouts = await _fetch_whoop_workouts(telegram_id, whoop, access_token)
        body = await _fetch_whoop_body(telegram_id, whoop, access_token)

    except httpx.HTTPStatusError as e:
        if e.response.status_code != 401:
            raise

        # Token expired, refresh and retry
        logger.info(f"Whoop token expired for {telegram_id}, refreshing...")
        new_tokens = await refresh_whoop_token(whoop_tokens["refresh_token"])
        store_whoop_tokens(telegram_id, new_tokens)
        access_token = new_tokens["access_token"]

        # Retry all fetches with new token
        recovery = await _fetch_whoop_recovery(telegram_id, whoop, access_token)
        sleep = await _fetch_whoop_sleep(telegram_id, whoop, access_token)
        cycles = await _fetch_whoop_cycles(telegram_id, whoop, access_token)
        workouts = await _fetch_whoop_workouts(telegram_id, whoop, access_token)
        body = await _fetch_whoop_body(telegram_id, whoop, access_token)

    finally:
        await whoop.close()

    return {
        "recovery": recovery,
        "sleep": sleep,
        "cycles": cycles,
        "workouts": workouts,
        "body": body,
    }


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
        "muscle_mass": None,  # not currently available
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
        context["whoop_data"] = await _fetch_all_whoop_data(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch Whoop data for {telegram_id}: {e}")

    try:
        context["withings_data"] = await _fetch_withings_data(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch Withings data for {telegram_id}: {e}")

    return context