"""
In-memory OAuth state management.

Stores OAuth state tokens in a simple dict with TTL expiry.
Acceptable for single-instance MVP. Will migrate to Supabase
once Railway DNS issues are resolved.
"""

import secrets
import time
from typing import Optional

from utils.logger import setup_logger

logger = setup_logger("milo.oauth_state")

# In-memory store: state -> (telegram_id, expires_at_timestamp)
_states: dict = {}

# States expire after 10 minutes
STATE_TTL_SECONDS = 600


def create_state(telegram_id: int) -> str:
    """Generate a unique OAuth state token for a user."""
    _cleanup_expired()
    state = secrets.token_urlsafe(6)[:8]
    _states[state] = (telegram_id, time.time() + STATE_TTL_SECONDS)
    logger.info(f"Created OAuth state for telegram_id={telegram_id}")
    return state


def validate_state(state: str) -> Optional[int]:
    """Validate and consume an OAuth state token. Returns telegram_id or None."""
    _cleanup_expired()
    entry = _states.pop(state, None)
    if entry is None:
        return None
    telegram_id, expires_at = entry
    if time.time() > expires_at:
        return None
    return telegram_id


def _cleanup_expired():
    """Remove expired state entries."""
    now = time.time()
    expired = [s for s, (_, exp) in _states.items() if now > exp]
    for s in expired:
        del _states[s]
