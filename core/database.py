"""
Supabase database layer for Milo bot.

Handles all persistent storage including user profiles,
workout logs, connected device tokens, and coaching history.
"""

import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from supabase import create_client

from utils.logger import setup_logger

logger = setup_logger("milo.database")

# Singleton client — initialized once when the module is first imported
_client = None


def get_supabase_client():
    """Return the Supabase client, creating it on first call."""
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
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
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }

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

    transport = httpx.HTTPTransport(retries=3)
    with httpx.Client(transport=transport, timeout=15.0) as client:
        response = client.post(
            f"{supabase_url}/rest/v1/withings_tokens?on_conflict=telegram_id",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
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
                "weight": weight,
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
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data
    return _retry_on_dns_error(_query)
