"""
Resistance training coaching logic for Milo bot.

Handles progressive overload tracking, program design,
exercise recommendations, and training load adjustments
based on recovery data.
"""

from __future__ import annotations

from enum import Enum

from utils.logger import setup_logger

logger = setup_logger("milo.training")


class TrainingStatus(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


GENERAL_VOLUME_GUIDE = {
    TrainingStatus.BEGINNER: {
        "minimum_growth_sets": (2, 4),
        "optimal_starting_sets": (5, 10),
        "volume_ceiling_sets": (15, 15),
    },
    TrainingStatus.INTERMEDIATE: {
        "minimum_growth_sets": (5, 8),
        "optimal_starting_sets": (10, 15),
        "volume_ceiling_sets": (20, 25),
    },
    TrainingStatus.ADVANCED: {
        "minimum_growth_sets": (8, 12),
        "optimal_starting_sets": (15, 20),
        "volume_ceiling_sets": (25, 35),
    },
}

BASE_ACCUMULATION_WEEKS = {
    TrainingStatus.BEGINNER: 10,
    TrainingStatus.INTERMEDIATE: 4,
    TrainingStatus.ADVANCED: 3,
}

MESOCYCLE_PHASE_TARGETS = {
    1: {"phase": "accumulation", "target_rir": "3-4", "volume_adjustment": "start_at_mev"},
    2: {"phase": "accumulation", "target_rir": "2-3", "volume_adjustment": "add_1_set"},
    3: {"phase": "accumulation", "target_rir": "2", "volume_adjustment": "add_1_to_2_sets"},
    4: {"phase": "accumulation", "target_rir": "1", "volume_adjustment": "approach_mrv"},
}

DELOAD_TARGET = {"phase": "deload", "target_rir": "4-5", "volume_adjustment": "reduce_volume_50pct"}


def training_status_from_experience_level(experience_level: str | None) -> TrainingStatus:
    value = (experience_level or "intermediate").strip().lower()
    if value == "beginner":
        return TrainingStatus.BEGINNER
    if value == "advanced":
        return TrainingStatus.ADVANCED
    return TrainingStatus.INTERMEDIATE


def get_general_volume_targets(training_status: TrainingStatus) -> dict:
    return GENERAL_VOLUME_GUIDE[training_status]


def get_mesocycle_length(training_status: TrainingStatus, fatigue_level: int | None = None) -> int:
    base = BASE_ACCUMULATION_WEEKS[training_status]
    if fatigue_level is None:
        return base
    if fatigue_level >= 4:
        return max(2, base - 2)
    if fatigue_level <= 2:
        return min(base + 1, 6) if training_status != TrainingStatus.BEGINNER else min(base + 1, 12)
    return base


def _fatigue_level_from_recovery_tier(recovery_status: dict | None) -> int:
    tier = (recovery_status or {}).get("composite_tier")
    if tier == "red":
        return 5
    if tier == "yellow":
        return 4
    if tier == "green":
        return 2
    return 3


def _find_latest_repeated_exercise(history: list[dict]) -> tuple[dict, dict] | None:
    if len(history) < 2:
        return None
    by_exercise = {}
    for workout in history:
        exercise = (workout.get("exercise") or "").lower()
        if not exercise:
            continue
        by_exercise.setdefault(exercise, []).append(workout)
    for workouts in by_exercise.values():
        if len(workouts) >= 2:
            return workouts[0], workouts[1]
    return None


def get_performance_trend(history: list[dict]) -> str:
    pair = _find_latest_repeated_exercise(history)
    if not pair:
        return "unknown"
    latest, previous = pair
    latest_weight = latest.get("weight_lbs", latest.get("weight")) or 0
    previous_weight = previous.get("weight_lbs", previous.get("weight")) or 0
    latest_reps = latest.get("reps") or 0
    previous_reps = previous.get("reps") or 0

    if latest_weight > previous_weight:
        return "improved"
    if latest_weight == previous_weight and latest_reps >= previous_reps:
        return "improved"
    if latest_weight < previous_weight or latest_reps <= previous_reps - 2:
        return "declined"
    return "maintained"


def assess_deload_trigger(
    recovery_status: dict | None,
    performance_trend: str,
    training_status: TrainingStatus,
    weeks_accumulated: int | None = None,
) -> bool:
    if weeks_accumulated is not None and weeks_accumulated >= BASE_ACCUMULATION_WEEKS[training_status]:
        return True

    tier = (recovery_status or {}).get("composite_tier")
    if tier == "red":
        return True

    if performance_trend == "declined" and tier in {"yellow", "red"}:
        return True

    if (recovery_status or {}).get("training_action") == "active_recovery_or_rest":
        return True

    return False


def build_training_guidance(
    recovery_status: dict | None,
    workout_history: list[dict],
    experience_level: str | None = None,
    weeks_accumulated: int | None = None,
) -> dict:
    training_status = training_status_from_experience_level(experience_level)
    fatigue_level = _fatigue_level_from_recovery_tier(recovery_status)
    mesocycle_length = get_mesocycle_length(training_status, fatigue_level=fatigue_level)
    performance_trend = get_performance_trend(workout_history)
    deload_now = assess_deload_trigger(
        recovery_status,
        performance_trend,
        training_status,
        weeks_accumulated=weeks_accumulated,
    )

    if deload_now:
        target = DELOAD_TARGET
        session_adjustment = "deload"
    else:
        week = weeks_accumulated or 1
        target = MESOCYCLE_PHASE_TARGETS.get(min(max(week, 1), 4), MESOCYCLE_PHASE_TARGETS[1])
        tier = (recovery_status or {}).get("composite_tier")
        if tier == "yellow":
            session_adjustment = "hold_or_reduce_1_set"
        elif tier == "red":
            session_adjustment = "active_recovery_or_rest"
        elif performance_trend == "improved":
            session_adjustment = "add_1_set"
        elif performance_trend == "declined":
            session_adjustment = "hold_volume"
        else:
            session_adjustment = target["volume_adjustment"]

    volume_targets = get_general_volume_targets(training_status)
    readiness = calculate_training_readiness((recovery_status or {}).get("composite_score"))

    if deload_now:
        summary = "Training fatigue looks high enough that a deload-style week is the best move right now."
    elif session_adjustment == "add_1_set":
        summary = "Performance is moving in the right direction, so you can add a small amount of volume if recovery stays solid."
    elif session_adjustment == "hold_or_reduce_1_set":
        summary = "Keep training quality high, but hold volume steady or trim it slightly until recovery improves."
    elif session_adjustment == "active_recovery_or_rest":
        summary = "Use today for recovery-focused work instead of pushing hard training volume."
    else:
        summary = "Stay near your current volume and keep execution sharp before adding more work."

    return {
        "training_status": training_status.value,
        "readiness": readiness,
        "mesocycle_length_weeks": mesocycle_length,
        "performance_trend": performance_trend,
        "deload_now": deload_now,
        "phase": target["phase"],
        "target_rir": target["target_rir"],
        "session_adjustment": session_adjustment,
        "volume_targets": volume_targets,
        "summary": summary,
    }


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


def _normalize_exercise_name(exercise: str | None) -> str:
    return (exercise or "").strip().lower()


def _get_workout_weight(workout: dict) -> float | None:
    weight = workout.get("weight_lbs", workout.get("weight"))
    if weight is None:
        return None
    return float(weight)


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
    normalized_exercise = _normalize_exercise_name(exercise)
    exercise_history = [
        workout
        for workout in history
        if _normalize_exercise_name(workout.get("exercise")) == normalized_exercise
    ]

    if len(exercise_history) < 2:
        return None

    latest = exercise_history[0]
    previous = exercise_history[1]
    latest_weight = _get_workout_weight(latest)
    previous_weight = _get_workout_weight(previous)
    latest_reps = int(latest.get("reps") or 0)
    previous_reps = int(previous.get("reps") or 0)
    latest_sets = int(latest.get("sets") or 0)
    previous_sets = int(previous.get("sets") or 0)

    if latest_weight is None or previous_weight is None:
        return None

    # If the user hit all prescribed reps at the same weight, suggest progression
    if latest_weight == previous_weight and (
        latest_reps > previous_reps or (latest_reps == previous_reps and latest_sets >= previous_sets)
    ):
        return {
            "exercise": exercise,
            "current_weight": latest_weight,
            "suggested_weight": latest_weight + 5,
            "reason": "You matched or beat your last session at the same load — consider a small weight increase next time.",
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
