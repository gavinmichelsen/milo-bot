"""
Claude-powered coaching brain for Milo bot.

This module handles all interactions with the Anthropic API,
building context-rich prompts from user data and returning
personalized coaching responses.
"""

import os

import anthropic

from coaching.prompts import MILO_SYSTEM_PROMPT
from utils.logger import setup_logger

logger = setup_logger("milo.agent")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-4-20250514"


def build_user_context(user_context: dict) -> str:
    """Build a context string from available user data.

    Assembles Whoop recovery, Withings body metrics, and workout
    history into a structured context block that gets prepended
    to the user's message for the coaching agent.

    Args:
        user_context: Dict containing user data from various sources.

    Returns:
        Formatted context string, or empty string if no data available.
    """
    sections = []

    # Whoop data
    if user_context.get("whoop_data"):
        whoop = user_context["whoop_data"]
        sections.append(
            f"[WHOOP DATA]\n"
            f"Recovery: {whoop.get('recovery_score', 'N/A')}%\n"
            f"HRV: {whoop.get('hrv', 'N/A')} ms\n"
            f"Resting HR: {whoop.get('resting_hr', 'N/A')} bpm\n"
            f"Sleep Performance: {whoop.get('sleep_score', 'N/A')}%"
        )

    # Withings data
    if user_context.get("withings_data"):
        withings = user_context["withings_data"]
        sections.append(
            f"[WITHINGS DATA]\n"
            f"Weight: {withings.get('weight', 'N/A')} lbs\n"
            f"Body Fat: {withings.get('body_fat', 'N/A')}%\n"
            f"Muscle Mass: {withings.get('muscle_mass', 'N/A')} lbs"
        )

    # Workout history
    if user_context.get("workout_history"):
        workouts = user_context["workout_history"][:5]
        workout_lines = []
        for w in workouts:
            workout_lines.append(
                f"  - {w['exercise'].title()}: {w['sets']}x{w['reps']} @ {w['weight']} lbs"
            )
        sections.append(f"[RECENT WORKOUTS]\n" + "\n".join(workout_lines))

    if not sections:
        return ""

    return "--- USER DATA ---\n" + "\n\n".join(sections) + "\n--- END USER DATA ---\n\n"


async def get_coaching_response(user_message: str, user_context: dict) -> str:
    """Generate a coaching response using the Claude API.

    Builds context from the user's available data (Whoop, Withings,
    workout history) and sends it alongside the user's message to
    Claude for a personalized coaching response.

    Args:
        user_message: The user's text message from Telegram.
        user_context: Dict with user data (whoop_data, withings_data, workout_history).

    Returns:
        Coaching response string from Claude.
    """
    context_str = build_user_context(user_context)
    full_message = context_str + user_message

    username = user_context.get("username", "there")

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=MILO_SYSTEM_PROMPT + f"\n\nYou are coaching {username}.",
            messages=[{"role": "user", "content": full_message}],
        )
        return response.content[0].text

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        return "I'm having trouble thinking right now. Try again in a moment."
