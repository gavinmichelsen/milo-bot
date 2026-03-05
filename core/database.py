"""
Supabase database layer for Milo bot.

Handles all persistent storage including user profiles,
workout logs, connected device tokens, and coaching history.
"""

from __future__ import annotations

import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from supabase import create_client

from utils.logger import setup_logger

logger = setup_logger("milo.database")

# Singleton client — initialized once when the module is first imported
_client = None


def _get_rest_headers() -> dict[str, str]:
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    return {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }


def _postgrest_upsert(table: str, payload: dict[str, Any], on_conflict: str) -> None:
    supabase_url = os.getenv("SUPABASE_URL")
    transport = httpx.HTTPTransport(retries=3)
    with httpx.Client(transport=transport, timeout=15.0) as client:
        response = client.post(
            f"{supabase_url}/rest/v1/{table}?on_conflict={on_conflict}",
            headers=_get_rest_headers(),
            json=payload,
        )
        response.raise_for_status()


def get_supabase_client():
    """Return the Supabase client, creating it on first call."""
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and a Supabase API key must be set in .env")
        logger.info(f"Connecting to Supabase at {url}")
        _client = create_client(url, key)
        logger.info("Supabase client initialized")
    return _client


def _reset_client():
    """Reset the singleton client so the next call recreates it."""
    global _client
    _client = None
    logger.info("Supabase client reset — will reconnect on next call")


def _retry_on_dns_error(func, max_retries: int = 3):
    """Retry a Supabase operation if DNS resolution or connection fails.

    Railway containers can experience transient DNS failures.
    This wrapper retries with backoff and resets the client between attempts.
    """
    for attempt in range(max_retries):
        try:
            return func()
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            err_str = str(e)
            if "Name or service not known" in err_str or "Errno -2" in err_str or isinstance(e, httpx.ConnectTimeout):
                logger.warning(
                    f"Connection failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                _reset_client()
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))
                else:
                    raise
            else:
                raise


def get_user(telegram_id: int) -> Optional[dict]:
    """Fetch a user profile by their Telegram ID."""
    def _query():
        client = get_supabase_client()
        result = (
            client.table("users")
            .select("*")
            .eq("telegram_id", telegram_id)
            .execute()
        )
        if result.data:
            return result.data[0]
        return None
    return _retry_on_dns_error(_query)


def get_all_users() -> list:
    def _query():
        client = get_supabase_client()
        result = client.table("users").select("*").execute()
        return result.data or []
    return _retry_on_dns_error(_query)


def get_user_profile(telegram_id: int) -> Optional[dict]:
    def _query():
        client = get_supabase_client()
        result = (
            client.table("user_profiles")
            .select("*")
            .eq("user_id", telegram_id)
            .execute()
        )
        if result.data:
            return result.data[0]
        return None
    return _retry_on_dns_error(_query)


def upsert_user_profile(telegram_id: int, profile: dict) -> None:
    payload = {
        "user_id": telegram_id,
        "sex": profile.get("sex"),
        "age_years": profile.get("age_years"),
        "height_cm": profile.get("height_cm"),
        "body_weight_lbs": profile.get("body_weight_lbs"),
        "estimated_body_fat_pct": profile.get("estimated_body_fat_pct"),
        "activity_multiplier": profile.get("activity_multiplier"),
        "primary_goal": profile.get("primary_goal"),
        "experience_level": profile.get("experience_level"),
        "training_days_per_week": profile.get("training_days_per_week"),
        "nutrition_mode": profile.get("nutrition_mode"),
        "target_wake_time": profile.get("target_wake_time"),
        "target_bedtime": profile.get("target_bedtime"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _postgrest_upsert("user_profiles", payload, "user_id")
    logger.info(f"Upserted user profile for telegram_id={telegram_id}")


def store_chat_message(telegram_id: int, role: str, content: str) -> None:
    def _query():
        client = get_supabase_client()
        client.table("chat_history").insert({
            "user_id": telegram_id,
            "role": role,
            "content": content,
        }).execute()

    _retry_on_dns_error(_query)
    logger.info(f"Stored chat message for telegram_id={telegram_id}, role={role}")


def get_recent_chat_history(telegram_id: int, limit: int = 6) -> list:
    def _query():
        client = get_supabase_client()
        result = (
            client.table("chat_history")
            .select("role, content, created_at")
            .eq("user_id", telegram_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = result.data or []
        return list(reversed(rows))

    return _retry_on_dns_error(_query)


def upsert_user(telegram_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]) -> dict:
    """Create or update a user profile."""
    def _query():
        client = get_supabase_client()
        row = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
        }
        result = (
            client.table("users")
            .upsert(row, on_conflict="telegram_id")
            .execute()
        )
        logger.info(f"Upserted user: {telegram_id} (@{username})")
        return result.data[0]
    return _retry_on_dns_error(_query)


def create_oauth_state(telegram_id: int) -> str:
    """Create a unique OAuth state token tied to a telegram_id."""
    state = secrets.token_urlsafe(32)
    def _query():
        client = get_supabase_client()
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        client.table("oauth_states").insert({
            "telegram_id": telegram_id,
            "state": state,
            "expires_at": expires_at,
        }).execute()
        logger.info(f"Created OAuth state for telegram_id={telegram_id}")
        return state
    return _retry_on_dns_error(_query)


def validate_oauth_state(state: str) -> Optional[int]:
    """Validate an OAuth state token and return the associated telegram_id."""
    def _query():
        client = get_supabase_client()
        result = (
            client.table("oauth_states")
            .select("telegram_id, expires_at")
            .eq("state", state)
            .execute()
        )
        if not result.data:
            return None

        row = result.data[0]
        expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires_at:
            client.table("oauth_states").delete().eq("state", state).execute()
            return None

        client.table("oauth_states").delete().eq("state", state).execute()
        return row["telegram_id"]
    return _retry_on_dns_error(_query)


def store_whoop_tokens(telegram_id: int, token_data: dict) -> None:
    """Store Whoop OAuth tokens via direct HTTP (bypasses supabase-py DNS issues)."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    expires_in = token_data.get("expires_in", 3600)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).isoformat()

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }

    payload = {
        "telegram_id": telegram_id,
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "expires_at": expires_at,
        "scopes": token_data.get("scope", ""),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    transport = httpx.HTTPTransport(retries=3)
    with httpx.Client(transport=transport, timeout=15.0) as client:
        response = client.post(
            f"{supabase_url}/rest/v1/whoop_tokens?on_conflict=telegram_id",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
    logger.info(f"Stored Whoop tokens for telegram_id={telegram_id}")


def get_whoop_tokens(telegram_id: int) -> Optional[dict]:
    """Fetch stored Whoop tokens for a user."""
    def _query():
        client = get_supabase_client()
        result = (
            client.table("whoop_tokens")
            .select("*")
            .eq("telegram_id", telegram_id)
            .execute()
        )
        if result.data:
            return result.data[0]
        return None
    return _retry_on_dns_error(_query)


def get_all_whoop_tokens() -> list:
    """Return all rows from whoop_tokens table."""
    def _query():
        client = get_supabase_client()
        result = client.table("whoop_tokens").select("*").execute()
        return result.data or []
    return _retry_on_dns_error(_query)


def store_withings_tokens(telegram_id: int, token_data: dict) -> None:
    """Store Withings OAuth tokens via direct HTTP."""
    expires_in = token_data.get("expires_in", 10800)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).isoformat()

    payload = {
        "telegram_id": telegram_id,
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "expires_at": expires_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    _postgrest_upsert("withings_tokens", payload, "telegram_id")
    logger.info(f"Stored Withings tokens for telegram_id={telegram_id}")


def get_withings_tokens(telegram_id: int) -> Optional[dict]:
    """Fetch stored Withings tokens for a user."""
    def _query():
        client = get_supabase_client()
        result = (
            client.table("withings_tokens")
            .select("*")
            .eq("telegram_id", telegram_id)
            .execute()
        )
        if result.data:
            return result.data[0]
        return None
    return _retry_on_dns_error(_query)


def get_all_withings_tokens() -> list:
    """Return all rows from withings_tokens table."""
    def _query():
        client = get_supabase_client()
        result = client.table("withings_tokens").select("*").execute()
        return result.data or []
    return _retry_on_dns_error(_query)


def _merge_snapshot_payload(table: str, telegram_id: int, snapshot_date: str, payload: dict[str, Any]) -> dict[str, Any]:
    def _query():
        client = get_supabase_client()
        result = (
            client.table(table)
            .select("*")
            .eq("user_id", telegram_id)
            .eq("snapshot_date", snapshot_date)
            .execute()
        )
        existing = result.data[0] if result.data else {}
        merged = {}
        for key, value in payload.items():
            merged[key] = existing.get(key) if value is None and key in existing else value
        return merged

    return _retry_on_dns_error(_query)


def store_body_metrics(telegram_id: int, metrics: dict) -> None:
    snapshot_date = metrics.get("snapshot_date") or datetime.now(timezone.utc).date().isoformat()
    payload = {
        "user_id": telegram_id,
        "weight_lbs": metrics.get("weight_lbs"),
        "body_fat_pct": metrics.get("body_fat_pct"),
        "muscle_mass_lbs": metrics.get("muscle_mass_lbs"),
        "recorded_at": metrics.get("recorded_at") or datetime.now(timezone.utc).isoformat(),
        "snapshot_date": snapshot_date,
    }
    payload = _merge_snapshot_payload("body_metrics", telegram_id, snapshot_date, payload)
    _postgrest_upsert("body_metrics", payload, "user_id,snapshot_date")
    logger.info(f"Stored body metrics for telegram_id={telegram_id}")


def store_whoop_snapshot(telegram_id: int, snapshot: dict) -> None:
    snapshot_date = snapshot.get("snapshot_date") or datetime.now(timezone.utc).date().isoformat()
    payload = {
        "user_id": telegram_id,
        "recovery_score": snapshot.get("recovery_score"),
        "hrv": snapshot.get("hrv"),
        "resting_hr": snapshot.get("resting_hr"),
        "sleep_duration_hrs": snapshot.get("sleep_duration_hrs"),
        "sleep_efficiency_pct": snapshot.get("sleep_efficiency_pct"),
        "sleep_performance_pct": snapshot.get("sleep_performance_pct"),
        "strain": snapshot.get("strain"),
        "spo2": snapshot.get("spo2"),
        "respiratory_rate": snapshot.get("respiratory_rate"),
        "skin_temp": snapshot.get("skin_temp"),
        "recorded_at": snapshot.get("recorded_at") or datetime.now(timezone.utc).isoformat(),
        "snapshot_date": snapshot_date,
    }
    payload = _merge_snapshot_payload("whoop_snapshots", telegram_id, snapshot_date, payload)
    _postgrest_upsert("whoop_snapshots", payload, "user_id,snapshot_date")
    logger.info(f"Stored Whoop snapshot for telegram_id={telegram_id}")


def log_workout(telegram_id: int, exercise: str, sets: int, reps: int, weight: float) -> dict:
    """Log a workout entry for a user."""
    def _query():
        client = get_supabase_client()
        result = (
            client.table("workouts")
            .insert({
                "user_id": telegram_id,
                "exercise": exercise,
                "sets": sets,
                "reps": reps,
                "weight_lbs": weight,
            })
            .execute()
        )
        logger.info(f"Logged workout for {telegram_id}: {exercise} {sets}x{reps} @ {weight}")
        return result.data[0]
    return _retry_on_dns_error(_query)


def get_workout_history(telegram_id: int, limit: int = 10) -> list:
    """Fetch recent workout history for a user."""
    def _query():
        client = get_supabase_client()
        result = (
            client.table("workouts")
            .select("*")
            .eq("user_id", telegram_id)
            .order("logged_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = result.data or []
        return [
            {
                **row,
                "weight": row.get("weight_lbs"),
            }
            for row in rows
        ]
    return _retry_on_dns_error(_query)


def get_nutrition_state(telegram_id: int) -> Optional[dict]:
    def _query():
        client = get_supabase_client()
        result = (
            client.table("nutrition_states")
            .select("*")
            .eq("user_id", telegram_id)
            .execute()
        )
        if result.data:
            return result.data[0]
        return None
    return _retry_on_dns_error(_query)


def store_nutrition_state(telegram_id: int, nutrition_state: dict, reason_code: str | None = None) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    current_payload = {
        "user_id": telegram_id,
        "phase": nutrition_state.get("phase"),
        "nutrition_mode": nutrition_state.get("nutrition_mode", "tracked"),
        "current_calorie_target": nutrition_state.get("calorie_target"),
        "current_protein_target_g": nutrition_state.get("protein_target_g"),
        "estimated_tdee": nutrition_state.get("estimated_tdee"),
        "adaptive_tdee": nutrition_state.get("adaptive_tdee"),
        "working_tdee": nutrition_state.get("working_tdee"),
        "goal_rate_pct_per_week": nutrition_state.get("goal_rate_pct_per_week"),
        "started_at": nutrition_state.get("started_at") or now_iso,
        "updated_at": now_iso,
    }
    history_payload = {
        "user_id": telegram_id,
        "phase": nutrition_state.get("phase"),
        "nutrition_mode": nutrition_state.get("nutrition_mode", "tracked"),
        "calorie_target": nutrition_state.get("calorie_target"),
        "protein_target_g": nutrition_state.get("protein_target_g"),
        "estimated_tdee": nutrition_state.get("estimated_tdee"),
        "adaptive_tdee": nutrition_state.get("adaptive_tdee"),
        "working_tdee": nutrition_state.get("working_tdee"),
        "goal_rate_pct_per_week": nutrition_state.get("goal_rate_pct_per_week"),
        "reason_code": reason_code,
    }
    _postgrest_upsert("nutrition_states", current_payload, "user_id")

    def _insert_history():
        client = get_supabase_client()
        client.table("nutrition_state_history").insert(history_payload).execute()

    _retry_on_dns_error(_insert_history)
    logger.info(f"Stored nutrition state for telegram_id={telegram_id}")


def get_recent_whoop_snapshots(telegram_id: int, limit: int = 30) -> list:
    def _query():
        client = get_supabase_client()
        result = (
            client.table("whoop_snapshots")
            .select("*")
            .eq("user_id", telegram_id)
            .order("snapshot_date", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    return _retry_on_dns_error(_query)


def get_recent_body_metrics(telegram_id: int, limit: int = 8) -> list:
    def _query():
        client = get_supabase_client()
        result = (
            client.table("body_metrics")
            .select("*")
            .eq("user_id", telegram_id)
            .order("snapshot_date", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    return _retry_on_dns_error(_query)


def get_recent_recovery_statuses(telegram_id: int, limit: int = 7) -> list:
    def _query():
        client = get_supabase_client()
        result = (
            client.table("recovery_daily_status")
            .select("*")
            .eq("user_id", telegram_id)
            .order("snapshot_date", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    return _retry_on_dns_error(_query)


def store_recovery_daily_status(telegram_id: int, recovery_status: dict) -> None:
    payload = {
        "user_id": telegram_id,
        "snapshot_date": recovery_status.get("snapshot_date") or datetime.now(timezone.utc).date().isoformat(),
        "composite_score": recovery_status.get("composite_score"),
        "composite_tier": recovery_status.get("composite_tier", "insufficient_data"),
        "hrv_status": recovery_status.get("hrv_status"),
        "rhr_status": recovery_status.get("rhr_status"),
        "sleep_duration_status": recovery_status.get("sleep_duration_status"),
        "sleep_efficiency_status": recovery_status.get("sleep_efficiency_status"),
        "baseline_ready": recovery_status.get("baseline_ready", False),
        "should_send": recovery_status.get("should_send", False),
        "training_action": recovery_status.get("training_action"),
        "message_text": recovery_status.get("message_text"),
    }
    _postgrest_upsert("recovery_daily_status", payload, "user_id,snapshot_date")
    logger.info(f"Stored recovery daily status for telegram_id={telegram_id}")
