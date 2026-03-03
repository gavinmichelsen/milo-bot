"""
Supabase-backed OAuth state management.

Stores OAuth state tokens in Supabase so they survive across
multiple Railway container instances.
"""

import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

from core.database import get_supabase_client
from utils.logger import setup_logger

logger = setup_logger("milo.oauth_state")

STATE_TTL_SECONDS = 600


def create_state(telegram_id: int) -> str:
    """Generate a unique OAuth state token and persist it to Supabase."""
    state = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=STATE_TTL_SECONDS)
    supabase = get_supabase_client()
    supabase.table("oauth_states").insert({
        "state": state,
        "telegram_id": telegram_id,
        "expires_at": expires_at.isoformat(),
    }).execute()
    logger.info(f"Created OAuth state for telegram_id={telegram_id}")
    return state


def validate_state(state: str) -> Optional[int]:
    """Validate and consume an OAuth state token. Returns telegram_id or None."""
    supabase = get_supabase_client()
    result = supabase.table("oauth_states").select("*").eq("state", state).execute()
    if not result.data:
        logger.warning(f"State not found: {state}")
        return None
    row = result.data[0]
    # Delete it immediately (one-time use)
    supabase.table("oauth_states").delete().eq("state", state).execute()
    # Check expiry
    expires_at = datetime.fromisoformat(row["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        logger.warning(f"State expired for telegram_id={row['telegram_id']}")
        return None
    return row["telegram_id"]
