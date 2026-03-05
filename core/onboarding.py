from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from core.database import get_onboarding_state, upsert_onboarding_state, upsert_user_profile
from core.user_context import build_user_context

WELCOME_PROMPT = (
    "Hey! I'm Milo, your AI fitness coach. I'm going to help you build a training plan and dial in your nutrition — all over Telegram.\n\n"
    "Before I can build anything useful, I need to get to know you a bit. It'll take maybe 10 minutes and I'll ask questions in chunks so it doesn't feel like a questionnaire. Ready to get started?"
)

MEDICAL_PROMPT = (
    "Before we get started — just to keep things legit: I'm an AI fitness coach, not a doctor. Everything I give you is general fitness and nutrition guidance, not medical advice. If you have any health conditions, injuries, or concerns, please check in with a physician before starting a new training or nutrition program. That goes double if you're under 18 — I'll need you (or a parent) to confirm you've consulted or will consult a doctor before we begin. Sound good?\n\n"
    "Are you 18 or older?"
)

MINOR_CLEARANCE_PROMPT = (
    "Got it. I can absolutely work with you, but I want to make sure a parent or guardian is aware, and that you've either spoken to a doctor or plan to before starting any new training program. Can you confirm that's the case?"
)

BASICS_PROMPT = (
    "Alright, let's start with the basics.\n\n"
    "Three quick ones:\n"
    "1. Are you male or female?\n"
    "2. How tall are you? Feet/inches or cm, either works.\n"
    "3. How old are you?"
)

WEIGHT_PROMPT = (
    "Now for weight:\n"
    "- What do you weigh right now? lbs or kg — your choice.\n"
    "- And do you happen to know your body fat percentage? If not, totally fine — I'll work with what I have."
)

TRAINING_PROMPT = (
    "A few questions about your training history:\n\n"
    "1. How long have you been lifting consistently? Even a rough answer is fine — like 'never really been consistent' or '2 years mostly.'\n"
    "2. Do you have any injuries or movement issues I should know about? Dodgy knee, shoulder that doesn't like pressing, that kind of thing."
)

INJURY_FOLLOWUP_PROMPT = (
    "Thanks for telling me that — I'll build around it. A couple follow-up questions: Is this something that's been diagnosed and/or rehabbed, or is it more of an 'it hurts when I do X' situation? And is it currently painful day to day, or only during certain movements?"
)

GOAL_PROMPT = (
    "Now for what you actually want:\n\n"
    "1. What's your main goal right now? Getting bigger, getting leaner, or both — basically improving how you look and what you can do?\n"
    "2. How many days per week can you realistically train? Be honest — 3 consistent days beats 5 days when you skip two."
)

EQUIPMENT_PROMPT = (
    "Last couple of logistical questions:\n\n"
    "1. What's your equipment situation? Full gym with barbells, machines, everything — or more of a home gym or minimal setup?\n"
    "2. Do you have any preference for how your training looks — more upper body focus, lower body, arms, or just balanced across everything?"
)

NUTRITION_PROMPT = (
    "Now for nutrition. I can work with you two ways:\n\n"
    "*Option 1 — Tracked:* I give you a calorie target and macros, you log your food. More precise, more effort.\n\n"
    "*Option 2 — Habit-based (no tracking):* I coach you using food habits and heuristics. No calorie counting. Works great for most people, especially when you're starting out.\n\n"
    "Which sounds more like you?"
)

WEARABLES_PROMPT = (
    "One last thing — do you use any fitness wearables? Specifically:\n"
    "- Whoop (gives me HRV, recovery, sleep data)\n"
    "- Withings scale (gives me body composition trends)\n\n"
    "If you have either, I can use that data to make smarter recommendations on a day-to-day basis. If you don't, that's fine — plenty of people make great progress without them."
)

COMMUNICATION_PROMPT = (
    "Last thing — how much do you want to hear from me?\n\n"
    "Some people like a daily check-in. Others prefer I reach out a few times a week when there's something worth saying. What works for you?"
)

YES_WORDS = {"yes", "y", "yeah", "yep", "sure", "ok", "okay", "ready", "sounds good", "good", "correct", "absolutely"}
ESSENTIAL_FIELDS = {
    "sex",
    "age_years",
    "height_cm",
    "body_weight_lbs",
    "primary_goal",
    "training_days_per_week",
    "nutrition_mode",
}

SESSION_LIBRARY = {
    "full_gym": {
        "A": [
            ("Back Squat", "5-8", "150s", "lower_compound"),
            ("Chest-Supported Row", "6-10", "150s", "upper_compound"),
            ("Bench Press", "6-10", "150s", "upper_compound"),
            ("Romanian Deadlift", "8-12", "120s", "lower_compound"),
            ("DB Lateral Raise", "12-15", "60s", "upper_accessory"),
            ("DB Curl", "10-15", "60s", "arms_accessory"),
            ("Tricep Pushdown", "10-15", "60s", "arms_accessory"),
        ],
        "B": [
            ("Leg Press", "8-12", "150s", "lower_compound"),
            ("Lat Pulldown", "8-12", "120s", "upper_compound"),
            ("Incline DB Press", "8-12", "120s", "upper_compound"),
            ("Seated Hamstring Curl", "10-15", "75s", "lower_accessory"),
            ("Rear Delt Fly", "12-20", "60s", "upper_accessory"),
            ("Overhead Tricep Extension", "10-15", "60s", "arms_accessory"),
            ("Standing Calf Raise", "10-15", "60s", "lower_accessory"),
        ],
        "C": [
            ("Front Squat", "5-8", "150s", "lower_compound"),
            ("Cable Row", "8-12", "120s", "upper_compound"),
            ("Overhead Press", "6-10", "120s", "upper_compound"),
            ("Bulgarian Split Squat", "8-12", "90s", "lower_compound"),
            ("Cable Lateral Raise", "12-20", "60s", "upper_accessory"),
            ("Hammer Curl", "10-15", "60s", "arms_accessory"),
            ("Cable Crunch", "10-15", "60s", "core_accessory"),
        ],
        "D": [
            ("Hack Squat", "8-12", "150s", "lower_compound"),
            ("Pull-Up or Assisted Pull-Up", "6-10", "120s", "upper_compound"),
            ("Machine Chest Press", "8-12", "120s", "upper_compound"),
            ("Hip Thrust", "8-12", "120s", "lower_compound"),
            ("Face Pull", "12-20", "60s", "upper_accessory"),
            ("EZ-Bar Curl", "10-15", "60s", "arms_accessory"),
            ("Cable Pressdown", "10-15", "60s", "arms_accessory"),
        ],
    },
    "home_gym": {
        "A": [
            ("Back Squat", "5-8", "150s", "lower_compound"),
            ("Barbell Row", "6-10", "120s", "upper_compound"),
            ("Bench Press", "6-10", "150s", "upper_compound"),
            ("Romanian Deadlift", "8-12", "120s", "lower_compound"),
            ("DB Lateral Raise", "12-15", "60s", "upper_accessory"),
            ("DB Curl", "10-15", "60s", "arms_accessory"),
            ("Lying Tricep Extension", "10-15", "60s", "arms_accessory"),
        ],
        "B": [
            ("Front Squat or Goblet Squat", "8-12", "120s", "lower_compound"),
            ("Pull-Up or Band Pulldown", "6-10", "120s", "upper_compound"),
            ("Incline DB Press", "8-12", "120s", "upper_compound"),
            ("Split Squat", "8-12", "90s", "lower_compound"),
            ("Rear Delt Raise", "12-20", "60s", "upper_accessory"),
            ("Hammer Curl", "10-15", "60s", "arms_accessory"),
            ("Standing Calf Raise", "12-20", "60s", "lower_accessory"),
        ],
        "C": [
            ("Deadlift", "4-6", "150s", "lower_compound"),
            ("One-Arm DB Row", "8-12", "90s", "upper_compound"),
            ("Overhead Press", "6-10", "120s", "upper_compound"),
            ("DB Romanian Deadlift", "8-12", "90s", "lower_compound"),
            ("DB Lateral Raise", "12-20", "60s", "upper_accessory"),
            ("Close-Grip Push-Up", "8-15", "60s", "arms_accessory"),
            ("Hanging Knee Raise", "10-15", "60s", "core_accessory"),
        ],
        "D": [
            ("Pause Squat", "5-8", "150s", "lower_compound"),
            ("Chest-Supported DB Row", "8-12", "90s", "upper_compound"),
            ("Flat DB Press", "8-12", "120s", "upper_compound"),
            ("Hip Thrust", "8-12", "120s", "lower_compound"),
            ("Band Face Pull", "12-20", "60s", "upper_accessory"),
            ("DB Curl", "10-15", "60s", "arms_accessory"),
            ("Skull Crusher", "10-15", "60s", "arms_accessory"),
        ],
    },
    "minimal": {
        "A": [
            ("Goblet Squat", "8-12", "90s", "lower_compound"),
            ("One-Arm DB Row", "8-12", "90s", "upper_compound"),
            ("Push-Up", "8-15", "75s", "upper_compound"),
            ("DB Romanian Deadlift", "10-15", "90s", "lower_compound"),
            ("DB Lateral Raise", "12-20", "60s", "upper_accessory"),
            ("DB Curl", "10-15", "60s", "arms_accessory"),
            ("Overhead Tricep Extension", "10-15", "60s", "arms_accessory"),
        ],
        "B": [
            ("Split Squat", "8-12", "90s", "lower_compound"),
            ("Band or Inverted Row", "8-15", "75s", "upper_compound"),
            ("DB Floor Press", "8-12", "90s", "upper_compound"),
            ("Single-Leg Romanian Deadlift", "10-12", "75s", "lower_compound"),
            ("Rear Delt Raise", "12-20", "60s", "upper_accessory"),
            ("Hammer Curl", "10-15", "60s", "arms_accessory"),
            ("Standing Calf Raise", "15-20", "60s", "lower_accessory"),
        ],
        "C": [
            ("Tempo Goblet Squat", "10-15", "90s", "lower_compound"),
            ("One-Arm DB Row", "10-15", "75s", "upper_compound"),
            ("Pike Push-Up or DB Press", "8-12", "75s", "upper_compound"),
            ("Glute Bridge", "12-20", "75s", "lower_compound"),
            ("DB Lateral Raise", "12-20", "60s", "upper_accessory"),
            ("DB Curl", "10-15", "60s", "arms_accessory"),
            ("Dead Bug", "8-12/side", "45s", "core_accessory"),
        ],
        "D": [
            ("Reverse Lunge", "8-12", "75s", "lower_compound"),
            ("Band Row", "10-15", "60s", "upper_compound"),
            ("Feet-Elevated Push-Up", "8-15", "75s", "upper_compound"),
            ("DB Romanian Deadlift", "10-15", "75s", "lower_compound"),
            ("Band Face Pull", "12-20", "45s", "upper_accessory"),
            ("Hammer Curl", "10-15", "45s", "arms_accessory"),
            ("Diamond Push-Up", "8-15", "45s", "arms_accessory"),
        ],
    },
}


def needs_onboarding(user_profile: dict | None, onboarding_state: dict | None) -> bool:
    if onboarding_state and onboarding_state.get("status") == "completed":
        return False
    if user_profile:
        present = {key for key, value in user_profile.items() if value is not None}
        if ESSENTIAL_FIELDS.issubset(present):
            return False
    return True


def begin_or_resume_onboarding(telegram_id: int) -> list[str]:
    state = get_onboarding_state(telegram_id)
    if not state:
        upsert_onboarding_state(
            telegram_id,
            status="in_progress",
            current_step="welcome_ready",
            profile_data={},
            last_question=WELCOME_PROMPT,
        )
        return [WELCOME_PROMPT]
    if state.get("status") == "completed":
        return []
    return [state.get("last_question") or _prompt_for_step(state.get("current_step"), state.get("profile_data") or {})]


async def process_onboarding_message(telegram_id: int, username: str, message_text: str, onboarding_state: dict | None = None) -> list[str]:
    state = onboarding_state or get_onboarding_state(telegram_id) or {}
    step = state.get("current_step") or "welcome_ready"
    profile = dict(state.get("profile_data") or {})
    text = (message_text or "").strip()

    if step == "welcome_ready":
        if _is_affirmative(text):
            return _transition(telegram_id, profile, "medical_age", MEDICAL_PROMPT)
        return ["Whenever you're ready, send me a quick yes and we'll get into it.", WELCOME_PROMPT]

    if step == "medical_age":
        age = _extract_age(text)
        lowered = text.lower()
        if age is not None:
            profile["age_years"] = age
            profile["medical_disclaimer_acknowledged"] = True
            if age >= 18:
                profile["age_under_18"] = False
                return _transition(telegram_id, profile, "basics", _prompt_for_step("basics", profile), prefix="Great. Acknowledged — let's build something.")
            profile["age_under_18"] = True
            return _transition(telegram_id, profile, "minor_clearance", MINOR_CLEARANCE_PROMPT)
        if _is_affirmative(lowered):
            profile["medical_disclaimer_acknowledged"] = True
            profile["age_under_18"] = False
            return _transition(telegram_id, profile, "basics", _prompt_for_step("basics", profile), prefix="Great. Acknowledged — let's build something.")
        if _looks_under_18(lowered):
            profile["medical_disclaimer_acknowledged"] = True
            profile["age_under_18"] = True
            return _transition(telegram_id, profile, "minor_clearance", MINOR_CLEARANCE_PROMPT)
        return ["I just need to confirm the disclaimer and whether you're 18 or older.", MEDICAL_PROMPT]

    if step == "minor_clearance":
        if _is_affirmative(text):
            profile["medical_clearance_confirmed"] = True
            profile["age_under_18"] = True
            return _transition(telegram_id, profile, "basics", _prompt_for_step("basics", profile), prefix="Got it. We'll keep volume and intensity conservative to start.")
        upsert_onboarding_state(telegram_id, status="paused", current_step="minor_clearance", profile_data=profile, last_question=MINOR_CLEARANCE_PROMPT)
        return ["No worries — come back when you've had that conversation and I'll be here."]

    if step == "basics":
        profile.update(_extract_basics(text, profile))
        missing = []
        if profile.get("sex") is None:
            missing.append("sex")
        if profile.get("height_cm") is None:
            missing.append("height")
        if profile.get("age_years") is None:
            missing.append("age")
        if missing:
            prompt = _prompt_for_step("basics", profile)
            upsert_onboarding_state(telegram_id, current_step="basics", profile_data=profile, last_question=prompt)
            return [f"I still need your {' and '.join(missing)}.", prompt]
        return _transition(telegram_id, profile, "weight_bodyfat", WEIGHT_PROMPT)

    if step == "weight_bodyfat":
        body = _extract_weight_bodyfat(text)
        profile.update(body)
        if profile.get("body_weight_lbs") is None:
            upsert_onboarding_state(telegram_id, current_step="weight_bodyfat", profile_data=profile, last_question=WEIGHT_PROMPT)
            return ["I still need your current body weight.", WEIGHT_PROMPT]
        messages = []
        if body.get("body_fat_unknown"):
            messages.append("No worries at all — most people don't know their exact BF%. I'll use a formula that doesn't need it for now. If you ever get a DEXA scan or InBody test, we can update your numbers and sharpen the calculations. For now we're good.")
        elif profile.get("estimated_body_fat_pct") is None:
            upsert_onboarding_state(telegram_id, current_step="weight_bodyfat", profile_data=profile, last_question=WEIGHT_PROMPT)
            return ["Tell me your body fat percentage if you know it, or just say you don't know.", WEIGHT_PROMPT]
        messages.extend(_transition(telegram_id, profile, "training_background", TRAINING_PROMPT))
        return messages

    if step == "training_background":
        profile.update(_extract_training_background(text))
        missing = []
        if profile.get("training_age_months") is None:
            missing.append("how long you've been lifting")
        if "injury_notes" not in profile:
            missing.append("whether you have any injuries")
        if missing:
            upsert_onboarding_state(telegram_id, current_step="training_background", profile_data=profile, last_question=TRAINING_PROMPT)
            return [f"I still need {' and '.join(missing)}.", TRAINING_PROMPT]
        if profile.get("injury_notes"):
            return _transition(telegram_id, profile, "injury_followup", INJURY_FOLLOWUP_PROMPT)
        return _transition(telegram_id, profile, "goal_schedule", GOAL_PROMPT)

    if step == "injury_followup":
        profile["injury_details"] = text
        profile["injury_status"] = "diagnosed_or_rehabbed" if any(word in text.lower() for word in ["diagnosed", "rehab", "pt", "physical therapy", "doctor"]) else "movement_specific"
        return _transition(telegram_id, profile, "goal_schedule", GOAL_PROMPT, prefix="Thanks for the detail — I'll build around that.")

    if step == "goal_schedule":
        profile.update(_extract_goal_schedule(text))
        missing = []
        if profile.get("primary_goal") is None:
            missing.append("your main goal")
        if profile.get("training_days_per_week") is None:
            missing.append("training days per week")
        if missing:
            upsert_onboarding_state(telegram_id, current_step="goal_schedule", profile_data=profile, last_question=GOAL_PROMPT)
            return [f"I still need {' and '.join(missing)}.", GOAL_PROMPT]
        messages = []
        if profile.get("primary_goal") == "recomp":
            messages.append("That makes total sense — most people want to look better and get stronger. The good news is those goals overlap a lot. For now, we'll treat this as a recomp starting point and tighten it up once I have your full picture.")
        messages.extend(_transition(telegram_id, profile, "equipment", EQUIPMENT_PROMPT))
        return messages

    if step == "equipment":
        profile.update(_extract_equipment(text))
        missing = []
        if profile.get("equipment_access") is None:
            missing.append("equipment setup")
        if profile.get("emphasis_preference") is None:
            missing.append("training emphasis")
        if missing:
            upsert_onboarding_state(telegram_id, current_step="equipment", profile_data=profile, last_question=EQUIPMENT_PROMPT)
            return [f"I still need your {' and '.join(missing)}.", EQUIPMENT_PROMPT]
        return _transition(telegram_id, profile, "nutrition_mode", NUTRITION_PROMPT)

    if step == "nutrition_mode":
        mode = _parse_nutrition_mode(text)
        lowered = text.lower()
        if mode is None and any(phrase in lowered for phrase in ["not sure", "unsure", "don't know", "dont know", "either one"]):
            upsert_onboarding_state(telegram_id, current_step="nutrition_mode", profile_data=profile, last_question=NUTRITION_PROMPT)
            return [
                "If you're not sure, I'd suggest starting with the habit-based approach. It's lower friction and works really well. If you're not seeing progress after a few weeks, we can switch to tracked mode — it's easy to upgrade but harder to downgrade once you're burned out on counting.",
                NUTRITION_PROMPT,
            ]
        if mode is None:
            upsert_onboarding_state(telegram_id, current_step="nutrition_mode", profile_data=profile, last_question=NUTRITION_PROMPT)
            return ["Tell me which sounds more like you: tracked or habit-based.", NUTRITION_PROMPT]
        profile["nutrition_mode"] = mode
        return _transition(telegram_id, profile, "wearables", WEARABLES_PROMPT)

    if step == "wearables":
        wearable_data = _extract_wearables(text)
        if not wearable_data:
            upsert_onboarding_state(telegram_id, current_step="wearables", profile_data=profile, last_question=WEARABLES_PROMPT)
            return ["Just tell me Whoop, Withings, both, or neither.", WEARABLES_PROMPT]
        profile.update(wearable_data)
        prefix = "Once you connect those in the app, I'll be able to use your actual recovery and sleep data to guide training intensity. It won't change the fundamental program — it just lets me fine-tune things." if profile.get("uses_whoop") or profile.get("uses_withings") else "No worries — I'll use your self-reported readiness and training performance as my primary signals. Works fine."
        return _transition(telegram_id, profile, "communication", COMMUNICATION_PROMPT, prefix=prefix)

    if step == "communication":
        preference = _parse_communication_preference(text)
        if preference is None:
            upsert_onboarding_state(telegram_id, current_step="communication", profile_data=profile, last_question=COMMUNICATION_PROMPT)
            return ["Give me a rough preference: daily, training days only, or weekly.", COMMUNICATION_PROMPT]
        profile["communication_preference"] = preference
        summary = build_onboarding_summary(profile)
        upsert_onboarding_state(telegram_id, current_step="confirm_summary", profile_data=profile, last_question=summary)
        return [summary]

    if step == "confirm_summary":
        if _is_affirmative(text):
            return await _complete_onboarding(telegram_id, username, profile)
        updates = _extract_summary_updates(text, profile)
        if updates:
            profile.update(updates)
            summary = build_onboarding_summary(profile)
            upsert_onboarding_state(telegram_id, current_step="confirm_summary", profile_data=profile, last_question=summary)
            return ["Got it. Updated.", summary]
        return ["Tell me what you want to change and I'll adjust it before I build the plan.", build_onboarding_summary(profile)]

    return [WELCOME_PROMPT]


def build_onboarding_summary(profile: dict[str, Any]) -> str:
    lines = ["Alright, here's what I've got on you:", "", "*Your Profile:*"]
    lines.append(f"- Sex: {profile.get('sex', 'N/A')}")
    lines.append(f"- Height: {_format_height(profile.get('height_cm'))}")
    lines.append(f"- Weight: {_format_weight(profile.get('body_weight_lbs'))}")
    body_fat = profile.get("estimated_body_fat_pct")
    lines.append(f"- Body fat: {body_fat}%" if body_fat is not None else "- Body fat: unknown")
    lines.append(f"- Age: {profile.get('age_years', 'N/A')}")
    lines.append(f"- Training age: {_format_training_age(profile.get('training_age_months'))}")
    lines.append(f"- Goal: {_goal_label(profile.get('primary_goal'))}")
    lines.append(f"- Training days: {profile.get('training_days_per_week', 'N/A')}/week")
    lines.append(f"- Equipment: {_labelize(profile.get('equipment_access'))}")
    lines.append(f"- Emphasis: {_labelize(profile.get('emphasis_preference'))}")
    lines.append(f"- Nutrition mode: {_nutrition_label(profile.get('nutrition_mode'))}")
    lines.append(f"- Wearables: {_wearables_label(profile)}")
    if profile.get("injury_notes"):
        lines.append(f"- Injury note: {profile.get('injury_notes')}")
    lines.append("")
    lines.append("Any of that wrong, or anything you want to add?")
    return "\n".join(lines)


async def _complete_onboarding(telegram_id: int, username: str, profile: dict[str, Any]) -> list[str]:
    now_iso = datetime.now(timezone.utc).isoformat()
    profile = {**profile}
    profile.setdefault("experience_level", _derive_experience_level(profile.get("training_age_months")))
    profile.setdefault("activity_multiplier", _activity_multiplier(profile.get("training_days_per_week")))
    profile["onboarding_status"] = "completed"
    profile["onboarding_completed_at"] = now_iso
    upsert_user_profile(telegram_id, profile)
    upsert_onboarding_state(telegram_id, status="completed", current_step="completed", profile_data=profile, last_question=None, completed=True)
    user_context = await build_user_context(telegram_id=telegram_id, username=username, refresh_nutrition=True)
    nutrition = user_context.get("nutrition_state") or {}
    return [
        "Perfect. Give me a moment and I'll put together your initial training plan and nutrition setup.",
        _build_nutrition_message(profile, nutrition),
        _build_training_message(profile),
        _build_next_steps_message(profile),
    ]


def _transition(telegram_id: int, profile: dict[str, Any], next_step: str, prompt: str, prefix: str | None = None) -> list[str]:
    upsert_onboarding_state(telegram_id, status="in_progress", current_step=next_step, profile_data=profile, last_question=prompt)
    return [message for message in [prefix, prompt] if message]


def _prompt_for_step(step: str | None, profile: dict[str, Any]) -> str:
    if step == "medical_age":
        return MEDICAL_PROMPT
    if step == "basics":
        if profile.get("sex") is not None and profile.get("age_years") is not None and profile.get("height_cm") is None:
            return "I already have your sex and age. I just need your height now."
        return BASICS_PROMPT
    if step == "weight_bodyfat":
        return WEIGHT_PROMPT
    if step == "training_background":
        return TRAINING_PROMPT
    if step == "injury_followup":
        return INJURY_FOLLOWUP_PROMPT
    if step == "goal_schedule":
        return GOAL_PROMPT
    if step == "equipment":
        return EQUIPMENT_PROMPT
    if step == "nutrition_mode":
        return NUTRITION_PROMPT
    if step == "wearables":
        return WEARABLES_PROMPT
    if step == "communication":
        return COMMUNICATION_PROMPT
    if step == "confirm_summary":
        return build_onboarding_summary(profile)
    return WELCOME_PROMPT


def _is_affirmative(text: str) -> bool:
    lowered = text.strip().lower()
    return lowered in YES_WORDS or lowered.startswith("yes") or lowered.startswith("yep")


def _looks_under_18(text: str) -> bool:
    return any(phrase in text for phrase in ["under 18", "not 18", "i'm 17", "im 17", "i am 17", "17 years old", "16 years old", "15 years old"])


def _extract_age(text: str) -> int | None:
    patterns = [r"(\d{1,2})\s*(?:years? old|yo|y/o)", r"age\s*(\d{1,2})", r"i'?m\s*(\d{1,2})", r"i am\s*(\d{1,2})"]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            age = int(match.group(1))
            if 13 <= age <= 100:
                return age
    candidates = [int(value) for value in re.findall(r"\b(\d{1,3})\b", text) if 13 <= int(value) <= 100]
    return candidates[-1] if candidates else None


def _extract_height_cm(text: str) -> float | None:
    lowered = text.lower()
    cm_match = re.search(r"(\d{3}(?:\.\d+)?)\s*cm", lowered)
    if cm_match:
        return round(float(cm_match.group(1)), 1)
    ft_match = re.search(r"(\d)\s*(?:ft|feet|')\s*(\d{1,2})?", lowered)
    if ft_match:
        feet = int(ft_match.group(1))
        inches = int(ft_match.group(2) or 0)
        return round((feet * 12 + inches) * 2.54, 1)
    inch_match = re.search(r"(\d{2})\s*(?:in|inches)", lowered)
    if inch_match:
        return round(int(inch_match.group(1)) * 2.54, 1)
    return None


def _extract_weight_bodyfat(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    lowered = text.lower()
    weight_match = re.search(r"(\d{2,3}(?:\.\d+)?)\s*(lb|lbs|pounds|kg|kgs|kilograms?)", lowered)
    if weight_match:
        weight = float(weight_match.group(1))
        unit = weight_match.group(2)
        result["body_weight_lbs"] = round(weight * 2.205, 1) if unit.startswith("kg") else round(weight, 1)
    else:
        weigh_match = re.search(r"weigh\s*(\d{2,3}(?:\.\d+)?)", lowered)
        if weigh_match:
            result["body_weight_lbs"] = round(float(weigh_match.group(1)), 1)
    bodyfat_match = re.search(r"(\d{1,2}(?:\.\d+)?)\s*(?:%|percent)", lowered)
    if bodyfat_match:
        result["estimated_body_fat_pct"] = round(float(bodyfat_match.group(1)), 1)
    elif any(phrase in lowered for phrase in ["don't know", "dont know", "not sure", "no idea", "unknown"]):
        result["body_fat_unknown"] = True
    return result


def _extract_training_age_months(text: str) -> int | None:
    lowered = text.lower()
    year_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", lowered)
    if year_match:
        return max(0, round(float(year_match.group(1)) * 12))
    month_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:months?|mos?)", lowered)
    if month_match:
        return max(0, round(float(month_match.group(1))))
    if any(phrase in lowered for phrase in ["just starting", "brand new", "never really", "beginner"]):
        return 0
    return None


def _extract_training_background(text: str) -> dict[str, Any]:
    lowered = text.lower()
    result: dict[str, Any] = {}
    months = _extract_training_age_months(text)
    if months is not None:
        result["training_age_months"] = months
    if any(phrase in lowered for phrase in ["no injury", "no injuries", "none", "healthy", "all good"]):
        result["injury_notes"] = None
        result["injury_status"] = "none"
    elif any(word in lowered for word in ["shoulder", "knee", "back", "hip", "elbow", "wrist", "ankle", "pain", "injury"]):
        result["injury_notes"] = text.strip()
    return result


def _extract_basics(text: str, profile: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    sex = _extract_sex(text)
    if profile.get("sex") is None and sex is not None:
        result["sex"] = sex
    if profile.get("age_years") is None:
        age = _extract_age(text)
        if age is not None:
            result["age_years"] = age
    height_cm = _extract_height_cm(text)
    if height_cm is not None:
        result["height_cm"] = height_cm
    return result


def _extract_goal_schedule(text: str) -> dict[str, Any]:
    lowered = text.lower()
    result: dict[str, Any] = {}
    if any(word in lowered for word in ["both", "recomp", "recomposition", "leaner and stronger", "stronger and leaner", "build muscle and lose fat", "aesthetic", "aesthetics"]):
        result["primary_goal"] = "recomp"
    elif any(word in lowered for word in ["fat loss", "lose fat", "lean", "cut", "get leaner"]):
        result["primary_goal"] = "fat_loss"
    elif any(word in lowered for word in ["muscle", "bigger", "bulk", "gain", "size"]):
        result["primary_goal"] = "muscle_gain"
    elif any(word in lowered for word in ["maintain", "maintenance"]):
        result["primary_goal"] = "maintain"
    day_match = re.search(r"([1-7])\s*(?:days?|x)", lowered)
    if day_match:
        result["training_days_per_week"] = int(day_match.group(1))
    else:
        number_match = re.search(r"\b([1-7])\b", lowered)
        if number_match:
            result["training_days_per_week"] = int(number_match.group(1))
    return result


def _extract_equipment(text: str) -> dict[str, Any]:
    lowered = text.lower()
    result: dict[str, Any] = {}
    if any(word in lowered for word in ["home gym", "garage", "rack", "barbell at home"]):
        result["equipment_access"] = "home_gym"
    elif any(word in lowered for word in ["minimal", "bodyweight", "bands", "dumbbells only", "hotel gym"]):
        result["equipment_access"] = "minimal"
    elif "gym" in lowered or "full gym" in lowered or "commercial" in lowered:
        result["equipment_access"] = "full_gym"
    if any(word in lowered for word in ["upper", "chest", "back", "shoulders"]):
        result["emphasis_preference"] = "upper"
    elif any(word in lowered for word in ["lower", "legs", "glutes"]):
        result["emphasis_preference"] = "lower"
    elif any(word in lowered for word in ["arms", "biceps", "triceps"]):
        result["emphasis_preference"] = "arms"
    elif any(word in lowered for word in ["balanced", "no preference", "overall", "everything"]):
        result["emphasis_preference"] = "balanced"
    return result


def _parse_nutrition_mode(text: str) -> str | None:
    lowered = text.lower()
    if any(word in lowered for word in ["habit", "habit-based", "ad libitum", "no tracking", "don't want to track", "dont want to track"]):
        return "ad_libitum"
    if any(word in lowered for word in ["tracked", "track", "logging", "log food", "calories", "macros"]):
        return "tracked"
    return None


def _extract_wearables(text: str) -> dict[str, Any]:
    lowered = text.lower()
    if "both" in lowered:
        return {"uses_whoop": True, "uses_withings": True}
    negative_whoop = any(phrase in lowered for phrase in ["no whoop", "not whoop", "don't have whoop", "dont have whoop", "without whoop"])
    negative_withings = any(phrase in lowered for phrase in ["no withings", "not withings", "don't have withings", "dont have withings", "without withings"])
    has_whoop = "whoop" in lowered and not negative_whoop
    has_withings = "withings" in lowered and not negative_withings
    if has_whoop or has_withings:
        return {"uses_whoop": has_whoop, "uses_withings": has_withings}
    if any(word in lowered for word in ["neither", "none", "nope"]):
        return {"uses_whoop": False, "uses_withings": False}
    return {}


def _parse_communication_preference(text: str) -> str | None:
    lowered = text.lower()
    if "daily" in lowered or "every day" in lowered:
        return "daily"
    if any(word in lowered for word in ["few times", "couple times", "training days", "workout days"]):
        return "training_days_only"
    if any(word in lowered for word in ["weekly", "light touch", "low touch", "only when needed"]):
        return "weekly"
    return None


def _extract_summary_updates(text: str, profile: dict[str, Any]) -> dict[str, Any]:
    updates = {}
    updates.update(_extract_basics(text, profile))
    updates.update({k: v for k, v in _extract_weight_bodyfat(text).items() if k != "body_fat_unknown"})
    updates.update(_extract_training_background(text))
    updates.update(_extract_goal_schedule(text))
    updates.update(_extract_equipment(text))
    nutrition_mode = _parse_nutrition_mode(text)
    if nutrition_mode:
        updates["nutrition_mode"] = nutrition_mode
    communication = _parse_communication_preference(text)
    if communication:
        updates["communication_preference"] = communication
    wearables = _extract_wearables(text)
    if wearables:
        updates.update(wearables)
    return updates


def _derive_experience_level(training_age_months: Any) -> str:
    months = int(training_age_months or 0)
    if months < 6:
        return "beginner"
    if months < 36:
        return "intermediate"
    return "advanced"


def _activity_multiplier(training_days_per_week: Any) -> float:
    days = int(training_days_per_week or 3)
    if days <= 2:
        return 1.4
    if days == 3:
        return 1.5
    if days == 4:
        return 1.55
    return 1.6


def _build_nutrition_message(profile: dict[str, Any], nutrition: dict[str, Any]) -> str:
    protein = nutrition.get("current_protein_target_g") or nutrition.get("protein_target_g") or round(float(profile.get("body_weight_lbs") or 180) * 0.82)
    phase = str(nutrition.get("phase") or _goal_label(profile.get("primary_goal"))).replace("_", " ")
    if profile.get("nutrition_mode") == "tracked":
        calories = nutrition.get("current_calorie_target") or nutrition.get("calorie_target") or "N/A"
        fat_target = max(50, round(float(profile.get("body_weight_lbs") or 180) * 0.3))
        return (
            "Here's your nutrition starting point:\n\n"
            "*Daily Targets (Tracked Mode):*\n"
            f"- Calories: {calories} kcal/day\n"
            f"- Protein: {protein} g\n"
            "- The rest of your calories can come from carbs and fat in whatever ratio you prefer — protein is the priority.\n"
            f"- Fat: minimum about {fat_target} g/day\n"
            "- Carbs: fill the rest\n\n"
            "Protein is the priority. If you only hit one number, make it that one.\n\n"
            "These are starting numbers. Every two weeks I'll check your weight trend and adjust if needed."
        )
    plate = "Half your plate vegetables, quarter protein, quarter carbs" if profile.get("primary_goal") == "fat_loss" else "Build most meals around protein, carbs, and fruit or vegetables"
    return (
        "Here's your nutrition approach:\n\n"
        "*Habit-Based Nutrition:*\n"
        "- Protein at every meal — at least a palm-sized serving (roughly 25–35g)\n"
        f"- {plate}\n"
        "- 80% of what you eat should be whole, minimally processed foods\n"
        "- 3–4 meals per day, no need to track\n\n"
        "I'll check in every two weeks to see how your weight is trending and how training is feeling. We adjust from there."
    )


def _build_training_message(profile: dict[str, Any]) -> str:
    days = int(profile.get("training_days_per_week") or 3)
    equipment = profile.get("equipment_access") or "full_gym"
    emphasis = profile.get("emphasis_preference") or "balanced"
    sessions = SESSION_LIBRARY.get(equipment, SESSION_LIBRARY["full_gym"])
    order = ["A"] if days == 1 else ["A", "B"] if days == 2 else ["A", "B", "C"] if days == 3 else ["A", "B", "C", "D"]
    months = int(profile.get("training_age_months") or 0)
    lines = [
        "Now for training. Based on your goals and your schedule, here's your program:",
        "",
        f"*{min(days, 4)}-Day Full-Body Program*",
        "",
    ]
    for session_name in order:
        lines.append(f"*Session {session_name}*")
        for index, (exercise, reps, rest, category) in enumerate(sessions[session_name], start=1):
            sets = _sets_for(category, months, emphasis)
            lines.append(f"{index}. {exercise} — {sets} sets x {reps} reps, RIR 3-4, rest {rest}")
        lines.append("")
    if days > 4:
        lines.append("You gave me 5+ possible days, but I'm starting you with 4 lifting days so recovery stays ahead of fatigue. Use any extra day for easy cardio, walking, or mobility.")
        lines.append("")
    lines.append("A few quick notes:")
    lines.append("- *RIR (Reps in Reserve):* how many more reps you could have done before failure. This week, stop with 3–4 reps left in the tank.")
    lines.append("- *Log your lifts:* after each session, send me weights, sets, reps, and how it felt — easy, moderate, or hard.")
    lines.append("- *Warm-ups:* do 5 minutes of light cardio plus a few build-up sets before your first working set.")
    lines.append("")
    lines.append("Any questions before we kick things off?")
    return "\n".join(lines)


def _build_next_steps_message(profile: dict[str, Any]) -> str:
    wearable_line = "If you're using Whoop or Withings, hit /connect when you're ready so I can pull that data in.\n\n" if profile.get("uses_whoop") or profile.get("uses_withings") else ""
    return (
        f"{wearable_line}"
        "When you finish your first session, send me the lifts — weights, sets, reps, and how it felt. I'll take it from there."
    )


def _sets_for(category: str, months: int, emphasis: str) -> int:
    base = 2 if months < 6 else 3
    if category.endswith("accessory") and months < 18:
        base = 2
    region = "arms" if category.startswith("arms") else "lower" if category.startswith("lower") else "upper"
    if emphasis == region:
        base += 1
    if emphasis == "upper" and region == "lower" and base > 2:
        base -= 1
    if emphasis == "lower" and region == "upper" and base > 2:
        base -= 1
    return max(2, base)


def _goal_label(goal: Any) -> str:
    if goal == "fat_loss":
        return "fat loss"
    if goal == "muscle_gain":
        return "muscle gain"
    if goal == "recomp":
        return "recomp"
    return "maintenance"


def _nutrition_label(mode: Any) -> str:
    return "habit-based" if mode == "ad_libitum" else str(mode or "tracked")


def _wearables_label(profile: dict[str, Any]) -> str:
    uses_whoop = bool(profile.get("uses_whoop"))
    uses_withings = bool(profile.get("uses_withings"))
    if uses_whoop and uses_withings:
        return "Whoop + Withings"
    if uses_whoop:
        return "Whoop only"
    if uses_withings:
        return "Withings only"
    return "none"


def _format_height(height_cm: Any) -> str:
    if height_cm is None:
        return "N/A"
    return f"{height_cm} cm"


def _format_weight(weight_lbs: Any) -> str:
    if weight_lbs is None:
        return "N/A"
    return f"{weight_lbs} lb"


def _format_training_age(months: Any) -> str:
    if months is None:
        return "N/A"
    months = int(months)
    if months >= 12:
        years = months / 12
        return f"{years:.1f} years"
    return f"{months} months"


def _labelize(value: Any) -> str:
    return str(value or "N/A").replace("_", " ")
