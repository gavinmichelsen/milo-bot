"""
Nutrition coaching logic for Milo bot.

Handles protein target calculations, calorie awareness,
meal timing recommendations, and body composition focused
nutrition guidance.
"""

from __future__ import annotations

from enum import Enum

from utils.logger import setup_logger

logger = setup_logger("milo.nutrition")

PROTEIN_TARGET_G_PER_LB = 0.82


class NutritionalPhase(str, Enum):
    CUT = "cut"
    MAINTENANCE = "maintenance"
    LEAN_BULK = "lean_bulk"


def phase_from_goal(primary_goal: str | None) -> NutritionalPhase:
    goal = (primary_goal or "maintain").lower()
    if goal == "fat_loss":
        return NutritionalPhase.CUT
    if goal == "muscle_gain":
        return NutritionalPhase.LEAN_BULK
    return NutritionalPhase.MAINTENANCE


def _to_lbs(body_weight: float, unit: str) -> float:
    if unit == "kg":
        return body_weight * 2.205
    return body_weight


def _to_kg(body_weight: float, unit: str) -> float:
    if unit == "lbs":
        return body_weight / 2.205
    return body_weight


def calculate_mifflin_st_jeor_bmr(weight_kg: float, height_cm: float, age_years: int, sex: str) -> float:
    sex_term = 5 if sex.lower() == "male" else -161
    return (10 * weight_kg) + (6.25 * height_cm) - (5 * age_years) + sex_term


def estimate_initial_tdee(
    body_weight: float,
    height_cm: float,
    age_years: int,
    sex: str,
    activity_multiplier: float = 1.55,
    unit: str = "lbs",
) -> int:
    weight_kg = _to_kg(body_weight, unit)
    bmr = calculate_mifflin_st_jeor_bmr(weight_kg, height_cm, age_years, sex)
    return round(bmr * activity_multiplier)


def get_phase_rate_target(phase: NutritionalPhase, experience_level: str = "intermediate") -> float:
    if phase == NutritionalPhase.CUT:
        return -0.75
    if phase == NutritionalPhase.MAINTENANCE:
        return 0.0
    if experience_level == "beginner":
        return 0.375
    return 0.175


def calculate_calorie_target(working_tdee: int, phase: NutritionalPhase, experience_level: str = "intermediate") -> int:
    if phase == NutritionalPhase.CUT:
        return round(working_tdee - 400)
    if phase == NutritionalPhase.MAINTENANCE:
        return round(working_tdee)
    if experience_level == "beginner":
        return round(working_tdee + 275)
    return round(working_tdee + 150)


def calculate_protein_target(body_weight: float, unit: str = "lbs") -> dict:
    """Calculate daily protein target based on body weight.

    Uses the evidence-based range of 0.8-1.0g per pound of body weight
    for individuals focused on building or maintaining muscle.

    Args:
        body_weight: User's current body weight.
        unit: Weight unit — 'lbs' or 'kg'.

    Returns:
        Dict with minimum and maximum daily protein targets in grams.
    """
    body_weight_lbs = _to_lbs(body_weight, unit)

    return {
        "minimum_g": round(body_weight_lbs * 0.8),
        "target_g": round(body_weight_lbs * PROTEIN_TARGET_G_PER_LB),
        "maximum_g": round(body_weight_lbs * 1.0),
        "body_weight_lbs": round(body_weight_lbs),
    }


def build_nutrition_targets(
    body_weight: float,
    height_cm: float,
    age_years: int,
    sex: str,
    phase: NutritionalPhase,
    activity_multiplier: float = 1.55,
    unit: str = "lbs",
    experience_level: str = "intermediate",
    adaptive_tdee: int | None = None,
) -> dict:
    protein = calculate_protein_target(body_weight, unit=unit)
    estimated_tdee = estimate_initial_tdee(
        body_weight=body_weight,
        height_cm=height_cm,
        age_years=age_years,
        sex=sex,
        activity_multiplier=activity_multiplier,
        unit=unit,
    )
    working_tdee = adaptive_tdee or estimated_tdee
    calorie_target = calculate_calorie_target(
        working_tdee=working_tdee,
        phase=phase,
        experience_level=experience_level,
    )

    return {
        "phase": phase.value,
        "estimated_tdee": estimated_tdee,
        "adaptive_tdee": adaptive_tdee,
        "working_tdee": working_tdee,
        "calorie_target": calorie_target,
        "protein_target_g": protein["target_g"],
        "goal_rate_pct_per_week": get_phase_rate_target(phase, experience_level=experience_level),
    }


def get_meal_timing_advice(training_time: str | None) -> str:
    """Generate meal timing recommendations around training.

    Args:
        training_time: Approximate training time (e.g. 'morning', 'evening'),
                       or None if unknown.

    Returns:
        Meal timing recommendation string.
    """
    if training_time is None:
        return (
            "Aim for a meal with protein and carbs 2-3 hours before training, "
            "and a protein-rich meal within 1-2 hours after. "
            "Total daily protein matters more than exact timing."
        )

    if training_time == "morning":
        return (
            "For morning training: have a light meal or shake 30-60 minutes before "
            "(banana + whey works great). Prioritize a solid post-workout meal with "
            "30-40g protein and carbs to kickstart recovery."
        )

    return (
        "For evening training: your pre-workout meal is lunch or an afternoon snack — "
        "make sure it includes protein and carbs. Post-workout dinner should be your "
        "biggest protein meal of the day."
    )
