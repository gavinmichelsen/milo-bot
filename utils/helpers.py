"""
Shared utility functions used across the Milo bot.
"""

from datetime import datetime, timezone


def timestamp_now() -> str:
    """Return the current UTC timestamp as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def format_weight(value: float, unit: str = "lbs") -> str:
    """Format a weight value with its unit for display.

    Args:
        value: Numeric weight value.
        unit: Weight unit (default: lbs).

    Returns:
        Formatted string like '185 lbs'.
    """
    if value == int(value):
        return f"{int(value)} {unit}"
    return f"{value} {unit}"


def parse_sets_reps(text: str) -> dict | None:
    """Parse a sets x reps string like '3x5' into components.

    Args:
        text: String in the format 'SETSxREPS' (e.g. '3x5').

    Returns:
        Dict with 'sets' and 'reps' keys, or None if parsing fails.
    """
    text = text.strip().lower()
    if "x" not in text:
        return None

    parts = text.split("x", 1)
    try:
        return {"sets": int(parts[0]), "reps": int(parts[1])}
    except ValueError:
        return None
