"""
User context assembly for coaching + stats flows.

Centralizes fetching biometric and workout context so handlers and
scheduled jobs can share one code path.
"""

from __future__ import annotations

import httpx

from coaching.nutrition import build_nutrition_targets, phase_from_goal
from coaching.training import build_training_guidance
from core.database import (
    get_recent_chat_history,
    get_nutrition_state,
    get_recent_recovery_statuses,
    get_training_program,
    get_user_profile,
    get_whoop_tokens,
    get_withings_tokens,
    get_workout_history,
    store_body_metrics,
    store_nutrition_state,
    store_whoop_tokens,
    store_whoop_snapshot,
    store_withings_tokens,
    upsert_user_profile,
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


def _ms_to_hours(ms: int | None) -> float | None:
    if ms is None:
        return None
    return round(ms / 3_600_000, 2)


def _build_whoop_summary(whoop_data: dict | None) -> dict | None:
    if not whoop_data:
        return None

    recovery = whoop_data.get("recovery") or {}
    sleep = whoop_data.get("sleep") or {}
    cycles = whoop_data.get("cycles") or {}
    body = whoop_data.get("body") or {}

    total_in_bed_ms = sleep.get("total_in_bed_ms")
    total_awake_ms = sleep.get("total_awake_ms") or 0
    sleep_duration_hrs = None
    if total_in_bed_ms is not None:
        sleep_duration_hrs = _ms_to_hours(max(total_in_bed_ms - total_awake_ms, 0))

    return {
        "recovery_score": recovery.get("recovery_score"),
        "hrv": recovery.get("hrv"),
        "resting_hr": recovery.get("resting_hr"),
        "spo2": recovery.get("spo2"),
        "skin_temp": recovery.get("skin_temp"),
        "sleep_performance_pct": sleep.get("sleep_performance_pct"),
        "sleep_efficiency_pct": sleep.get("sleep_efficiency_pct"),
        "sleep_duration_hrs": sleep_duration_hrs,
        "respiratory_rate": sleep.get("respiratory_rate"),
        "strain": cycles.get("strain"),
        "calories_burned": cycles.get("calories_burned"),
        "weight_lbs": body.get("weight_lbs"),
        "weight_kg": body.get("weight_kg"),
        "max_heart_rate": body.get("max_heart_rate"),
    }


def _maybe_initialize_nutrition_state(
    profile: dict | None,
    nutrition_state: dict | None,
    withings_data: dict | None,
    force_refresh: bool = False,
) -> dict | None:
    if nutrition_state and not force_refresh:
        return nutrition_state
    if not profile:
        return None

    body_weight_lbs = None
    if withings_data:
        body_weight_lbs = withings_data.get("weight_lbs")
    if body_weight_lbs is None:
        body_weight_lbs = profile.get("body_weight_lbs")

    if body_weight_lbs is None:
        return None

    sex = profile.get("sex")
    age_years = profile.get("age_years")
    height_cm = profile.get("height_cm")
    if sex is None or age_years is None or height_cm is None:
        return None

    nutrition_state = build_nutrition_targets(
        body_weight=body_weight_lbs,
        height_cm=float(height_cm),
        age_years=int(age_years),
        sex=str(sex),
        phase=phase_from_goal(profile.get("primary_goal")),
        activity_multiplier=float(profile.get("activity_multiplier") or 1.55),
        unit="lbs",
        experience_level=str(profile.get("experience_level") or "intermediate"),
    )
    nutrition_state["nutrition_mode"] = profile.get("nutrition_mode") or "tracked"
    store_nutrition_state(
        profile["user_id"],
        nutrition_state,
        reason_code="profile_refresh" if force_refresh else "profile_bootstrap",
    )
    return nutrition_state


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
        "weight_lbs": measurements.get("weight_lbs"),
        "body_fat_pct": measurements.get("fat_ratio"),
        "muscle_mass_lbs": None,
        "weight": measurements.get("weight_lbs"),
        "body_fat": measurements.get("fat_ratio"),
        "muscle_mass": None,
    }


async def build_user_context(telegram_id: int, username: str, refresh_nutrition: bool = False) -> dict:
    """Build complete user context for the coaching agent."""
    context = {
        "telegram_id": telegram_id,
        "username": username,
        "chat_history": [],
        "recovery_status": None,
        "user_profile": None,
        "nutrition_state": None,
        "training_guidance": None,
        "training_program": None,
        "whoop_data": None,
        "whoop_summary": None,
        "withings_data": None,
        "workout_history": [],
    }

    try:
        context["user_profile"] = get_user_profile(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch user profile for {telegram_id}: {e}")

    try:
        context["training_program"] = get_training_program(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch training program for {telegram_id}: {e}")

    try:
        context["chat_history"] = get_recent_chat_history(telegram_id, limit=6)
    except Exception as e:
        logger.error(f"Failed to fetch chat history for {telegram_id}: {e}")

    try:
        context["nutrition_state"] = get_nutrition_state(telegram_id)
    except Exception as e:
        logger.error(f"Failed to fetch nutrition state for {telegram_id}: {e}")

    try:
        recovery_statuses = get_recent_recovery_statuses(telegram_id, limit=1)
        context["recovery_status"] = recovery_statuses[0] if recovery_statuses else None
    except Exception as e:
        logger.error(f"Failed to fetch recovery status for {telegram_id}: {e}")

    # workouts are local DB reads; non-fatal on failure
    try:
        context["workout_history"] = get_workout_history(telegram_id, limit=5) or []
    except Exception as e:
        logger.error(f"Failed to fetch workout history for {telegram_id}: {e}")

    # fetch external data independently so one failure doesn't block the other
    try:
        context["whoop_data"] = await _fetch_all_whoop_data(telegram_id)
        context["whoop_summary"] = _build_whoop_summary(context["whoop_data"])
        if context["whoop_summary"]:
            store_whoop_snapshot(telegram_id, context["whoop_summary"])
    except Exception as e:
        logger.error(f"Failed to fetch Whoop data for {telegram_id}: {e}")

    try:
        context["withings_data"] = await _fetch_withings_data(telegram_id)
        if context["withings_data"]:
            store_body_metrics(telegram_id, context["withings_data"])
            if context["user_profile"]:
                merged_profile = {
                    **context["user_profile"],
                    "body_weight_lbs": context["withings_data"].get("weight_lbs"),
                    "estimated_body_fat_pct": context["withings_data"].get("body_fat_pct"),
                }
                upsert_user_profile(telegram_id, merged_profile)
                context["user_profile"] = merged_profile
    except Exception as e:
        logger.error(f"Failed to fetch Withings data for {telegram_id}: {e}")

    try:
        context["nutrition_state"] = _maybe_initialize_nutrition_state(
            context.get("user_profile"),
            context.get("nutrition_state"),
            context.get("withings_data"),
            force_refresh=refresh_nutrition,
        ) or context.get("nutrition_state")
    except Exception as e:
        logger.error(f"Failed to initialize nutrition state for {telegram_id}: {e}")

    try:
        recovery_for_training = context.get("recovery_status")
        if recovery_for_training is None and context.get("whoop_summary"):
            recovery_for_training = {
                "composite_score": context["whoop_summary"].get("recovery_score"),
            }
        context["training_guidance"] = build_training_guidance(
            recovery_status=recovery_for_training,
            workout_history=context.get("workout_history") or [],
            experience_level=(context.get("user_profile") or {}).get("experience_level"),
        )
    except Exception as e:
        logger.error(f"Failed to build training guidance for {telegram_id}: {e}")

    return context