"""
Supabase database layer for Milo bot.

Handles all persistent storage including user profiles,
workout logs, connected device tokens, and coaching history.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from supabase import create_client, Client

from utils.logger import setup_logger

logger = setup_logger("milo.database")

# Singleton client — initialized once when the module is first imported
_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Return the Supabase client, creating it on first call.

    Returns:
        Authenticated Supabase client.
    """
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        _client = create_client(url, key)
        logger.info("Supabase client initialized")
    return _client


def get_user(telegram_id: int) -> Optional[dict]:
    """Fetch a user profile by their Telegram ID.

    Args:
        telegram_id: The user's Telegram user ID.

    Returns:
        User record dict or None if not found.
    """
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


def upsert_user(telegram_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]) -> dict:
    """Create or update a user profile.

    Uses telegram_id as the conflict key — if the user already exists
    their username, first_name, and last_name are updated, otherwise
    a new row is created.

    Args:
        telegram_id: The user's Telegram user ID.
        username: The user's Telegram @username (may be None).
        first_name: The user's Telegram first name (may be None).
        last_name: The user's Telegram last name (may be None).

    Returns:
        The upserted user record.
    """
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


def create_oauth_state(telegram_id: int) -> str:
    """Create a unique OAuth state token tied to a telegram_id.

    The state is stored in Supabase with a 10-minute expiry
    and used to validate the OAuth callback (CSRF protection).

    Returns:
        The state string to embed in the OAuth URL.
    """
    client = get_supabase_client()
    state = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    client.table("oauth_states").insert({
        "telegram_id": telegram_id,
        "state": state,
        "expires_at": expires_at,
    }).execute()
    logger.info(f"Created OAuth state for telegram_id={telegram_id}")
    return state


def validate_oauth_state(state: str) -> Optional[int]:
    """Validate an OAuth state token and return the associated telegram_id.

    Deletes the state row after validation (single-use).

    Args:
        state: The state string from the OAuth callback.

    Returns:
        The telegram_id if valid, None if invalid or expired.
    """
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

    # Valid — delete the state (single-use) and return telegram_id
    client.table("oauth_states").delete().eq("state", state).execute()
    return row["telegram_id"]


def store_whoop_tokens(telegram_id: int, token_data: dict) -> dict:
    """Store or update Whoop OAuth tokens for a user.

    Args:
        telegram_id: The user's Telegram ID.
        token_data: Token response from Whoop containing
                    access_token, refresh_token, expires_in.

    Returns:
        The upserted token record.
    """
    client = get_supabase_client()
    expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])
    ).isoformat()
    row = {
        "telegram_id": telegram_id,
        "access_token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"],
        "expires_at": expires_at,
        "scopes": token_data.get("scope", ""),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    result = (
        client.table("whoop_tokens")
        .upsert(row, on_conflict="telegram_id")
        .execute()
    )
    logger.info(f"Stored Whoop tokens for telegram_id={telegram_id}")
    return result.data[0]


def get_whoop_tokens(telegram_id: int) -> Optional[dict]:
    """Fetch stored Whoop tokens for a user.

    Args:
        telegram_id: The user's Telegram ID.

    Returns:
        Token record dict or None if not connected.
    """
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


async def log_workout(telegram_id: int, exercise: str, sets: int, reps: int, weight: float) -> dict:
    """Log a workout entry for a user.

    Args:
        telegram_id: The user's Telegram user ID.
        exercise: Name of the exercise (e.g. 'bench press').
        sets: Number of sets performed.
        reps: Number of reps per set.
        weight: Weight used in the exercise.

    Returns:
        The created workout log record.
    """
    client = get_supabase_client()
    result = (
        client.table("workouts")
        .insert({
            "telegram_id": telegram_id,
            "exercise": exercise,
            "sets": sets,
            "reps": reps,
            "weight": weight,
        })
        .execute()
    )
    logger.info(f"Logged workout for {telegram_id}: {exercise} {sets}x{reps} @ {weight}")
    return result.data[0]


async def get_workout_history(telegram_id: int, limit: int = 10) -> list:
    """Fetch recent workout history for a user.

    Args:
        telegram_id: The user's Telegram user ID.
        limit: Maximum number of records to return.

    Returns:
        List of workout log records, most recent first.
    """
    client = get_supabase_client()
    result = (
        client.table("workouts")
        .select("*")
        .eq("telegram_id", telegram_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data
