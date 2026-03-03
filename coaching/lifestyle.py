"""
Lifestyle coaching logic for Milo bot.

Covers stress management, HRV trend analysis, daily habits,
hydration, and longevity-focused recommendations.
"""

from utils.logger import setup_logger

logger = setup_logger("milo.lifestyle")


def analyze_hrv_trend(hrv_values: list[float]) -> dict:
    """Analyze HRV trend over recent days to assess stress and recovery.

    A declining HRV trend often signals accumulated stress, poor recovery,
    or overtraining. A rising trend indicates good adaptation.

    Args:
        hrv_values: List of daily HRV readings (most recent last).

    Returns:
        Dict with trend direction, interpretation, and recommendation.
    """
    if len(hrv_values) < 3:
        return {
            "trend": "insufficient_data",
            "interpretation": "Need at least 3 days of HRV data to identify a trend.",
            "recommendation": "Keep wearing your Whoop consistently to build a baseline.",
        }

    recent_avg = sum(hrv_values[-3:]) / 3
    older_avg = sum(hrv_values[:-3]) / max(len(hrv_values[:-3]), 1)

    if recent_avg > older_avg * 1.05:
        return {
            "trend": "improving",
            "interpretation": "Your HRV is trending up — your body is adapting well.",
            "recommendation": "You're in a good position to push training intensity.",
        }
    elif recent_avg < older_avg * 0.95:
        return {
            "trend": "declining",
            "interpretation": "Your HRV is trending down — possible accumulated stress or fatigue.",
            "recommendation": "Consider a deload, extra sleep, or reducing life stressors this week.",
        }
    else:
        return {
            "trend": "stable",
            "interpretation": "Your HRV is stable — maintaining a solid baseline.",
            "recommendation": "Stay consistent with your current routine.",
        }


def get_daily_habits_checklist() -> list[str]:
    """Return a daily habits checklist for optimal performance.

    Returns:
        List of daily habit recommendations.
    """
    return [
        "Get 10-15 minutes of morning sunlight exposure",
        "Drink at least half your body weight (lbs) in ounces of water",
        "Hit your protein target across 3-4 meals",
        "Move for at least 30 minutes outside of training",
        "Wind down 30-60 minutes before bed — no screens",
    ]
