"""
Nutrition coaching logic for Milo bot.

Handles protein target calculations, calorie awareness,
meal timing recommendations, and body composition focused
nutrition guidance.
"""

from utils.logger import setup_logger

logger = setup_logger("milo.nutrition")


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
    if unit == "kg":
        body_weight_lbs = body_weight * 2.205
    else:
        body_weight_lbs = body_weight

    return {
        "minimum_g": round(body_weight_lbs * 0.8),
        "maximum_g": round(body_weight_lbs * 1.0),
        "body_weight_lbs": round(body_weight_lbs),
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
