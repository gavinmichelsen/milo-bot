from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from core.database import get_onboarding_state, upsert_onboarding_state, upsert_user_profile
from core.user_context import build_user_context

from agent import get_coaching_response


@dataclass
class OnboardingMessage:
    """A message with optional inline keyboard buttons."""
    text: str
    buttons: list[list[tuple[str, str]]] = field(default_factory=list)  # rows of (label, callback_data)

    @property
    def reply_markup(self) -> InlineKeyboardMarkup | None:
        if not self.buttons:
            return None
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(label, callback_data=f"ob:{data}") for label, data in row]
            for row in self.buttons
        ])


def _msg(text: str, buttons: list[list[tuple[str, str]]] | None = None) -> OnboardingMessage:
    return OnboardingMessage(text=text, buttons=buttons or [])


# Button presets for each step
BUTTONS_WELCOME = [[("Yes, I understand — let's go", "yes")]]
BUTTONS_GOAL = [
    [("Get bigger", "muscle_gain"), ("Get leaner", "fat_loss")],
    [("Both / recomp", "recomp"), ("Maintain", "maintain")],
]
BUTTONS_TRAINING_DAYS = [
    [("2 days", "2"), ("3 days", "3"), ("4 days", "4"), ("5 days", "5")],
]
BUTTONS_EQUIPMENT = [
    [("Full gym", "full_gym"), ("Home gym", "home_gym"), ("Minimal", "minimal")],
]
BUTTONS_EMPHASIS = [
    [("Balanced", "balanced"), ("Upper body", "upper")],
    [("Lower body", "lower"), ("Arms", "arms")],
]
BUTTONS_NUTRITION = [[("Tracked", "tracked"), ("Habit-based", "habit")]]
BUTTONS_WEARABLES = [
    [("Whoop", "whoop"), ("Withings", "withings")],
    [("Both", "both"), ("Neither", "neither")],
]
BUTTONS_COMMUNICATION = [[("Daily", "daily"), ("Training days", "training_days"), ("Weekly", "weekly")]]
BUTTONS_CONFIRM = [[("Looks good", "yes"), ("Change something", "change")]]

WELCOME_PROMPT = (
    "Hey! I'm Milo, your AI fitness coach. I'm going to help you build a training plan and dial in your nutrition — all over Telegram.\n\n"
    "Before we get started, quick disclaimer: I'm an AI coach, not a doctor. Everything I give you is general fitness and nutrition guidance, not medical advice. If you have any health conditions or concerns, check with a physician before starting a new program.\n\n"
    "Before I can build anything useful, I need to get to know you. It'll take a few minutes — ready to get started?"
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
    "What's your main goal right now? Getting bigger, getting leaner, or both — basically improving how you look and what you can do?"
)

TRAINING_DAYS_PROMPT = (
    "How many days per week can you realistically train? Be honest — 3 consistent days beats 5 days when you skip two."
)

EQUIPMENT_PROMPT = (
    "Which best describes your setup?\n\n"
    "*Full gym* — barbell, squat rack, bench, dumbbells, cable machine, pull-up bar, leg press, machines\n"
    "*Home gym* — power rack/squat stand, barbell, dumbbells, bench (no machines)\n"
    "*Minimal* — dumbbells, bands, bodyweight only"
)

EMPHASIS_PROMPT = (
    "Any training emphasis? Upper body, lower body, arms — or just balanced across everything?"
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


def begin_or_resume_onboarding(telegram_id: int) -> list[OnboardingMessage]:
    state = get_onboarding_state(telegram_id)
    if not state:
        upsert_onboarding_state(
            telegram_id,
            status="in_progress",
            current_step="welcome_ready",
            profile_data={},
            last_question=WELCOME_PROMPT,
        )
        return [_msg(WELCOME_PROMPT, BUTTONS_WELCOME)]
    if state.get("status") == "completed":
        return []
    step = state.get("current_step")
    text = state.get("last_question") or _prompt_for_step(step, state.get("profile_data") or {})
    return [_msg(text, STEP_BUTTONS.get(step))]


async def process_onboarding_message(telegram_id: int, username: str, message_text: str, onboarding_state: dict | None = None) -> list[OnboardingMessage]:
    state = onboarding_state or get_onboarding_state(telegram_id) or {}
    step = state.get("current_step") or "welcome_ready"
    profile = dict(state.get("profile_data") or {})
    text = (message_text or "").strip()

    # Detect clarifying questions and route to Claude instead of failing extraction
    if step not in ("welcome_ready",) and _is_question(text):
        last_question = state.get("last_question")
        answer = await _answer_onboarding_question(telegram_id, username, text, step, last_question)
        return [_msg(answer)]

    if step == "welcome_ready":
        if _is_affirmative(text):
            profile["medical_disclaimer_acknowledged"] = True
            return _transition(telegram_id, profile, "basics", BASICS_PROMPT, prefix="Let's build something.")
        return [_msg("Whenever you're ready, send me a quick yes and we'll get into it."), _msg(WELCOME_PROMPT, BUTTONS_WELCOME)]

    if step == "basics":
        ai_extracted = await _agentic_extract(text, "basics")
        for key in ("sex", "height_cm", "age_years"):
            if profile.get(key) is None and key in ai_extracted:
                profile[key] = ai_extracted[key]
        missing = [f for f in ["sex", "height_cm", "age_years"] if profile.get(f) is None]
        if missing:
            field_labels = {"sex": "sex", "height_cm": "height", "age_years": "age"}
            prompt = _prompt_for_step("basics", profile)
            upsert_onboarding_state(telegram_id, current_step="basics", profile_data=profile, last_question=prompt)
            return [_msg(f"I still need your {' and '.join(field_labels[f] for f in missing)}."), _msg(prompt)]
        return _transition(telegram_id, profile, "weight_bodyfat", WEIGHT_PROMPT)

    if step == "weight_bodyfat":
        ai_extracted = await _agentic_extract(text, "weight_bodyfat")
        for key in ("body_weight_lbs", "estimated_body_fat_pct", "body_fat_unknown"):
            if key in ai_extracted:
                profile[key] = ai_extracted[key]
        if profile.get("body_weight_lbs") is None:
            upsert_onboarding_state(telegram_id, current_step="weight_bodyfat", profile_data=profile, last_question=WEIGHT_PROMPT)
            return [_msg("I still need your current body weight."), _msg(WEIGHT_PROMPT)]
        messages: list[OnboardingMessage] = []
        if profile.get("body_fat_unknown"):
            messages.append(_msg("No worries at all — most people don't know their exact BF%. I'll use a formula that doesn't need it for now. If you ever get a DEXA scan or InBody test, we can update your numbers and sharpen the calculations. For now we're good."))
        elif profile.get("estimated_body_fat_pct") is None:
            upsert_onboarding_state(telegram_id, current_step="weight_bodyfat", profile_data=profile, last_question=WEIGHT_PROMPT)
            return [_msg("Tell me your body fat percentage if you know it, or just say you don't know."), _msg(WEIGHT_PROMPT)]
        messages.extend(_transition(telegram_id, profile, "training_background", TRAINING_PROMPT))
        return messages

    if step == "training_background":
        ai_extracted = await _agentic_extract(text, "training_background")
        for key in ("training_age_months", "injury_notes", "injury_status"):
            if key in ai_extracted:
                profile[key] = ai_extracted[key]
        # If AI determined no injuries, explicitly mark it so we don't loop
        if ai_extracted.get("injury_status") == "none" and "injury_notes" not in profile:
            profile["injury_notes"] = None
            profile["injury_status"] = "none"
        missing = []
        if profile.get("training_age_months") is None:
            missing.append("how long you've been lifting")
        if "injury_notes" not in profile and "injury_status" not in profile:
            missing.append("whether you have any injuries")
        if missing:
            upsert_onboarding_state(telegram_id, current_step="training_background", profile_data=profile, last_question=TRAINING_PROMPT)
            return [_msg(f"I still need {' and '.join(missing)}."), _msg(TRAINING_PROMPT)]
        if profile.get("injury_notes"):
            return _transition(telegram_id, profile, "injury_followup", INJURY_FOLLOWUP_PROMPT)
        return _transition(telegram_id, profile, "goal", GOAL_PROMPT)

    if step == "injury_followup":
        profile["injury_details"] = text
        ai_extracted = await _agentic_extract(text, "injury_followup")
        profile["injury_status"] = ai_extracted.get("injury_status", "movement_specific")
        return _transition(telegram_id, profile, "goal", GOAL_PROMPT, prefix="Thanks for the detail — I'll build around that.")

    if step == "goal":
        ai_extracted = await _agentic_extract(text, "goal")
        if profile.get("primary_goal") is None and "primary_goal" in ai_extracted:
            profile["primary_goal"] = ai_extracted["primary_goal"]
        if profile.get("primary_goal") is None:
            upsert_onboarding_state(telegram_id, current_step="goal", profile_data=profile, last_question=GOAL_PROMPT)
            return [_msg("I still need your main goal."), _msg(GOAL_PROMPT, BUTTONS_GOAL)]
        messages = []
        if profile.get("primary_goal") == "recomp":
            messages.append(_msg("That makes total sense — most people want to look better and get stronger. The good news is those goals overlap a lot. For now, we'll treat this as a recomp starting point and tighten it up once I have your full picture."))
        messages.extend(_transition(telegram_id, profile, "training_days", TRAINING_DAYS_PROMPT))
        return messages

    if step == "training_days":
        ai_extracted = await _agentic_extract(text, "training_days")
        if profile.get("training_days_per_week") is None and "training_days_per_week" in ai_extracted:
            profile["training_days_per_week"] = ai_extracted["training_days_per_week"]
        if profile.get("training_days_per_week") is None:
            upsert_onboarding_state(telegram_id, current_step="training_days", profile_data=profile, last_question=TRAINING_DAYS_PROMPT)
            return [_msg("I still need how many days per week you can train."), _msg(TRAINING_DAYS_PROMPT, BUTTONS_TRAINING_DAYS)]
        return _transition(telegram_id, profile, "equipment", EQUIPMENT_PROMPT)

    if step == "equipment":
        ai_extracted = await _agentic_extract(text, "equipment")
        if profile.get("equipment_access") is None and "equipment_access" in ai_extracted:
            profile["equipment_access"] = ai_extracted["equipment_access"]
        if profile.get("equipment_access") is None:
            upsert_onboarding_state(telegram_id, current_step="equipment", profile_data=profile, last_question=EQUIPMENT_PROMPT)
            return [_msg("I still need your equipment setup."), _msg(EQUIPMENT_PROMPT, BUTTONS_EQUIPMENT)]
        return _transition(telegram_id, profile, "emphasis", EMPHASIS_PROMPT)

    if step == "emphasis":
        ai_extracted = await _agentic_extract(text, "emphasis")
        if profile.get("emphasis_preference") is None and "emphasis_preference" in ai_extracted:
            profile["emphasis_preference"] = ai_extracted["emphasis_preference"]
        if profile.get("emphasis_preference") is None:
            upsert_onboarding_state(telegram_id, current_step="emphasis", profile_data=profile, last_question=EMPHASIS_PROMPT)
            return [_msg("I still need your training emphasis."), _msg(EMPHASIS_PROMPT, BUTTONS_EMPHASIS)]
        return _transition(telegram_id, profile, "nutrition_mode", NUTRITION_PROMPT)

    if step == "nutrition_mode":
        ai_extracted = await _agentic_extract(text, "nutrition_mode")
        mode = ai_extracted.get("nutrition_mode")
        if mode not in ("tracked", "ad_libitum"):
            # Check if they're just unsure
            lowered = text.lower()
            if any(phrase in lowered for phrase in ["not sure", "unsure", "don't know", "dont know", "either one"]):
                upsert_onboarding_state(telegram_id, current_step="nutrition_mode", profile_data=profile, last_question=NUTRITION_PROMPT)
                return [
                    _msg("If you're not sure, I'd suggest starting with the habit-based approach. It's lower friction and works really well. If you're not seeing progress after a few weeks, we can switch to tracked mode — it's easy to upgrade but harder to downgrade once you're burned out on counting."),
                    _msg(NUTRITION_PROMPT, BUTTONS_NUTRITION),
                ]
            upsert_onboarding_state(telegram_id, current_step="nutrition_mode", profile_data=profile, last_question=NUTRITION_PROMPT)
            return [_msg("Tell me which sounds more like you: tracked or habit-based."), _msg(NUTRITION_PROMPT, BUTTONS_NUTRITION)]
        profile["nutrition_mode"] = mode
        return _transition(telegram_id, profile, "wearables", WEARABLES_PROMPT)

    if step == "wearables":
        ai_extracted = await _agentic_extract(text, "wearables")
        if "uses_whoop" not in ai_extracted and "uses_withings" not in ai_extracted:
            upsert_onboarding_state(telegram_id, current_step="wearables", profile_data=profile, last_question=WEARABLES_PROMPT)
            return [_msg("Just tell me Whoop, Withings, both, or neither."), _msg(WEARABLES_PROMPT, BUTTONS_WEARABLES)]
        profile["uses_whoop"] = ai_extracted.get("uses_whoop", False)
        profile["uses_withings"] = ai_extracted.get("uses_withings", False)
        messages: list[OnboardingMessage] = []
        if profile.get("uses_whoop") or profile.get("uses_withings"):
            devices = []
            if profile.get("uses_whoop"):
                devices.append("Whoop")
            if profile.get("uses_withings"):
                devices.append("Withings")
            messages.append(_msg(
                f"Great — let's connect your {' and '.join(devices)} now so I can start pulling data right away. "
                "Use /connect to link your account. You can do it now or come back to it later, but the sooner it's connected, "
                "the smarter your coaching gets."
            ))
        else:
            messages.append(_msg("No worries — I'll use your self-reported readiness and training performance as my primary signals. Works fine."))
        messages.extend(_transition(telegram_id, profile, "communication", COMMUNICATION_PROMPT))
        return messages

    if step == "communication":
        ai_extracted = await _agentic_extract(text, "communication")
        preference = ai_extracted.get("communication_preference")
        if preference not in ("daily", "training_days_only", "weekly"):
            upsert_onboarding_state(telegram_id, current_step="communication", profile_data=profile, last_question=COMMUNICATION_PROMPT)
            return [_msg("Give me a rough preference: daily, training days only, or weekly."), _msg(COMMUNICATION_PROMPT, BUTTONS_COMMUNICATION)]
        profile["communication_preference"] = preference
        summary = build_onboarding_summary(profile)
        upsert_onboarding_state(telegram_id, current_step="confirm_summary", profile_data=profile, last_question=summary)
        return [_msg(summary, BUTTONS_CONFIRM)]

    if step == "confirm_summary":
        if _is_affirmative(text):
            return await _complete_onboarding(telegram_id, username, profile)
        if text.strip().lower() == "change":
            return [_msg("Tell me what you want to change and I'll adjust it before I build the plan."), _msg(build_onboarding_summary(profile), BUTTONS_CONFIRM)]
        updates = await _agentic_summary_update(text)
        if updates:
            profile.update(updates)
            summary = build_onboarding_summary(profile)
            upsert_onboarding_state(telegram_id, current_step="confirm_summary", profile_data=profile, last_question=summary)
            return [_msg("Got it. Updated."), _msg(summary, BUTTONS_CONFIRM)]
        return [_msg("Tell me what you want to change and I'll adjust it before I build the plan."), _msg(build_onboarding_summary(profile), BUTTONS_CONFIRM)]

    return [_msg(WELCOME_PROMPT, BUTTONS_WELCOME)]


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


async def _complete_onboarding(telegram_id: int, username: str, profile: dict[str, Any]) -> list[OnboardingMessage]:
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
        _msg("Perfect. Give me a moment and I'll put together your initial training plan and nutrition setup."),
        _msg(_build_nutrition_message(profile, nutrition)),
        _msg(_build_training_message(profile)),
        _msg(_build_next_steps_message(profile)),
    ]


STEP_BUTTONS = {
    "welcome_ready": BUTTONS_WELCOME,
    "goal": BUTTONS_GOAL,
    "training_days": BUTTONS_TRAINING_DAYS,
    "equipment": BUTTONS_EQUIPMENT,
    "emphasis": BUTTONS_EMPHASIS,
    "nutrition_mode": BUTTONS_NUTRITION,
    "wearables": BUTTONS_WEARABLES,
    "communication": BUTTONS_COMMUNICATION,
    "confirm_summary": BUTTONS_CONFIRM,
}


def _transition(telegram_id: int, profile: dict[str, Any], next_step: str, prompt: str, prefix: str | None = None) -> list[OnboardingMessage]:
    upsert_onboarding_state(telegram_id, status="in_progress", current_step=next_step, profile_data=profile, last_question=prompt)
    messages: list[OnboardingMessage] = []
    if prefix:
        messages.append(_msg(prefix))
    messages.append(_msg(prompt, STEP_BUTTONS.get(next_step)))
    return messages


def _prompt_for_step(step: str | None, profile: dict[str, Any]) -> str:
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
    if step == "goal":
        return GOAL_PROMPT
    if step == "training_days":
        return TRAINING_DAYS_PROMPT
    if step == "equipment":
        return EQUIPMENT_PROMPT
    if step == "emphasis":
        return EMPHASIS_PROMPT
    if step == "nutrition_mode":
        return NUTRITION_PROMPT
    if step == "wearables":
        return WEARABLES_PROMPT
    if step == "communication":
        return COMMUNICATION_PROMPT
    if step == "confirm_summary":
        return build_onboarding_summary(profile)
    return WELCOME_PROMPT


def _is_question(text: str) -> bool:
    """Detect if the user is asking a clarifying question rather than providing info."""
    lowered = text.strip().lower()
    if "?" in text:
        return True
    question_starters = [
        "what ", "what's", "whats", "how ", "why ", "can you", "could you",
        "should i", "do i", "is it", "what do you mean", "explain",
        "tell me more", "give me", "help me", "i don't understand",
        "i dont understand", "what does that mean", "can i ask",
    ]
    return any(lowered.startswith(s) or s in lowered for s in question_starters)


STEP_CONTEXT = {
    "basics": "asking for their sex, age, and height",
    "weight_bodyfat": "asking for their weight and body fat percentage",
    "training_background": "asking about their training history and injuries",
    "injury_followup": "asking about injury details",
    "goal": "asking about their main fitness goal",
    "training_days": "asking how many days per week they can train",
    "equipment": "asking about their gym equipment setup",
    "emphasis": "asking about their training emphasis preference",
    "nutrition_mode": "asking whether they want tracked calories or habit-based coaching",
    "wearables": "asking if they use Whoop or Withings wearables",
    "communication": "asking about their preferred coaching frequency",
}


async def _answer_onboarding_question(telegram_id: int, username: str, question: str, step: str, last_question: str | None) -> str:
    """Route a clarifying question to Claude with onboarding context."""
    step_desc = STEP_CONTEXT.get(step, "onboarding")
    context = {
        "telegram_id": telegram_id,
        "username": username,
        "onboarding_step": step,
        "onboarding_context": (
            f"The user is currently in the onboarding flow. Milo is {step_desc}. "
            f"The last question Milo asked was: \"{last_question or 'N/A'}\". "
            "Answer the user's question briefly (2-3 sentences max), then gently guide them "
            "back to answering the onboarding question. Do NOT re-ask the full onboarding question — "
            "just answer and nudge them back."
        ),
    }
    return await get_coaching_response(question, context)


_STEP_EXTRACTION_SCHEMA = {
    "basics": {
        "instructions": "Extract sex (male/female), height in cm, and age in years from the user's message.",
        "fields": {
            "sex": "string: 'male' or 'female'",
            "height_cm": "number in cm (convert from feet/inches if needed: 5'10 = 177.8, 6'1 = 185.4, 5 foot 10 = 177.8)",
            "age_years": "integer",
        },
    },
    "weight_bodyfat": {
        "instructions": "Extract body weight and body fat percentage. Convert kg to lbs if needed (multiply by 2.205).",
        "fields": {
            "body_weight_lbs": "number in lbs",
            "estimated_body_fat_pct": "number or null if unknown",
            "body_fat_unknown": "boolean: true if they said they don't know their body fat",
        },
    },
    "training_background": {
        "instructions": "Extract how long they've been training (in months) and any injury info. 'Just starting' or 'brand new' = 0 months. '2 years' = 24 months.",
        "fields": {
            "training_age_months": "integer months (0 if beginner/just starting)",
            "injury_notes": "string description or null if no injuries",
            "injury_status": "'none' if no injuries, 'has_injury' otherwise",
        },
    },
    "goal": {
        "instructions": "Extract the user's primary fitness goal.",
        "fields": {
            "primary_goal": "one of: muscle_gain, fat_loss, recomp, maintain",
        },
    },
    "training_days": {
        "instructions": "Extract how many days per week the user can train.",
        "fields": {
            "training_days_per_week": "integer 1-7",
        },
    },
    "equipment": {
        "instructions": "Extract their gym equipment level.",
        "fields": {
            "equipment_access": "one of: full_gym, home_gym, minimal",
        },
    },
    "emphasis": {
        "instructions": "Extract their training emphasis preference.",
        "fields": {
            "emphasis_preference": "one of: balanced, upper, lower, arms (default to 'balanced' if not specified)",
        },
    },
    "injury_followup": {
        "instructions": "Categorize this injury description. Has it been professionally diagnosed/rehabbed, or is it more of a movement-specific pain?",
        "fields": {
            "injury_status": "one of: diagnosed_or_rehabbed, movement_specific",
        },
    },
    "nutrition_mode": {
        "instructions": "Determine if the user wants to track calories/macros or use a habit-based approach.",
        "fields": {
            "nutrition_mode": "one of: tracked, ad_libitum (habit-based/no tracking = ad_libitum)",
        },
    },
    "wearables": {
        "instructions": "Determine which fitness wearables the user has.",
        "fields": {
            "uses_whoop": "boolean",
            "uses_withings": "boolean",
        },
    },
    "communication": {
        "instructions": "Determine how often the user wants coaching check-ins.",
        "fields": {
            "communication_preference": "one of: daily, training_days_only, weekly",
        },
    },
}


_VALID_ENUMS = {
    "sex": {"male", "female"},
    "primary_goal": {"muscle_gain", "fat_loss", "recomp", "maintain"},
    "experience_level": {"beginner", "intermediate", "advanced"},
    "equipment_access": {"full_gym", "home_gym", "minimal"},
    "emphasis_preference": {"balanced", "upper", "lower", "arms"},
    "nutrition_mode": {"tracked", "ad_libitum"},
    "communication_preference": {"daily", "training_days_only", "weekly"},
    "injury_status": {"none", "has_injury", "diagnosed_or_rehabbed", "movement_specific"},
}

_NUMERIC_RANGES = {
    "age_years": (13, 100, int),
    "height_cm": (100.0, 250.0, float),
    "body_weight_lbs": (50.0, 700.0, float),
    "estimated_body_fat_pct": (2.0, 65.0, float),
    "training_age_months": (0, 720, int),
    "training_days_per_week": (1, 7, int),
    "activity_multiplier": (1.2, 2.0, float),
}


def _normalize_extracted(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize and validate AI-extracted values before they enter the profile.

    Ensures all values match the types and constraints expected by Supabase:
    - Enum fields are lowercased and validated against allowed values
    - Numeric fields are cast to the correct type and clamped to valid ranges
    - Booleans are coerced from truthy/falsy values
    - Invalid or out-of-range values are silently dropped
    """
    _NULLABLE_FIELDS = {"injury_notes", "injury_details", "estimated_body_fat_pct"}
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            if key in _NULLABLE_FIELDS:
                cleaned[key] = None
            continue

        # Enum fields
        if key in _VALID_ENUMS:
            normalized = str(value).strip().lower().replace(" ", "_").replace("-", "_")
            # Common AI synonyms
            synonyms = {
                "habit_based": "ad_libitum", "habit": "ad_libitum", "no_tracking": "ad_libitum",
                "training_days": "training_days_only",
                "no_injuries": "none", "no_injury": "none", "healthy": "none",
            }
            normalized = synonyms.get(normalized, normalized)
            if normalized in _VALID_ENUMS[key]:
                cleaned[key] = normalized
            continue

        # Numeric fields
        if key in _NUMERIC_RANGES:
            lo, hi, cast = _NUMERIC_RANGES[key]
            try:
                num = cast(value)
                if lo <= num <= hi:
                    cleaned[key] = round(num, 1) if cast is float else num
            except (ValueError, TypeError):
                pass
            continue

        # Boolean fields
        if key in ("uses_whoop", "uses_withings", "body_fat_unknown", "medical_disclaimer_acknowledged"):
            if isinstance(value, bool):
                cleaned[key] = value
            elif isinstance(value, str):
                cleaned[key] = value.strip().lower() in ("true", "yes", "1")
            continue

        # String fields (injury_notes, injury_details, etc.) — pass through if non-empty
        if isinstance(value, str) and value.strip():
            cleaned[key] = value.strip()
        elif not isinstance(value, str):
            cleaned[key] = value

    return cleaned


async def _agentic_extract(text: str, step: str) -> dict[str, Any]:
    """Use Claude to extract structured data from a user's message, then normalize it.

    Sends the user's text to Claude with a structured schema prompt.
    The raw extraction is then passed through _normalize_extracted() to
    enforce types, ranges, and valid enum values before anything touches
    the profile or database.
    """
    schema = _STEP_EXTRACTION_SCHEMA.get(step)
    if not schema:
        return {}
    import json
    fields_desc = "\n".join(f"  - {k}: {v}" for k, v in schema["fields"].items())
    prompt = (
        f"{schema['instructions']}\n\n"
        f"User said: \"{text}\"\n\n"
        f"Extract these fields:\n{fields_desc}\n\n"
        "Respond with ONLY a JSON object. Use null for fields you cannot determine. "
        "Do not include any other text, explanation, or markdown formatting."
    )
    context = {"telegram_id": 0, "username": "system", "onboarding_extraction": True}
    try:
        raw = await get_coaching_response(prompt, context)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = json.loads(cleaned)
        # Filter to known fields, then normalize
        # Preserve explicit nulls for nullable fields (injury_notes = null means "no injuries")
        _NULLABLE_FIELDS = {"injury_notes", "injury_details", "estimated_body_fat_pct"}
        extracted = {}
        for k, v in result.items():
            if k not in schema["fields"]:
                continue
            if v is None and k in _NULLABLE_FIELDS:
                extracted[k] = None
            elif v is not None:
                extracted[k] = v
        return _normalize_extracted(extracted)
    except Exception:
        return {}


async def _agentic_summary_update(text: str) -> dict[str, Any]:
    """Use Claude to extract profile updates from a user's correction during summary review."""
    import json
    prompt = (
        "The user is reviewing their onboarding profile summary and wants to change something.\n\n"
        f"User said: \"{text}\"\n\n"
        "Extract any profile fields they want to update. Possible fields:\n"
        "  - sex: 'male' or 'female'\n"
        "  - height_cm: number in cm (convert from feet/inches if needed)\n"
        "  - age_years: integer\n"
        "  - body_weight_lbs: number in lbs (convert from kg if needed)\n"
        "  - estimated_body_fat_pct: number\n"
        "  - training_age_months: integer\n"
        "  - primary_goal: one of: muscle_gain, fat_loss, recomp, maintain\n"
        "  - training_days_per_week: integer 1-7\n"
        "  - equipment_access: one of: full_gym, home_gym, minimal\n"
        "  - emphasis_preference: one of: balanced, upper, lower, arms\n"
        "  - nutrition_mode: one of: tracked, ad_libitum\n"
        "  - communication_preference: one of: daily, training_days_only, weekly\n"
        "  - uses_whoop: boolean\n"
        "  - uses_withings: boolean\n\n"
        "Respond with ONLY a JSON object containing the fields to update. "
        "Only include fields the user explicitly wants to change. Use null for unclear values."
    )
    context = {"telegram_id": 0, "username": "system", "onboarding_extraction": True}
    try:
        raw = await get_coaching_response(prompt, context)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = json.loads(cleaned)
        return _normalize_extracted({k: v for k, v in result.items() if v is not None})
    except Exception:
        return {}


def _is_affirmative(text: str) -> bool:
    lowered = text.strip().lower()
    return lowered in YES_WORDS or lowered.startswith("yes") or lowered.startswith("yep")


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
