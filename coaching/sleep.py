"""
Sleep coaching logic for Milo bot.

Analyzes Whoop sleep data to provide recovery optimization
recommendations and sleep hygiene guidance.
"""

from utils.logger import setup_logger

logger = setup_logger("milo.sleep")


def assess_sleep_quality(sleep_data: dict | None) -> dict:
    """Assess sleep quality from Whoop sleep data.

    Args:
        sleep_data: Whoop sleep response dict, or None if unavailable.

    Returns:
        Dict with quality rating, summary, and recommendations.
    """
    if sleep_data is None:
        return {
            "rating": "unknown",
            "summary": "No sleep data available yet.",
            "recommendations": [
                "Connect your Whoop to start tracking sleep quality.",
                "Aim for 7-9 hours of sleep per night.",
                "Keep a consistent sleep and wake time.",
            ],
        }

    # Placeholder scoring — will be refined with real Whoop data structure
    return {
        "rating": "good",
        "summary": "Sleep data connected. Detailed analysis coming soon.",
        "recommendations": [
            "Maintain your consistent sleep schedule.",
            "Keep your room cool (65-68F) for optimal sleep quality.",
            "Avoid screens 30-60 minutes before bed.",
        ],
    }


def get_sleep_recommendations(recovery_score: float | None) -> list[str]:
    """Generate sleep recommendations based on recovery status.

    Args:
        recovery_score: Whoop recovery percentage (0-100), or None.

    Returns:
        List of actionable sleep recommendations.
    """
    base_tips = [
        "Keep a consistent sleep schedule — even on weekends.",
        "Aim for 7-9 hours of actual sleep time.",
    ]

    if recovery_score is None:
        return base_tips

    if recovery_score < 34:
        return [
            "Your recovery is low — prioritize sleep above everything tonight.",
            "Get to bed 30-60 minutes earlier than usual.",
            "Skip caffeine after noon to improve sleep quality.",
            "Consider a rest day or light session tomorrow.",
        ]
    elif recovery_score < 67:
        return base_tips + [
            "Your recovery is moderate. A solid night of sleep will get you back to green.",
        ]
    else:
        return base_tips + [
            "Recovery is strong — your sleep is working. Keep doing what you're doing.",
        ]
