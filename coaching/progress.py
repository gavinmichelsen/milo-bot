from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone


def _to_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None


def _format_weight_delta(delta: float) -> str:
    if delta > 0:
        return f"up {delta:.1f} lb"
    if delta < 0:
        return f"down {abs(delta):.1f} lb"
    return "flat"


def build_weekly_progress_summary(
    recovery_statuses: list[dict],
    body_metrics: list[dict],
    workouts: list[dict],
    nutrition_state: dict | None,
) -> str | None:
    lines = ["Weekly summary", ""]
    included_sections = 0

    if recovery_statuses:
        counts = Counter(status.get("composite_tier") for status in recovery_statuses if status.get("composite_tier"))
        avg_score_values = [_to_float(status.get("composite_score")) for status in recovery_statuses]
        avg_score_values = [value for value in avg_score_values if value is not None]
        if counts or avg_score_values:
            avg_score = round(sum(avg_score_values) / len(avg_score_values), 1) if avg_score_values else None
            lines.append("Recovery")
            if avg_score is not None:
                lines.append(f"- Average recovery score: {avg_score}")
            lines.append(
                f"- Tier mix: {counts.get('green', 0)} green, {counts.get('yellow', 0)} yellow, {counts.get('red', 0)} red"
            )
            lines.append("")
            included_sections += 1

    if workouts:
        now = datetime.now(timezone.utc)
        week_workouts = []
        for workout in workouts:
            logged_at = _parse_dt(workout.get("logged_at"))
            if logged_at is None or logged_at >= now - timedelta(days=7):
                week_workouts.append(workout)
        if week_workouts:
            unique_exercises = len({workout.get("exercise") for workout in week_workouts if workout.get("exercise")})
            lines.append("Training")
            lines.append(f"- Logged {len(week_workouts)} workout entries across {unique_exercises} exercises")
            lines.append("")
            included_sections += 1

    if body_metrics:
        weights = [_to_float(metric.get("weight_lbs")) for metric in body_metrics]
        weights = [weight for weight in weights if weight is not None]
        if weights:
            latest_weight = weights[0]
            oldest_weight = weights[-1]
            lines.append("Body metrics")
            lines.append(f"- Latest weight: {latest_weight:.1f} lb")
            if len(weights) >= 2:
                lines.append(f"- Trend: {_format_weight_delta(latest_weight - oldest_weight)} this week")
            latest_body_fat = _to_float(body_metrics[0].get("body_fat_pct"))
            if latest_body_fat is not None:
                lines.append(f"- Latest body fat: {latest_body_fat:.1f}%")
            lines.append("")
            included_sections += 1

    if nutrition_state:
        lines.append("Nutrition")
        lines.append(f"- Phase: {nutrition_state.get('phase', 'N/A')}")
        lines.append(f"- Calorie target: {nutrition_state.get('current_calorie_target', 'N/A')} kcal")
        lines.append(f"- Protein target: {nutrition_state.get('current_protein_target_g', 'N/A')} g")
        lines.append("")
        included_sections += 1

    if included_sections == 0:
        return None

    red_days = sum(1 for status in recovery_statuses if status.get("composite_tier") == "red")
    yellow_days = sum(1 for status in recovery_statuses if status.get("composite_tier") == "yellow")
    if red_days >= 2:
        focus = "Keep the next week recovery-friendly and be ready to pull intensity down early if fatigue lingers."
    elif yellow_days >= 3:
        focus = "Recovery has been okay but not perfect, so prioritize sleep and keep your hardest work high-quality."
    else:
        focus = "Keep stacking consistent training, protein, and sleep habits into next week."

    lines.append(f"Next focus: {focus}")
    return "\n".join(lines)
