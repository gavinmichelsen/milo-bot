"""
Resistance training coaching logic for Milo bot.

Handles progressive overload tracking, program design,
exercise recommendations, and training load adjustments
based on recovery data.
"""

from utils.logger import setup_logger

logger = setup_logger("milo.training")


def calculate_training_readiness(recovery_score: float | None) -> str:
    """Determine training intensity recommendation based on Whoop recovery.

    Args:
        recovery_score: Whoop recovery percentage (0-100), or None if unavailable.

    Returns:
        Training intensity recommendation string.
    """
    if recovery_score is None:
        return "moderate"

    if recovery_score >= 67:
        return "high"
    elif recovery_score >= 34:
        return "moderate"
    else:
        return "low"


def check_progressive_overload(history: list[dict], exercise: str) -> dict | None:
    """Analyze workout history to detect progressive overload opportunities.

    Looks at the last few sessions for a given exercise and determines
    whether the user is ready to increase weight, reps, or sets.

    Args:
        history: List of workout log dicts with exercise, sets, reps, weight.
        exercise: The exercise name to analyze.

    Returns:
        Dict with overload recommendation, or None if insufficient data.
    """
    exercise_history = [w for w in history if w.get("exercise", "").lower() == exercise.lower()]

    if len(exercise_history) < 2:
        return None

    latest = exercise_history[0]
    previous = exercise_history[1]

    # If the user hit all prescribed reps at the same weight, suggest progression
    if latest["weight"] == previous["weight"] and latest["reps"] >= previous["reps"]:
        return {
            "exercise": exercise,
            "current_weight": latest["weight"],
            "suggested_weight": latest["weight"] + 5,
            "reason": "You hit your target reps — time to add weight. Progressive overload in action.",
        }

    return None


def format_workout_log(exercise: str, sets: int, reps: int, weight: float) -> str:
    """Format a workout entry for display.

    Args:
        exercise: Exercise name.
        sets: Number of sets.
        reps: Number of reps per set.
        weight: Weight used.

    Returns:
        Formatted string like 'Bench Press — 3x5 @ 185 lbs'.
    """
    return f"{exercise.title()} — {sets}x{reps} @ {int(weight)} lbs"
