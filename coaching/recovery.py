from __future__ import annotations


def _to_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _avg(values: list[float | None]) -> float | None:
    valid = [value for value in values if value is not None]
    if not valid:
        return None
    return sum(valid) / len(valid)


def _points(status: str) -> int:
    if status == "green":
        return 2
    if status == "yellow":
        return 1
    if status == "red":
        return 0
    return 1


def _score_to_tier(score: float | None) -> str:
    if score is None:
        return "insufficient_data"
    if score >= 55:
        return "green"
    if score >= 35:
        return "yellow"
    return "red"


def _status_from_absolute(value: float | None, green_floor: float, yellow_floor: float) -> str:
    if value is None:
        return "insufficient_data"
    if value >= green_floor:
        return "green"
    if value >= yellow_floor:
        return "yellow"
    return "red"


def _status_from_rhr(recent_avg: float | None, baseline_avg: float | None) -> str:
    if recent_avg is None or baseline_avg is None:
        return "insufficient_data"
    delta = recent_avg - baseline_avg
    if delta < 3:
        return "green"
    if delta <= 5:
        return "yellow"
    return "red"


def _status_from_hrv(recent_avg: float | None, baseline_avg: float | None) -> str:
    if recent_avg is None or baseline_avg is None or baseline_avg <= 0:
        return "insufficient_data"
    pct_delta = ((recent_avg - baseline_avg) / baseline_avg) * 100
    if pct_delta >= -5:
        return "green"
    if pct_delta >= -15:
        return "yellow"
    return "red"


def _status_from_recovery_score(value: float | None) -> str:
    if value is None:
        return "insufficient_data"
    if value >= 67:
        return "green"
    if value >= 34:
        return "yellow"
    return "red"


def _build_message(tier: str, training_action: str, sleep_duration_status: str, sleep_efficiency_status: str, streak: int) -> str | None:
    sleep_flag = sleep_duration_status in {"yellow", "red"} or sleep_efficiency_status in {"yellow", "red"}
    if tier == "green":
        return None
    if tier == "yellow":
        if streak >= 1:
            message = "Still in an adaptation phase today, so keep training a little lighter than planned and let recovery catch up."
        else:
            message = "Your body looks like it is working through a heavier adaptation phase today, so keep the session a bit lighter than planned."
        if sleep_flag:
            return message + " The biggest lever right now is sleep, so aim for an earlier night and a low-stress evening."
        return message + " Focus on good food, hydration, and a normal bedtime tonight."
    if tier == "red":
        if streak >= 1:
            message = "Recovery still needs to be the priority today, so skip hard training and stick to easy movement or full rest."
        else:
            message = "Your body is giving strong signals that recovery should be the priority today, so skip hard training and choose easy movement or full rest."
        if sleep_flag:
            return message + " Prioritize sleep tonight and keep the rest of the day as low-friction as possible."
        return message + " Treat recovery as part of the program, not a setback."
    return None


def evaluate_recovery(snapshots: list[dict], previous_statuses: list[dict] | None = None) -> dict:
    rows = snapshots or []
    previous_statuses = previous_statuses or []
    if not rows:
        return {
            "composite_tier": "insufficient_data",
            "baseline_ready": False,
            "should_send": False,
            "training_action": "train_as_programmed",
            "message_text": None,
        }

    latest = rows[0]
    snapshot_date = latest.get("snapshot_date")
    recovery_status = _status_from_recovery_score(_to_float(latest.get("recovery_score")))

    if len(rows) < 7:
        composite_score = 50.0 if recovery_status == "insufficient_data" else float(_points(recovery_status) * 25)
        tier = _score_to_tier(composite_score)
        training_action = {
            "green": "train_as_programmed",
            "yellow": "reduce_intensity_20_30",
            "red": "active_recovery_or_rest",
            "insufficient_data": "train_as_programmed",
        }[tier]
        return {
            "snapshot_date": snapshot_date,
            "composite_score": round(composite_score, 1),
            "composite_tier": tier,
            "hrv_status": "insufficient_data",
            "rhr_status": "insufficient_data",
            "sleep_duration_status": "insufficient_data",
            "sleep_efficiency_status": "insufficient_data",
            "baseline_ready": False,
            "should_send": tier in {"yellow", "red"},
            "training_action": training_action,
            "message_text": _build_message(tier, training_action, "insufficient_data", "insufficient_data", 0),
        }

    recent_rows = rows[:7]
    baseline_rows = rows[7:30]
    baseline_ready = len(rows) >= 14 and len(baseline_rows) >= 7

    recent_hrv = _avg([_to_float(row.get("hrv")) for row in recent_rows])
    baseline_hrv = _avg([_to_float(row.get("hrv")) for row in baseline_rows])
    hrv_status = _status_from_hrv(recent_hrv, baseline_hrv if baseline_ready else None)

    recent_rhr = _avg([_to_float(row.get("resting_hr")) for row in recent_rows])
    baseline_rhr = _avg([_to_float(row.get("resting_hr")) for row in baseline_rows])
    rhr_status = _status_from_rhr(recent_rhr, baseline_rhr if baseline_ready else None)

    recent_sleep_duration = _avg([_to_float(row.get("sleep_duration_hrs")) for row in recent_rows])
    sleep_duration_status = _status_from_absolute(recent_sleep_duration, 7.0, 6.0)

    recent_sleep_efficiency = _avg([_to_float(row.get("sleep_efficiency_pct")) for row in recent_rows])
    sleep_efficiency_status = _status_from_absolute(recent_sleep_efficiency, 80.0, 70.0)

    status_values = [
        status
        for status in [hrv_status, rhr_status, sleep_duration_status, sleep_efficiency_status, recovery_status]
        if status != "insufficient_data"
    ]
    if not status_values:
        composite_score = None
    else:
        composite_score = (sum(_points(status) for status in status_values) / (len(status_values) * 2)) * 100

    tier = _score_to_tier(composite_score)
    training_action = {
        "green": "train_as_programmed",
        "yellow": "reduce_intensity_20_30",
        "red": "active_recovery_or_rest",
        "insufficient_data": "train_as_programmed",
    }[tier]

    streak = 0
    for status in previous_statuses:
        if status.get("composite_tier") == tier:
            streak += 1
        else:
            break

    should_send = tier in {"yellow", "red"}
    message_text = _build_message(tier, training_action, sleep_duration_status, sleep_efficiency_status, streak)

    return {
        "snapshot_date": snapshot_date,
        "composite_score": round(composite_score, 1) if composite_score is not None else None,
        "composite_tier": tier,
        "hrv_status": hrv_status,
        "rhr_status": rhr_status,
        "sleep_duration_status": sleep_duration_status,
        "sleep_efficiency_status": sleep_efficiency_status,
        "baseline_ready": baseline_ready,
        "should_send": should_send,
        "training_action": training_action,
        "message_text": message_text,
    }
