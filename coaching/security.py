"""
Security policy for the Milo coaching agent.

Defines topic boundaries, blocked patterns, and rate limiting
rules to prevent API abuse and keep the bot focused on its
domain: fitness, health, and wellness coaching.
"""

import re
import time
from collections import defaultdict
from typing import Tuple

from utils.logger import setup_logger

logger = setup_logger("milo.security")

# Allowed topic domains — messages must relate to at least one
ALLOWED_TOPICS = {
    "training", "workout", "exercise", "lift", "strength", "hypertrophy",
    "muscle", "sets", "reps", "weight", "squat", "bench", "deadlift",
    "press", "pull", "push", "cardio", "run", "deload", "overload",
    "program", "split", "volume", "intensity", "pr", "gym",
    "sleep", "recovery", "rest", "nap", "insomnia", "circadian",
    "hrv", "heart rate", "whoop",
    "nutrition", "protein", "calories", "carbs", "fat", "meal",
    "diet", "eating", "food", "macro", "supplement", "creatine",
    "hydration", "water", "electrolyte",
    "stress", "meditation", "mindfulness", "habit", "routine",
    "lifestyle", "wellness", "health", "body", "physique",
    "weight loss", "fat loss", "bulk", "cut", "recomp", "lean",
    "bmi", "body fat", "withings", "scale", "measurement",
    "injury", "pain", "mobility", "flexibility", "stretch",
    "warmup", "cooldown", "foam roll",
    "coach", "milo", "progress", "goal", "motivation",
    "hey", "hello", "hi", "thanks", "thank you", "help",
}

# Patterns that indicate prompt injection or off-topic abuse
BLOCKED_PATTERNS = [
    r"ignore\s+(your|all|previous)\s+(instructions|prompts|rules)",
    r"you\s+are\s+now\s+a",
    r"pretend\s+(to\s+be|you\s+are)",
    r"act\s+as\s+(a|an)\s+(?!coach|trainer)",
    r"write\s+(me\s+)?(a|an)\s+(essay|story|poem|script|code|email|letter|resume)",
    r"(translate|summarize|summarise)\s+(this|the|a)",
    r"(what|who)\s+(is|was|are|were)\s+the\s+(president|capital|population)",
    r"help\s+me\s+(with\s+)?(my\s+)?(homework|assignment|exam|test|interview)",
    r"(generate|create|build)\s+(a\s+)?(website|app|program|software|database)",
    r"(explain|teach)\s+(me\s+)?(quantum|javascript|python|coding|programming|math)",
]

# Compile blocked patterns for performance
_blocked_re = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS]

# Rate limiting: max messages per user per window
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 10     # messages per window
_user_timestamps = defaultdict(list)

# Response for off-topic messages
OFF_TOPIC_RESPONSE = (
    "I'm Milo — I only coach on fitness, health, and wellness. "
    "Ask me about training, nutrition, sleep, or lifestyle and I've got you."
)

RATE_LIMIT_RESPONSE = (
    "Slow down — you're sending messages too fast. "
    "Take a breath and try again in a minute."
)

BLOCKED_RESPONSE = (
    "That's outside what I do. I'm a fitness and health coach — "
    "ask me about training, nutrition, sleep, or lifestyle."
)


def check_rate_limit(telegram_id: int) -> bool:
    """Check if a user has exceeded the message rate limit.

    Args:
        telegram_id: The user's Telegram ID.

    Returns:
        True if the user is within limits, False if rate limited.
    """
    now = time.time()
    timestamps = _user_timestamps[telegram_id]

    # Remove timestamps outside the window
    _user_timestamps[telegram_id] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]

    if len(_user_timestamps[telegram_id]) >= RATE_LIMIT_MAX:
        logger.warning(f"Rate limited user {telegram_id}")
        return False

    _user_timestamps[telegram_id].append(now)
    return True


def check_blocked_patterns(message: str) -> bool:
    """Check if a message matches any blocked prompt injection patterns.

    Args:
        message: The user's message text.

    Returns:
        True if the message is safe, False if it matches a blocked pattern.
    """
    for pattern in _blocked_re:
        if pattern.search(message):
            logger.warning(f"Blocked pattern detected: {pattern.pattern}")
            return False
    return True


def check_topic_relevance(message: str) -> bool:
    """Check if a message is related to fitness, health, or wellness.

    Uses keyword matching as a fast pre-filter. Short messages
    (greetings, follow-ups) are allowed through since they're
    likely part of an ongoing coaching conversation.

    Args:
        message: The user's message text.

    Returns:
        True if the message appears on-topic, False otherwise.
    """
    msg_lower = message.lower()

    # Allow short messages — likely greetings or conversational follow-ups
    if len(msg_lower.split()) <= 4:
        return True

    # Check if any allowed topic keyword appears in the message
    for topic in ALLOWED_TOPICS:
        if topic in msg_lower:
            return True

    return False


def validate_message(telegram_id: int, message: str) -> Tuple[bool, str]:
    """Run all security checks on an incoming message.

    Checks are run in order of cost (cheapest first):
    1. Rate limiting
    2. Blocked pattern detection
    3. Topic relevance

    Args:
        telegram_id: The user's Telegram ID.
        message: The user's message text.

    Returns:
        Tuple of (is_allowed, rejection_message).
        If allowed, rejection_message is empty.
    """
    if not check_rate_limit(telegram_id):
        return False, RATE_LIMIT_RESPONSE

    if not check_blocked_patterns(message):
        return False, BLOCKED_RESPONSE

    if not check_topic_relevance(message):
        return False, OFF_TOPIC_RESPONSE

    return True, ""
