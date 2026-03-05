"""
Claude-powered coaching brain for Milo bot.

This module handles all interactions with the Anthropic API,
building context-rich prompts from user data and returning
personalized coaching responses.
"""

import os
from typing import Optional

import anthropic

from coaching.prompts import MILO_SYSTEM_PROMPT
from coaching.security import validate_message
from utils.logger import setup_logger

logger = setup_logger("milo.agent")

MODEL = os.getenv("MILO_MODEL", "claude-sonnet-4-6")

# Lazy client — created on first use so the bot can start without an API key
_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your-anthropic-api-key":
            raise RuntimeError("ANTHROPIC_API_KEY not set in .env")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


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
    whoop = user_context.get("whoop_summary") or user_context.get("whoop_data")
    if whoop:
        sleep_performance = whoop.get("sleep_performance_pct")
        if sleep_performance is None:
            sleep = whoop.get("sleep") or {}
            sleep_performance = sleep.get("sleep_performance_pct")

        sections.append(
            f"[WHOOP DATA]\n"
            f"Recovery: {whoop.get('recovery_score', 'N/A')}%\n"
            f"HRV: {whoop.get('hrv', 'N/A')} ms\n"
            f"Resting HR: {whoop.get('resting_hr', 'N/A')} bpm\n"
            f"Sleep Performance: {sleep_performance if sleep_performance is not None else 'N/A'}%"
        )

    # Withings data
    if user_context.get("withings_data"):
        withings = user_context["withings_data"]
        weight = withings.get("weight_lbs", withings.get("weight", "N/A"))
        body_fat = withings.get("body_fat_pct", withings.get("body_fat", "N/A"))
        muscle_mass = withings.get("muscle_mass_lbs", withings.get("muscle_mass", "N/A"))
        sections.append(
            f"[WITHINGS DATA]\n"
            f"Weight: {weight} lbs\n"
            f"Body Fat: {body_fat}%\n"
            f"Muscle Mass: {muscle_mass} lbs"
        )

    # User profile
    if user_context.get("user_profile"):
        profile = user_context["user_profile"]
        sections.append(
            f"[USER PROFILE]\n"
            f"Sex: {profile.get('sex', 'N/A')}\n"
            f"Age: {profile.get('age_years', 'N/A')}\n"
            f"Height: {profile.get('height_cm', 'N/A')} cm\n"
            f"Goal: {profile.get('primary_goal', 'N/A')}\n"
            f"Experience: {profile.get('experience_level', 'N/A')}\n"
            f"Training Days: {profile.get('training_days_per_week', 'N/A')}"
        )

    # Nutrition state
    if user_context.get("nutrition_state"):
        nutrition = user_context["nutrition_state"]
        sections.append(
            f"[NUTRITION STATE]\n"
            f"Phase: {nutrition.get('phase', 'N/A')}\n"
            f"Mode: {nutrition.get('nutrition_mode', 'N/A')}\n"
            f"Calorie Target: {nutrition.get('current_calorie_target', 'N/A')} kcal\n"
            f"Protein Target: {nutrition.get('current_protein_target_g', 'N/A')} g\n"
            f"Working TDEE: {nutrition.get('working_tdee', 'N/A')} kcal"
        )

    if user_context.get("recovery_status"):
        recovery = user_context["recovery_status"]
        sections.append(
            f"[RECOVERY STATE]\n"
            f"Tier: {recovery.get('composite_tier', 'N/A')}\n"
            f"Score: {recovery.get('composite_score', 'N/A')}\n"
            f"Training Action: {recovery.get('training_action', 'N/A')}\n"
            f"Sleep Duration Status: {recovery.get('sleep_duration_status', 'N/A')}\n"
            f"Sleep Efficiency Status: {recovery.get('sleep_efficiency_status', 'N/A')}"
        )

    if user_context.get("training_guidance"):
        training = user_context["training_guidance"]
        sections.append(
            f"[TRAINING GUIDANCE]\n"
            f"Status: {training.get('training_status', 'N/A')}\n"
            f"Readiness: {training.get('readiness', 'N/A')}\n"
            f"Phase: {training.get('phase', 'N/A')}\n"
            f"Target RIR: {training.get('target_rir', 'N/A')}\n"
            f"Session Adjustment: {training.get('session_adjustment', 'N/A')}\n"
            f"Performance Trend: {training.get('performance_trend', 'N/A')}\n"
            f"Summary: {training.get('summary', 'N/A')}"
        )

    # Workout history
    if user_context.get("workout_history"):
        workouts = user_context["workout_history"][:5]
        workout_lines = []
        for w in workouts:
            weight = w.get("weight_lbs", w.get("weight", "N/A"))
            workout_lines.append(
                f"  - {w['exercise'].title()}: {w['sets']}x{w['reps']} @ {weight} lbs"
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
    telegram_id = user_context.get("telegram_id", 0)

    # Run security checks before hitting the API
    is_allowed, rejection = validate_message(telegram_id, user_message)
    if not is_allowed:
        logger.info(f"Message rejected for user {telegram_id}: {rejection}")
        return rejection

    context_str = build_user_context(user_context)
    full_message = context_str + user_message

    conversation_messages = []
    for item in (user_context.get("chat_history") or [])[-6:]:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            conversation_messages.append({"role": role, "content": content})
    conversation_messages.append({"role": "user", "content": full_message})

    username = user_context.get("username", "there")
    system_prompt = (
        MILO_SYSTEM_PROMPT
        + f"\n\nYou are coaching {username}."
        + "\nWhen nutrition state, recovery state, or training guidance are present, treat them as the primary decision constraints."
        + " Do not contradict calorie/protein targets, recovery actions, or training adjustments unless the user explicitly asks to override them."
    )

    try:
        response = _get_client().messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=conversation_messages,
        )
        return response.content[0].text

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        return "I'm having trouble thinking right now. Try again in a moment."
