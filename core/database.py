"""
Supabase database layer for Milo bot.

Handles all persistent storage including user profiles,
workout logs, connected device tokens, and coaching history.
"""

import os
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
