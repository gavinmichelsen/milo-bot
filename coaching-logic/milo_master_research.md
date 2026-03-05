# MILO AI FITNESS COACHING SYSTEM — MASTER RESEARCH DOCUMENT
## Unified Backend Logic Reference for Algorithm Development

**Version:** 1.0  
**Compiled:** 2026-03-05  
**Purpose:** Single source of truth for all Milo backend coaching algorithms. Do NOT summarize or simplify — this document preserves all formulas, pseudocode, decision trees, thresholds, and numeric values from source research tracks.  
**Audience:** AI backend agent generating production code for Milo

---

## TABLE OF CONTENTS

- [Part 0: System Overview & Onboarding](#part-0-system-overview--onboarding)
- [Part 1: Energy Expenditure & Calorie Management](#part-1-energy-expenditure--calorie-management)
- [Part 2: Protein & Macronutrient Targets](#part-2-protein--macronutrient-targets)
- [Part 3: Nutritional Phase Management](#part-3-nutritional-phase-management)
- [Part 4: Ad Libitum Nutrition Mode](#part-4-ad-libitum-nutrition-mode)
- [Part 5: Training Volume & Progression](#part-5-training-volume--progression)
- [Part 6: Training Programming](#part-6-training-programming)
- [Part 7: RIR-Based Autoregulation](#part-7-rir-based-autoregulation)
- [Part 8: Fatigue Detection & Deload Protocols](#part-8-fatigue-detection--deload-protocols)
- [Part 9: Recovery Integration](#part-9-recovery-integration)
- [Part 10: Sleep Hygiene Coaching](#part-10-sleep-hygiene-coaching)
- [Part 11: Coaching Communication Framework](#part-11-coaching-communication-framework)
- [Appendix A: Master Variable Dictionary](#appendix-a-master-variable-dictionary)
- [Appendix B: Master Constants & Thresholds](#appendix-b-master-constants--thresholds)
- [Appendix C: Citation Index](#appendix-c-citation-index)

---

## PART 0: SYSTEM OVERVIEW & ONBOARDING

### 0.1 System Identity

- **Product name:** Milo
- **Delivery channel:** Telegram (AI coaching agent)
- **Target population:** Males, high school age and above, beginner to intermediate lifters
- **Primary goals:** Hypertrophy + strength (aesthetics focus) AND fat loss
- **Training approach:** Full-body preferred, RIR-based autoregulation, volume landmarks (MEV/MAV/MRV)
- **Wearable integrations:** Whoop, Withings scale
- **Autonomy:** Highly autonomous; user override capability maintained at all times
- **Medical disclaimer:** Required for ALL users at onboarding (see §0.6)

### 0.2 Onboarding Variables (Required Collection)

The following variables are collected during user onboarding:

| Variable | Type | Unit | Notes |
|---|---|---|---|
| `body_weight_lbs` | float | lbs | Current body weight |
| `body_weight_kg` | float | kg | Derived: `body_weight_lbs / 2.2046` |
| `body_fat_pct` | float | % | Optional; enables LBM-based equations |
| `height_cm` | float | cm | Standing height |
| `height_inches` | float | in | Derived or direct input |
| `age_yr` | int | years | Age in whole years |
| `sex` | enum | — | Currently: MALE only in Milo |
| `training_age_months` | int | months | Months of consistent resistance training |
| `experience_level` | enum | — | BEGINNER (<12 months) / INTERMEDIATE (1–5 yrs) / ADVANCED (5+ yrs) |
| `goal` | enum | — | FAT_LOSS / HYPERTROPHY / STRENGTH / RECOMP |
| `injuries` | list[str] | — | Free-text injury/limitation notes |
| `frequency_preference` | int | days/week | Preferred training days per week (2–6) |
| `equipment_access` | enum | — | FULL_GYM / HOME_WEIGHTS / MINIMAL |
| `activity_level` | enum | — | SEDENTARY / LIGHTLY_ACTIVE / MODERATELY_ACTIVE / VERY_ACTIVE / EXTREMELY_ACTIVE |
| `emphasis_mode` | enum | — | BALANCED / UPPER_EMPHASIS / LOWER_EMPHASIS / ARMS_EMPHASIS / CUSTOM |
| `nutrition_mode` | enum | — | TRACKED / AD_LIBITUM |
| `wake_time_target` | string | HH:MM | Target wake time for sleep coaching |
| `bedtime_target` | string | HH:MM | Target bedtime |

### 0.3 Wearable Data Streams

**Whoop Integration:**
| Metric | Variable | Unit | Usage |
|---|---|---|---|
| HRV (rMSSD) | `hrv_raw` | ms | Recovery composite, deload triggers |
| Resting Heart Rate | `rhr_daily` | bpm | Recovery composite |
| Sleep duration | `sleep_duration_hrs` | hours | Recovery, sleep coaching |
| Sleep efficiency | `sleep_efficiency_pct` | % | Recovery composite |
| Sleep performance score | `sleep_perf_score` | 0–100 | Recovery composite |
| Slow-wave sleep | `sws_minutes` | min | GH secretion monitoring |
| REM sleep | `rem_minutes` | min | Recovery monitoring |
| Sleep latency | `sleep_latency_min` | min | Sleep coaching trigger |
| Sleep consistency | `sleep_consistency_score` | 0–100 | Circadian stability |
| SpO2 average | `spo2_avg` | % | Medical flag |
| Recovery score | `recovery_score_pct` | 0–100 | Internal reference only (NEVER shown to user) |
| Sleep onset time | `sleep_onset` | HH:MM | Sleep coaching |
| Wake time | `wake_time` | HH:MM | Sleep consistency tracking |

**Withings Scale Integration:**
| Metric | Variable | Unit | Usage |
|---|---|---|---|
| Body weight | `weight_kg` | kg | TDEE calibration, phase management |
| Body fat % (BIA) | `body_fat_pct_withings` | % | Trend tracking (not absolute) |
| Fat mass | `fat_mass_kg` | kg | Body composition trend |
| Fat-free mass | `ffm_kg` | kg | Muscle retention monitoring |

### 0.4 Two Nutrition Modes

**MODE 1: TRACKED (Calorie/Macro Targets)**
- System calculates TDEE, sets calorie targets with phase-appropriate surplus/deficit
- Fixed protein: `0.82 g/lb` body weight (see Part 2)
- Biweekly calorie adjustment based on weight trend (see Part 1)
- User logs calories and macros in app
- System adjusts targets every 14 days

**MODE 2: AD LIBITUM (Heuristic-Based)**
- No calorie counting or macro tracking required
- System provides 7 behavioral heuristic rules (see Part 4)
- Progress monitored via weight trend, body composition, training performance, subjective feedback
- Escalation logic determines when to suggest switching to tracked mode
- Protein-first strategy approximates 0.82 g/lb target without tracking

**Mode Selection Logic:**
```python
nutrition_mode: Literal["TRACKED", "AD_LIBITUM"]

# Default assignment at onboarding:
if user.preference == "TRACKED" OR user.goal == "AGGRESSIVE_FAT_LOSS":
    nutrition_mode = "TRACKED"
elif user.preference == "AD_LIBITUM" OR user.dislike_tracking == True:
    nutrition_mode = "AD_LIBITUM"
else:
    nutrition_mode = "AD_LIBITUM"  # Default; less friction for new users

# Escalation path: AD_LIBITUM → TRACKED (see Part 4, Section 6)
# User can switch modes at any time (autonomy override)
```

### 0.5 System Design Principles

1. **Highly autonomous:** Milo makes all recommendations without asking for confirmation on routine adjustments
2. **User override:** Any system recommendation can be overridden by user at any time
3. **Biweekly adjustment cadence:** Calorie and volume adjustments on 14-day cycles
4. **No calorie cycling, no refeeds, no diet breaks** (see Part 3 for evidence justification)
5. **Trend-based recovery signals:** Never act on single-day readings (see Part 9)
6. **Nocebo avoidance:** Raw wearable scores never exposed to users (see Part 9, Section 4)
7. **Progressive volume model:** MEV → MAV → MRV within mesocycles (see Part 5)
8. **Autonomy-supportive communication:** SDT-based language framework (see Part 11)

### 0.6 Medical Disclaimer (Required)

**MUST be presented and acknowledged by ALL users at onboarding:**

```
MEDICAL DISCLAIMER: The Milo AI coaching system provides general fitness and 
nutrition guidance for educational purposes only. This is NOT medical advice. 
You should consult a qualified healthcare professional before beginning any 
new exercise or nutrition program, especially if you have any pre-existing 
medical conditions, injuries, or health concerns. Milo's recommendations are 
not a substitute for professional medical, dietary, or clinical advice. 
Discontinue exercise and seek medical attention if you experience pain, 
dizziness, shortness of breath, or other concerning symptoms.

By continuing, you confirm you are in generally good health and understand 
these limitations.
```

`medical_disclaimer_acknowledged: bool` — must be `True` before system activates

---

## PART 1: ENERGY EXPENDITURE & CALORIE MANAGEMENT

*Source: Track 1 — TDEE & Calorie Algorithms; Track 7 — Protein Phases*

### 1.1 TDEE Estimation Models

TDEE is calculated as:
```
TDEE = BMR × activity_multiplier
```

#### Model Selection Logic

```python
if body_fat_pct is not None:
    LBM_kg = weight_kg * (1 - (body_fat_pct / 100))
    if is_resistance_training:
        if user_category == "athletic" OR body_fat_pct < 15:
            use Cunningham           # Preferred for lean/athletic users
        else:
            use Katch-McArdle        # BF% known, less athletic
    else:
        use Katch-McArdle
else:
    use Mifflin_St_Jeor              # Primary fallback when BF% unknown
    # Harris-Benedict (Roza-Shizgal) = secondary fallback ONLY

# Recommendation hierarchy for Milo:
# 1. Cunningham — if BF% known and user is resistance-training
# 2. Katch-McArdle — if BF% known, lower activity
# 3. Mifflin-St Jeor — if BF% unknown (most common at onboarding)
# 4. Harris-Benedict (Roza-Shizgal) — last resort
```

#### 1.1.1 Mifflin-St Jeor (1990) — PRIMARY when BF% unknown

**Source:** Mifflin MD et al., *Am J Clin Nutr.* 1990;51(2):241–247. Designated by Academy of Nutrition and Dietetics as evidence-based standard in 2005.

```
// Males (Milo target population):
BMR_mifflin = (10 × weight_kg) + (6.25 × height_cm) − (5 × age_yr) + 5
```

**Validation:**
- Predicts RMR within ±10% in 82% of non-obese and 75% of obese individuals
- Lowest bias of all tested equations: 95% CI −26 to +8 kcal/day
- Academy of Nutrition and Dietetics recommends over Harris-Benedict

#### 1.1.2 Harris-Benedict Revised (Roza & Shizgal, 1984) — SECONDARY FALLBACK

**Source:** Roza AM, Shizgal HM. *Am J Clin Nutr.* 1984;40(1):168–182.

```
// Males:
BMR_hb_male = 88.362 + (13.397 × weight_kg) + (4.799 × height_cm) − (5.677 × age_yr)
```
95% confidence limits: ±213 kcal/day (men). Use ONLY if Mifflin cannot be calculated.

#### 1.1.3 Katch-McArdle (1975) — PRIMARY when BF% known

**Source:** Katch FI, McArdle WD., *Hum Biol.* 1973;45(3):445–454.

```
LBM_kg = weight_kg × (1 − (body_fat_pct / 100))
BMR_katch = 370 + (21.6 × LBM_kg)
```

#### 1.1.4 Cunningham (1980) — PREFERRED for lean/athletic users with BF%

**Source:** Cunningham JJ. *Am J Clin Nutr.* 1980;33(11):2372–2374.

```
LBM_kg = weight_kg × (1 − (body_fat_pct / 100))
RMR_cunningham = 500 + (22 × LBM_kg)
```

**Example:** 80 kg male, 12% BF → LBM = 70.4 kg → RMR_cunningham = 500 + (22 × 70.4) = **2,049 kcal/day**
Cunningham yields ~150–200 kcal/day higher than Katch-McArdle for the same LBM.

#### 1.1.5 Equation Comparison Summary

| Equation | Year | Inputs | Best For | Avg Error | Accuracy (±10%) |
|---|---|---|---|---|---|
| Mifflin-St Jeor | 1990 | Weight, Height, Age, Sex | General population, no BF% | −26 to +8 kcal/day | 82% non-obese |
| Harris-Benedict (Roza-Shizgal) | 1984 | Weight, Height, Age, Sex | Secondary fallback only | ±213 kcal (men) | ~70–80% |
| Katch-McArdle | 1975 | LBM (from BF%) | BF% available, non-athletic | N/A | Better than H-B for lean |
| Cunningham | 1980 | LBM (from BF%) | Resistance-trained/athletic | ~±100–150 kcal | Highest for athletes |

### 1.2 Activity Multiplier Table

Source: FAO/WHO/UNU 1985 physical activity level (PAL) framework.

| Activity Level | Label | Multiplier | Description |
|---|---|---|---|
| Sedentary | `SEDENTARY` | 1.2 | Desk job, no exercise, <2,000 steps/day |
| Lightly Active | `LIGHTLY_ACTIVE` | 1.375 | Light exercise 1–3 days/week |
| Moderately Active | `MODERATELY_ACTIVE` | 1.55 | Moderate exercise 3–5 days/week |
| Very Active | `VERY_ACTIVE` | 1.725 | Hard exercise 6–7 days/week or physical job |
| Extremely Active | `EXTREMELY_ACTIVE` | 1.9 | Hard daily exercise + physical job OR 2× daily training |

```python
default_activity_multiplier = 1.55  # MODERATELY_ACTIVE — Milo default for target population
```

**Note:** Activity multipliers have ±200–400 kcal/day individual error. This is why adaptive TDEE calibration (§1.3) is critical — equation-based TDEE is only the starting estimate.

### 1.3 Initial TDEE Calculation — Full Pseudocode

```python
def calculate_initial_TDEE(weight_kg, height_cm, age_yr, activity_level, 
                            body_fat_pct=None, is_resistance_training=True):
    """
    Returns initial estimated TDEE in kcal/day.
    Uses best available equation based on data provided.
    """
    # Select BMR equation
    if body_fat_pct is not None:
        LBM_kg = weight_kg * (1 - (body_fat_pct / 100))
        if is_resistance_training:
            BMR = 500 + (22 * LBM_kg)            # Cunningham
            equation_used = "Cunningham"
        else:
            BMR = 370 + (21.6 * LBM_kg)          # Katch-McArdle
            equation_used = "Katch-McArdle"
    else:
        BMR = (10 * weight_kg) + (6.25 * height_cm) - (5 * age_yr) + 5  # Mifflin (male)
        equation_used = "Mifflin-St Jeor"
    
    multiplier_map = {
        "SEDENTARY": 1.2,
        "LIGHTLY_ACTIVE": 1.375,
        "MODERATELY_ACTIVE": 1.55,
        "VERY_ACTIVE": 1.725,
        "EXTREMELY_ACTIVE": 1.9
    }
    multiplier = multiplier_map.get(activity_level, 1.55)
    TDEE_estimated = BMR * multiplier
    
    return {
        "TDEE_estimated": round(TDEE_estimated),
        "BMR": round(BMR),
        "equation_used": equation_used,
        "activity_multiplier": multiplier,
        "LBM_kg": LBM_kg if body_fat_pct is not None else None
    }
```

### 1.4 Adaptive TDEE Calibration From Weight Data

**Core principle (Helms, Valdez & Morgan, Muscle and Strength Pyramid: Nutrition, 3D Muscle Journey, 2019):** Track weekly weight averages. A change of ±1 kg in average weight reflects approximately ±7,700 kcal of energy imbalance over that period.

#### 1.4.1 Rolling Weight Average Calculation

```python
def rolling_weight_average(weight_log: list[tuple[date, float]], window_days: int = 7) -> float:
    """
    weight_log: list of (date, weight_kg) tuples sorted ascending by date
    window_days: number of days to average (7 or 14)
    Returns: average weight in kg for the window
    """
    if len(weight_log) < window_days:
        weights = [w for _, w in weight_log]
    else:
        recent = weight_log[-window_days:]
        weights = [w for _, w in recent]
    return sum(weights) / len(weights)


def get_biweekly_weight_trend(weight_log: list[tuple[date, float]]) -> dict:
    """
    For a 14-day window: compute 7-day average at beginning vs. end.
    Returns weight_delta_kg and rate_of_change_pct_per_week.
    """
    if len(weight_log) < 10:
        return {"insufficient_data": True}
    week1_weights = [w for _, w in weight_log[:7]]
    week1_avg = sum(week1_weights) / len(week1_weights)
    week2_weights = [w for _, w in weight_log[-7:]]
    week2_avg = sum(week2_weights) / len(week2_weights)
    weight_delta_kg = week2_avg - week1_avg          # positive = gained
    rate_pct_per_week = (weight_delta_kg / week1_avg) * 100
    return {
        "week1_avg_kg": round(week1_avg, 2),
        "week2_avg_kg": round(week2_avg, 2),
        "weight_delta_kg": round(weight_delta_kg, 3),
        "rate_pct_per_week": round(rate_pct_per_week, 3)
    }
```

#### 1.4.2 Back-Calculating Actual TDEE

```
// SIGN CONVENTION:
// weight_delta_kg > 0  →  gained weight  →  was in surplus
// weight_delta_kg < 0  →  lost weight    →  was in deficit

KCAL_PER_KG_TISSUE = 7700  # mixed tissue energy value (Hall et al. model)
energy_balance_kcal = weight_delta_kg × 7700
actual_TDEE = avg_daily_calories - (energy_balance_kcal / days_in_period)
```

```python
KCAL_PER_KG_TISSUE = 7700

def calculate_adaptive_TDEE(avg_daily_calories: float, 
                              weight_delta_kg: float, 
                              days_in_period: int) -> float:
    """
    weight_delta_kg: positive = weight gained; negative = weight lost
    """
    daily_energy_balance = (weight_delta_kg * KCAL_PER_KG_TISSUE) / days_in_period
    adaptive_TDEE = avg_daily_calories - daily_energy_balance
    return round(adaptive_TDEE)
```

**Example:** User logs 2,400 kcal/day for 14 days; weight: 82.4 → 81.9 kg (delta = −0.5 kg)
→ Energy balance = (−0.5 × 7700) / 14 = −275 kcal/day
→ Adaptive TDEE = 2,400 − (−275) = **2,675 kcal/day**

#### 1.4.3 TDEE Confidence Blending (Data Maturity)

| Weeks of data | Reliability | Action |
|---|---|---|
| 0–1 weeks | `INSUFFICIENT` | Use equation-based estimate only |
| 2 weeks | `LOW_CONFIDENCE` | Blend 30% adaptive + 70% equation |
| 3–4 weeks | `MODERATE_CONFIDENCE` | Blend 60% adaptive + 40% equation |
| 5+ weeks | `HIGH_CONFIDENCE` | 85% adaptive + 15% equation |

```python
def get_working_TDEE(equation_TDEE: float, 
                      adaptive_TDEE: float | None, 
                      weeks_of_data: int) -> dict:
    if adaptive_TDEE is None or weeks_of_data < 2:
        return {"working_TDEE": equation_TDEE, "confidence": "INSUFFICIENT", "source": "equation_only"}
    elif weeks_of_data < 3:
        working_TDEE = (0.3 * adaptive_TDEE) + (0.7 * equation_TDEE)
        confidence = "LOW_CONFIDENCE"
    elif weeks_of_data < 5:
        working_TDEE = (0.6 * adaptive_TDEE) + (0.4 * equation_TDEE)
        confidence = "MODERATE_CONFIDENCE"
    else:
        working_TDEE = (0.85 * adaptive_TDEE) + (0.15 * equation_TDEE)
        confidence = "HIGH_CONFIDENCE"
    return {
        "working_TDEE": round(working_TDEE),
        "confidence": confidence,
        "source": "blended",
        "adaptive_TDEE": adaptive_TDEE,
        "equation_TDEE": equation_TDEE
    }
```

**Adaptive TDEE reliability requirements:**
- Calorie logging ≥80% of days in the period
- No major perturbations (illness, travel, extreme sodium/alcohol)
- At least 7 valid weight readings in the 14-day window

#### 1.4.4 Weight Reading Validation

```python
def is_weight_reading_valid(weight_kg: float, 
                              user_weight_history: list[float],
                              max_single_day_delta_kg: float = 2.5) -> bool:
    if len(user_weight_history) < 3:
        return True
    recent_avg = sum(user_weight_history[-7:]) / min(len(user_weight_history), 7)
    delta = abs(weight_kg - recent_avg)
    if delta > max_single_day_delta_kg:
        return False  # water/sodium spike — exclude
    return True

# Minimum readings per 7-day window:
if valid_readings_in_window < 4:
    flag_as "LOW_DATA_QUALITY"
    use previous window's average as fallback
```

**Recommendation (Helms):** Weigh every morning, fasted, post-void. Use 7-day rolling average. Compare weekly averages, not daily readings. Only act on 2-week trends.

### 1.5 Biweekly Calorie Adjustment Protocol

**Trigger:** Every 14 days, compare 7-day weight average at end vs. start of period.

#### 1.5.1 Target Rates of Weight Change

**Fat Loss Phase (CUTTING):**
```python
CUTTING_RATE_MIN_PCT_PER_WEEK = 0.5    # % of body weight per week
CUTTING_RATE_MAX_PCT_PER_WEEK = 1.0    # % of body weight per week
CUTTING_RATE_TARGET_PCT_PER_WEEK = 0.75  # midpoint default
MAX_CUTTING_DEFICIT_KCAL_PER_DAY = 750

# Source: Helms et al. (2014) JISSN 11:20; Aguilar-Navarro et al. (2021) Nutrients
# At 80 kg: 0.5%/week = 400g/week → ~440 kcal/day deficit
# At 80 kg: 1.0%/week = 800g/week → ~880 kcal/day deficit

if current_loss_rate_pct_per_week < 0.5:
    status = "LOSS_TOO_SLOW"; action = "reduce_calories"
elif current_loss_rate_pct_per_week > 1.0:
    status = "LOSS_TOO_FAST"; action = "increase_calories"  # LBM loss risk
else:
    status = "LOSS_ON_TARGET"; action = "hold_calories"
```

**Lean Bulk Phase (BULKING):**
```python
# Source: Iraki J, Fitschen P, Espinar S, Helms E. Sports (Basel). 2019;7(7):154.
BULKING_RATE_MIN_PCT_PER_MONTH = 0.25    # intermediates (lower bound)
BULKING_RATE_MAX_PCT_PER_MONTH = 1.0     # beginners (upper bound)
BULKING_RATE_INTERMEDIATE_PCT = 0.5      # default for intermediate lifters
# As % per WEEK:
BULKING_RATE_MIN_PCT_PER_WEEK = 0.0625   # 0.25% per month / 4 weeks
BULKING_RATE_MAX_PCT_PER_WEEK = 0.25     # 1.0% per month / 4 weeks

def get_target_bulk_rate_pct_per_week(experience_level: str) -> dict:
    rates = {
        "BEGINNER":      {"min": 0.25/4, "target": 0.5/4, "max": 2.0/4},
        "INTERMEDIATE":  {"min": 0.25/4, "target": 0.25/4, "max": 0.5/4},
        "ADVANCED":      {"min": 0.0,    "target": 0.125/4, "max": 0.25/4}
    }
    return rates.get(experience_level, rates["INTERMEDIATE"])
```

#### 1.5.2 Adjustment Amounts Table

| Phase | Scenario | Adjustment |
|---|---|---|
| CUTTING | Loss stalled (< 0.25% BW/week for 2 consecutive weeks) | −100 to −200 kcal/day |
| CUTTING | Loss too fast (> 1.0% BW/week) | +100 to +200 kcal/day |
| CUTTING | Loss on target (0.5–1.0% BW/week) | No change |
| BULKING | Gain stalled (< 0.06% BW/week for 2 weeks) | +100 to +200 kcal/day |
| BULKING | Gain too fast (> 0.25% BW/week for intermediates) | −100 to −200 kcal/day |
| BULKING | Gain on target | No change |
| MAINTENANCE | Weight trending up (>0.5% BW over 2 weeks) | −100 to −150 kcal/day |
| MAINTENANCE | Weight trending down (< −0.5% BW over 2 weeks) | +100 to +150 kcal/day |

#### 1.5.3 Full Biweekly Adjustment Pseudocode

```python
GoalPhase = Enum("GoalPhase", ["CUTTING", "BULKING", "MAINTENANCE"])

def biweekly_calorie_adjustment(goal_phase: GoalPhase,
                                 current_calories: int,
                                 rate_pct_per_week: float,
                                 body_weight_kg: float,
                                 experience_level: str,
                                 consecutive_stall_periods: int = 0) -> dict:
    """
    rate_pct_per_week: positive = gaining, negative = losing
    """
    adjustment = 0
    reason = "ON_TARGET"
    
    if goal_phase == GoalPhase.CUTTING:
        if rate_pct_per_week > -0.5:  # not losing fast enough
            if rate_pct_per_week >= 0:  # stable or gaining
                adjustment = -200
                reason = "CUTTING_STALLED"
            else:  # losing but slower than target
                adjustment = -100
                reason = "CUTTING_TOO_SLOW"
            if consecutive_stall_periods >= 2:
                adjustment = -200
                reason = "CUTTING_PERSISTENT_STALL"
        elif rate_pct_per_week < -1.0:  # losing too fast
            adjustment = +150
            reason = "CUTTING_TOO_FAST_LBM_RISK"
        else:
            reason = "CUTTING_ON_TARGET"
    
    elif goal_phase == GoalPhase.BULKING:
        target_rates = get_target_bulk_rate_pct_per_week(experience_level)
        if rate_pct_per_week < target_rates["min"]:
            adjustment = +200
            reason = "BULKING_TOO_SLOW"
            if consecutive_stall_periods >= 2:
                adjustment = +200
                reason = "BULKING_PERSISTENT_STALL"
        elif rate_pct_per_week > target_rates["max"]:
            adjustment = -150
            reason = "BULKING_TOO_FAST"
        else:
            reason = "BULKING_ON_TARGET"
    
    elif goal_phase == GoalPhase.MAINTENANCE:
        if rate_pct_per_week > 0.25:
            adjustment = -100
            reason = "MAINTENANCE_GAINING"
        elif rate_pct_per_week < -0.25:
            adjustment = +100
            reason = "MAINTENANCE_LOSING"
        else:
            reason = "MAINTENANCE_ON_TARGET"
    
    new_calories = max(current_calories + adjustment, 1200)  # hard floor
    
    return {
        "previous_calories": current_calories,
        "adjustment_kcal": adjustment,
        "new_calories": new_calories,
        "reason": reason,
        "rate_observed_pct_per_week": round(rate_pct_per_week, 3)
    }
```

### 1.6 Calorie Floor and Ceiling Constraints

```python
CALORIE_FLOOR_MALE = 1500          # kcal/day; below this, muscle loss risk increases dramatically
CALORIE_FLOOR_ABSOLUTE = 1200      # never go below this regardless of circumstances
MAX_DEFICIT_PCT_OF_TDEE = 0.25     # 25% below TDEE maximum
MAX_SURPLUS_KCAL = 600             # kcal/day above TDEE for bulking

def apply_calorie_bounds(target_calories: int, 
                          working_TDEE: int, 
                          goal_phase: GoalPhase) -> int:
    if target_calories < CALORIE_FLOOR_MALE:
        target_calories = CALORIE_FLOOR_MALE
    if goal_phase == GoalPhase.CUTTING:
        min_allowed = int(working_TDEE * (1 - MAX_DEFICIT_PCT_OF_TDEE))
        target_calories = max(target_calories, min_allowed, CALORIE_FLOOR_MALE)
    elif goal_phase == GoalPhase.BULKING:
        max_allowed = working_TDEE + MAX_SURPLUS_KCAL
        target_calories = min(target_calories, max_allowed)
    return target_calories
```

### 1.7 Metabolic Adaptation Modeling

**Definition:** Metabolic adaptation (adaptive thermogenesis) is the decline in TDEE that exceeds what would be predicted from body composition changes alone during caloric deficit.

**Key evidence:**
- Trexler et al. (2014): TDEE declines beyond body mass loss prediction; persists >1 year after weight loss. [PMC3943438](https://pmc.ncbi.nlm.nih.gov/articles/PMC3943438/)
- Rosenbaum & Leibel (2010): ≥10% body weight reduction → ~20–25% decline in 24h energy expenditure; 10–15% below prediction from composition changes. 85–90% of unexplained decline from NREE. [PMC3673773](https://pmc.ncbi.nlm.nih.gov/articles/PMC3673773/)
- Martins et al. (2020): After 14 kg (~13%) weight loss: −92 kcal/day immediate adaptation; −38 kcal/day after 4 weeks stabilization; ~50 kcal/day at weight-stable RMR.

**CRITICAL DESIGN DECISION:** Do NOT pre-emptively reduce calorie targets to account for adaptation. The adaptive TDEE calculation (§1.4.2) already captures adaptation in real-world data — the adaptive TDEE will naturally fall as adaptation occurs. Separate adaptation modeling would double-count the adjustment.

```python
METABOLIC_ADAPTATION_BUFFER_KCAL = 50   # kcal/day correction when equation-based ONLY

# Apply adaptation buffer ONLY when:
# 1. User has < 2 weeks of tracking data (equation-based only)
# 2. User is > 6 weeks into a cut
# 3. Weight loss has been ≥ 7% of starting body weight

def apply_adaptation_buffer(equation_TDEE: float,
                              weeks_in_deficit: int,
                              cumulative_weight_loss_pct: float,
                              using_adaptive_TDEE: bool) -> float:
    if using_adaptive_TDEE:
        return equation_TDEE  # no correction — adaptive TDEE already captures it
    if weeks_in_deficit < 6 or cumulative_weight_loss_pct < 7:
        return equation_TDEE  # no significant adaptation yet
    if cumulative_weight_loss_pct < 12:
        buffer = 75
    else:
        buffer = 125
    return equation_TDEE - buffer
```

**Magnitude reference data:**
| Study | Weight Loss | RMR Adaptation | Total TDEE Decline |
|---|---|---|---|
| Leibel et al. 1995 | 10% body weight | −137 kcal/day (immediate) | −10–15% below predicted |
| Martins et al. 2020 | 13–14 kg | −92 kcal/day (immediate); −38 kcal/day (stable) | — |
| Rosenbaum & Leibel 2010 | ≥10% body weight | 10–15% of decline at REE | 85–90% from NREE |

### 1.8 NEAT Suppression Flag

```python
NEAT_SUPPRESSION_THRESHOLD_KCAL = 200  # kcal/day below equation-based TDEE

def flag_neat_suppression(equation_TDEE: float, adaptive_TDEE: float,
                           current_weight_kg: float, baseline_weight_kg: float) -> dict:
    weight_loss_kg = baseline_weight_kg - current_weight_kg
    expected_TDEE_reduction = weight_loss_kg * 21  # kcal/kg lost
    adjusted_equation_TDEE = equation_TDEE - expected_TDEE_reduction
    adaptation_kcal = adjusted_equation_TDEE - adaptive_TDEE
    if adaptation_kcal > NEAT_SUPPRESSION_THRESHOLD_KCAL:
        return {
            "flag": "SIGNIFICANT_NEAT_SUPPRESSION_SUSPECTED",
            "adaptation_magnitude_kcal": round(adaptation_kcal),
            "action": "Consider mandatory maintenance phase or activity increase"
        }
    return {"flag": "WITHIN_NORMAL_RANGE", "adaptation_kcal": round(adaptation_kcal)}
```

### 1.9 Cut Duration Limits

```python
CUT_DURATION_WARNING_WEEKS = 12    # issue advisory, monitor closely
CUT_DURATION_MAX_WEEKS = 16        # recommend transitioning to maintenance
CUT_DURATION_ABSOLUTE_MAX_WEEKS = 20  # force maintenance phase regardless

def check_cut_duration(weeks_in_active_deficit: int,
                        cumulative_weight_loss_pct: float) -> dict:
    if weeks_in_active_deficit >= CUT_DURATION_ABSOLUTE_MAX_WEEKS:
        return {
            "status": "FORCE_MAINTENANCE",
            "action": "transition_to_maintenance",
            "reason": "Cut duration exceeded maximum recommended period",
            "recommended_maintenance_weeks": 6
        }
    elif weeks_in_active_deficit >= CUT_DURATION_MAX_WEEKS:
        return {
            "status": "TRANSITION_RECOMMENDED",
            "action": "suggest_maintenance_phase",
            "reason": "Metabolic adaptation and hormonal disruption risk",
            "recommended_maintenance_weeks": 4
        }
    elif weeks_in_active_deficit >= CUT_DURATION_WARNING_WEEKS:
        return {
            "status": "MONITOR_CLOSELY",
            "action": "advisory_only",
            "reason": "Approaching maximum recommended cut duration"
        }
    return {"status": "WITHIN_SAFE_DURATION"}
```

**Rate-based stall → maintenance trigger:**
```python
def check_rate_based_transition(consecutive_stall_cycles: int,
                                  current_calories: int,
                                  working_TDEE: int,
                                  goal_phase: GoalPhase) -> dict:
    if goal_phase != GoalPhase.CUTTING:
        return {"status": "NOT_CUTTING"}
    current_deficit_pct = (working_TDEE - current_calories) / working_TDEE
    at_maximum_deficit = current_deficit_pct >= 0.22  # close to 25% max
    if consecutive_stall_cycles >= 3 and at_maximum_deficit:
        return {
            "status": "STALLED_AT_MAX_DEFICIT",
            "action": "TRANSITION_TO_MAINTENANCE",
            "reason": "Metabolic adaptation suspected — further reduction inadvisable",
            "recommended_maintenance_calories": working_TDEE,
            "recommended_maintenance_duration_weeks": 4
        }
    elif consecutive_stall_cycles >= 4:
        return {
            "status": "PERSISTENT_STALL",
            "action": "TRANSITION_TO_MAINTENANCE",
            "reason": "Progress has halted for 8+ weeks — diet break recommended"
        }
    return {"status": "ADJUSTABLE", "consecutive_stalls": consecutive_stall_cycles}
```

### 1.10 Biweekly Adjustment — Decision Logic Master Flow

```
START BIWEEKLY ADJUSTMENT CYCLE
│
├── Input: 14-day weight log, 14-day calorie log, current goal_phase
│
├── STEP 1: Data Quality Check
│   ├── valid_weight_readings >= 8 of 14 days?
│   │   ├── YES → proceed
│   │   └── NO → flag LOW_DATA_QUALITY; hold current calories; request more data
│   └── calorie_logging_completeness >= 80%?
│       ├── YES → proceed with adaptive TDEE calculation
│       └── NO → use equation-based TDEE only
│
├── STEP 2: Compute Weight Trend
│   ├── week1_avg = average(days 1–7 weights)
│   ├── week2_avg = average(days 8–14 weights)
│   ├── weight_delta_kg = week2_avg − week1_avg
│   └── rate_pct_per_week = (weight_delta_kg / week1_avg) × 100
│
├── STEP 3: Update Adaptive TDEE
│   ├── avg_daily_calories = total_logged_calories / logged_days
│   ├── adaptive_TDEE = avg_daily_calories − (weight_delta_kg × 7700 / 14)
│   └── working_TDEE = blend(adaptive_TDEE, equation_TDEE, weeks_of_data)
│
├── STEP 4: Check Safety Triggers
│   ├── cut_duration_check(weeks_in_deficit)
│   ├── rate_based_transition_check(consecutive_stall_cycles, current_calories)
│   └── neat_suppression_flag(equation_TDEE, adaptive_TDEE)
│
├── STEP 5: Compute Calorie Adjustment (see §1.5.3)
│
├── STEP 6: Apply Bounds
│   ├── new_calories = current_calories + adjustment
│   ├── new_calories = max(new_calories, CALORIE_FLOOR_MALE)  // 1500 kcal floor
│   └── IF CUTTING: new_calories = max(new_calories, working_TDEE × 0.75)
│
└── OUTPUT:
    ├── new_calorie_target (int, kcal/day)
    ├── adjustment_made (int, kcal)
    ├── reason_code (string)
    ├── working_TDEE_estimate (int, kcal/day)
    ├── weight_trend_rate_pct_per_week (float)
    └── any advisory flags
```

---

## PART 2: PROTEIN & MACRONUTRIENT TARGETS

*Source: Track 7 — Protein Phases; Track 5 — Ad Libitum*

### 2.1 Protein Calculation Formula

**Fixed system target:** `0.82 g/lb` of body weight — IMMUTABLE ACROSS ALL PHASES

**Evidence basis:**
- Morton et al. (2018) meta-analysis (49 RCTs, n=1,863): protein breakpoint = 1.62 g/kg (mean; 95% CI: 1.03–2.20 g/kg = 0.735–0.998 g/lb). [BJSM DOI: 10.1136/bjsports-2017-097608](https://bjsm.bmj.com/lookup/doi/10.1136/bjsports-2017-097608)
- Henselmans (2012): 0.82 g/lb represents the upper safety margin (double 95% CI convention) — `1.8 g/kg / 2.2046 = 0.8165 ≈ 0.82 g/lb`. [mennohenselmans.com](https://mennohenselmans.com/the-myth-of-1glb-optimal-protein-intake-for-bodybuilders/)
- Henselmans (2024): No higher protein needed in energy deficit. [mennohenselmans.com](https://mennohenselmans.com/you-dont-need-more-protein-in-energy-deficit/)
- Safety ceiling: Antonio et al. studies show 3.3 g/kg (1.5 g/lb) for 1 year → no adverse effects on kidney, liver, lipids. 0.82 g/lb is well below any safety concern.

```python
system_protein_target_per_lb: float = 0.82  # FIXED, immutable by phase

def calculate_protein_target_lbs(user_weight_lbs: float) -> float:
    """Returns daily protein target in grams. Uses Milo fixed rate: 0.82 g/lb."""
    PROTEIN_RATE_G_PER_LB: float = 0.82
    return user_weight_lbs * PROTEIN_RATE_G_PER_LB

def calculate_protein_target_kg(user_weight_kg: float) -> float:
    LBS_PER_KG: float = 2.2046
    return calculate_protein_target_lbs(user_weight_kg * LBS_PER_KG)

# Examples:
# 180 lb user: 180 * 0.82 = 147.6 g/day
# 90 kg user:  90 * 2.2046 * 0.82 = 163.0 g/day
```

### 2.2 Adjusted Body Weight for Obese Users

**Rule:**
- BMI < 30: Use total body weight directly (no adjustment)
- BMI 30–40: Use Adjusted Body Weight (AjBW) formula
- BMI > 40: Use AjBW formula with clinical judgment

```python
def calculate_ideal_body_weight_male_kg(height_inches: float) -> float:
    """Robinson formula for ideal body weight (male)."""
    BASE_WEIGHT_KG: float = 52.0
    KG_PER_INCH_OVER_60: float = 1.9
    if height_inches <= 60:
        return BASE_WEIGHT_KG
    return BASE_WEIGHT_KG + KG_PER_INCH_OVER_60 * (height_inches - 60)

def calculate_adjusted_body_weight_kg(actual_body_weight_kg: float, 
                                        height_inches: float) -> float:
    """
    AjBW = IBW + 0.4 × (ABW - IBW)
    The factor 0.4 reflects ~40% of excess weight contributes to metabolically relevant mass.
    """
    ADJUSTMENT_FACTOR: float = 0.4
    ibw = calculate_ideal_body_weight_male_kg(height_inches)
    if actual_body_weight_kg <= ibw:
        return actual_body_weight_kg
    return ibw + ADJUSTMENT_FACTOR * (actual_body_weight_kg - ibw)

def calculate_protein_target_with_obesity_adjustment(
    user_weight_lbs: float, user_height_inches: float, user_bmi: float) -> dict:
    PROTEIN_RATE: float = 0.82
    BMI_OBESITY_THRESHOLD: float = 30.0
    user_weight_kg = user_weight_lbs / 2.2046
    if user_bmi >= BMI_OBESITY_THRESHOLD:
        ajbw_kg = calculate_adjusted_body_weight_kg(user_weight_kg, user_height_inches)
        ajbw_lbs = ajbw_kg * 2.2046
        protein_target_g = ajbw_lbs * PROTEIN_RATE
        weight_basis = "adjusted_body_weight"
        weight_used_lbs = ajbw_lbs
    else:
        protein_target_g = user_weight_lbs * PROTEIN_RATE
        weight_basis = "total_body_weight"
        weight_used_lbs = user_weight_lbs
    return {
        "protein_target_g": round(protein_target_g, 1),
        "weight_used_lbs": round(weight_used_lbs, 1),
        "weight_basis": weight_basis,
        "protein_rate_g_per_lb": PROTEIN_RATE
    }
```

**Example calculations:**
| User | TBW (lbs) | Height | BMI | AjBW (lbs) | Protein Target |
|---|---|---|---|---|---|
| Normal weight male | 180 | 5'10" | 25.8 | N/A | 147.6 g |
| Obese male | 250 | 5'10" | 35.9 | 196.5 | 161.1 g |
| Obese male | 300 | 5'10" | 43.0 | 210.9 | 173.0 g |

### 2.3 Protein Distribution Across Meals

**Source:** Schoenfeld BJ, Aragon AA. (2018). JISSN 15:10. [PubMed: 29497353](https://pubmed.ncbi.nlm.nih.gov/29497353/)

```python
per_meal_protein_min_g_per_kg: float = 0.40   # minimum per meal to maximize MPS
per_meal_protein_max_g_per_kg: float = 0.55   # upper per meal for high-protein protocols
min_meals_per_day: int = 3
optimal_meals_per_day: int = 4

# Per-meal target for a 180 lb (81.6 kg) user:
# per_meal_minimum = 81.65 * 0.40 = 32.7 g
# per_meal_upper   = 81.65 * 0.55 = 44.9 g
```

**Key findings:**
- Redistributing 90g/day of protein from skewed (10-20-60g) to even (30-30-30g) increased net daily MPS by **25%** (Paddon-Jones)
- Minimum ~24–30g per meal to reliably elicit satiety response and MPS (Leidy; Paddon-Jones)
- Timing relative to training does NOT significantly affect hypertrophy when total daily protein is adequate (Schoenfeld et al. 2013)
- Total protein intake is the strongest predictor of hypertrophy effect size magnitude

### 2.4 Fat and Carbohydrate Guidance (Lighter Macronutrient Guidance)

**Fat (minimum):**
```python
FAT_MINIMUM_PCT_OF_CALORIES = 0.20    # 20% of total calories minimum for hormonal health
FAT_MINIMUM_G_PER_KG = 0.5           # g/kg body weight per day

# Fat floors:
fat_minimum_g = max(
    FAT_MINIMUM_PCT_OF_CALORIES * total_calories / 9,
    weight_kg * FAT_MINIMUM_G_PER_KG
)
```

**Carbohydrates:**
```python
# Carbs fill remaining calories after protein and fat are accounted for:
protein_calories = protein_g * 4
fat_calories = fat_g * 9
carb_calories = total_calories - protein_calories - fat_calories
carb_g = max(0, carb_calories / 4)
# No carb minimum specified; carbs are the flexible macro
```

**Note:** Milo does NOT use calorie cycling or macronutrient cycling. Fixed daily protein. No refeeds.

---

## PART 3: NUTRITIONAL PHASE MANAGEMENT

*Source: Track 7 — Protein Phases; Track 1 — TDEE*

### 3.1 Phase Definitions

```python
from enum import Enum

class NutritionalPhase(Enum):
    CUT = "cut"
    MAINTENANCE = "maintenance"
    LEAN_BULK = "lean_bulk"

class CutAggression(Enum):
    MODERATE = "moderate"      # 300–500 kcal/day deficit
    AGGRESSIVE = "aggressive"  # 500–750 kcal/day deficit

class BulkRate(Enum):
    BEGINNER = "beginner"         # 200–350 kcal/day surplus
    INTERMEDIATE = "intermediate"  # 100–200 kcal/day surplus
```

### 3.2 CUT Phase

**Definition:** Deliberate caloric deficit targeting maximal fat loss while preserving LBM.

**Source:** Helms ER, Aragon AA, Fitschen PJ. (2014). JISSN 11:20. [PMC4033492](https://pmc.ncbi.nlm.nih.gov/articles/PMC4033492/); Ruiz-Castellano et al. (2021) Nutrients. [PMC8471721](https://pmc.ncbi.nlm.nih.gov/articles/PMC8471721/)

```python
class CutDeficitRange:
    MODERATE_LOWER: int = 300    # kcal/day
    MODERATE_UPPER: int = 500    # kcal/day
    AGGRESSIVE_LOWER: int = 500  # kcal/day
    AGGRESSIVE_UPPER: int = 750  # kcal/day

class WeightLossRateTargets:
    MINIMUM_RATE_PCT: float = 0.25    # % BW/week
    OPTIMAL_LOWER_PCT: float = 0.50   # % BW/week
    OPTIMAL_UPPER_PCT: float = 1.00   # % BW/week (Helms 2014)
    MAX_SAFE_RATE_PCT: float = 1.00   # above this, muscle loss risk increases

class CutDurationLimits:
    MINIMUM_CUT_WEEKS: int = 4
    OPTIMAL_CUT_LOWER_WEEKS: int = 8
    OPTIMAL_CUT_UPPER_WEEKS: int = 12
    SOFT_MAX_WEEKS: int = 16        # Recommend transition at/before this point
    HARD_MAX_WEEKS: int = 20        # Strong recommendation to exit regardless
```

**Evidence on LBM retention during cuts:**
- Aguilar-Navarro et al. (2021): weekly weight losses of 0.5% BW show meaningfully greater FFM retention than 0.7% or 1.0% BW/week (at 1.0%/week, LBM loss reached 42.8% of total weight lost)
- RP Strength / Israetel: max deficit ≤500 kcal/day for muscle-preserving cuts; aiming for ~1 lb/week for most of cut

### 3.3 MAINTENANCE Phase

**Definition:** Eating at estimated TDEE (±100 kcal tolerance).

```python
class MaintenanceCalorieRange:
    DEFICIT_TOLERANCE_KCAL: int = 100
    SURPLUS_TOLERANCE_KCAL: int = 100

class MaintenanceDurationGuidelines:
    POST_CUT_MIN_WEEKS: int = 2
    POST_CUT_OPTIMAL_WEEKS: int = 4
    POST_CUT_MAX_WEEKS: int = 12
    POST_BULK_MIN_WEEKS: int = 2
    POST_BULK_OPTIMAL_WEEKS: int = 4

maintenance_trigger_conditions = {
    "post_cut_recovery": True,
    "between_phases": True,
    "high_life_stress": True,
    "training_performance_declining": True,
    "pre_bulk_normalization": True,
}
```

### 3.4 LEAN BULK Phase

**Definition:** Deliberate caloric surplus targeting muscle hypertrophy while minimizing fat gain.

**Source:** Helms ER, Iraki J, et al. (2019). Sports 7(7):154. [PMC6680710](https://pmc.ncbi.nlm.nih.gov/articles/PMC6680710/)

```python
class LeanBulkSurplusTargets:
    BEGINNER_SURPLUS_LOWER: int = 200
    BEGINNER_SURPLUS_UPPER: int = 350
    INTERMEDIATE_SURPLUS_LOWER: int = 100
    INTERMEDIATE_SURPLUS_UPPER: int = 200
    BEGINNER_GAIN_RATE_LOWER_PCT: float = 0.25    # % BW/week
    BEGINNER_GAIN_RATE_UPPER_PCT: float = 0.50
    INTERMEDIATE_GAIN_RATE_LOWER_PCT: float = 0.10
    INTERMEDIATE_GAIN_RATE_UPPER_PCT: float = 0.25

class LeanBulkDurationLimits:
    MINIMUM_BULK_WEEKS: int = 8
    OPTIMAL_BULK_LOWER_WEEKS: int = 12
    OPTIMAL_BULK_UPPER_WEEKS: int = 20
    SOFT_MAX_WEEKS: int = 24
    EXIT_BF_THRESHOLD_PCT: float = 20.0  # Exit bulk if BF% reaches ~20%

class BulkBodyCompositionExpectations:
    BEGINNER_MUSCLE_FRACTION_MODERATE_SURPLUS: float = 0.50
    BEGINNER_MUSCLE_FRACTION_AGGRESSIVE_SURPLUS: float = 0.30
    INTERMEDIATE_MUSCLE_FRACTION_MODERATE_SURPLUS: float = 0.30
    INTERMEDIATE_MUSCLE_FRACTION_AGGRESSIVE_SURPLUS: float = 0.15
    BEGINNER_MAX_MUSCLE_GAIN_LBS_PER_YEAR: float = 12.0
    INTERMEDIATE_MAX_MUSCLE_GAIN_LBS_PER_YEAR: float = 6.0
    ADVANCED_MAX_MUSCLE_GAIN_LBS_PER_YEAR: float = 2.0
```

### 3.5 Phase Transition Logic

#### 3.5.1 CUT → MAINTENANCE

```python
def should_transition_cut_to_maintenance(inputs: PhaseTransitionInputs) -> dict:
    """
    PhaseTransitionInputs fields:
        current_weight_lbs, estimated_body_fat_pct, goal_weight_lbs, goal_body_fat_pct,
        current_phase, phase_start_date, phase_duration_weeks,
        weekly_weight_change_lbs, rate_of_change_pct_bw,
        training_performance_score (1–5), fatigue_level_score (1–5),
        hunger_level_score (1–5), adherence_score (1–5),
        user_wants_to_cut, user_wants_to_bulk, user_wants_maintenance
    """
    reasons = []
    urgency = "routine"
    
    # TRIGGER 1: Goal reached
    goal_weight_reached = (inputs.current_weight_lbs <= inputs.goal_weight_lbs + 1.0)
    goal_bf_reached = (inputs.estimated_body_fat_pct is not None and
                       inputs.estimated_body_fat_pct <= inputs.goal_body_fat_pct + 1.0)
    if goal_weight_reached or goal_bf_reached:
        reasons.append("goal_reached"); urgency = "routine"
    
    # TRIGGER 2: Max cut duration exceeded
    if inputs.phase_duration_weeks >= CutDurationLimits.HARD_MAX_WEEKS:
        reasons.append("max_duration_exceeded_hard"); urgency = "urgent"
    elif inputs.phase_duration_weeks >= CutDurationLimits.SOFT_MAX_WEEKS:
        reasons.append("max_duration_exceeded_soft"); urgency = max(urgency, "recommended")
    
    # TRIGGER 3: Metabolic adaptation signal
    metabolic_adaptation_signal = (
        abs(inputs.rate_of_change_pct_bw) < 0.10 and
        inputs.phase_duration_weeks >= 8
    )
    if metabolic_adaptation_signal:
        reasons.append("metabolic_adaptation_signal"); urgency = max(urgency, "recommended")
    
    # TRIGGER 4: Performance decline
    if inputs.training_performance_score <= 2:
        reasons.append("training_performance_declining"); urgency = max(urgency, "recommended")
    
    # TRIGGER 5: Excessive fatigue or hunger
    if inputs.fatigue_level_score <= 2 or inputs.hunger_level_score <= 2:
        reasons.append("excessive_fatigue_or_hunger"); urgency = max(urgency, "recommended")
    
    # TRIGGER 6: Adherence declining
    if inputs.adherence_score <= 2:
        reasons.append("adherence_declining"); urgency = max(urgency, "recommended")
    
    # TRIGGER 7: User request
    if inputs.user_wants_maintenance:
        reasons.append("user_requested"); urgency = "routine"
    
    return {"should_transition": len(reasons) > 0, "reasons": reasons,
            "urgency": urgency, "transition_to": NutritionalPhase.MAINTENANCE}
```

#### 3.5.2 MAINTENANCE → LEAN BULK

```python
def should_transition_maintenance_to_lean_bulk(inputs: PhaseTransitionInputs) -> dict:
    reasons = []
    MINIMUM_MAINTENANCE_WEEKS_BEFORE_BULK: int = 4
    MAX_BF_TO_START_BULK_PCT: float = 15.0
    IDEAL_BF_TO_START_BULK_PCT: float = 12.0
    
    min_duration_met = inputs.phase_duration_weeks >= MINIMUM_MAINTENANCE_WEEKS_BEFORE_BULK
    recovery_strong = (inputs.training_performance_score >= 4 and inputs.fatigue_level_score >= 4)
    bf_acceptable_for_bulk = (inputs.estimated_body_fat_pct is None or
                               inputs.estimated_body_fat_pct <= MAX_BF_TO_START_BULK_PCT)
    
    # BLOCK: BF too high
    if (inputs.estimated_body_fat_pct is not None and 
        inputs.estimated_body_fat_pct > MAX_BF_TO_START_BULK_PCT):
        return {"should_transition": False, "reasons": ["body_fat_too_high_for_bulk"],
                "recommendation": "CUT first to bring body fat below 15%", "transition_to": None}
    
    if min_duration_met and recovery_strong:
        reasons.append("minimum_maintenance_complete_with_good_recovery")
    if bf_acceptable_for_bulk and min_duration_met:
        reasons.append("body_fat_acceptable_for_bulk")
    if inputs.user_wants_to_bulk and min_duration_met and bf_acceptable_for_bulk:
        reasons.append("user_requested")
    
    return {"should_transition": len(reasons) > 0 and min_duration_met,
            "reasons": reasons, "urgency": "routine",
            "transition_to": NutritionalPhase.LEAN_BULK if len(reasons) > 0 else None}
```

#### 3.5.3 LEAN BULK → CUT

```python
def should_transition_lean_bulk_to_cut(inputs: PhaseTransitionInputs) -> dict:
    reasons = []
    urgency = "routine"
    BF_SOFT_CEILING_PCT: float = 18.0
    BF_HARD_CEILING_PCT: float = 20.0
    
    # TRIGGER 1: BF ceiling
    if inputs.estimated_body_fat_pct is not None:
        if inputs.estimated_body_fat_pct >= BF_HARD_CEILING_PCT:
            reasons.append("body_fat_hard_ceiling_reached"); urgency = "urgent"
        elif inputs.estimated_body_fat_pct >= BF_SOFT_CEILING_PCT:
            reasons.append("body_fat_soft_ceiling_reached"); urgency = "recommended"
    
    # TRIGGER 2: Max bulk duration
    if inputs.phase_duration_weeks >= LeanBulkDurationLimits.SOFT_MAX_WEEKS:
        reasons.append("max_bulk_duration_reached"); urgency = max(urgency, "recommended")
    
    # TRIGGER 3: User request
    if inputs.user_wants_to_cut:
        reasons.append("user_requested")
    
    return {"should_transition": len(reasons) > 0, "reasons": reasons,
            "urgency": urgency, "transition_to": NutritionalPhase.CUT if len(reasons) > 0 else None}
```

#### 3.5.4 MAINTENANCE → CUT

```python
def should_transition_maintenance_to_cut(inputs: PhaseTransitionInputs) -> dict:
    reasons = []
    MIN_MAINTENANCE_WEEKS_BEFORE_CUT: int = 2
    CUT_BF_TRIGGER_PCT: float = 20.0
    recovery_adequate = inputs.phase_duration_weeks >= MIN_MAINTENANCE_WEEKS_BEFORE_CUT
    
    if inputs.user_wants_to_cut:
        reasons.append("user_goal_fat_loss")
    if (inputs.estimated_body_fat_pct is not None and
        inputs.estimated_body_fat_pct >= CUT_BF_TRIGGER_PCT):
        reasons.append("body_fat_above_cut_trigger")
    
    return {"should_transition": len(reasons) > 0 and recovery_adequate, "reasons": reasons,
            "transition_to": NutritionalPhase.CUT if len(reasons) > 0 and recovery_adequate else None,
            "blocked_reason": "insufficient_maintenance_duration" if not recovery_adequate else None}
```

### 3.6 Phase State Machine Summary

```
States: CUT | MAINTENANCE | LEAN_BULK
Initial state: determined by onboarding profile

┌─────────────────────────────────────────────────────────┐
│                    STATE: CUT                           │
│  Deficit: 300–500 kcal/day (moderate)                   │
│  Target: -0.5% to -1.0% BW/week                         │
│  Protein: user_weight_lbs × 0.82 g                      │
│  Max duration: 16 weeks soft, 20 weeks hard              │
│  Biweekly adjustment: ±150 kcal vs. target rate         │
└────────────────┬────────────────────────────────────────┘
                 │  TRANSITIONS TO MAINTENANCE:
                 │  Goal reached / Max duration / Metabolic stall /
                 │  Performance declining (≤2/5) / Excessive fatigue/hunger /
                 │  Adherence failing (≤2/5) / User requests
                 ▼
┌─────────────────────────────────────────────────────────┐
│                 STATE: MAINTENANCE                      │
│  Calories: TDEE (±100 kcal tolerance)                   │
│  Protein: user_weight_lbs × 0.82 g                      │
│  Post-cut optimal: 4 weeks / Minimum before CUT: 2 wks  │
│  Minimum before LEAN_BULK: 4 weeks                      │
└────────┬──────────────────────────────┬─────────────────┘
         │ → CUT: Goal=fat loss /       │ → LEAN_BULK: 4+ wks done /
         │   BF%≥20% / Min 2 wks met   │   Recovery strong (≥4/5) /
         ▼                              │   BF%≤15% / User requests
   (back to CUT)                        ▼
                              ┌──────────────────────────┐
                              │    STATE: LEAN_BULK       │
                              │  Surplus: 200–350 (bgn)   │
                              │  100–200 kcal/d (interm)  │
                              │  Target: +0.25–0.50%/wk  │
                              │  Protein: TBW × 0.82 g   │
                              │  Max: 24 weeks            │
                              └──────────┬───────────────┘
                                         │ → CUT: BF%≥18% (soft) /
                                         │   BF%≥20% (urgent) /
                                         │   Duration ≥24 wks / User
                                         ▼
                                    (back to CUT)
```

### 3.7 Recomposition Handling

**Evidence:** Barakat et al. (2020) SCJ — Recomp possible in trained individuals. Very high likelihood for: beginners (<12 months), detrained, overfat (>25% BF males). [DOI: 10.1519/SSC.0000000000000584](https://journals.lww.com/10.1519/SSC.0000000000000584)

**Milo design decision:** Recomposition is NOT a separate named phase. Handled as **MAINTENANCE calories + progressive resistance training + 0.82 g/lb protein**.

```python
class RecompPhaseHandling:
    PHASE_ASSIGNMENT: NutritionalPhase = NutritionalPhase.MAINTENANCE
    CALORIE_TARGET: str = "TDEE"
    PROTEIN_RATE_G_PER_LB: float = 0.82
    RECOMP_PLATEAU_TRIGGER_WEEKS: int = 10  # If no body comp improvement → recommend phase transition
    RECOMP_SUCCESS_INDICATOR: str = "stable_weight + improved_bf_pct_or_measurements"

def assess_recomposition_eligibility(
    training_age_months: int, body_fat_pct: float,
    training_quality_score: int, nutrition_quality_score: int, recovery_quality_score: int
) -> dict:
    BEGINNER_THRESHOLD_MONTHS: int = 12
    HIGH_BF_THRESHOLD_PCT: float = 25.0
    is_beginner = training_age_months < BEGINNER_THRESHOLD_MONTHS
    is_high_bf = body_fat_pct > HIGH_BF_THRESHOLD_PCT
    has_optimization_headroom = (training_quality_score <= 3 or
                                  nutrition_quality_score <= 3 or
                                  recovery_quality_score <= 3)
    if is_beginner or is_high_bf or has_optimization_headroom:
        return {"recomp_probability": "high" if (is_beginner or is_high_bf) else "moderate",
                "recommended_approach": "maintenance_calories_with_optimized_training",
                "recommended_phase": NutritionalPhase.MAINTENANCE}
    else:
        return {"recomp_probability": "low",
                "recommended_approach": "traditional_bulk_cut_cycles",
                "recommended_phase": None}
```

### 3.8 Evidence on Refeeds and Diet Breaks (EXCLUDED)

**Design decision:** Milo does NOT include refeeds or diet breaks. Evidence justification:

- MATADOR study (Byrne et al. 2018): Diet breaks showed benefit in **obese men** — not Milo's resistance-trained target population. [PMC5803575](https://pmc.ncbi.nlm.nih.gov/articles/PMC5803575/)
- Campbell et al. (2023): Diet breaks — no benefit for body composition or RMR in resistance-trained females. [PMC10170537](https://pmc.ncbi.nlm.nih.gov/articles/PMC10170537/)
- Meta-analysis (2024, Norton): Only ~50 kcal/day difference in metabolic adaptation; no differences in LBM retention or fat loss.
- ICECAP Trial: 12-week intermittent ER did not produce superior fat loss, LBM, or REE vs. continuous ER in athletes. [PMC6359485](https://pmc.ncbi.nlm.nih.gov/articles/PMC6359485/)
- Diet breaks double total time required (30 weeks instead of 16 weeks).
- Milo's biweekly calorie adjustment mechanism already captures metabolic adaptation functionally.

```python
class RefeedDietBreakPolicy:
    INCLUDED: bool = False
    # Future consideration: Could add for advanced athlete/contest prep support
```

### 3.9 Biweekly Calorie Adjustment Logic (Phase-Specific)

```python
def calculate_biweekly_calorie_adjustment(
    current_phase: NutritionalPhase,
    actual_weight_change_lbs_over_2_weeks: float,
    user_weight_lbs: float,
    current_calories: int
) -> dict:
    actual_weekly_change_pct = (actual_weight_change_lbs_over_2_weeks / 2) / user_weight_lbs * 100
    ADJUSTMENT_INCREMENT_KCAL: int = 150
    
    if current_phase == NutritionalPhase.CUT:
        TARGET_LOWER = -1.00; TARGET_UPPER = -0.50
        if actual_weekly_change_pct > TARGET_UPPER:
            adjustment = -ADJUSTMENT_INCREMENT_KCAL; reason = "weight_loss_too_slow"
        elif actual_weekly_change_pct < TARGET_LOWER:
            adjustment = +ADJUSTMENT_INCREMENT_KCAL; reason = "weight_loss_too_fast"
        else:
            adjustment = 0; reason = "on_target"
    
    elif current_phase == NutritionalPhase.LEAN_BULK:
        TARGET_LOWER = +0.25; TARGET_UPPER = +0.50
        if actual_weekly_change_pct < TARGET_LOWER:
            adjustment = +ADJUSTMENT_INCREMENT_KCAL; reason = "weight_gain_too_slow"
        elif actual_weekly_change_pct > TARGET_UPPER:
            adjustment = -ADJUSTMENT_INCREMENT_KCAL; reason = "weight_gain_too_fast"
        else:
            adjustment = 0; reason = "on_target"
    
    elif current_phase == NutritionalPhase.MAINTENANCE:
        TARGET_RANGE = 1.0
        if actual_weight_change_lbs_over_2_weeks > TARGET_RANGE:
            adjustment = -ADJUSTMENT_INCREMENT_KCAL; reason = "unintended_weight_gain"
        elif actual_weight_change_lbs_over_2_weeks < -TARGET_RANGE:
            adjustment = +ADJUSTMENT_INCREMENT_KCAL; reason = "unintended_weight_loss"
        else:
            adjustment = 0; reason = "on_target"
    
    return {
        "calorie_adjustment": adjustment,
        "new_calorie_target": current_calories + adjustment,
        "actual_weekly_change_pct": round(actual_weekly_change_pct, 3),
        "reason": reason
    }
```

---

## PART 4: AD LIBITUM NUTRITION MODE

*Source: Track 5 — Ad Libitum Dieting*

### 4.1 Evidence Base

**Definition:** Ad libitum (AL) mode — eating to voluntary satiety without tracking. Works via high-protein, high-fiber, low-energy-density, minimally processed food structures that induce caloric deficit automatically through enhanced satiety.

**Key studies:**
- **Weigle et al. (2005):** N=19, high-protein AL diet (30% protein) → spontaneous energy intake ↓441 ± 63 kcal/day; body weight ↓4.9 ± 0.5 kg; fat mass ↓3.7 ± 0.4 kg. Mechanism: ↑CNS leptin sensitivity; ↓ghrelin AUC. [PubMed 16002798](https://pubmed.ncbi.nlm.nih.gov/16002798/)
- **Antonio et al. (2015):** HP group (3.4 g/kg/day): fat mass −1.7 ± 2.3 kg; %BF −2.4 ± 2.9%. NP group: fat mass −0.3 ± 2.2 kg; %BF −0.7 ± 2.8%. [PubMed 26500462](https://pubmed.ncbi.nlm.nih.gov/26500462/)
- **Hall et al. (2019):** RCT UPF vs. unprocessed diet (matched macros/calories) — UPF participants ate **~500 kcal/day MORE** ad libitum; gained 0.9 kg vs. −0.9 kg for MPF group. [PMC7946062](https://pmc.ncbi.nlm.nih.gov/articles/PMC7946062/)
- **Astbury et al. (2025):** 8-week RCT free-living — MPF diet produced significantly greater weight loss than UPF diet even when both met healthy eating guidelines. [Nature Medicine 2025](https://www.nature.com/articles/s41591-025-03842-0)

**Recomposition potential without tracking (beginners):** High under conditions of: untrained/detrained status, high baseline BF, protein ≥0.7–0.8 g/lb, consistent progressive overload, primarily whole foods.

**Aragon flexible dieting principle:** Rigid dietary control → higher disinhibition → binge tendencies → higher BMI. Flexible/habits-based control → better long-term outcomes. [Flexible Dieting guide](https://studylib.net/doc/27825114/flexible-dieting---alan-aragon)

### 4.2 Protein-First Strategy

**Protein satiety mechanisms:**
| Mechanism | Effect |
|---|---|
| Ghrelin suppression | Reduces hunger signal |
| PYY elevation | Increases fullness signal |
| GLP-1 elevation | Extends satiety window |
| CNS leptin sensitivity | Reduces appetite long-term |
| Reduced reward-driven eating | Reduced cravings |
| Higher thermic effect (25–30% vs. 5–10%) | More calories burned in digestion |

**Minimum protein per meal for satiety/MPS:** ≥24–30 grams (Leidy; Paddon-Jones)

**Palm-sized protein heuristic (Precision Nutrition: 95% as accurate as weighing):**
```
PROTEIN_TARGET_g = 0.82 × bodyweight_lbs

Palm-sized serving of chicken/fish/beef ≈ 25–35g protein
Greek yogurt (1 cup) ≈ 17–22g protein
3 eggs ≈ 18g protein
Cottage cheese (1 cup) ≈ 25–28g protein

Per-meal protein anchoring:
140–160 lb: 1 palm-sized serving (25–35g) per meal
160–200 lb: 1–1.5 palm-sized servings per meal
200+ lb: 2 palm-sized servings OR supplement with protein shake
```

### 4.3 The 7 Heuristic Rules for Ad Libitum Mode

#### RULE 01: Protein at Every Meal
**Statement:** Every meal must include ≥25g quality protein.  
**Evidence:** STRONG (consistent RCTs; Leidy; Weigle; Paddon-Jones)  
```
IF meal.protein_present == FALSE:
  milo_nudge = "Looks like this meal might be light on protein — any way to add 
                some chicken, eggs, Greek yogurt, or cottage cheese?"
```

#### RULE 02: Plate Composition
**Statement:** ½ plate non-starchy vegetables, ¼ plate lean protein, ¼ plate starchy carbs.  
**Evidence:** MODERATE (plate model RCT: −1.27 ± 3.58 kg vs. −0.26 ± 2.42 kg at 12 wks). [PMC6511685](https://pmc.ncbi.nlm.nih.gov/articles/PMC6511685/)
```python
if meal_context == "fat_loss":
    plate_template = {protein: 0.25, veggies: 0.50, carbs: 0.25}
elif meal_context in ("recomp", "muscle_gain"):
    plate_template = {protein: 0.33, veggies: 0.33, carbs: 0.33}
```

#### RULE 03: 80/20 Food Quality
**Statement:** ≥80% of food from whole/minimally processed sources; ≤20% ultra-processed.  
**Evidence:** STRONG (Hall et al. 2019: UPF → 500 kcal/day excess)  
```
TIER_1 (Minimally processed — preferred):
  Eggs, chicken, fish, lean beef, Greek yogurt, cottage cheese, oats, rice,
  potatoes, sweet potatoes, vegetables, fruits, legumes, nuts, olive oil

TIER_2 (Processed — occasional):
  Deli meats, canned fish, protein bars/powders, whole grain bread, low-fat dairy

TIER_3 (Ultra-processed — limit ≤20%):
  Chips, cookies, fast food, packaged pastries, sugar-sweetened beverages
```

#### RULE 04: Hunger/Fullness Scale (Stop at 7)
**Statement:** Eat when ≥3 on hunger scale; stop at ≤7 (comfortable fullness).  
**Evidence:** MODERATE for fat loss; STRONG for maintenance and psychological outcomes
```
1 = Starving; 2 = Very hungry; 3 = Moderately hungry (time to eat)
4 = Slightly hungry; 5 = Neutral; 6 = Slightly satisfied
7 = Comfortably full — STOP HERE; 8 = Overfull; 9 = Very full; 10 = Stuffed

IF fullness_rating > 8:
  milo_response = "Sounds like you were a bit too full — next time, 
                   try pausing at 7 and seeing how you feel 10 minutes later."
```

#### RULE 05: Meal Frequency (3–4 Meals/Day)
**Statement:** Default 3–4 structured meals/day with protein at each.  
**Evidence:** MODERATE (meta-analysis of 16 RCTs: no significant difference in body composition between ≤3 vs. ≥4 meals/day when protein equated). [PMC10647044](https://pmc.ncbi.nlm.nih.gov/articles/PMC10647044/)
```python
MEAL_FREQUENCY_DEFAULT = 3
MEAL_FREQUENCY_OPTIONAL = 4   # if user is very active or larger
SNACK_POLICY = "Protein-rich snacks acceptable; low-protein/high-calorie snacks discouraged"
```

#### RULE 06: Pre/Post Workout Nutrition
**Statement:** Protein-containing meal within 1–3h before training AND 1–2h after.  
**Evidence:** MODERATE-STRONG  
```
Pre-workout: protein ~0.25–0.4 g/kg + carbs, 1–4h before; avoid high fat/fiber directly pre-workout
Post-workout: 20–40g quality protein within 1–2h; carbs ~1 g/kg to refill glycogen
"Anabolic window" not as narrow as once believed; total daily protein matters most
```

#### RULE 07: Hydration
**Statement:** 3–4 liters total fluid/day on training days; urine color check.  
**Evidence:** MODERATE-STRONG
```
URINE_COLOR_GUIDE:
  Clear to pale yellow → Well hydrated
  Medium yellow → Drink more
  Dark yellow/amber → Dehydrated

DAILY_FLUID_TARGET: Training day ~3.5–4L; Rest day ~3L
Simple rule: 500mL with each meal + 500mL before + 500mL during/after training ≈ 3–3.5L/day
```

### 4.4 Progress Monitoring Without Calorie Data

```python
MONITORING_STREAMS = [
    "weight_trend",          # Primary: biweekly rolling average
    "body_composition",      # Secondary: Withings BF% trend
    "training_performance",  # Secondary: lifts progressing?
    "subjective_feedback"    # Tertiary: energy, hunger, visual
]
```

**Weight trend decision rules:**
```
GOAL: FAT_LOSS
  IF avg_weight_trend == DECREASING (>0.5 lb/week over 2 weeks): ON_TRACK
  IF avg_weight_trend == STABLE (±0.5 lb/week over 2 weeks): STALLED
    → Review Rules 01-03; add 1-2 vegetable servings; add protein serving
  IF avg_weight_trend == INCREASING (>1 lb/week): GAINING_FAT → escalation

GOAL: MUSCLE_GAIN / RECOMP
  IF weight STABLE (±1 lb) AND lifts progressing: RECOMPING → optimal, maintain
  IF weight INCREASING (+0.5–1 lb/week) AND lifts progressing: LEAN_GAIN
    → Monitor BF%; acceptable if BF% not rising
  IF weight INCREASING (>1.5 lb/week): EXCESSIVE_SURPLUS → moderate portions

Fat loss target rate: 0.5–1.0 lb/week (beginner); 0.25–0.75 lb/week (intermediate)
Muscle gain target: 0.25–0.5 lb/week (beginner); 0.1–0.25 lb/week (intermediate)
Recomp target: weight stable ±1 lb + performance improving
```

**Integrated Progress Assessment Matrix:**
```python
def compute_composite_score(user: UserALProfile, goal: str) -> int:
    score = 0
    if goal == "fat_loss":
        if user.weight_trend_2wk == "decreasing": score += 1
        elif user.weight_trend_2wk == "increasing": score -= 1
    elif goal == "muscle_gain":
        if user.weight_trend_2wk == "stable" and user.lift_performance_trend == "progressing":
            score += 2
    elif goal == "recomp":
        if user.weight_trend_2wk == "stable" and user.lift_performance_trend == "progressing":
            score += 2
    if user.fat_mass_trend == "decreasing": score += 1
    elif user.fat_mass_trend == "increasing": score -= 1
    if user.ffm_trend == "increasing": score += 1
    elif user.ffm_trend == "decreasing": score -= 1
    if user.lift_performance_trend == "progressing": score += 1
    elif user.lift_performance_trend == "declining": score -= 2
    if 3 <= user.avg_hunger_1_10 <= 5: score += 1
    elif user.avg_hunger_1_10 >= 7: score -= 1
    if user.avg_energy_1_10 >= 7: score += 1
    elif user.avg_energy_1_10 <= 4: score -= 1
    return score

# IF composite_score >= 3: "On track — maintain approach"
# IF composite_score 0–2: "Mixed signals — reinforce rules, check-in in 1 week"
# IF composite_score < 0: "Not working — escalation review required"
```

**Withings BIA protocol:**
```
WEIGH_IN_CONDITIONS: Morning only, post-void, pre-food, pre-workout, barefoot,
                      same hard floor, no weighing within 3h of exercise
EVALUATION_INTERVAL: Every 2 weeks minimum
METRIC_TO_TRACK: Fat mass trend (kg), NOT absolute BF%
Fat_mass_decreasing + FFM_stable_or_increasing = FAVORABLE
Fat_mass_stable + FFM_increasing = FAVORABLE
Fat_mass_increasing + FFM_stable = UNFAVORABLE
Both_declining = CONCERN (under-eating/muscle loss risk)
```

### 4.5 Escalation Logic: When to Suggest Switching to Tracked Mode

```
START: User has been in AL mode for ≥4 weeks

TRIGGER_1: Weight trend wrong direction
  - Weight moving wrong direction for ≥2 consecutive biweekly periods
  - Behavioral reinforcement of Rules 01–03 applied
  - Still not correcting after 4 weeks total
  → ESCALATION_FLAG = TRUE (weak)

TRIGGER_2: Training performance declining
  - Lifts declining for 3+ consecutive sessions
  - Sleep, stress, illness ruled out
  - Protein heuristic compliance confirmed
  → ESCALATION_FLAG = TRUE (moderate)

TRIGGER_3: Body composition unfavorable
  - Withings fat mass increasing + FFM declining + weight trending up
  → ESCALATION_FLAG = TRUE (strong)

TRIGGER_4: Composite score persistently negative
  - composite_score < 0 for 2+ consecutive biweekly reviews
  → ESCALATION_FLAG = TRUE (strong)

IF ESCALATION_FLAG count >= 2 (moderate+): SUGGEST_TRACKED_MODE = TRUE

def should_escalate_to_tracked_mode(user: UserALProfile) -> Tuple[bool, str]:
    triggers = []
    if len(user.escalation_triggers_active) >= 2:
        triggers.append("multiple_triggers")
    if user.weeks_in_al_mode >= 4:
        score = compute_composite_score(user, user.goal)
        if score < 0:
            triggers.append("persistent_negative_score")
    if user.lift_performance_trend == "declining" and user.weeks_in_al_mode >= 3:
        triggers.append("performance_declining")
    if user.fat_mass_trend == "increasing" and user.ffm_trend == "decreasing":
        triggers.append("body_comp_unfavorable")
    escalate = len(triggers) >= 2
    reason = "; ".join(triggers) if triggers else "none"
    return escalate, reason
```

**Escalation scenario logic:**
```
SCENARIO: Fat loss goal, no weight movement after 4 weeks

Step 1: Compliance audit — protein at every meal? 80/20 rule? Plate composition?
Step 2: If compliance confirmed → suggest tracking just protein for 7 days
  → If protein is below target: protein intervention first
  → If protein adequate: may have higher TDEE than estimated; escalate to full tracking
Step 3: If protein + food quality confirmed adequate AND still not losing:
  → ESCALATE TO TRACKED MODE
  → Set calorie target: TDEE - 300 to 500 kcal/day

SCENARIO: Muscle gain goal, weight slowly increasing, lifts progressing
  → STATUS = OPTIMAL for AL mode; NO ESCALATION NEEDED

SCENARIO: User explicitly requests tracked mode
  → IMMEDIATE ESCALATION; honor user autonomy
```

---

## PART 5: TRAINING VOLUME & PROGRESSION

*Source: Track 2 — Volume & Progression; Track 8 — Programming*

### 5.1 Volume Landmarks Framework

**Source:** Dr. Mike Israetel / Renaissance Periodization (RP Strength). [RP Strength Volume Landmarks (2017, updated 2025)](https://rpstrength.com/blogs/articles/training-volume-landmarks-muscle-growth)

A "hard set" assumes: load 30–85% 1RM, rep range 5–30, effort 0–4 RIR.

```
Variable | Definition
---------|------------
MV       | Maintenance Volume — weekly sets to PRESERVE current muscle.
         | ~6 sets/week for most muscles when training 2x/week.
         | Remarkably stable regardless of training age.
MEV      | Minimum Effective Volume — lowest weekly sets that produce measurable 
         | hypertrophic gains. Mesocycle starting point.
         | Increases with training age.
MAV      | Maximum Adaptive Volume — range between MEV and MRV where optimal gains
         | occur. Dynamic zone that progresses upward as mesocycle advances.
MRV      | Maximum Recoverable Volume — upper weekly set limit beyond which recovery
         | is impaired and gains stop. Briefly exceeding causes functional overreaching;
         | chronically exceeding causes accumulated fatigue and performance decline.

Key relationships:
MV < MEV < MAV_low < MAV_high < MRV
MV is stable across training age (~6 sets/wk for most muscles)
MEV increases with training age
MAV_high approaches MRV in advanced lifters (narrowing window)
```

### 5.2 Per-Muscle-Group Volume Landmarks Table (Intermediate Male Reference)

All values represent **weekly direct sets** for an **intermediate male lifter** (1–5 years consistent training).

**Source:** Israetel / RP Strength per-muscle guides (2018–2024); [RP Volume Guide PDF](https://www.scribd.com/document/489839887/RP-Volume-Guide)

```python
VOLUME_LANDMARKS = {
    "chest":       {"MV": 4,  "MEV": 8,  "MAV": (8, 18),  "MRV": 22},
    "back":        {"MV": 6,  "MEV": 10, "MAV": (12, 20), "MRV": 25},
    "quads":       {"MV": 6,  "MEV": 8,  "MAV": (10, 18), "MRV": 22},
    "hamstrings":  {"MV": 4,  "MEV": 4,  "MAV": (8, 14),  "MRV": 18},
    "glutes":      {"MV": 2,  "MEV": 4,  "MAV": (8, 16),  "MRV": 20},
    "side_delts":  {"MV": 6,  "MEV": 8,  "MAV": (10, 22), "MRV": 26},
    "rear_delts":  {"MV": 0,  "MEV": 6,  "MAV": (8, 16),  "MRV": 26},
    "front_delts": {"MV": 0,  "MEV": 0,  "MAV": (0, 8),   "MRV": 16},
    "biceps":      {"MV": 4,  "MEV": 8,  "MAV": (10, 18), "MRV": 26},
    "triceps":     {"MV": 4,  "MEV": 6,  "MAV": (8, 16),  "MRV": 20},
    "calves":      {"MV": 0,  "MEV": 6,  "MAV": (10, 16), "MRV": 20},
    "abs":         {"MV": 0,  "MEV": 4,  "MAV": (8, 20),  "MRV": 25},
    "traps":       {"MV": 0,  "MEV": 4,  "MAV": (8, 20),  "MRV": 25},
}
```

**Track 8 version (includes additional breakdown):**
```
Muscle Group    | MV  | MEV    | MAV Range | MRV    | Default Freq
----------------|-----|--------|-----------|--------|-------------
Chest           | 6   | 10–12  | 14–20     | 20–26  | 2x
Back (lats)     | 6   | 10–12  | 14–22     | 20–35  | 2–4x
Back (traps)    | 0   | 0–6    | 12–20     | 26+    | 2–3x
Front Deltoid   | 0   | 0      | 6–8       | 12     | 2x
Lateral Deltoid | 6   | 6–8    | 16–22     | 26     | 2–3x
Rear Deltoid    | 0   | 6      | 16–22     | 26     | 2–3x
Biceps          | 4   | 8–10   | 14–20     | 18–26  | 2–4x
Triceps         | 4   | 8–10   | 10–14     | 18–26  | 2–4x
Quads           | 6   | 8–10   | 14–20     | 20–28  | 2x
Hamstrings      | 4   | 6–8    | 12–18     | 18–24  | 2x
Glutes          | 0   | 0      | 12–20     | 16+    | 2–3x
Calves          | 6   | 8–10   | 12–16     | 18–24  | 2–4x
Abs/Core        | 0   | 0      | 8–20      | 25     | 3x
```

**Compound set-counting (RP methodology):**
- Bench press = 1 direct chest set, ~0.5 triceps set, ~0.25 front delt set
- Pulldown/row = 1 direct back set, ~0.5 biceps set, ~0.25 rear delt set
- Do NOT double-count: a barbell row counted as 1 back set should NOT also be a full biceps set

### 5.3 Beginner vs. Intermediate Adjustments

```python
BEGINNER_MULTIPLIERS = {"MEV": 0.60, "MAV_high": 0.70, "MRV": 0.65}

def get_volume_landmark(muscle_group: str, status: TrainingStatus, landmark: str):
    base = VOLUME_LANDMARKS[muscle_group][landmark]
    if status == BEGINNER:
        if landmark == "MEV": return max(2, int(base * 0.6))
        if landmark == "MAV": return (int(base[0] * 0.6), int(base[1] * 0.75))
        if landmark == "MRV": return int(base * 0.65)
    elif status == INTERMEDIATE:
        return base  # use table values directly
    elif status == ADVANCED:
        if landmark == "MEV": return int(base * 1.1)
        if landmark == "MAV": return (int(base[0] * 1.0), int(base[1] * 1.15))
        if landmark == "MRV": return int(base * 1.1)
```

```
Beginner (<12 months):   MEV = table × 0.5–0.7; MAV = table × 0.6–0.8; MRV = table × 0.5–0.75
  "Growth occurs at 2–6 sets/muscle/week. Emphasize technique."
Intermediate (1–5 yrs):  Use table values directly.
Advanced (5+ yrs):       MEV = table × 1.0–1.2; MAV–MEV window narrows; may require specialization.
```

### 5.4 Volume-Response Relationship

**Source:** Schoenfeld BJ & Krieger J (2017). *Journal of Sports Sciences*, 35(11), 1073–1082. [PubMed 27433992](https://pubmed.ncbi.nlm.nih.gov/27433992/) (N=34 treatment groups, 15 studies, 363 subjects)

```
Volume Category    | ES    | % Hypertrophy Gain
-------------------|-------|-------------------
< 5 sets/week      | 0.307 | 5.4%
5–9 sets/week      | 0.397 | 6.6%
10+ sets/week      | 0.544 | 9.8%
Continuous model   | +0.023 ES per additional set (P=0.002)
Higher vs. Lower   | ES diff = 0.241 (3.9% greater gain; P=0.03)
```

**Diminishing returns pattern:**
```
1–5 sets/week:    Rapid gains; large marginal return per set
5–12 sets/week:   Strong gains; dose-response clearly present
12–20 sets/week:  Good gains; diminishing returns begin
20–30 sets/week:  Some benefit; recovery demands rise steeply
30–40 sets/week:  Further benefit possible but systemically constrained
40+ sets/week:    Likely impractical

Per-session ceiling: ~6–8 hard sets per muscle per session
Above ~11 sets/muscle/session: unclear additional benefit (Dr. Milo Wolf, 2026)

Working range: 10–20 sets/muscle/week for most trained individuals
```

### 5.5 Volume Distribution / Emphasis Model

**Priority Tier System:**
```
Tier       | Volume Level | Description
-----------|--------------|--------------------------------------------
PRIMARY    | MAV range    | Emphasis muscles. Target: (MEV + MRV) / 2 to MRV - 3
SECONDARY  | MEV to MAV   | Maintained but not emphasized. Target: MEV to (MEV + MRV) / 2
TERTIARY   | MV to MEV    | Maintenance-only. Target: MV to MEV
```

```python
user_goal_emphasis: enum = {
    BALANCED,        # Equal distribution
    UPPER_BODY,      # Upper > Lower
    LOWER_BODY,      # Lower > Upper
    ARMS,            # Biceps/Triceps/Shoulders
    CHEST_AND_BACK,  # V-taper focus
    GLUTES_AND_LEGS, # Lower body aesthetic
    CUSTOM           # Per-muscle priority by user
}

def assign_tier(muscle: str, user_emphasis: GoalEmphasis, custom_priorities: dict) -> Tier:
    if user_emphasis == CUSTOM:
        return custom_priorities[muscle]
    elif user_emphasis == UPPER_BODY:
        upper = ["chest", "back", "side_delts", "rear_delts", "biceps", "triceps", "traps"]
        lower = ["quads", "hamstrings", "glutes", "calves"]
        if muscle in upper: return PRIMARY
        if muscle in lower: return TERTIARY
        return SECONDARY
    elif user_emphasis == LOWER_BODY:
        if muscle in ["quads", "hamstrings", "glutes", "calves"]: return PRIMARY
        if muscle in ["chest", "back"]: return SECONDARY
        return TERTIARY
    elif user_emphasis == BALANCED:
        return SECONDARY

def calculate_target_sets(muscle: str, status: TrainingStatus, tier: Tier) -> int:
    landmarks = get_volume_landmark(muscle, status)
    mev = landmarks["MEV"]
    mav_high = landmarks["MAV"][1]
    mrv = landmarks["MRV"]
    mv = landmarks["MV"]
    if tier == PRIMARY:    return int((mav_high + mrv) / 2)
    elif tier == SECONDARY: return int((mev + mav_high) / 2)
    elif tier == TERTIARY:  return max(mv, mev - 2)
```

**Total weekly volume caps:**
```python
TOTAL_WEEKLY_SETS_LIMIT = {BEGINNER: 80, INTERMEDIATE: 120, ADVANCED: 160}

if sum(target_sets.values()) > TOTAL_WEEKLY_SETS_LIMIT[status]:
    reduce_tertiary_sets_first()   # drop TERTIARY to MV floor
    reduce_secondary_sets_second() # reduce SECONDARY toward MEV
```

### 5.6 Progression Models

| Model | Best For | Mechanism | Complexity |
|---|---|---|---|
| Linear Progression (LP) | True beginners (0–6 months) | Add load every session | Low |
| Double Progression | Beginners → Intermediates | Add reps → then add load | Low-Med |
| Daily Undulating Periodization (DUP) | Intermediates | Vary rep range across days/weeks | Medium |
| Block/Mesocycle Periodization | Intermediates | Volume ramps across blocks; deload | Medium-High |

**Selection logic:**
```python
def select_progression_model(status: TrainingStatus, goal: Goal) -> ProgressionModel:
    if status == BEGINNER:
        return LinearProgression
    elif status == INTERMEDIATE:
        if goal == PRIMARILY_HYPERTROPHY:
            return DoubleProgression  # default for intermediates
        elif goal == HYPERTROPHY_AND_STRENGTH:
            return BlockPeriodization
    elif status == ADVANCED:
        return BlockPeriodization

# Override: if user has <12 consistent training months, always start LP first.
# Switch to double progression when: LP stalls for 2+ consecutive sessions
# OR user hits 6 months consistent training.
```

#### 5.6.1 Linear Progression (LP)

```python
lp_params = {
    "rep_target": int,           # e.g., 8 reps
    "sets": int,                 # e.g., 3
    "load_increment_barbell": float,  # e.g., 5.0 lbs/session
    "load_increment_dumbbell": float, # e.g., 5.0 lbs per 2-3 sessions
    "stall_threshold": int,      # sessions without progress, e.g., 2
}

def lp_next_session(exercise, current_load, current_reps, target_reps, status):
    if current_reps >= target_reps:
        return (current_load + lp_params["load_increment"], target_reps)
    else:
        return (current_load, current_reps)

if sessions_stalled >= lp_params["stall_threshold"]:
    switch_to_double_progression()
```

#### 5.6.2 Double Progression (Primary Intermediate Model)

**Source:** Helms & Wolf — "How to Train for Maximum Muscle Growth" (YouTube, 2024); [Ripped Body (2025)](https://rippedbody.com/progression/)

```python
DOUBLE_PROGRESSION_DEFAULTS = {
    "rep_range_low": 8,
    "rep_range_high": 12,
    "rir_start": 3,
    "rir_end_meso": 1,
    "load_increase_barbell_lbs": 5.0,
    "load_increase_dumbbell_lbs": 5.0,
    "load_increase_pct": 0.025   # 2.5%
}

def double_progression_next(exercise, sessions: list[Session]) -> (float, int):
    current = sessions[-1]
    all_sets_hit_top = all(s.reps >= double_prog_params["rep_range_high"] for s in current.sets)
    rir_acceptable = all(
        abs(s.rir - double_prog_params["rir_target"]) <= double_prog_params["rir_tolerance"]
        for s in current.sets
    )
    if all_sets_hit_top and rir_acceptable:
        # LOAD PROGRESSION
        load_increase = min(current.load * double_prog_params["load_increase_pct"],
                            double_prog_params["load_increase_abs"])
        return (current.load + load_increase, double_prog_params["rep_range_low"])
    else:
        # REP PROGRESSION
        return (current.load, min(current.reps + 1, double_prog_params["rep_range_high"]))
```

**Load increase rules:**
```
Barbell compound (squat, deadlift, row): +5 lbs per increment
Barbell isolation (curl, extension): +2.5 lbs per increment
Dumbbell (all): +5 lbs per dumbbell per increment
Machine: smallest available increment (1 plate = typically 5–10 lbs)

Progression cadence:
Beginners: every 1–2 sessions (weekly)
Intermediates: 3–6 sessions (2–4 weeks) to hit all reps at target RIR
Advanced: 5–10+ sessions (4–8+ weeks)
```

### 5.7 Mesocycle Structure

```
Variable          | Definition
------------------|-----------------------------------------------
mesocycle_length  | Weeks of accumulation + 1 deload week. Typical: 4–6 weeks total
accumulation_weeks| Weeks of progressive training within the mesocycle
deload_week       | 1 week at MV-level volume; always included at end
microcycle        | 1 week of training
macrocycle        | 3–4 mesocycles; ~12–20 weeks; one training phase
```

**Recommended mesocycle length:**
```
Training Status | Accumulation Weeks | Deload | Total Mesocycle
----------------|-------------------|--------|------------------
Beginner        | 8–12 weeks        | 1 week | 9–13 weeks
Intermediate    | 3–5 weeks         | 1 week | 4–6 weeks (4+1 most common)
Advanced        | 2–4 weeks         | 1 week | 3–5 weeks
```

```python
MESOCYCLE_DEFAULTS = {
    BEGINNER:     {"accumulation_weeks": 8, "deload_weeks": 1, "sets_per_week_increase": 1.5},
    INTERMEDIATE: {"accumulation_weeks": 4, "deload_weeks": 1, "sets_per_week_increase": 2.0},
    ADVANCED:     {"accumulation_weeks": 3, "deload_weeks": 1, "sets_per_week_increase": 1.0},
}

def get_mesocycle_length(status: TrainingStatus, fatigue_level: int) -> int:
    """fatigue_level: 1–5 (1=fresh, 5=crushed)"""
    base = {BEGINNER: 10, INTERMEDIATE: 4, ADVANCED: 3}[status]
    if fatigue_level >= 4: return max(2, base - 2)  # shorten
    elif fatigue_level <= 2: return min(base + 1, 6)  # extend
    else: return base
```

### 5.8 Volume Ramp Across the Mesocycle (MEV → MRV)

**Example: 5-week mesocycle, intermediate, chest (MEV=8, MRV=20):**
```
Week | Sets/week | Target RIR | Phase
-----|-----------|------------|----------------------
1    | 8         | 3–4 RIR    | MEV start; resensitization
2    | 10        | 2–3 RIR    | Early MAV; adding volume
3    | 14        | 2 RIR      | Mid MAV; productive zone
4    | 18        | 1 RIR      | Approaching MRV; max stimulus
5    | 4–6       | 4–5 RIR    | DELOAD (MV level, ~50% reduction)
```

**RIR by week (standard 4-week meso):**
```python
RIR_BY_WEEK = {1: 3, 2: 2, 3: 2, 4: 1}  # standard 4-week
# For longer mesos: {1: 4, 2: 3, 3: 3, 4: 2, 5: 1}
```

**Rate of volume increase per week:**
```
Standard rate: +1 to +2 sets per muscle group per week

Formula: sets_increase_per_week = (MRV - MEV) / accumulation_weeks
Example (chest, intermediate): (20 - 8) / 4 weeks = 3 sets/week increase
Example (chest, beginner): (14 - 5) / 6 weeks ≈ 1.5 sets/week increase
Round to nearest whole set; tolerance ±1 set per week
```

**Autoregulated set addition algorithm:**
```python
def should_add_set_next_week(muscle: str, recovery_score: int, 
                              pump_score: int, performance_trend: str) -> bool:
    """
    recovery_score: 1–4 (1=no soreness, 4=still sore/impaired)
    pump_score:     1–4 (1=no pump, 4=excellent pump)
    performance_trend: 'improved' | 'maintained' | 'declined'
    """
    score = 0
    if recovery_score == 1: score += 1
    elif recovery_score == 3: score -= 1
    elif recovery_score == 4: return False  # do not add
    if pump_score >= 3: score += 1
    elif pump_score <= 1: score -= 1
    if performance_trend == 'improved': score += 1
    elif performance_trend == 'declined': return False  # may be at MRV
    if score >= 2: return True
    elif score <= 0: return False
    else: return False  # borderline

def calculate_set_increment(score: int) -> int:
    if score >= 2: return 2
    elif score == 1: return 1
    elif score == 0: return 0
    else: return -1
```

### 5.9 Cross-Mesocycle Progression

**Each successive mesocycle starts slightly higher MEV than the previous:**
```
Meso 1 Week 1: 3 sets, 185 lb, 3 RIR → Meso 1 Week 4: 5 sets, 200 lb, 0 RIR
Meso 2 Week 1: 4 sets, 200 lb, 3 RIR → Meso 2 Week 4: 6 sets, 215 lb, 0 RIR
Meso 3 Week 1: 5 sets, 215 lb, 3 RIR → Meso 3 Week 4: 7 sets, 230 lb, 0 RIR
```

```python
def calculate_next_meso_starting_volume(muscle: str, prev_meso_avg_volume: int,
                                         prev_meso_performance_change: float) -> int:
    """prev_meso_performance_change: % change in strength on benchmark lift"""
    if prev_meso_performance_change > 0.02:    # > 2% strength gain
        return prev_meso_avg_volume + 1        # increase MEV starting point
    elif prev_meso_performance_change <= 0:    # performance decline
        return max(MEV_floor[muscle], prev_meso_avg_volume - 2)
    else:
        return prev_meso_avg_volume

# Exercise rotation rule (between mesocycles):
# Keep 1 core compound; rotate 1–2 accessory movements
# Re-sensitizes muscle to stimulus; trains different strength curve portions
```

**Deload parameters:**
```python
DELOAD_PARAMS = {
    "duration_weeks": 1,
    "volume_pct_of_peak": 0.40,    # ~40–50% of final accumulation week volume
    "load_pct_of_working": 0.90,   # keep weights at 90%
    "rir_floor": 5,                 # very easy effort
}
```

---

## PART 6: TRAINING PROGRAMMING

*Source: Track 8 — Full-Body Programming Design*

### 6.1 Training Frequency Evidence

**Core finding (Schoenfeld et al. 2016):** Training ≥2x/week is superior to 1x/week for hypertrophy (ES = 0.49 vs. 0.30, p=0.002; 6.8% vs. 3.7% mean percent change). [PubMed 27102172](https://pubmed.ncbi.nlm.nih.gov/27102172/)

**2x vs. 3x/week:** When volume is equated, no significant difference in hypertrophy (Schoenfeld 2018 meta, 25 studies; Colquhoun et al. 2019 [PMC6724585](https://pmc.ncbi.nlm.nih.gov/articles/PMC6724585/)). Frequency is primarily a tool to manage per-session volume load.

**Israetel frequency growth factors (qualitative):**
```
1x/week = growth factor ~1.0
2x/week = ~1.5x growth factor
3x/week = ~1.75x growth factor
Beyond 3x/week = diminishing returns
```

```python
MINIMUM_FREQUENCY_PER_MUSCLE_PER_WEEK = 2  # default based on Schoenfeld 2016

def get_target_muscle_frequency(training_days, muscle_priority):
    if training_days <= 2:
        return 1  # compensate with higher per-session volume
    elif training_days in [3, 4]:
        return 2  # standard 2x/week
    elif training_days >= 5:
        return 3 if muscle_priority == "HIGH" else 2
```

**Frequency distribution by training days:**
| Training Days/Week | Muscle Frequency/Week | Schedule Pattern |
|---|---|---|
| 2 | 2x all major muscles | Any 2 non-consecutive days |
| 3 | 2x (A-B-A / B-A-B rotation) | Mon-Wed-Fri |
| 4 | 2–3x depending on rotation | Mon-Tue-Thu-Fri |
| 5 | 2–3x depending on priority | Mon-Tue-Wed-Fri-Sat |
| 6 | 2–3x most; 3x priority | Mon-Tue-Wed-Thu-Fri-Sat |

**Rule:** Minimum 48h recovery between sessions targeting the same muscle group.

### 6.2 Full-Body Programming Advantages

**Evidence:** Ramos-Campo et al. (2021) [PMC8372753](https://pmc.ncbi.nlm.nih.gov/articles/PMC8372753/) — 67 untrained subjects, split vs. full-body (volume equated): similar bench press 1RM (+18.1% vs. +17.5%), squat 1RM (+28.2% vs. +28.6%), and muscle thickness.

**Advantages for beginners/intermediates:**
1. Scheduling resilience — missing one session doesn't create muscle group gaps
2. Frequency efficiency — 2x/week per muscle in as few as 2 sessions
3. Neural reinforcement — more frequent movement pattern practice for technique
4. Lower per-session fatigue accumulation
5. Balanced development

**Split transition logic:**
```python
def recommend_split_transition(training_age_months, weekly_sets_per_muscle, training_days):
    if (training_age_months > 18 and 
        max(weekly_sets_per_muscle.values()) > 20 and 
        training_days >= 4):
        return True  # upper/lower split recommended
    return False
```

**Split transition thresholds:**
| Indicator | Threshold |
|---|---|
| Training age | > 18–24 months consistent training |
| Weekly volume need | Any major muscle > 20 sets/week |
| Session duration | > 90 min at 3x/week to meet volume |
| Per-session fatigue | Systemic fatigue persisting > 48h |
| Training days | ≥5 days with high volume needs |
| Plateau with full-body | No progress after 2+ mesocycles at MRV |

### 6.3 Exercise Selection Framework and Taxonomy

```python
EXERCISE_TAXONOMY = {
    "PRIMARY_COMPOUNDS": {
        "squat_variations": ["back_squat", "front_squat", "goblet_squat", "hack_squat",
                              "box_squat", "safety_bar_squat"],
        "hinge_variations": ["conventional_deadlift", "romanian_deadlift", "sumo_deadlift",
                              "trap_bar_deadlift", "good_morning"],
        "horizontal_press": ["barbell_bench_press", "dumbbell_bench_press", "incline_barbell_press",
                              "incline_dumbbell_press", "decline_bench_press"],
        "vertical_press": ["barbell_overhead_press", "dumbbell_overhead_press",
                            "seated_db_shoulder_press", "arnold_press"],
        "horizontal_pull": ["barbell_bent_over_row", "dumbbell_bent_over_row", "cable_row",
                             "chest_supported_row", "pendlay_row", "t_bar_row"],
        "vertical_pull": ["pull_up", "chin_up", "lat_pulldown", "neutral_grip_pulldown",
                           "assisted_pull_up"]
    },
    "SECONDARY_COMPOUNDS": {
        "lower_body": ["lunge_dumbbell", "lunge_barbell", "bulgarian_split_squat",
                        "leg_press", "step_up", "hip_thrust"],
        "upper_body_push": ["dips", "push_up_weighted", "cable_chest_press", "landmine_press"],
        "upper_body_pull": ["single_arm_dumbbell_row", "cable_face_pull", "seal_row",
                             "inverted_row", "neutral_grip_chin_up"]
    },
    "ISOLATION_EXERCISES": {
        "biceps": ["dumbbell_curl", "barbell_curl", "hammer_curl", "preacher_curl",
                   "incline_curl", "cable_curl"],
        "triceps": ["tricep_pushdown_cable", "overhead_tricep_extension", "skull_crusher",
                    "close_grip_bench_press", "dumbbell_kickback"],
        "lateral_deltoid": ["dumbbell_lateral_raise", "cable_lateral_raise", "machine_lateral_raise"],
        "rear_deltoid": ["dumbbell_reverse_fly", "cable_face_pull", "machine_rear_delt_fly",
                          "band_pull_apart"],
        "quadriceps": ["leg_extension_machine", "sissy_squat"],
        "hamstrings": ["leg_curl_lying", "leg_curl_seated", "nordic_hamstring_curl"],
        "glutes": ["hip_thrust_barbell", "cable_kickback", "glute_bridge"],
        "calves": ["calf_raise_standing", "calf_raise_seated", "leg_press_calf_raise"],
        "abs_core": ["crunch", "cable_crunch", "leg_raise", "plank", "ab_wheel_rollout",
                     "hanging_knee_raise"]
    }
}
```

**Muscles requiring direct isolation (not adequately trained by compounds):**
| Muscle | Why Needed | Required Isolation |
|---|---|---|
| Lateral deltoid | No compound involves shoulder abduction | Lateral raises |
| Biceps (full) | Rows/pulldowns insufficient for full development | Curls |
| Triceps long head | Presses don't train shoulder-extended position | Overhead extensions |
| Rear deltoid | Rows involve but don't fully isolate | Reverse flyes, face pulls |
| Hamstrings (knee flexion) | Hinges train hip extension only | Leg curls |
| Calves | Rarely adequately loaded in compounds | Calf raises |

**Exercise rotation rules:**
```python
EXERCISE_ROTATION_RULES = {
    "WITHIN_SESSION": "Do not repeat identical exercises within the same session",
    "SESSION_TO_SESSION": "Rotate at least one primary compound variation per muscle between A and B",
    "MESOCYCLE": "Change primary exercise variations every 4–6 weeks (mesocycle boundary)",
    "MINIMUM_VARIETY": "Minimum 2 different exercise stimuli per muscle per week",
    "ISOLATION_VARIATION": "Allow same isolation exercise to repeat across sessions (progressive overload)",
    "SPECIFICITY_CONSTRAINT": "Avoid weekly exercise changes — progressive overload tracking requires consistency"
}

# Session A: Back Squat | Session B: Romanian Deadlift
# Session A: Barbell Row | Session B: Lat Pulldown
# Session A: Barbell Bench | Session B: Incline DB Press
```

**Compound-first exercise ordering:**
```
EXERCISE_ORDER_PRIORITY = [
    1: "Primary compound — lower body (squat or hinge)",
    2: "Primary compound — upper body pull (row or vertical pull)",
    3: "Primary compound — upper body push (horizontal or vertical press)",
    4: "Secondary compound (lunge, dip, chin-up, secondary row)",
    5: "Isolation — large muscles (leg curls, lateral raises, rear delts)",
    6: "Isolation — small muscles (curls, tricep extensions, calf raises)",
    7: "Core (abs/obliques)"
]
```

```python
def check_compound_adjacency(exercise_queue):
    """Flag consecutive CNS-heavy exercises."""
    HIGH_CNS = ["back_squat", "deadlift", "rdl_barbell", "ohp_barbell"]
    for i in range(len(exercise_queue) - 1):
        if (exercise_queue[i] in HIGH_CNS and exercise_queue[i+1] in HIGH_CNS):
            return "WARNING: Consecutive CNS-heavy compounds. Reorder or separate."
    return "OK"
```

### 6.4 Customizable Volume Distribution Model

**Emphasis Modes:**
```python
class EmphasisMode(Enum):
    BALANCED = "balanced"
    UPPER_EMPHASIS = "upper_emphasis"
    LOWER_EMPHASIS = "lower_emphasis"
    ARMS_EMPHASIS = "arms_emphasis"
    CUSTOM = "custom"
```

**Volume Multiplier Matrix:**
| Muscle Group | Balanced | Upper Emphasis | Lower Emphasis | Arms Emphasis |
|---|---|---|---|---|
| Chest | 1.0 | 1.3 | 0.7 | 1.0 |
| Back (lats) | 1.0 | 1.3 | 0.7 | 1.0 |
| Lateral Delts | 1.0 | 1.2 | 0.7 | 1.0 |
| Rear Delts | 1.0 | 1.2 | 0.7 | 1.0 |
| Biceps | 1.0 | 1.0 | 0.7 | 1.5 |
| Triceps | 1.0 | 1.0 | 0.7 | 1.5 |
| Quads | 1.0 | 0.7 | 1.3 | 0.7 |
| Hamstrings | 1.0 | 0.7 | 1.3 | 0.7 |
| Glutes | 1.0 | 0.7 | 1.3 | 0.7 |
| Calves | 1.0 | 0.7 | 1.1 | 0.7 |

```python
BASELINE_MAV_MID = {
    "chest": 12, "back_lats": 14, "back_traps": 8, "front_delts": 4,
    "lateral_delts": 12, "rear_delts": 10, "biceps": 10, "triceps": 10,
    "quads": 12, "hamstrings": 10, "glutes": 8, "calves": 10, "abs": 8
}

def compute_target_weekly_sets(muscle, emphasis_mode, user_training_age="beginner"):
    baseline = BASELINE_MAV_MID[muscle]
    multiplier = VOLUME_MULTIPLIER_TABLE[emphasis_mode][muscle]
    raw_target = round(baseline * multiplier)
    clamped = max(MEV[muscle], min(raw_target, MRV[muscle]))  # always clamp to [MEV, MRV]
    return clamped

SYSTEMIC_FATIGUE_CAP = {
    "beginner_2day": 50,    "beginner_3day": 60,
    "intermediate_3day": 80, "intermediate_4day": 100,
    "intermediate_5day": 115, "intermediate_6day": 130
}
```

### 6.5 Weekly Template Generation Algorithm

**Inputs:**
```python
class WeeklyPlanInputs:
    training_days_per_week: int           # 2–6
    training_day_indices: List[int]       # e.g., [0,2,4] for Mon/Wed/Fri
    emphasis_mode: EmphasisMode
    priority_muscles: List[str]           # up to 2 (for CUSTOM mode)
    volume_targets: Dict[str, int]        # weekly sets per muscle
    experience_level: str                 # "beginner" | "intermediate"
    session_duration_limit: int           # minutes; default 60
    rir_target: int                       # current mesocycle RIR target (1–4)
```

**Algorithm pseudocode:**
```python
def generate_weekly_plan(inputs: WeeklyPlanInputs) -> WeeklyPlan:
    # Step 1: Compute volume targets per muscle
    volume_targets = {m: compute_target_weekly_sets(m, inputs.emphasis_mode) for m in ALL_MUSCLES}
    
    # Step 2: Determine session count and labels
    n = inputs.training_days_per_week
    session_labels = assign_session_labels(n)  # ["A","B"] for 2-day; ["A","B","A"] for 3-day
    
    # Step 3: Distribute volume across sessions
    session_targets = distribute_volume_to_sessions(volume_targets, n, inputs.emphasis_mode)
    
    # Step 4: Select exercises for each session
    for session_idx, session_label in enumerate(session_labels):
        exercises = select_exercises_for_session(
            session_label=session_label, session_targets=session_targets[session_idx],
            available_exercises=EXERCISE_TAXONOMY, rotation_rules=EXERCISE_ROTATION_RULES,
            priority_muscles=inputs.priority_muscles
        )
        exercises = sort_by_session_order_priority(exercises)
        
        # Step 5: Assign sets, reps, RIR, rest
        for exercise in exercises:
            exercise.sets = calculate_sets(exercise.target_muscle, session_targets, n)
            exercise.rep_range = get_rep_range(exercise.category, inputs.emphasis_mode)
            exercise.rir = inputs.rir_target
            exercise.rest_seconds = get_rest_period(exercise.category)
        
        # Step 6: Enforce duration limit
        estimated_duration = estimate_session_duration(exercises)
        if estimated_duration > inputs.session_duration_limit:
            exercises = trim_exercises(exercises, inputs.session_duration_limit)
    
    return WeeklyPlan(sessions=sessions, weekly_sets_achieved=tally_sets(sessions))
```

**Per-session volume caps:**
```python
SESSION_VOLUME_CAP = {2: 24, 3: 18, 4: 15, 5: 12, 6: 10}  # total working sets/session
```

**Sets per session calculation:**
```python
def calculate_sets_per_session(weekly_sets_target, training_days, muscle):
    base = weekly_sets_target / training_days
    if base < 2.0:
        sessions_needed = max(1, round(weekly_sets_target / 2))
        sets_per_active_session = round(weekly_sets_target / sessions_needed)
        return sets_per_active_session, sessions_needed
    return round(base), training_days
```

**Rules:** No single session should carry >40% of weekly volume for any muscle (exception: 2-day programs where 50% per session is expected).

**Consecutive day rules:**
```
"back_squat + conventional_deadlift": "Never on consecutive days"
"heavy_compound_lower + heavy_compound_lower": "Require ≥48h gap"
"5-6_day_programs": "Day 5/6 = reduced intensity (RIR +1 to +2 vs. days 1-4)"
```

### 6.6 Rep Range and RIR Assignment

```python
REP_RANGE_BY_CATEGORY = {
    "primary_compound": "5–8",
    "secondary_compound": "8–12",
    "isolation_large": "10–15",
    "isolation_small": "12–20"
}

RIR_SCALE = {
    "week_1_mesocycle": 4,
    "week_2_mesocycle": 3,
    "week_3_mesocycle": 2,
    "week_4_mesocycle": 1,
    "deload_week": 5
}
```

### 6.7 Rest Period Recommendations

**Evidence:** Schoenfeld et al. (2016) — 3-min rest > 1-min rest: greater quad thickness (+13.3%) and strength. [Brookbush Institute](https://brookbushinstitute.com/articles/longer-interset-rest-periods-enhance-muscle-strength-hypertrophy-resistance-trained-men)

```python
REST_PERIODS = {
    "primary_compound": 150,       # 2.5 minutes (90–180s range)
    "secondary_compound": 90,      # 90 seconds
    "isolation_large_muscle": 75,  # 60–90 seconds
    "isolation_small_muscle": 60   # 60 seconds
}

def estimate_session_duration(exercises):
    """Total time = sum(sets × (avg_set_time + rest_period)) + warm_up_time"""
    total_seconds = 600  # 10 min warm-up
    for ex in exercises:
        set_time = 45  # seconds per set
        rest = REST_PERIODS[ex.category]
        total_seconds += ex.sets * (set_time + rest)
    return total_seconds / 60  # return minutes
```

### 6.8 Session Templates

#### Warm-Up Protocol (ALL sessions)

**Phase 1: General (5 min)** — Light cardio (bike/row/treadmill) OR dynamic mobility (leg swings, arm circles, hip rotations)

**Phase 2: Specific build-up sets for first compound:**
```
Set 1: 40–50% working weight × 6–8 reps
Set 2: 60–70% working weight × 4–6 reps
Set 3: 80–90% working weight × 1–3 reps

Example (200 lb squat): 95 lb × 8, 135 lb × 5, 175 lb × 2 → working sets begin
```
**RULE:** Warm-up sets are NOT counted toward working set totals.

#### 3-Day Full-Body Program (A–B–A rotation)

**Session A:**
| Order | Exercise | Category | Sets | Reps | RIR | Rest |
|---|---|---|---|---|---|---|
| 1 | Back Squat | Primary compound — squat | 3 | 5–8 | 2 | 150s |
| 2 | Barbell Bent-Over Row | Primary compound — horiz. pull | 3 | 6–10 | 2 | 150s |
| 3 | Barbell Bench Press | Primary compound — horiz. press | 3 | 6–10 | 2 | 150s |
| 4 | Romanian Deadlift | Secondary compound — hinge | 3 | 8–12 | 2 | 120s |
| 5 | Dumbbell Lateral Raise | Isolation — lateral delt | 3 | 12–15 | 2 | 60s |
| 6 | Dumbbell Curl | Isolation — biceps | 2 | 10–15 | 2 | 60s |
| 7 | Tricep Pushdown | Isolation — triceps | 2 | 10–15 | 2 | 60s |
**Duration: ~65–70 min**

**Session B:**
| Order | Exercise | Category | Sets | Reps | RIR | Rest |
|---|---|---|---|---|---|---|
| 1 | Romanian Deadlift (heavy) | Primary compound — hinge | 3 | 5–8 | 2 | 150s |
| 2 | Lat Pulldown | Primary compound — vert. pull | 3 | 8–12 | 2 | 120s |
| 3 | Incline Dumbbell Press | Primary compound — horiz. press | 3 | 8–12 | 2 | 120s |
| 4 | Bulgarian Split Squat | Secondary compound — lower | 3 | 8–12 ea | 2 | 120s |
| 5 | Cable Row | Secondary compound — horiz. pull | 3 | 10–12 | 2 | 90s |
| 6 | Rear Delt Fly | Isolation — rear delt | 2 | 15–20 | 2 | 60s |
| 7 | Lying Leg Curl | Isolation — hamstrings | 2 | 12–15 | 2 | 60s |
**Duration: ~65–70 min**

#### 4-Day Full-Body Program (A–B–A–B, Mon–Tue–Thu–Fri)

**Session A (Mon/Thu):**
| Order | Exercise | Category | Sets | Reps | RIR | Rest |
|---|---|---|---|---|---|---|
| 1 | Back Squat | Primary compound | 3 | 5–8 | 2 | 150s |
| 2 | Barbell Row | Primary compound — horiz. pull | 3 | 6–10 | 2 | 150s |
| 3 | Overhead Dumbbell Press | Primary compound — vert. press | 3 | 8–12 | 2 | 120s |
| 4 | Dumbbell Lateral Raise | Isolation — lateral delt | 3 | 12–15 | 2 | 60s |
| 5 | Tricep Overhead Extension | Isolation — triceps | 2 | 12–15 | 2 | 60s |
**Duration: ~50–55 min**

**Session B (Tue/Fri):**
| Order | Exercise | Category | Sets | Reps | RIR | Rest |
|---|---|---|---|---|---|---|
| 1 | Romanian Deadlift | Primary compound — hinge | 3 | 6–10 | 2 | 150s |
| 2 | Incline Dumbbell Bench | Primary compound — horiz. press | 3 | 8–12 | 2 | 120s |
| 3 | Neutral-Grip Lat Pulldown | Primary compound — vert. pull | 3 | 8–12 | 2 | 120s |
| 4 | Bulgarian Split Squat | Secondary compound — lower | 3 | 8–12 ea | 2 | 90s |
| 5 | Dumbbell Curl | Isolation — biceps | 2 | 10–15 | 2 | 60s |
| 6 | Lying Leg Curl | Isolation — hamstrings | 2 | 12–15 | 2 | 60s |
**Duration: ~55–60 min**

#### 5-Day Full-Body Program (A–B–C–A–B, Mon–Tue–Wed–Fri–Sat)

**Fatigue management rule:** Session 5 (Saturday) = RIR target +1 vs. days 1–4. Heaviest sessions = Monday and Wednesday.

**Session A (Mon/Fri):** Back Squat 3×5-8 RIR2 | Lat Pulldown 3×8-12 RIR2 | DB Bench 3×8-12 RIR2 | Lateral Raise 2×12-15 RIR2 | DB Curl 2×10-15 RIR2 (~50 min)

**Session B (Tue/Sat):** Romanian Deadlift 3×6-10 RIR3 | Cable Row 3×10-12 RIR3 | Overhead DB Press 3×8-12 RIR3 | Lying Leg Curl 2×12-15 RIR3 | Tricep Pushdown 2×12-15 RIR3 (~50 min, Saturday uses RIR3)

**Session C (Wed):** Leg Press 3×10-15 RIR2 | Incline DB Press 3×8-12 RIR2 | Single-Arm DB Row 3×10-12/side RIR2 | Bulgarian Split Squat 2×10-12/side RIR2 | Rear Delt Fly 2×15-20 RIR2 | Calf Raise 3×15-20 RIR2 (~55 min)

#### 2-Day Template (Mon + Thu, high per-session volume)

**Session A:** Back Squat 4×5-8 | Barbell Row 4×6-10 | Barbell Bench 4×6-10 | Lateral Raise 3×12-15 | DB Curl 3×10-15 | Tricep Pushdown 3×10-15 | Lying Leg Curl 3×12-15 (~75–80 min)

**Session B:** Trap Bar Deadlift/RDL 4×5-8 | Neutral-Grip Pulldown 4×8-12 | Incline DB Press 4×8-12 | Bulgarian Split Squat 3×8-12/side | Cable Row 3×10-12 | Rear Delt Fly 3×15-20 | Calf Raise 3×15-20 (~80–85 min)

---

## PART 7: RIR-BASED AUTOREGULATION

*Source: Track 3 — RIR-Based Autoregulation*

### 7.1 RIR/RPE Definitions and Scale

**RIR (Reps in Reserve):** Additional reps a lifter could perform before momentary muscular failure.

```
RPE = 10 - RIR
```

| RPE | RIR | Descriptor |
|-----|-----|------------|
| 10 | 0 | True max — no further reps possible |
| 9.5 | 0 | Could not do another rep, but could add tiny load |
| 9 | 1 | 1 rep left in the tank |
| 8.5 | 1–2 | 1–2 reps in reserve |
| 8 | 2 | 2 reps in reserve |
| 7.5 | 2–3 | 2–3 reps in reserve |
| 7 | 3 | 3 reps in reserve |
| 6 | 4 | 4 reps in reserve |
| 5 | 5 | 5 reps in reserve |
| ≤4 | 6+ | Light-to-moderate effort |

**Source:** Zourdos et al. (2016). JSCR 30:267–275. [PubMed 26049792](https://pubmed.ncbi.nlm.nih.gov/26049792/) — RIR shows strong inverse relationship with average concentric velocity (experienced squatters r = −0.88; novice r = −0.77, both p<0.001).

**Evidence for RIR superiority:**
- Helms et al. (2018): RPE group trained at higher average relative intensity (84.14% vs. 78.70% 1RM for bench press, p<0.001) and higher probability of superior strength gains. [Frontiers in Physiology DOI:10.3389/fphys.2018.00247](https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2018.00247/full)
- Graham & Cleather (2019): RIR autoregulation produced superior strength adaptations vs. fixed loading over 12 weeks. [PubMed 31009432](https://pubmed.ncbi.nlm.nih.gov/31009432/)
- Lovegrove et al. (2022): RIR is reliable for prescribing resistance training load for deadlift and bench press (test-retest reliability confirmed).

### 7.2 Phase-Specific RIR Targets

| Mesocycle Phase | Week Position | RIR Target | RPE Equivalent | Rationale |
|---|---|---|---|---|
| Early meso (intro) | Weeks 1–2 | 3–4 | RPE 6–7 | Acclimatization, technique, low fatigue accumulation |
| Mid meso | Weeks 3–4 | 2–3 | RPE 7–8 | Stimulus ascending, manageable fatigue |
| Late meso | Weeks 5–6+ | 1–2 | RPE 8–9 | Near-failure stimuli, fatigue accumulation peak |
| Deload | N/A | 4–5 | RPE 5–6 | Active recovery, technique maintenance |

```python
def get_phase_rir_target(week_in_meso: int, meso_length: int) -> tuple[int, int]:
    """Returns (rir_min, rir_max) for current week."""
    progress_ratio = week_in_meso / meso_length
    if progress_ratio <= 0.33:     return (3, 4)  # Early meso
    elif progress_ratio <= 0.67:   return (2, 3)  # Mid meso
    else:                          return (1, 2)  # Late meso

def get_deload_rir_target() -> tuple[int, int]:
    return (4, 5)
```

**Theoretical basis (Israetel / Helms 2016):** Starting at RIR 3 corresponds to "just barely effective" threshold producing hypertrophy without excessive fatigue. Proximity to failure increases through the meso, creating a predictable fatigue arc from MEV toward MRV.

### 7.3 Exercise-Type RIR Rules

| Exercise Category | Examples | Recommended Minimum RIR | Notes |
|---|---|---|---|
| High-complexity compound | Squat, Deadlift, Olympic lifts | ≥2 (never go to true 0 RIR) | High injury risk, high systemic fatigue |
| Low-complexity compound | Bench press, OHP, Row | 1–2 in late meso | Moderately high fatigue, more controllable |
| Isolation / machine | Leg curl, lat pulldown, cable fly | 0–1 in late meso | Low systemic fatigue, failure more acceptable |

```python
def get_exercise_rir_floor(exercise_type: str, phase: str) -> int:
    floors = {
        "high_complexity_compound": 2,
        "low_complexity_compound": 1,
        "isolation": 0
    }
    base_floor = floors.get(exercise_type, 1)
    if phase == "deload":
        return base_floor + 2  # During deload, all floors increase by 2
    return base_floor
```

### 7.4 Beginner RIR Accuracy Correction

**Evidence:**
- Average underprediction (thinks fewer reps available than actual): ~0.95–1.1 reps. SD of error: ~1.45 reps. [Stronger by Science](https://www.strongerbyscience.com/reps-in-reserve/)
- Accuracy improves when: <12 reps/set, predictions made later in set, set closer to failure.
- Training status does NOT significantly improve RIR accuracy in controlled studies (Zourdos 2016).
- Helms et al. (2016): "novice lifters should practice recording RIR, but likely not base training intensity solely on RIR until increased accuracy is achieved."

```python
BEGINNER_RIR_CORRECTION = +1  # Add 1 RIR buffer for lifters < 12 months experience

def apply_beginner_correction(reported_rir: int, training_age_months: int,
                               reps_performed: int) -> int:
    if training_age_months < 12:
        correction = BEGINNER_RIR_CORRECTION
        if reps_performed <= 8:
            correction = max(0, correction - 1)  # Less correction needed near failure
        return reported_rir + correction
    return reported_rir
```

**Practical guidance:** For beginners in weeks 1–4, prescribe RIR target of 4–5 to ensure actual proximity to failure is ~3, accounting for systematic underprediction.

### 7.5 Performance Tracking (e1RM Calculation)

**Key variables:**
```
session_date, exercise_id, set_number, load_kg, reps_completed, reported_rir,
adjusted_rir, e1rm, session_e1rm, rolling_e1rm_7d, rolling_e1rm_28d,
e1rm_pct_change, consecutive_decline_ct
```

**Epley Formula (primary — best for 1–10 reps):**
```
e1RM = load × (1 + reps / 30)
```
Source: Boyd Epley (1985). [maxcalculator.com](https://maxcalculator.com/guides/epley-formula)

**Brzycki Formula (alternative — better for higher rep sets):**
```
e1RM = load / (1.0278 − 0.0278 × reps)
```

**RPE-Adjusted e1RM (recommended for Milo):**
```python
def calc_e1rm_rir_adjusted(load: float, reps: int, rir: int) -> float:
    """
    RIR Adjustment table (based on RTS charts, approximated):
    RIR 0 → multiplier 1.00
    RIR 1 → multiplier 1.03
    RIR 2 → multiplier 1.06
    RIR 3 → multiplier 1.09
    RIR 4 → multiplier 1.12
    RIR 5 → multiplier 1.15
    """
    RIR_MULTIPLIERS = {0: 1.00, 1: 1.03, 2: 1.06, 3: 1.09, 4: 1.12, 5: 1.15}
    base_e1rm = load * (1 + reps / 30)  # Epley
    multiplier = RIR_MULTIPLIERS.get(rir, 1.00 + (rir * 0.03))
    return base_e1rm * multiplier

def get_session_e1rm(sets: list[dict]) -> float:
    """Returns best (highest) e1RM from all working sets in a session."""
    valid_sets = [s for s in sets if s['reps'] <= 10 and s['reps'] >= 1]
    if not valid_sets: return None
    return max(calc_e1rm_rir_adjusted(s['load'], s['reps'], s['rir']) for s in valid_sets)
```

---

## PART 8: FATIGUE DETECTION & DELOAD PROTOCOLS

*Source: Track 3 — RIR-Based Autoregulation & Reactive Deload Protocols*  
*Cross-reference: Part 9 (Recovery Integration) for HRV/sleep inputs to deload decisions*

### 8.1 Performance Decline Thresholds

```
THRESHOLD_SHORT_TERM_DECLINE_PCT  = 0.05   (5% e1RM drop vs. 7-day rolling avg)
THRESHOLD_LONG_TERM_DECLINE_PCT   = 0.10   (10% e1RM drop vs. 28-day rolling avg)
THRESHOLD_CONSECUTIVE_DECLINES    = 2      (sessions)
```

**Normal variation:** ±2–3% session-to-session is within expected biological variance for trained individuals. Beginners may show ±5%.

```python
def is_performance_declining(current_e1rm: float, rolling_7d_e1rm: float, rolling_28d_e1rm: float) -> dict:
    short_term_change = (current_e1rm - rolling_7d_e1rm) / rolling_7d_e1rm if rolling_7d_e1rm else 0.0
    long_term_change  = (current_e1rm - rolling_28d_e1rm) / rolling_28d_e1rm if rolling_28d_e1rm else 0.0
    return {
        "short_term_decline": short_term_change < -0.05,
        "long_term_decline":  long_term_change < -0.10,
        "short_term_pct": short_term_change,
        "long_term_pct":  long_term_change,
        "severity": "high"     if long_term_change  < -0.10 else
                    "moderate" if short_term_change < -0.05 else "none"
    }
```

**RPE drift as leading indicator:** Same load/reps but reported RIR decreasing (difficulty increasing) signals accumulating fatigue before absolute e1RM drops.

### 8.2 Systemic vs. Local Fatigue Classification

| Signal Pattern | Interpretation | Response |
|---|---|---|
| e1RM drops on 1 lift, others unaffected | Local muscle group fatigue OR technique issue | Reduce volume/intensity on that movement only |
| e1RM drops on 2+ major compounds simultaneously | Systemic/CNS fatigue | Trigger full reactive deload |
| RPE elevating across all lifts but no load drop | Systemic fatigue early signal | Increase monitoring; consider early deload |
| Joint pain + localized soreness | Local structural fatigue/overuse | Remove offending movement; investigate form |
| Subjective markers degraded + ≥1 lift declining | Systemic fatigue (CNS + hormonal) | Trigger reactive deload |

```python
def classify_fatigue_type(declining_lifts: list[str], total_key_lifts: int, systemic_symptoms: bool) -> str:
    proportion_declining = len(declining_lifts) / total_key_lifts
    if len(declining_lifts) == 0: return "none"
    elif proportion_declining >= 0.5 or systemic_symptoms: return "systemic"
    else: return "local"
```

### 8.3 Reactive Deload Trigger Decision Tree

**All threshold constants:**
```
T_E1RM_SHORT_DECLINE   = -0.05   (5%)
T_E1RM_LONG_DECLINE    = -0.10   (10%)
T_CONSECUTIVE_DECLINES = 2       (sessions)
T_RIR_MISS_THRESHOLD   = 2       (RIR below target by this amount)
T_RIR_MISS_SESSION_PCT = 0.50    (% of sets missing RIR target in a session)
T_RIR_MISS_SESSIONS    = 2       (consecutive sessions)
T_SUBJECTIVE_SESSIONS  = 3       (consecutive sessions with poor subjective markers)
T_HRV_SUPPRESSION_DAYS = 4       (consecutive days HRV below personal baseline)
T_SLEEP_DEBT_DAYS      = 4       (consecutive nights poor sleep)
T_STAGNATION_SESSIONS  = 5       (consecutive sessions with zero progress)
```

```python
def evaluate_deload_trigger(
    key_lift_declines: list[bool],         # Per-lift decline flags (≥5%)
    consecutive_decline_counts: list[int], # Per-lift consecutive decline count
    rir_miss_rate_sessions: list[float],   # Per session: fraction of sets missing RIR by ≥2
    consecutive_rir_miss_sessions: int,
    consecutive_poor_motivation: int,
    joint_pain_reported: bool,
    hrv_suppressed_days: int,             # ← from Part 9 recovery system
    sleep_debt_days: int,                  # ← from Part 9 recovery system
    consecutive_stagnation: int
) -> dict:
    """Returns: {'trigger': bool, 'urgency': 'immediate'|'recommended'|'monitor', 
                 'reason': str, 'fatigue_type': 'systemic'|'local'|'none'}"""
    
    # RULE 1: Immediate — joint pain
    if joint_pain_reported:
        return {'trigger': True, 'urgency': 'immediate', 'reason': 'joint_pain_reported', 'fatigue_type': 'local'}
    
    # RULE 2: Systemic performance regression
    declining_lift_count = sum(1 for i, declining in enumerate(key_lift_declines)
                                if declining and consecutive_decline_counts[i] >= T_CONSECUTIVE_DECLINES)
    if declining_lift_count >= 2:
        return {'trigger': True, 'urgency': 'immediate', 'reason': 'multi_lift_e1rm_decline', 'fatigue_type': 'systemic'}
    
    # RULE 3: Single lift consecutive decline (local, not full deload)
    if any(c >= T_CONSECUTIVE_DECLINES and d for c, d in zip(consecutive_decline_counts, key_lift_declines)):
        if declining_lift_count == 1:
            return {'trigger': False, 'urgency': 'monitor', 'reason': 'single_lift_local_decline', 'fatigue_type': 'local'}
    
    # RULE 4: RIR target chronically missed
    if consecutive_rir_miss_sessions >= T_RIR_MISS_SESSIONS:
        return {'trigger': True, 'urgency': 'recommended', 'reason': 'rir_target_missed_repeatedly', 'fatigue_type': 'systemic'}
    
    # RULE 5: Performance stagnation
    if consecutive_stagnation >= T_STAGNATION_SESSIONS:
        return {'trigger': True, 'urgency': 'recommended', 'reason': 'performance_stagnation', 'fatigue_type': 'systemic'}
    
    # RULE 6: Recovery metric cluster
    recovery_signals_red = sum([
        hrv_suppressed_days >= T_HRV_SUPPRESSION_DAYS,   # cross-reference Part 9
        sleep_debt_days >= T_SLEEP_DEBT_DAYS,              # cross-reference Part 9
        consecutive_poor_motivation >= T_SUBJECTIVE_SESSIONS
    ])
    if recovery_signals_red >= 2:
        return {'trigger': True, 'urgency': 'recommended', 'reason': 'recovery_signal_cluster', 'fatigue_type': 'systemic'}
    
    # RULE 7: Moderate signals — monitor
    recovery_signals_amber = sum([
        hrv_suppressed_days >= 2,
        sleep_debt_days >= 2,
        consecutive_poor_motivation >= 2,
        declining_lift_count >= 1
    ])
    if recovery_signals_amber >= 2:
        return {'trigger': False, 'urgency': 'monitor', 'reason': 'multiple_amber_signals', 'fatigue_type': 'potential_systemic'}
    
    return {'trigger': False, 'urgency': 'none', 'reason': 'no_fatigue_signals', 'fatigue_type': 'none'}
```

**Consecutive sessions required before triggering:**
| Scenario | Required Consecutive Sessions |
|---|---|
| e1RM drop ≥5% on 2+ lifts | 2 |
| RIR target missed by ≥2 reps | 2 |
| Poor motivation / subjective fatigue | 3 |
| Performance zero progress | 5 |
| Joint pain | 0 (immediate) |

### 8.4 Deload Protocol

**Evidence:**
- Bell et al. (2023): Universal expert consensus — training volume MUST decrease; intensity can be maintained or slightly reduced; frequency generally unchanged; 5–7 days standard. [PMC10511399](https://pmc.ncbi.nlm.nih.gov/articles/PMC10511399/)
- Bosquet taper meta-analysis: Volume reduction of 41–60% produced largest effect size (0.72 ± 0.36, p<0.001) while maintaining intensity/frequency.
- Juggernaut/Israetel: "When you put on the brakes, put them on hard." Anything above ~50% of normal volume+effort during deload is likely excess work.
- Pritchard et al. (2019): Higher-intensity taper (~70% volume reduction + maintained intensity) superior to lower-intensity taper. [PubMed 30204523](https://pubmed.ncbi.nlm.nih.gov/30204523/)

**PRIMARY lever: cut sets by 50%**  
**SECONDARY lever: increase RIR target to 4–5**  
**TERTIARY option only if high recovery needs: reduce load by 10–15%**

```python
def generate_deload_session(
    pre_deload_sets_per_exercise: dict,
    pre_deload_working_loads: dict,
    recovery_needs: str,               # 'low', 'moderate', 'high'
    pre_deload_rep_ranges: dict
) -> dict:
    volume_reduction = {'low': 0.35, 'moderate': 0.50, 'high': 0.70}[recovery_needs]
    load_reduction   = {'low': 0.00, 'moderate': 0.10, 'high': 0.15}[recovery_needs]
    
    deload_prescription = {}
    for exercise_id in pre_deload_sets_per_exercise:
        original_sets = pre_deload_sets_per_exercise[exercise_id]
        original_load = pre_deload_working_loads[exercise_id]
        deload_prescription[exercise_id] = {
            'sets': max(1, round(original_sets * (1 - volume_reduction))),
            'load': original_load * (1 - load_reduction),
            'rir_target': (4, 5),
            'reps': pre_deload_rep_ranges[exercise_id]
        }
    return deload_prescription
```

**Volume reduction by recovery needs:**
| Recovery Needs | Volume Reduction | Sets Remaining |
|---|---|---|
| Low (mild fatigue) | 25–45% | ~55–75% of normal |
| Moderate (typical deload) | 40–60% | ~40–60% of normal |
| High (severe fatigue) | 60–90% | ~10–40% of normal |

**Duration:**
- Standard deload: 7 days (1 full training week)
- Extended deload (severe fatigue/injury): 10–14 days with 2–5 days complete rest at start
- Mini-deload: Single reduced session — for localized fatigue on one lift

**Evidence on deload safety (Ogasawara et al. 2013):**
- Periodic training (3× cycles of 6-week training + 3-week detraining) produced SIMILAR hypertrophy and strength as continuous training after 24 weeks, despite 25% fewer sessions and 33.5% lower total volume.
- During retraining, adaptation rates returned to early-phase levels (re-sensitization).
- **Implication:** Aggressive 1-week deloads (not total cessation) are unlikely to cost meaningful muscle or strength. [PubMed 23053130](https://pubmed.ncbi.nlm.nih.gov/23053130/)

### 8.5 Post-Deload Progression Rules

**Exit criteria (objective, not motivation-based):**
| Criterion | Signal |
|---|---|
| HRV trending back toward personal baseline | Recovery metric normalized |
| Resting HR drift resolved | Autonomic recovery |
| Sleep debt stabilized | Acute recovery |
| First quality session without strain completed | Performance signal |
| e1RM on first session ≥ 95% of pre-deload baseline | Strength retention confirmed |

**Post-deload performance expectations:**
- Week 1 post-deload: Strength may be slightly below pre-deload peak — NORMAL. **Do not flag as decline.**
- Weeks 2–3: Performance returns to or exceeds pre-deload baseline.
- Weeks 3–4+: Supercompensation — strength expression may exceed any previous level.

```
NOTE FOR MILO BACKEND: Suppress decline detection for 7 days post-deload end.
Post-deload performance baseline updated only after 2 full training weeks.
post_deload_flag: bool — True if within 14 days of deload end
post_deload_days: int — Days since deload ended (0–14)
```

**Post-deload volume baseline:**
```python
def calc_post_deload_baseline(pre_deload_peak_sets, deload_triggered_by,
                               e1rm_week1_post_deload, e1rm_pre_deload_peak) -> dict:
    restart_ratio = {'systemic': 0.70, 'local': 0.80, 'scheduled': 0.80}[deload_triggered_by]
    prescriptions = {}
    for exercise_id, peak_sets in pre_deload_peak_sets.items():
        restart_sets = max(2, round(peak_sets * restart_ratio))
        current_e1rm = e1rm_week1_post_deload.get(exercise_id, e1rm_pre_deload_peak.get(exercise_id, 0))
        prescriptions[exercise_id] = {
            'sets': restart_sets,
            'target_rir': (3, 4),        # Early meso
            'load_basis': current_e1rm,
            'mesocycle_week': 1,
            'progression_note': 'Reset. Progress from current performance baseline.'
        }
    return prescriptions
```

**Ramp-back protocol (moderate recovery needs):**
| Days Post-Deload | Volume Target | Intensity/RIR |
|---|---|---|
| 1–4 (Week 1) | 70–75% of pre-deload peak | RIR 3–4 (early meso) |
| 5–9 (Week 2) | 80–85% if markers stable | RIR 2–3 (mid meso entry) |
| 10–14 (Week 2–3) | Return to pre-deload levels if markers aligned | Follow new meso schedule |

**Mesocycle restart recommendation:** Restart at MEV (early-meso RIR 3–4). Do NOT resume at the same intensity/volume that caused the deload.

**Exception:** If deload was triggered by a single local issue and all other lifts unaffected, continue mesocycle for unaffected muscle groups while restarting affected movement at early-meso targets.

---

## PART 9: RECOVERY INTEGRATION

*Source: Track 4 — HRV, RHR, Sleep, and Nocebo Avoidance*  
*Cross-references: Part 8 (deload triggers use `hrv_suppressed_days` and `sleep_debt_days`)*

### 9.1 HRV Analysis

**Evidence base:**
- Kiviniemi et al. (2007): HRV-guided training → significantly greater improvements in maximal running performance (Load_max: +0.9 ± 0.2 vs. +0.5 ± 0.4 km/h, p=0.048). [PubMed 17849143](https://pubmed.ncbi.nlm.nih.gov/17849143/)
- Plews et al.: Acute (single-day) HRV values are "too varied and cannot really mean much." Use 7-day or 10-day rolling windows. Use 0.5 coefficient of variation (CV) over two weeks as boundary for "substantial change."
- Meta-analysis (2021): HRV-guided training, SMD+ = 0.20 (95% CI = −0.09, 0.48) favoring it over predefined training. [PMC8507742](https://pmc.ncbi.nlm.nih.gov/articles/PMC8507742/)

**Day-to-day HRV variability:**
- Between-day CV for RMSSD: **17.88%** in younger adults; LnrMSSD: **4.42%** [PMC11055755](https://pmc.ncbi.nlm.nih.gov/articles/PMC11055755/)
- Normal day-to-day fluctuations: 10% one way or the other are NOT unusual. Single readings carry high false-positive risk for overtraining signals.

**Recommended HRV metric:** LnrMSSD (natural log of rMSSD)

```
hrv_raw    TYPE: float  UNIT: ms    SOURCE: Whoop (PPG during slow-wave sleep)
hrv_ln     TYPE: float  UNIT: ln(ms) FORMULA: ln(hrv_raw)
```

**Why LnrMSSD:** rMSSD is preferred time-domain metric for vagal modulation monitoring; log-transformation normalizes distribution; used in all Plews, Kiviniemi, and Javaloyes methodologies.

#### 9.1.1 Rolling Average Windows

**7-Day Rolling Average (Primary Signal):**
```
hrv_7d_avg[t] = (1/7) × Σ hrv_ln[t-i] for i in {0, 1, 2, 3, 4, 5, 6}
Requirements: minimum 4 of 7 days must have valid readings; otherwise return NULL
Applied to LnrMSSD, NOT raw rMSSD
```

**30-Day Baseline (Personal Norm):**
```
hrv_30d_mean[t] = (1/30) × Σ hrv_ln[t-i] for i in {0..29}
hrv_30d_sd[t]   = sqrt( (1/29) × Σ (hrv_ln[t-i] - hrv_30d_mean[t])² for i in {0..29} )

Bootstrapping: During onboarding (days 1–30), use all available days.
Do not generate readiness recommendations until ≥14 days of data exist.
```

#### 9.1.2 Coefficient of Variation (CV) as Stability Indicator

```
hrv_7d_cv[t] = (hrv_7d_sd / hrv_7d_mean) × 100

CV < 5%:   Very stable; well-adapted to current training load
CV 5–10%:  Normal physiological variation during moderate training
CV > 10%:  Elevated instability; increased training stress
CV > 15%:  High instability; reduce confidence in single HRV-based triggers
```

#### 9.1.3 Meaningful Deviation Threshold

**Plews methodology:**
```
hrv_normal_upper = hrv_30d_mean + (0.5 × hrv_30d_sd)
hrv_normal_lower = hrv_30d_mean - (0.5 × hrv_30d_sd)
hrv_below_normal = (hrv_7d_avg < hrv_normal_lower)  # boolean

Z-score approach:
hrv_z_score[t] = (hrv_7d_avg[t] - hrv_30d_mean[t]) / hrv_30d_sd[t]

Z > +1.0:        Elevated (parasympathetic dominant — green, ready to push)
−0.5 to +1.0:   Normal range
−1.0 to −0.5:   Mild suppression (watch)
−1.5 to −1.0:   Moderate suppression (yellow)
< −1.5:          Significant suppression (red)
```

**Milo uses ±0.5 SD** as activation boundary (more conservative than HRV4Training's ±1 SD).

#### 9.1.4 HRV Status Decision Logic

**CRITICAL: Never flag on a single day. Require sustained trend (minimum 3 consecutive days).**

```python
def compute_hrv_status(hrv_7d_avg_history: list[float], hrv_30d_mean: float,
                        hrv_30d_sd: float, min_consecutive_days: int = 3) -> str:
    """Returns: 'green', 'yellow', 'red', or 'insufficient_data'"""
    if len(hrv_7d_avg_history) < min_consecutive_days:
        return 'insufficient_data'
    lower_bound = hrv_30d_mean - (0.5 * hrv_30d_sd)
    red_bound   = hrv_30d_mean - (1.5 * hrv_30d_sd)
    recent = hrv_7d_avg_history[-min_consecutive_days:]
    days_below_lower = sum(1 for v in recent if v < lower_bound)
    days_below_red   = sum(1 for v in recent if v < red_bound)
    if days_below_red >= min_consecutive_days:   return 'red'
    elif days_below_lower >= min_consecutive_days: return 'yellow'
    else:                                          return 'green'
```

- Yellow trigger: 3 consecutive days hrv_7d_avg < (hrv_30d_mean − 0.5 SD)
- Red trigger: 3 consecutive days hrv_7d_avg < (hrv_30d_mean − 1.5 SD)

### 9.2 Resting Heart Rate Analysis

**Evidence:** RHR elevation established early marker of overreaching. A sustained increase of 3–5 bpm above baseline for several days is one of the most reliable objective markers of accumulating fatigue. [TrainingPeaks](https://www.trainingpeaks.com/coach-blog/the-4-signs-of-overtraining/); [Runners Connect](https://runnersconnect.net/overtraining-in-runners/)

**Variables:**
```
rhr_daily         TYPE: float  UNIT: bpm   SOURCE: Whoop/Withings
rhr_14d_mean      TYPE: float  UNIT: bpm
rhr_30d_mean      TYPE: float  UNIT: bpm
rhr_30d_sd        TYPE: float  UNIT: bpm
rhr_z_score       TYPE: float
rhr_delta_bpm     TYPE: float  UNIT: bpm   (current − baseline)

rhr_30d_mean[t] = (1/N) × Σ rhr_daily[t-i] where N = min(available_days, 30)
rhr_delta_bpm   = rhr_7d_avg - rhr_30d_mean
```

**Elevation thresholds:**
| Elevation | Interpretation |
|---|---|
| < +3 bpm | Normal fluctuation — no action |
| +3–5 bpm | Mild elevation — watch; combine with HRV and sleep |
| > +5 bpm | Significant elevation — recovery concern (yellow/red) |
| > +8 bpm | Severe elevation — likely illness or acute overreaching (red) |

**Note:** A SINGLE-DAY spike of 5–8 bpm after a hard workout is expected and NOT a flag. Requires sustained elevation.

```python
def compute_rhr_status(rhr_7d_avg_history: list[float], rhr_30d_mean: float,
                        rhr_30d_sd: float, min_consecutive_days: int = 3) -> str:
    if len(rhr_7d_avg_history) < min_consecutive_days: return 'insufficient_data'
    recent = rhr_7d_avg_history[-min_consecutive_days:]
    mild_upper = rhr_30d_mean + 3.0
    mod_upper  = rhr_30d_mean + 5.0
    sev_upper  = rhr_30d_mean + 8.0
    days_mild     = sum(1 for v in recent if v > mild_upper)
    days_moderate = sum(1 for v in recent if v > mod_upper)
    days_severe   = sum(1 for v in recent if v > sev_upper)
    if days_severe >= 2:                        return 'red'
    elif days_moderate >= min_consecutive_days: return 'red'
    elif days_mild >= min_consecutive_days:     return 'yellow'
    else:                                        return 'green'
```

**HRV × RHR combined status:**
```python
def combined_hrv_rhr_status(hrv_status: str, rhr_status: str) -> str:
    status_rank = {'green': 0, 'yellow': 1, 'red': 2, 'insufficient_data': -1}
    if hrv_status == 'insufficient_data' and rhr_status == 'insufficient_data':
        return 'insufficient_data'
    valid_statuses = [s for s in [hrv_status, rhr_status] if s != 'insufficient_data']
    if len(valid_statuses) == 1:
        return 'yellow' if valid_statuses[0] == 'red' else valid_statuses[0]
    ranks = [status_rank[s] for s in valid_statuses]
    if max(ranks) == 2 and min(ranks) >= 1: return 'red'
    elif max(ranks) == 2 and min(ranks) == 0: return 'yellow'
    else: return valid_statuses[status_rank.index(max(ranks))]
```

**Physiological rationale:** When both HRV drops AND RHR rises simultaneously over multiple days, signal reliability approaches >90%.

### 9.3 Sleep Metrics

**Evidence:**
- Sleep restriction to ~5h/night impairs endurance performance ~3%; sleep extension to >8h improves by ~3%. [HiitScience/Roberts et al.](https://hiitscience.com/sleep-endurance-performance/)
- Partial sleep restriction (4h) negatively affects muscle power, strength, and endurance. [PMC10354314](https://pmc.ncbi.nlm.nih.gov/articles/PMC10354314/)
- American Academy of Sleep Medicine recommends ≥7 hours; active individuals 7–9h; highly trained athletes 8–10h.

**Variables:**
```
sleep_duration_hrs    TYPE: float  UNIT: hours   SOURCE: Whoop
sleep_efficiency_pct  TYPE: float  UNIT: %       SOURCE: Whoop (time asleep / time in bed × 100)
sleep_perf_score      TYPE: float  UNIT: 0–100   SOURCE: Whoop Sleep Performance Score
sleep_7d_avg_hrs[t]   = (1/N) × Σ sleep_duration_hrs[t-i]  for i in {0..6}
sleep_7d_avg_eff[t]   = (1/N) × Σ sleep_efficiency_pct[t-i]
```

**Whoop Sleep Performance Score components:**
1. Sleep Sufficiency (hours obtained vs. hours needed) — ~20% of recovery score
2. Sleep Consistency (timing vs. prior 4 nights) — part of HRV weighting
3. Sleep Efficiency (% time in bed actually asleep)
4. Sleep Stress (time in high-stress state overnight)

**NOTE:** Milo does NOT passthrough Whoop's raw recovery score — nocebo risk (see §9.5).

**Sleep duration thresholds:**
| Duration | Status |
|---|---|
| ≥ 8.0 h | Optimal (green) |
| 7.0–7.9 h | Adequate (green-yellow) |
| 6.0–6.9 h | Suboptimal (yellow) |
| < 6.0 h | Deficit (yellow → red based on trend) |
| < 5.0 h | Acute deficit (red — same-day modifier) |

```python
def compute_sleep_status(sleep_7d_avg_hrs, sleep_7d_avg_eff, sleep_duration_history, min_consecutive_days=3) -> str:
    if sleep_7d_avg_hrs is None: return 'insufficient_data'
    if sleep_7d_avg_hrs >= 7.0 and sleep_7d_avg_eff >= 80: avg_status = 'green'
    elif sleep_7d_avg_hrs >= 6.0 and sleep_7d_avg_eff >= 70: avg_status = 'yellow'
    else: avg_status = 'red'
    if len(sleep_duration_history) >= min_consecutive_days:
        recent = sleep_duration_history[-min_consecutive_days:]
        acute_deficit_days = sum(1 for d in recent if d < 6.0)
        if acute_deficit_days >= min_consecutive_days: return 'red'
    return avg_status
```

**Sleep modifier rules:**
```
Single night < 6h              → No change (single-day noise)
2 consecutive nights < 6h     → Suggest avoiding max-effort sessions
3+ consecutive nights < 6h    → Recommend reduced intensity (-20% load)
7-day avg < 6h                → Deload recommendation regardless of HRV/RHR
7-day avg < 5.5h              → Rest/recovery-only recommendation
Sleep efficiency < 70% (3 days) → Flag for investigation, not training change
```

```python
def apply_sleep_modifier(composite_score: float, sleep_status: str, sleep_7d_avg_hrs: float) -> float:
    if sleep_status == 'red':    penalty = 15.0
    elif sleep_status == 'yellow': penalty = 7.5
    else:                          penalty = 0.0
    if sleep_7d_avg_hrs < 5.5:  penalty += 10.0
    return max(0.0, composite_score - penalty)
```

### 9.4 Composite Recovery Score Model

**Weights (based on Whoop internal algorithm and academic models):**
```
w_hrv   = 0.40   # HRV (LnrMSSD 7-day Z-score)
w_rhr   = 0.30   # RHR (7-day Z-score, inverted)
w_sleep = 0.30   # Sleep score (duration + efficiency)
```

**Step 1: Z-score each metric**
```
hrv_z   = (hrv_7d_avg   - hrv_30d_mean)   / hrv_30d_sd        # positive = better
rhr_z   = -1 × (rhr_7d_avg - rhr_30d_mean) / rhr_30d_sd       # inverted (elevated RHR = negative)
sleep_z = (sleep_7d_avg_score - sleep_score_30d_mean) / sleep_score_30d_sd
```

**Step 2: Compute raw composite**
```
composite_z = (w_hrv × hrv_z) + (w_rhr × rhr_z) + (w_sleep × sleep_z)
```

**Step 3: Convert to 0–100 scale**
```
composite_z_clamped = max(-3.0, min(3.0, composite_z))
composite_score_raw = 50 + (composite_z_clamped / 3.0) × 50
composite_score     = max(0.0, min(100.0, composite_score_raw))
```

**Step 4: Apply sleep debt modifier**
```
composite_score_final = apply_sleep_modifier(composite_score, sleep_status, sleep_7d_avg_hrs)
```

**Handling missing data — dynamic reweighting:**
```python
def compute_composite(hrv_z, rhr_z, sleep_z, w_hrv=0.40, w_rhr=0.30, w_sleep=0.30):
    available = {k: v for k, v in {'hrv': (hrv_z, w_hrv), 'rhr': (rhr_z, w_rhr), 
                                    'sleep': (sleep_z, w_sleep)}.items() if v[0] is not None}
    if len(available) == 0: return None
    total_weight = sum(w for _, w in available.values())
    composite_z = sum((z * w / total_weight) for z, w in available.values())
    composite_z_clamped = max(-3.0, min(3.0, composite_z))
    return 50.0 + (composite_z_clamped / 3.0) * 50.0
```

**SpO2 note:** Excluded from primary composite unless SpO2_avg < 94% for 3+ days, which triggers a medical referral flag separate from training recommendations.

### 9.5 Composite Tier Classification

| Tier | Score Range | Conditions |
|---|---|---|
| GREEN | 55–100 | composite_score_final ≥ 55 AND no individual metric in red |
| YELLOW | 35–54 | composite_score_final 35–54 OR one metric in yellow for 3+ days |
| RED | 0–34 | composite_score_final < 35 OR two+ metrics yellow/red simultaneously for 3+ days |

**Additional escalation:** Single metric hitting red-level threshold for 5+ consecutive days → system-level RED regardless of composite score.

```python
def classify_tier(composite_score, hrv_status, rhr_status, sleep_status) -> str:
    if composite_score is None: return 'insufficient_data'
    statuses = [hrv_status, rhr_status, sleep_status]
    red_count    = sum(1 for s in statuses if s == 'red')
    yellow_count = sum(1 for s in statuses if s == 'yellow')
    if composite_score >= 55 and red_count == 0 and yellow_count < 2: score_tier = 'green'
    elif composite_score >= 35 and red_count < 2: score_tier = 'yellow'
    else: score_tier = 'red'
    if red_count >= 2 or (red_count >= 1 and yellow_count >= 1): return 'red'
    return score_tier
```

### 9.6 Recovery-to-Action Mapping (Green/Yellow/Red)

**Tier GREEN — "Ready to Train as Programmed":**
```
Conditions (ALL must be true):
  composite_score_final ≥ 55
  hrv_status = 'green' OR hrv_z_score > -0.5
  rhr_status = 'green' OR rhr_delta_bpm < 3
  sleep_7d_avg_hrs ≥ 7.0
  sleep_status = 'green'
  No individual metric declining for 3+ days
  No concurrent SpO2 < 94%
Training directive: Execute session as programmed. No modifications.
```

**Tier YELLOW — "Consider Reducing Intensity":**
```
Conditions (ANY of the following):
  35 ≤ composite_score_final < 55
  hrv_7d_avg < (hrv_30d_mean - 0.5×SD) for 3+ days
  rhr_7d_avg elevated 3–5 bpm above baseline for 3+ days
  sleep_7d_avg_hrs between 6.0–6.9h
  MUST persist for: ≥ 3 consecutive days before triggering Telegram message
Training directive: Reduce intensity by 20–30%. Maintain skill work. 
                     Avoid new PRs or maximum effort sets.
```

**Tier RED — "Recommend Deload or Rest":**
```
Conditions (ANY of the following):
  composite_score_final < 35
  hrv_7d_avg < (hrv_30d_mean - 1.5×SD) for 3+ days
  rhr_7d_avg elevated > 5 bpm above baseline for 3+ days
  sleep_7d_avg_hrs < 6.0h for 5+ days
  Two+ individual metrics yellow/red simultaneously for 3+ days
  MUST persist for: ≥ 3 consecutive days (or 2 days if severely depressed)
Training directive: Full deload or rest. Active recovery only.
                     If RED > 7 days without identifiable cause: flag for professional review.
---

## PART 10: SLEEP HYGIENE COACHING

*Source: Track 6 — Sleep Hygiene Protocols for Muscle Recovery and Performance*

### 10.1 Evidence Framework

Sleep is a Tier 1 priority equal to nutrition and programming. Key evidence:

- **Lamon et al. (2021):** A single night of total sleep deprivation reduces muscle protein synthesis (MPS) by **18%**, accompanied by a 21% increase in cortisol and 24% decrease in testosterone. Source: [PMC7785053](https://pmc.ncbi.nlm.nih.gov/articles/PMC7785053/)
- **Leproult & Van Cauter (2011):** Five hours of sleep/night for one week reduced testosterone by **10–15%** in healthy young men — equivalent to 10–15 years of aging. Source: JAMA 305(21):2173. DOI: 10.1001/jama.2011.710
- **Nedeltcheva et al. (2010):** Sleeping 5.5h vs. 8.5h during caloric restriction: **55% less fat lost**, **60% more lean mass lost**. Sleep deprivation during a cut creates a catabolic, muscle-wasting state. Source: [PMC2951287](https://pmc.ncbi.nlm.nih.gov/articles/PMC2951287/)
- **Henselmans:** Sleep and stress are "top 2 underrated factors limiting gains." Comparable to macro tracking and programming. Source: [mennohenselmans.com](https://mennohenselmans.com/these-are-the-top-2-underrated-factors-killing-your-gains/)
- **Growth Hormone:** 70% of daily GH is released during the first slow-wave sleep (SWS) phase. Behaviors that fragment SWS directly suppress GH release. Source: [Nature Comm Bio 2022](https://www.nature.com/articles/s42003-022-03643-y)

### 10.2 Sleep Duration Targets

```python
SLEEP_DURATION_TARGET_HOURS = 7.5       # default nightly target
SLEEP_DURATION_TARGET_OPTIMAL = 8.5    # for trainees in caloric deficit or high volume
SLEEP_DURATION_MINIMUM = 7.0           # below this → coaching intervention
SLEEP_DURATION_CRITICAL = 6.0          # below this → flag for immediate attention
```

| Duration | Status |
|----------|--------|
| ≥ 8.0h | Optimal (green) |
| 7.0–7.9h | Adequate (green-yellow) |
| 6.0–6.9h | Suboptimal (yellow) |
| < 6.0h | Deficit (yellow → red) |
| < 5.0h | Acute deficit (red — same-day modifier) |

**Milo Application during CUT:** Sleep hygiene moves to CRITICAL priority. Failure to sleep adequately during a cut results in disproportionate muscle loss.

**Training vs. sleep trade-off decision rule:**
```python
if user_weekly_sets < MRV_estimate:
    priority = "complete_training_even_if_slightly_tired"
else:  # near MRV
    priority = "prioritize_sleep_over_extra_volume"
```

### 10.3 Prioritized Habit Stack

Habits ranked by evidence strength, impact magnitude, and ease of implementation (maximum 15 points):

| Rank | Habit | Evidence | Impact | Ease | Priority Score |
|------|-------|----------|--------|------|---------------|
| 1 | **Consistent wake time (±30 min daily)** | ★★★★★ | ★★★★★ | ★★★★☆ | 14/15 |
| 2 | **Caffeine cutoff 10h before bed** | ★★★★★ | ★★★★☆ | ★★★★☆ | 13/15 |
| 3 | **Morning sunlight (10 min, within 60 min of wake)** | ★★★★★ | ★★★★★ | ★★★☆☆ | 13/15 |
| 4 | **Total sleep duration ≥7.5h** | ★★★★★ | ★★★★★ | ★★★☆☆ | 13/15 |
| 5 | **No alcohol within 3h of bedtime** | ★★★★☆ | ★★★★★ | ★★★☆☆ | 12/15 |
| 6 | **Cool bedroom (65–68°F / 18–20°C)** | ★★★★☆ | ★★★★☆ | ★★★★☆ | 12/15 |
| 7 | **Dim/warm lights after 9 PM** | ★★★★☆ | ★★★★☆ | ★★★★☆ | 12/15 |
| 8 | **No high-strain exercise within 4h of bed** | ★★★★★ | ★★★★☆ | ★★★☆☆ | 12/15 |
| 9 | **Consistent bedtime (±30 min daily)** | ★★★★☆ | ★★★★☆ | ★★★☆☆ | 11/15 |
| 10 | **Warm shower 60–90 min before bed** | ★★★☆☆ | ★★★☆☆ | ★★★★★ | 11/15 |
| 11 | **Magnesium threonate/bisglycinate (300–400 mg)** | ★★★☆☆ | ★★★☆☆ | ★★★★☆ | 10/15 |
| 12 | **L-Theanine (100–200 mg before bed)** | ★★★☆☆ | ★★★☆☆ | ★★★★☆ | 10/15 |
| 13 | **Apigenin (50 mg before bed)** | ★★☆☆☆ | ★★★☆☆ | ★★★★☆ | 9/15 |
| 14 | **Avoid large meals within 2h of bed** | ★★★☆☆ | ★★☆☆☆ | ★★★☆☆ | 8/15 |
| 15 | **Pre-sleep protein (30–40g casein)** | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | 10/15 |

### 10.4 Huberman Protocol Details

#### 10.4.1 Morning Sunlight Exposure
- **Protocol:** 5–10 minutes outdoor sunlight within 30–60 minutes of waking. On overcast days: 15–20 minutes.
- **Mechanism:** Melanopsin ipRGCs (intrinsically photosensitive retinal ganglion cells) detect low-angle morning sunlight → signal the SCN (suprachiasmatic nucleus) → trigger cortisol spike, suppress melatonin, modulate dopamine/serotonin.
- **Critical rules:** No sunglasses (blocks photons). Prescription lenses/contacts OK. Windows filter >50% of relevant photons — indoor viewing is 1/50th–1/100th as effective. Indoor lighting delivers 200–500 lux; circadian system requires ≥10,000 lux.
- **Priority:** HIGHEST — downstream effects on cortisol, melatonin, dopamine for the next 16 hours.

```
MORNING_LIGHT_DONE = true/false
MINUTES_OUTDOOR = integer
WAKE_TIME = HH:MM
LIGHT_WITHIN_60MIN = (MORNING_LIGHT_TIME - WAKE_TIME <= 60 minutes)
```

#### 10.4.2 Evening Light Reduction
- **Protocol:** Reduce artificial bright light after sunset. Dim, warm-toned (amber/red) lighting after 9 PM. Avoid overhead fluorescent/LED in 2 hours before bed.
- **Mechanism:** Same melanopsin ipRGCs respond to artificial bright light at night. Even 15 seconds of bright light can suppress melatonin. Modern LED/fluorescent exceeds activation threshold. Moonlight/candlelight/firelight do NOT trigger false daytime signals.

```
EVENING_LIGHT_CUTOFF = 21:00 (local)
SCREEN_DIMMED = true/false (after 20:00)
OVERHEAD_LIGHTS_OFF = true/false (after 21:00)
```

#### 10.4.3 Temperature Regulation
- **Protocol:** Sleep in 65–68°F (18–20°C). Warm shower/bath 1–2 hours before bed accelerates sleep onset. Avoid cold exposure late evening (can phase-delay circadian clock).
- **Mechanism:** Core body temperature follows circadian rhythm (lowest ~4 AM, peaks 4–6 PM). Sleep onset requires a drop in core temperature. Warm bath raises skin temp → peripheral vasodilation → heat dissipation → accelerates core temperature drop.

```
BEDROOM_TEMP_TARGET = 65–68°F (18.3–20°C)
WARM_BATH_TIMING = 60–120 min before bedtime
COLD_SHOWER_TIMING = within first 2 hours of waking (phase-advance benefit)
```

#### 10.4.4 Caffeine Timing and Adenosine Management
- **Protocol:** Delay first caffeine to 90–120 minutes after waking. Last caffeine: 10–12 hours before bedtime.
- **Mechanism:** Caffeine is an adenosine receptor antagonist. Half-life: 5–6 hours. Quarter-life: 10–12 hours. 200mg caffeine in evening delays melatonin onset by ~40 minutes.
- **Evidence:** Caffeine at bedtime prolongs sleep latency, reduces sleep efficiency, reduces Stage 4 NREM, suppresses slow-wave activity (delta power). Source: [Landolt et al., Nature](https://www.nature.com/articles/1380255.pdf)

```
CAFFEINE_MORNING_DELAY = 60–90 min post-waking (recommended)
CAFFEINE_CUTOFF_HOURS_BEFORE_BED = 10        // conservative
CAFFEINE_CUTOFF_HOURS_BEFORE_BED_STRICT = 12 // for poor sleepers
CAFFEINE_HALF_LIFE_HOURS = 5.5               // default estimate
CAFFEINE_CUTOFF_TIME = BEDTIME_TARGET - 10h
```

#### 10.4.5 Consistent Wake Time (Primary Anchor)
- **Protocol:** Fix a consistent wake time every day, including weekends, regardless of when you went to sleep.
- **Mechanism:** Circadian clock is entrained primarily by light exposure and wake time consistency. Irregular wake times create chronic social jet lag, dampening circadian amplitude and disrupting cortisol, melatonin, core temperature rhythms, and anabolic hormone secretion.

```
WAKE_TIME_CONSISTENCY = |today_wake - 7day_avg_wake| <= 30min  // "consistent"
WAKE_TIME_CONSISTENCY_SCORE = rolling 7-day SD of wake time (minutes)
CONSISTENCY_THRESHOLD = SD < 30 min → "consistent"
CONSISTENCY_ALERT = SD > 45 min → trigger coaching message
```

#### 10.4.6 Exercise Timing
- High-intensity/high-strain exercise: complete at least **4 hours** before bedtime.
- Light exercise (yoga, walk, stretching): acceptable within 1–2 hours of bedtime.
- **Evidence (Leota et al. 2025, Nature Comm, n≈15,000):** Maximal exercise ending 2h before habitual sleep onset → 36-minute delay in sleep onset, 22-minute shorter total sleep, 14% lower HRV. Exercise ending ≥6h before sleep: no measurable negative impact. Source: [Nature Communications 2025](https://www.nature.com/articles/s41467-025-58271-x)

```
EXERCISE_CUTOFF_HOURS_BEFORE_BED = 4      // high-strain
EXERCISE_CUTOFF_HOURS_BEFORE_BED_LIGHT = 1 // light strain
EXERCISE_TIMING_WARNING = if (exercise_end_time > (bedtime - 4h) AND strain = "high")
```

### 10.5 Phased Implementation Protocol

**Phase 1 — Foundation (Weeks 1–2): Pick 2 habits**
- Focus: Consistent wake time + caffeine cutoff
- Trigger: New user onboarding OR user reports poor sleep for 3+ consecutive days

**Phase 2 — Light Hygiene (Weeks 3–4): Add 1–2 habits**
- Add: Morning sunlight + dim lights after 9 PM
- Trigger: Phase 1 habits confirmed at ≥70% compliance over 7 days

**Phase 3 — Environment (Weeks 5–6): Add 1–2 habits**
- Add: Bedroom temperature + consistent bedtime (+ optional warm shower)
- Trigger: Phase 2 habits confirmed at ≥70% compliance over 7 days

**Phase 4 — Exercise Timing Refinement (Weeks 7–8)**
- Exercise timing check via Whoop data + alcohol awareness
- Trigger: Whoop data shows ≥2 nights/week elevated nocturnal HR and reduced HRV correlated with late workouts

**Phase 5 — Supplements (Weeks 9+)**
- Add: Magnesium threonate/bisglycinate → L-Theanine → Apigenin (in order)
- Trigger: Whoop sleep score <70 despite behavioral habits optimized; user explicitly interested in supplements

```python
def sleep_coaching_decision(user_data):
    if user_data["avg_sleep_hours"] < 6.0:
        return "URGENT: insufficient sleep — duration intervention BEFORE anything else"
    if user_data["wake_time_sd_7day"] > 60:   # minutes
        return "PHASE_1: wake_time_consistency"
    if user_data["last_caffeine_hours_before_bed"] < 8:
        return "PHASE_1: caffeine_cutoff"
    if user_data["morning_light_compliance_7day"] < 0.5:
        return "PHASE_2: morning_sunlight"
    if user_data["evening_light_compliance"] < 0.5:
        return "PHASE_2: evening_light_reduction"
    if user_data["bedroom_temp"] > 22:  # Celsius
        return "PHASE_3: bedroom_temperature"
    if user_data["bedtime_sd_7day"] > 60:
        return "PHASE_3: bedtime_consistency"
    if user_data["late_exercise_nights_per_week"] >= 2:
        return "PHASE_4: exercise_timing"
    if user_data["sleep_score_avg_14day"] < 70 and behavioral_habits_optimized:
        return "PHASE_5: supplement_protocol"
    return "reinforce_existing_habits"
```

**Habit introduction rules:**
- Introduce new habit IF: current habit has ≥70% compliance for 7 days AND sleep score improved ≥5 points over 2 weeks
- Reinforce existing habit IF: compliance <70% OR sleep score flat/declining
- **NEVER add more than 1 new habit per 2-week window** (Gollwitzer 1999: habit stacking beyond 2–3 concurrent habits dramatically reduces compliance)

### 10.6 Sleep Hygiene Scoring System

Daily Sleep Hygiene Checklist (0–10 Score):

| # | Habit | Input Type | Points |
|---|-------|-----------|--------|
| 1 | Wake time within 30 min of target | `wake_time_deviation < 30min` | 2 |
| 2 | Morning sunlight ≥10 min within 60 min of wake | `morning_light = true` | 1.5 |
| 3 | Last caffeine ≥10h before bedtime | `caffeine_cutoff_met = true` | 1.5 |
| 4 | No alcohol within 3h of bedtime | `alcohol_cutoff_met = true` | 1 |
| 5 | Dim/warm lights after 9 PM | `evening_light_reduced = true` | 0.5 |
| 6 | No high-intensity exercise within 4h of bed | `exercise_cutoff_met = true` | 0.5 |
| 7 | Bedroom ≤20°C (68°F) at sleep onset | `bedroom_temp_ok = true` | 0.5 |
| 8 | Bedtime within 30 min of target | `bedtime_deviation < 30min` | 0.5 |
| 9 | Total sleep ≥7.5h | `sleep_hours >= 7.5` | 2 |
| BONUS | Pre-sleep protein (training day) | `pre_sleep_protein = true` | 0.5 |

```
SLEEP_SCORE = sum(points for completed habits)
SLEEP_SCORE_GRADE = {
    9–10: "Excellent",
    7–8.9: "Good",
    5–6.9: "Moderate — 1–2 habits to improve",
    <5: "Needs attention — prioritize foundation habits"
}
WEEKLY_SLEEP_SCORE = avg(daily_sleep_scores, last_7_days)
```

### 10.7 Whoop Integration for Sleep Coaching

| Metric | Whoop Variable | Relevant Threshold | What It Signals |
|--------|---------------|-------------------|-----------------| 
| Sleep Performance % | `sleep_performance_pct` | <70% = poor | Total sleep vs. needed |
| Time in SWS | `sws_minutes` | <60 min = low | GH secretion window |
| Time in REM | `rem_minutes` | <90 min = low | Memory, hormone regulation |
| Sleep Consistency | `sleep_consistency_score` | <70% = irregular | Circadian stability |
| Nocturnal HRV | `hrv_ms` | trend decline = stress | CNS recovery status |
| Nocturnal RHR | `rhr_bpm` | elevated vs. baseline | Sympathetic load |
| Sleep Latency | `sleep_latency_min` | >30 min = problematic | Arousal/caffeine/stress |
| Recovery Score | `recovery_score_pct` | <33% = red | Systemic readiness |
| 7-Day HRV trend | `hrv_7d_trend` | declining = overreach | Cumulative fatigue |

```python
WHOOP_TRIGGERS = {
    "chronic_insufficient_sleep": {
        "condition": "avg_sleep_hours_7d < 6.5",
        "priority": "CRITICAL",
        "action": "pause_new_habits; reinforce_duration_only"
    },
    "late_workout_HRV_impact": {
        "condition": "exercise_end_time > (sleep_onset - 4h) AND hrv_that_night < (baseline_hrv * 0.85)",
        "priority": "HIGH",
        "action": "send_exercise_timing_coaching"
    },
    "low_sws": {
        "condition": "sws_minutes_7d_avg < 50 AND sleep_duration_adequate",
        "priority": "MEDIUM",
        "action": "check_alcohol/caffeine/temperature; consider_supplement_phase"
    },
    "inconsistent_wake_time": {
        "condition": "wake_time_sd_7d > 45",   # minutes
        "priority": "HIGH",
        "action": "consistency_coaching"
    },
    "high_latency": {
        "condition": "sleep_latency_avg_7d > 25",   # minutes
        "priority": "MEDIUM",
        "action": "check_caffeine_cutoff; check_evening_light; check_stress"
    },
    "red_recovery_consecutive": {
        "condition": "recovery_score < 33 for 3+ consecutive days",
        "priority": "HIGH",
        "action": "reduce_training_volume; prioritize_sleep_over_workouts"
    }
}
```

### 10.8 Supplement Protocols

#### Magnesium Threonate or Bisglycinate
- **Dose:** 300–400 mg elemental magnesium, 30–60 min before bed
- **Evidence:** RCT (Hausenblas et al. 2024, Sleep Medicine: X, [PMC11381753](https://pmc.ncbi.nlm.nih.gov/articles/PMC11381753/)): 1g MgT/day for 21 days improved deep sleep score, REM sleep score, readiness score vs. placebo (p<0.001). Effects continued improving through 3 weeks.
- **Mechanism:** Natural NMDA receptor antagonist and GABA agonist. Threonate form crosses the blood-brain barrier efficiently. Increases GABAergic activity, serotonergic receptor expression, and melatonin levels.
- **Safety:** Generally safe. Very high doses may cause loose stools (use bisglycinate if GI issues).

#### L-Theanine
- **Dose:** 100–200 mg, 30–60 min before bed
- **Evidence:** Increases GABAergic and serotonergic receptor expression, reduces sleep latency, increases delta brain activity. [Frontiers in Nutrition 2022, PMC9017334](https://pmc.ncbi.nlm.nih.gov/articles/PMC9017334/)
- **Mechanism:** Promotes alpha brain wave activity (relaxed alertness); reduces excitatory glutamate activity; increases inhibitory GABA.
- **Best for:** Users who report difficulty winding down mentally; racing thoughts at bedtime.

#### Apigenin
- **Dose:** 50 mg (standardized chamomile extract or pure apigenin), 30–60 min before bed
- **Evidence:** Systematic review of 10 clinical trials: 9/10 concluded chamomile (primary apigenin source) effective in reducing anxiety. Source: [Clinical Nutrition Research 2024](https://e-cnr.org/DOIx.php?id=10.7762%2Fcnr.2024.13.2.139)
- **Mechanism:** Partial agonist at GABA-A receptors; anxiolytic effect reduces arousal that delays sleep onset.
- **Cautions:** Avoid if allergic to ragweed. Avoid combining with prescription sedatives or blood thinners without medical guidance. Avoid during pregnancy.
- **Priority note:** Introduce only after behavioral interventions (Phases 1–4) are established.

#### Pre-Sleep Protein (Synergistic)
- **Dose:** 30–40g casein protein, 30–60 min before bed (training days)
- **Evidence:** 40g casein before sleep increases overnight myofibrillar protein synthesis by 22–37% vs. placebo. Source: [van Loon lab, GSSI 2022](https://www.gssiweb.org/research/article/resistance-exercise-augments-postprandial-overnight-muscle-protein-synthesis-rates)
- **Rule:** At least 40g needed for robust overnight MPS effect.
```
PRE_SLEEP_PROTEIN_TRIGGER = (training_day = true AND protein_goal_met_before_dinner = false)
PRE_SLEEP_PROTEIN_DOSE = 30–40g casein or slow-digesting protein
TIMING = 30–60 min before bed
```

### 10.9 Telegram Templates for Sleep Coaching

#### Onboarding — Sleep Priority Introduction
```
"Before we dive into training, I want to talk about something that most people overlook — sleep.

Here's why it matters for your gains: one night of poor sleep reduces muscle protein synthesis by 18%. And sleeping just 5 hours instead of 7.5 hours can cut your fat loss by more than half, while simultaneously causing you to lose muscle instead.

Sleep isn't recovery time. It's when growth actually happens.

We're going to track two simple things this week:
1. Your wake time (same time every morning, even weekends)
2. Your last caffeine of the day

What time do you usually wake up? And what time do you usually have your last coffee or energy drink?"
```

#### Red Alert — Insufficient Sleep During Cut
```
"⚠️ I need to flag something important.

You're in a caloric deficit right now — and your sleep has been averaging [X] hours this week.

Here's the problem: a study in the Annals of Internal Medicine found that sleeping 5.5 hours instead of 8.5 hours during a diet cut your fat loss by 55% and increased the amount of muscle you lost by 60%.

Right now, your sleep is working against your cut. It's not a minor issue — it's potentially the biggest factor limiting your results.

For this week, I'd like to prioritize sleep above everything else. Let's troubleshoot what's cutting your sleep short.

Is it: (1) going to bed too late, (2) waking up too early, (3) waking up in the night, or (4) just not enough hours in the day?"
```

#### Weekly Sleep Check-In
```
"Quick sleep check-in for the week —

[INSERT WHOOP DATA IF AVAILABLE]:
- Average sleep: X hours
- Recovery avg: X%
- Sleep consistency: X%

Based on this, here's what's working and what to focus on:
✅ [HABITS COMPLETED ≥5/7 DAYS]
⚠️ [HABITS BELOW 70% COMPLIANCE]

One focus for this week: [SINGLE HABIT TO REINFORCE OR ADD]

Anything that made it harder to sleep this week? Travel, stress, late workouts?"
```

### 10.10 Sleep Variables Dictionary (Backend)

```python
# === SLEEP TRACKING VARIABLES ===
wake_time                    # HH:MM string
wake_time_target             # HH:MM string (user-set)
wake_time_deviation_min      # abs(wake_time - wake_time_target) in minutes
wake_time_sd_7d              # SD of wake times over 7 days (minutes)
bedtime                      # HH:MM string
bedtime_target               # HH:MM string
bedtime_deviation_min        # abs(bedtime - bedtime_target) in minutes
bedtime_sd_7d                # SD of bedtimes over 7 days
sleep_onset                  # HH:MM (when user actually fell asleep per Whoop)
sleep_duration_hours         # float
sleep_performance_pct        # Whoop metric: 0–100
sws_minutes                  # minutes in slow-wave sleep
rem_minutes                  # minutes in REM
sleep_latency_min            # minutes to fall asleep
hrv_ms                       # nightly HRV (ms)
hrv_7d_avg                   # 7-day rolling average HRV
hrv_baseline                 # established during first 14 days onboarding
rhr_bpm                      # nocturnal resting heart rate
recovery_score_pct           # Whoop recovery score: 0–100

# === HABITS TRACKING VARIABLES ===
morning_light_done           # bool
morning_light_minutes        # int
morning_light_timing_min     # minutes after wake
caffeine_last_time           # HH:MM
caffeine_last_hours_before_bed   # float
caffeine_cutoff_met          # bool
evening_lights_dimmed        # bool (after 21:00)
bedroom_temp_celsius         # float
exercise_end_time            # HH:MM
exercise_strain              # enum: light/moderate/high/maximal
exercise_cutoff_met          # bool
alcohol_last_drink_hours_before_bed  # float
pre_sleep_protein_done       # bool (training days only)
warm_shower_timing_min       # minutes before bed (if taken)

# === SUPPLEMENT VARIABLES ===
magnesium_taken              # bool
theanine_taken               # bool
apigenin_taken               # bool
supplement_phase_active      # enum: none/magnesium/theanine/apigenin/combo

# === COACHING STATE VARIABLES ===
active_habit_phase           # int: 1–5
habits_in_phase              # list of habit identifiers
habit_compliance_7d          # dict: {habit_id: compliance_rate (0-1)}
last_new_habit_introduced    # date
days_since_last_new_habit    # int
sleep_hygiene_score          # float: 0–10 (daily)
sleep_hygiene_score_7d_avg   # float
user_in_caloric_deficit      # bool (HIGH importance multiplier)
user_training_phase          # enum: bulk/cut/maintain/recomp
```

---

## PART 11: COACHING COMMUNICATION FRAMEWORK

*Sources: Track 4, Track 5, Track 6*

### 11.1 Self-Determination Theory (SDT) Foundation

SDT posits that sustainable health behavior change requires three basic psychological needs:
1. **Autonomy** — feeling in control; not coerced
2. **Competence** — feeling effective at producing desired outcomes
3. **Relatedness** — feeling accepted and supported

**Evidence:** Meta-analysis of 65 RCTs on SDT interventions:
- Sample-weighted average effect size: d = 0.23 (significant)
- Autonomous motivation and perceived competence fully *mediated* the effect on behavior change
- Overweight samples showed larger effects (d up to ~0.5)
- Autonomy support is the critical delivery variable — neither intervention setting, intensity, nor source moderated effectiveness
- Source: [Sheeran et al., Health Psychology 2020](https://selfdeterminationtheory.org/wp-content/uploads/2020/11/2020_SheeranWrightEtAl_SDTInterventions.pdf)

**Clinical applications:**
- Autonomy support predicts weight loss maintenance up to 3 years
- Permissive flexibility predicts long-term exercise adherence — 65% increase in physical activity participation maintained 10 months post-program. Source: [Mayo Clinic Proceedings 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11130595/)

### 11.2 Autonomy-Supportive Language Principles

| Context | Controlling (AVOID) | Autonomy-Supportive (USE) |
|---|---|---|
| Instruction | "You need to eat more protein" | "It might be worth trying to add some protein to this meal" |
| Course correction | "You're not following the plan" | "Your weight has been trending up — let's see what adjustments might help" |
| Success | "Good job hitting the rules" | "You've been consistent — that's entirely because of what you've been doing" |
| Setback | "You failed this week" | "That's useful data — let's think about what got in the way" |
| Food choice | "Don't eat that" | "That's totally fine — what did you have with it for protein?" |
| Escalation | "You need to track your food" | "Some people find that adding a bit more structure helps at this point — would you want to try that for a couple of weeks?" |

**Core principle:** Frame all guidance as information about what *might help*, not rules the user is *obligated* to follow.

### 11.3 Nocebo Avoidance Design Principles

Based on evidence from Track 4 (Gavriloff 2018, orthosomnia research, wearable anxiety studies):

1. **Trend-based, never single-day** — only surface recovery signals when a 3+ day trend is established
2. **Action-forward framing** — always tell the user what to *do*, not what is *wrong*
3. **Positive default** — most days, users receive an affirmative "ready to train" message
4. **Suppress suppression language** — replace "low recovery" with "your body is working on adapting"
5. **No alarming colors or absolute scores** — avoid red warning language unless truly warranted; never show raw scores (e.g., "your HRV is 42ms" or "recovery score: 38/100")
6. **Contextual attribution** — when flagging, offer benign explanations ("high training load this week," "travel/time zone adjustment")
7. **Silent by default** — only send a Telegram message if there is an actionable recommendation; do not message on normal-green days unless user requests daily check-in

**Evidence:** Gavriloff 2018 — false negative sleep feedback (telling people they slept poorly when they didn't) decreased alertness, increased sleepiness, impaired cognitive performance — caused by feedback alone, not actual sleep quality. Source: [Journal of Sleep Research, via Dr. James Hewitt](https://drjameshewitt.com/can-sleep-tracking-be-bad-for-your-performance/)

### 11.4 Positive Framing Strategies

**Gain-framing vs. loss-framing:**
- Gain-framed messages are more effective for promoting preventive health behaviors
- Frame as *adding positive things* (more protein, more vegetables) rather than *removing negatives* (eat less junk)
- Source: [USDA/FNS message framing literature review](https://fns-prod.azureedge.us/sites/default/files/LitReview_Framing.pdf)

**Identity-based framing:**
- Anchor feedback to the user's identity as a committed athlete, not to failure metrics
- "You're building the habit, which is the hardest part — that's already working."
- "You've been consistent — that's entirely because of what you've been doing."

**Data-forward message architecture (for AL mode check-ins):**
```
TELEGRAM_MESSAGE_TEMPLATE:
  [1] Observation (data only, no judgment): "Your weight is up about 1.5 lbs over the last 2 weeks."
  [2] Context (normalize): "That's within the normal range of fluctuation, especially early on."
  [3] Curiosity (open question): "How did your eating feel this week — any sense of where it might have drifted?"
  [4] One small suggestion (not a mandate): "One thing that tends to help is making sure there's protein on the plate at every meal — did that happen most of the time?"
  [5] Affirm forward momentum: "You're building the habit, which is the hardest part — that's already working."
```

### 11.5 Anti-Pattern Phrases to Avoid

```
❌ "Your recovery score is red today."
❌ "WARNING: HRV is significantly below baseline."
❌ "You are under-recovered."
❌ "Your sleep was poor last night."
❌ "You should not train today."
❌ "Your body battery is critically low."
❌ "You need to eat more protein."
❌ "You're not following the plan."
❌ "You failed this week."
❌ "Don't eat that."
❌ "Your weight has been going up consistently. You need to be more careful."
```

### 11.6 Telegram Templates for Common Scenarios

#### Recovery — YELLOW (Day 3 of sustained decline)
```
"Your body's working through a heavier adaptation period this week — that's a normal part of building fitness.

Today I'd suggest keeping the session a bit lighter: [modified session description — 20-30% intensity reduction].

Nothing to worry about — just let your system catch up. A bit more sleep tonight would also go a long way. 🙌"
```

#### Recovery — RED (First trigger)
```
"Your body's been sending consistent signals that it needs a recovery focus right now — this happens to every athlete, especially after periods of hard work.

Today's recommendation: skip the structured session and do something restorative instead — a 20-30 min walk, light stretching, or just rest.

This isn't a setback. Recovery IS training. How are you feeling overall this week?"
```

#### Nutrition — Weight Trending Wrong Direction
```
"Looking at your data from the last two weeks, your weight has been drifting up a bit — about [X] lbs. That's useful to know, not a problem.

A few things that tend to help in this situation:
- Making sure most of your plate is protein + vegetables at each meal
- Avoiding too much snacking on higher-calorie processed foods

What does your typical day of eating look like right now? I'd love to hear what's been working and what might be worth adjusting."
```

#### Nutrition — Lifts Not Progressing
```
"I noticed your [squat/bench] numbers have been about the same the last few sessions — that can sometimes be a signal to give nutrition a second look.

It's often worth checking:
1. Are you getting protein at every meal?
2. Are you eating enough total food to feel energized for training?

How's your energy been feeling going into workouts lately?"
```

#### Nutrition — User Reports Hunger/Cravings
```
"Feeling hungrier than usual can actually be a sign your body is working — it's adjusting. That said, strategic protein intake can make a real difference.

When you feel hungry, the first question is: when did you last eat something with protein? If it's been more than 3–4 hours, your body is likely just asking for amino acids — a Greek yogurt, some cottage cheese, or a few eggs usually handles it pretty well.

How does that track with what's been happening for you?"
```

#### Escalation to Tracked Mode (Soft)
```
"Your data has been a bit mixed for a couple weeks. That's not a failure — it just means we need a bit more information. One thing that often helps: tracking just your protein intake for a week. No calorie counting, no macro targets — just protein. It usually takes about 2 minutes a day and gives us a lot of clarity. Want to try it?"
```

#### Escalation to Tracked Mode (Strong)
```
"Looking at your last month of data, I think getting clearer numbers for a couple weeks would really help us figure out what's going on.

I'm suggesting we try a 2-week tracked phase — I'll set up a calorie target and protein goal in the app, and you log everything for 14 days. This isn't a permanent shift; it's just a diagnostic tool to figure out where things are landing. After that, we can go right back to the approach you prefer.

Would you be open to trying that?"
```

#### Weekly Protein/Nutrition Nudges (Rotate)
```
PROTEIN_REMINDER: "Quick mid-week nudge — are you getting protein at most meals? A palm-sized serving at breakfast makes the rest of the day way easier for hitting your intake. How's it going?"

FOOD_QUALITY: "One easy win this week: swap one processed snack for something whole — cheese, a hard-boiled egg, some fruit with Greek yogurt. Small swaps add up fast."

HYDRATION: "If energy feels low during training, check your hydration first — aim for pale yellow urine. Sometimes it's that simple."

PERFORMANCE: "How did training feel this week? Progress on your main lifts is one of the best signs your nutrition is doing its job."
```

#### Sleep Coaching — Habit Follow-Up
```
"How's the [HABIT_NAME] going?

A quick reminder of why it matters: [1-sentence evidence rationale].

If you're struggling with it, tell me the specific barrier — I can usually find a workaround.

Remember, consistency beats perfection. 5 out of 7 days is genuinely meaningful. We're not going for zero-to-perfect, we're building a system."
```

### 11.7 Communication Frequency and Format Rules

```
# Recovery communications
LEVEL 0 (default):    Only send Telegram messages on YELLOW/RED triggers
LEVEL 1 (opt-in):     Daily green confirmation + workout summary
LEVEL 2 (opt-in):     Weekly trend summary (no daily scores, only trend narrative)
NEVER available:      Raw metric dashboard, daily recovery score

# Nutrition (AL mode)
CHECKIN_FREQUENCY = biweekly    // Every 2 weeks for progress review
NUDGE_FREQUENCY = weekly        // Light weekly behavioral prompts
EMERGENCY_TRIGGER = weight_trend_unfavorable_for_2_weeks

# General format
MESSAGE_LENGTH_TARGET = 3–5 sentences (mobile-friendly)
TONE: Warm, curious, non-preachy, data-referencing
AVOID: Lecturing, long lists of rules, negative framing, mandatory language
```

---

## APPENDIX A: MASTER VARIABLE DICTIONARY

All named variables across all tracks, consolidated for backend reference:

### A.1 User Profile Variables

| Variable Name | Data Type | Units | Default | Source Section |
|---|---|---|---|---|
| `user_id` | str | — | — | Onboarding |
| `body_weight_lbs` | float | lbs | — | Onboarding (T1,T7) |
| `body_weight_kg` | float | kg | — | Derived: `lbs / 2.2046` |
| `height_cm` | float | cm | — | Onboarding (T1) |
| `height_inches` | float | inches | — | Onboarding (T7) |
| `age_yr` | int | years | — | Onboarding (T1) |
| `body_fat_pct` | float | % | None | Optional onboarding (T1,T7) |
| `LBM_kg` | float | kg | Computed | `weight_kg × (1 − BF%)` |
| `sex` | str | — | "male" | Onboarding (T1) |
| `training_age_months` | int | months | 0 | Onboarding (T3,T7) |
| `experience_level` | enum | — | BEGINNER | T2,T3 |
| `goal` | enum | — | — | Onboarding (T7) |
| `injuries` | list[str] | — | [] | Onboarding |
| `frequency_preference` | int | days/week | 3 | Onboarding (T8) |
| `equipment_access` | list[str] | — | ["barbell","dumbbells","cables"] | Onboarding |
| `emphasis_mode` | enum | — | BALANCED | T2,T8 |
| `nutrition_mode` | enum | — | TRACKED | Onboarding (T5) |
| `bmi` | float | kg/m² | Computed | T7 |

### A.2 TDEE and Calorie Variables

| Variable Name | Data Type | Units | Default | Source Section |
|---|---|---|---|---|
| `BMR` | float | kcal/day | Computed | T1 §1 |
| `BMR_mifflin` | float | kcal/day | Computed | T1 §1.2.1 |
| `BMR_katch` | float | kcal/day | Computed | T1 §1.2.3 |
| `RMR_cunningham` | float | kcal/day | Computed | T1 §1.2.4 |
| `BMR_hb_male` | float | kcal/day | Computed | T1 §1.2.2 |
| `activity_multiplier` | float | — | 1.55 | T1 §1.4 |
| `TDEE_estimated` | float | kcal/day | Computed | T1 §1.4 |
| `adaptive_TDEE` | float | kcal/day | None (until 2 wks) | T1 §2.3 |
| `working_TDEE` | float | kcal/day | Computed | T1 §2.4 |
| `target_calories` | int | kcal/day | Computed | T1 §3 |
| `KCAL_PER_KG_TISSUE` | int | kcal/kg | 7700 | T1 §2.3 |
| `weight_delta_kg` | float | kg | Computed | T1 §2.2 |
| `rate_pct_per_week` | float | %/week | Computed | T1 §2.2 |
| `consecutive_stall_cycles` | int | cycles | 0 | T1 §3.3 |
| `weeks_in_deficit` | int | weeks | 0 | T1 §4.4 |
| `cumulative_weight_loss_pct` | float | % | 0 | T1 §4 |
| `weeks_of_data` | int | weeks | 0 | T1 §2.4 |
| `avg_daily_calories` | float | kcal/day | — | T1 §2.3 |
| `equation_used` | str | — | — | T1 §1.4 |
| `calorie_logging_completeness` | float | 0–1 | — | T1 §6 |

### A.3 Protein and Nutrition Variables

| Variable Name | Data Type | Units | Default | Source Section |
|---|---|---|---|---|
| `PROTEIN_RATE_G_PER_LB` | float | g/lb | 0.82 | T7 §2.1 |
| `protein_target_g` | float | g/day | Computed | T7 §2 |
| `per_meal_protein_min_g_per_kg` | float | g/kg | 0.40 | T7 §1.4 |
| `per_meal_protein_max_g_per_kg` | float | g/kg | 0.55 | T7 §1.4 |
| `min_meals_per_day` | int | — | 3 | T7 §1.4 |
| `optimal_meals_per_day` | int | — | 4 | T7 §1.4 |
| `ibw_kg` | float | kg | Computed | T7 §2.2 |
| `ajbw_kg` | float | kg | Computed | T7 §2.2 |
| `adjusted_body_weight_for_protein` | float | lbs | Computed | T7 §2.2 |
| `current_phase` | enum | — | — | T7 §3 |
| `phase_start_date` | date | — | — | T7 §4.1 |
| `phase_duration_weeks` | int | weeks | 0 | T7 §4 |
| `goal_weight_lbs` | float | lbs | — | T7 §4.1 |
| `goal_body_fat_pct` | float | % | — | T7 §4.1 |
| `weekly_weight_change_lbs` | float | lbs/week | Computed | T7 §4.1 |
| `training_performance_score` | int | 1–5 | — | T7 §4.1 |
| `fatigue_level_score` | int | 1–5 | — | T7 §4.1 |
| `hunger_level_score` | int | 1–5 | — | T7 §4.1 |
| `adherence_score` | int | 1–5 | — | T7 §4.1 |
| `BIWEEKLY_CALORIE_ADJUSTMENT_KCAL` | int | kcal | 150 | T7 §4.6 |

### A.4 Ad Libitum Mode Variables

| Variable Name | Data Type | Units | Default | Source Section |
|---|---|---|---|---|
| `weight_trend_2wk` | enum | — | — | T5 §4.2 |
| `weight_trend_rate_lbs_per_week` | float | lbs/week | — | T5 §4.2 |
| `fat_mass_trend` | enum | — | — | T5 §4.3 |
| `ffm_trend` | enum | — | — | T5 §4.3 |
| `lift_performance_trend` | enum | — | — | T5 §4.4 |
| `avg_hunger_1_10` | float | 1–10 | — | T5 §4.5 |
| `avg_energy_1_10` | float | 1–10 | — | T5 §4.5 |
| `escalation_triggers_active` | list[str] | — | [] | T5 §6 |
| `weeks_in_al_mode` | int | weeks | 0 | T5 §6 |
| `protein_at_every_meal` | bool | — | — | T5 §7 |
| `food_quality_80_20` | bool | — | — | T5 §7 |
| `plate_composition_followed` | bool | — | — | T5 §7 |
| `MEAL_FREQUENCY_DEFAULT` | int | — | 3 | T5 §RULE05 |
| `AL_COMPOSITE_SCORE` | int | — | Computed | T5 §4.6 |

### A.5 Training Volume Variables

| Variable Name | Data Type | Units | Default | Source Section |
|---|---|---|---|---|
| `MV` | Dict[str, int] | sets/week | See table | T2 §1.2 |
| `MEV` | Dict[str, int] | sets/week | See table | T2 §1.2 |
| `MAV` | Dict[str, tuple] | sets/week | See table | T2 §1.2 |
| `MRV` | Dict[str, int] | sets/week | See table | T2 §1.2 |
| `volume_targets` | Dict[str, int] | sets/week | Computed | T2,T8 §4 |
| `volume_multiplier` | float | 0.6–1.5 | 1.0 | T8 §4.2 |
| `mesocycle_week` | int | 1-indexed | 1 | T2,T3 |
| `meso_length` | int | weeks | 4 | T2 §5.2 |
| `accumulation_weeks` | int | weeks | 4 | T2 §5.1 |
| `sets_per_week_increase` | float | sets | 2.0 | T2 §5.4 |
| `total_weekly_set_cap` | int | sets | 130 | T2 §3.4 |
| `SYSTEMIC_FATIGUE_CAP` | Dict | sets | varies | T8 §4.3 |

### A.6 RIR and Performance Variables

| Variable Name | Data Type | Units | Default | Source Section |
|---|---|---|---|---|
| `rir_reported` | int | 0–10 | — | T3 §1.1 |
| `rir_adjusted` | int | 0–10 | Computed | T3 §1.5 |
| `rpe_reported` | float | 1–10 | — | T3 §1.1 |
| `rir_target_min` | int | 0–5 | — | T3 §1.3 |
| `rir_target_max` | int | 0–6 | — | T3 §1.3 |
| `rir_floor` | int | 0–3 | — | T3 §1.4 |
| `load_kg` | float | kg | — | T3 §2.1 |
| `reps_completed` | int | 1–30 | — | T3 §2.1 |
| `e1rm` | float | kg | Computed | T3 §2.2 |
| `e1rm_rir_adjusted` | float | kg | Computed | T3 §2.2 |
| `session_e1rm` | float | kg | Computed | T3 §2.2 |
| `rolling_e1rm_7d` | float | kg | Computed | T3 §2.1 |
| `rolling_e1rm_28d` | float | kg | Computed | T3 §2.1 |
| `e1rm_pct_change` | float | -1 to +1 | Computed | T3 §2.3 |
| `consecutive_decline_ct` | int | sessions | 0 | T3 §2.4 |
| `consecutive_stagnation_ct` | int | sessions | 0 | T3 §3.2 |
| `consecutive_rir_misses` | int | sessions | 0 | T3 §3.2 |
| `consecutive_poor_motivation_ct` | int | sessions | 0 | T3 §3.2 |
| `joint_pain_reported` | bool | — | false | T3 §3.2 |
| `BEGINNER_RIR_CORRECTION` | int | — | +1 | T3 §1.5 |
| `exercise_type` | enum | — | — | T3 §1.4 |
| `deload_active` | bool | — | false | T3 §4.2 |
| `deload_trigger_reason` | str | — | — | T3 §3.3 |
| `fatigue_type` | enum | — | — | T3 §2.5 |
| `recovery_needs` | enum | — | — | T3 §4.3 |
| `post_deload_flag` | bool | — | false | T3 §5.2 |
| `post_deload_days` | int | 0–14 | 0 | T3 §5.2 |

### A.7 Recovery (HRV/RHR/Sleep) Variables

| Variable Name | Data Type | Units | Default | Source Section |
|---|---|---|---|---|
| `hrv_raw` | float | ms | — | T4 §1.3 |
| `hrv_ln` | float | ln(ms) | Computed | T4 §1.3 |
| `hrv_7d_avg` | float | ln(ms) | Computed | T4 §1.4 |
| `hrv_7d_sd` | float | ln(ms) | Computed | T4 §1.5 |
| `hrv_7d_cv` | float | % | Computed | T4 §1.5 |
| `hrv_30d_mean` | float | ln(ms) | Computed | T4 §1.4 |
| `hrv_30d_sd` | float | ln(ms) | Computed | T4 §1.4 |
| `hrv_z_score` | float | — | Computed | T4 §1.6 |
| `hrv_normal_lower` | float | ln(ms) | Computed | T4 §1.6 |
| `hrv_normal_upper` | float | ln(ms) | Computed | T4 §1.6 |
| `hrv_status` | str | — | — | T4 §1.7 |
| `rhr_daily` | float | bpm | — | T4 §2.2 |
| `rhr_7d_avg` | float | bpm | Computed | T4 §2.4 |
| `rhr_30d_mean` | float | bpm | Computed | T4 §2.3 |
| `rhr_30d_sd` | float | bpm | Computed | T4 §2.3 |
| `rhr_delta_bpm` | float | bpm | Computed | T4 §2.4 |
| `rhr_z_score` | float | — | Computed | T4 §2.4 |
| `rhr_status` | str | — | — | T4 §2.5 |
| `sleep_duration_hrs` | float | hours | — | T4 §3.2 |
| `sleep_efficiency_pct` | float | % | — | T4 §3.2 |
| `sleep_perf_score` | float | 0–100 | — | T4 §3.2 |
| `sleep_7d_avg_hrs` | float | hours | Computed | T4 §3.5 |
| `sleep_7d_avg_eff` | float | % | Computed | T4 §3.5 |
| `sleep_score_30d_mean` | float | 0–100 | Computed | T4 §5.2 |
| `sleep_score_30d_sd` | float | 0–100 | Computed | T4 §5.2 |
| `sleep_status` | str | — | — | T4 §3.6 |
| `spo2_avg` | float | % | — | T4 §3.2 |
| `composite_score` | float | 0–100 | Computed | T4 §5.2 |
| `composite_score_final` | float | 0–100 | Computed | T4 §5.2 |
| `composite_tier` | str | — | — | T4 §5.4 |
| `tier_history` | list[str] | — | [] | T4 §6.2 |
| `days_baseline` | int | days | 0 | T4 §9.1 |
| `baseline_ready` | bool | — | false | T4 §9.1 |
| `hrv_suppressed_days` | int | days | 0 | T3 §3.2 |
| `sleep_debt_days` | int | days | 0 | T3 §3.2 |

### A.8 Programming Variables

| Variable Name | Data Type | Units | Default | Source Section |
|---|---|---|---|---|
| `training_days_per_week` | int | 2–6 | 3 | T8 §5.1 |
| `session_label` | str | "A","B","C" | — | T8 §5.2 |
| `MINIMUM_FREQUENCY_PER_MUSCLE_PER_WEEK` | int | — | 2 | T8 §1.1 |
| `rep_range` | str | — | "8–12" | T8 §5.5 |
| `rest_period` | Dict[str,int] | seconds | varies | T8 §5.6 |
| `session_volume_cap` | Dict[int,int] | sets | varies | T8 §5.3 |
| `frequency_per_muscle` | int | 1–3 | 2 | T8 §1.2 |
| `exercise_category` | enum | — | — | T8 §3.1 |
| `priority_muscles` | list[str] | — | [] | T8 §5.1 |

---

## APPENDIX B: MASTER CONSTANTS & THRESHOLDS

### B.1 TDEE and Calorie Constants

```python
# BMR Equations
MIFFLIN_ST_JEOR_MALE_CONST = 5        # +5 for males
CUNNINGHAM_CONST = 500                 # constant term
CUNNINGHAM_COEFF = 22                  # per kg LBM
KATCH_MCCARDLE_CONST = 370            # constant term
KATCH_MCCARDLE_COEFF = 21.6           # per kg LBM
HB_ROZA_MALE_CONST = 88.362
HB_ROZA_MALE_WEIGHT_COEFF = 13.397
HB_ROZA_MALE_HEIGHT_COEFF = 4.799
HB_ROZA_MALE_AGE_COEFF = 5.677

# Activity Multipliers
ACTIVITY_MULTIPLIER_SEDENTARY = 1.2
ACTIVITY_MULTIPLIER_LIGHTLY_ACTIVE = 1.375
ACTIVITY_MULTIPLIER_MODERATELY_ACTIVE = 1.55   # Default for Milo
ACTIVITY_MULTIPLIER_VERY_ACTIVE = 1.725
ACTIVITY_MULTIPLIER_EXTREMELY_ACTIVE = 1.9

# TDEE Calibration Blending
BLEND_LOW_CONFIDENCE = {"adaptive": 0.30, "equation": 0.70}    # 2–3 weeks data
BLEND_MODERATE_CONFIDENCE = {"adaptive": 0.60, "equation": 0.40}  # 3–5 weeks data
BLEND_HIGH_CONFIDENCE = {"adaptive": 0.85, "equation": 0.15}     # 5+ weeks data

# Calorie Floors and Ceilings
CALORIE_FLOOR_MALE = 1500             # kcal/day
CALORIE_FLOOR_ABSOLUTE = 1200         # never go below
MAX_DEFICIT_PCT_OF_TDEE = 0.25        # 25% below TDEE
MAX_SURPLUS_KCAL = 600                # kcal/day above TDEE

# Energy Constants
KCAL_PER_KG_TISSUE = 7700            # mixed tissue energy content

# Biweekly Adjustment Amounts
CUTTING_STALLED_ADJUSTMENT = -200    # kcal
CUTTING_TOO_SLOW_ADJUSTMENT = -100   # kcal
CUTTING_TOO_FAST_ADJUSTMENT = +150   # kcal
BULKING_TOO_SLOW_ADJUSTMENT = +200   # kcal
BULKING_TOO_FAST_ADJUSTMENT = -150   # kcal
MAINTENANCE_GAINING_ADJUSTMENT = -100 # kcal
MAINTENANCE_LOSING_ADJUSTMENT = +100  # kcal

# Cut Duration Limits
CUT_DURATION_WARNING_WEEKS = 12
CUT_DURATION_MAX_WEEKS = 16
CUT_DURATION_ABSOLUTE_MAX_WEEKS = 20

# Metabolic Adaptation Buffer
METABOLIC_ADAPTATION_BUFFER_KCAL = 50   # when using equation-based only
NEAT_SUPPRESSION_THRESHOLD_KCAL = 200   # flag significant NEAT suppression

# Target Weight Change Rates
CUTTING_RATE_MIN_PCT_PER_WEEK = 0.5
CUTTING_RATE_MAX_PCT_PER_WEEK = 1.0
CUTTING_RATE_TARGET_PCT_PER_WEEK = 0.75
MAX_CUTTING_DEFICIT_KCAL_PER_DAY = 750
BULKING_RATE_MIN_PCT_PER_MONTH = 0.25
BULKING_RATE_MAX_PCT_PER_MONTH = 1.0
BULKING_RATE_INTERMEDIATE_PCT = 0.5
MAINTENANCE_WINDOW_PCT = 0.25
```

### B.2 Protein Constants

```python
PROTEIN_RATE_G_PER_LB = 0.82          # system-locked
PROTEIN_RATE_G_PER_KG = 1.81          # = 0.82 × 2.2046
PROTEIN_BREAKPOINT_MORTON_G_PER_KG = 1.62   # Morton 2018 mean
PROTEIN_BREAKPOINT_UPPER_CI_G_PER_KG = 2.20 # Morton 2018 upper 95% CI
PROTEIN_SAFETY_CEILING_G_PER_KG = 3.3       # Antonio et al.
PROTEIN_SAFETY_CEILING_G_PER_LB = 1.50
PROTEIN_MIN_PER_MEAL_G = 25             # minimum per meal (Leidy)
PROTEIN_OPTIMAL_PER_MEAL_G = 30         # optimal per meal (Paddon-Jones)
PER_MEAL_PROTEIN_MIN_G_PER_KG = 0.40   # Schoenfeld & Aragon 2018
PER_MEAL_PROTEIN_MAX_G_PER_KG = 0.55   # Schoenfeld & Aragon 2018
IBW_BASE_WEIGHT_KG_MALE = 52.0         # Robinson formula
IBW_KG_PER_INCH_OVER_60 = 1.9          # Robinson formula
AJBW_ADJUSTMENT_FACTOR = 0.4           # standard clinical formula
BMI_OBESITY_THRESHOLD = 30.0           # use AjBW above this
```

### B.3 Nutritional Phase Constants

```python
# Cut phase
CUT_DEFICIT_MODERATE_LOWER = 300   # kcal/day
CUT_DEFICIT_MODERATE_UPPER = 500   # kcal/day
CUT_DEFICIT_AGGRESSIVE_UPPER = 750 # kcal/day
CUT_WEIGHT_LOSS_TARGET_LOWER_PCT = 0.50  # % BW/week
CUT_WEIGHT_LOSS_TARGET_UPPER_PCT = 1.00  # % BW/week
CUT_MIN_DURATION_WEEKS = 4
CUT_SOFT_MAX_WEEKS = 16
CUT_HARD_MAX_WEEKS = 20

# Maintenance phase
MAINTENANCE_CALORIE_TOLERANCE_KCAL = 100    # ±100 kcal = maintenance
POST_CUT_MIN_MAINTENANCE_WEEKS = 2
POST_CUT_OPTIMAL_MAINTENANCE_WEEKS = 4
POST_BULK_MIN_MAINTENANCE_WEEKS = 2
POST_BULK_OPTIMAL_MAINTENANCE_WEEKS = 4

# Lean bulk phase
BULK_SURPLUS_BEGINNER_LOWER = 200      # kcal/day
BULK_SURPLUS_BEGINNER_UPPER = 350      # kcal/day
BULK_SURPLUS_INTERMEDIATE_LOWER = 100  # kcal/day
BULK_SURPLUS_INTERMEDIATE_UPPER = 200  # kcal/day
BULK_WEIGHT_GAIN_BEGINNER_LOWER_PCT = 0.25   # % BW/week
BULK_WEIGHT_GAIN_BEGINNER_UPPER_PCT = 0.50
BULK_WEIGHT_GAIN_INTERMEDIATE_LOWER_PCT = 0.10
BULK_WEIGHT_GAIN_INTERMEDIATE_UPPER_PCT = 0.25
BULK_MIN_DURATION_WEEKS = 8
BULK_SOFT_MAX_WEEKS = 24

# Body fat phase thresholds (male)
BF_MAX_TO_START_BULK_PCT = 15.0
BF_IDEAL_START_BULK_PCT = 12.0
BF_SOFT_EXIT_BULK_PCT = 18.0
BF_HARD_EXIT_BULK_PCT = 20.0
BF_CUT_TRIGGER_MAINTENANCE_PCT = 20.0

# Recomposition
RECOMP_TRAINING_AGE_BEGINNER_MONTHS = 12
RECOMP_HIGH_BF_THRESHOLD_PCT = 25.0
RECOMP_PLATEAU_WEEKS = 10
METABOLIC_ADAPTATION_STALL_THRESHOLD_PCT = 0.10

# Wellbeing thresholds (1–5 scale)
PERFORMANCE_DECLINE_THRESHOLD = 2
FATIGUE_EXCESSIVE_THRESHOLD = 2
HUNGER_EXCESSIVE_THRESHOLD = 2
ADHERENCE_FAILING_THRESHOLD = 2
RECOVERY_STRONG_THRESHOLD = 4
```

### B.4 Volume Landmark Constants (Intermediate Male)

```python
VOLUME_LANDMARKS = {
    "chest":       {"MV": 4,  "MEV": 8,  "MAV": (8, 18),  "MRV": 22},
    "back":        {"MV": 6,  "MEV": 10, "MAV": (12, 20), "MRV": 25},
    "quads":       {"MV": 6,  "MEV": 8,  "MAV": (10, 18), "MRV": 22},
    "hamstrings":  {"MV": 4,  "MEV": 4,  "MAV": (8, 14),  "MRV": 18},
    "glutes":      {"MV": 2,  "MEV": 4,  "MAV": (8, 16),  "MRV": 20},
    "side_delts":  {"MV": 6,  "MEV": 8,  "MAV": (10, 22), "MRV": 26},
    "rear_delts":  {"MV": 0,  "MEV": 6,  "MAV": (8, 16),  "MRV": 26},
    "front_delts": {"MV": 0,  "MEV": 0,  "MAV": (0, 8),   "MRV": 16},
    "biceps":      {"MV": 4,  "MEV": 8,  "MAV": (10, 18), "MRV": 26},
    "triceps":     {"MV": 4,  "MEV": 6,  "MAV": (8, 16),  "MRV": 20},
    "calves":      {"MV": 0,  "MEV": 6,  "MAV": (10, 16), "MRV": 20},
    "abs":         {"MV": 0,  "MEV": 4,  "MAV": (8, 20),  "MRV": 25},
    "traps":       {"MV": 0,  "MEV": 4,  "MAV": (8, 20),  "MRV": 25},
}

BEGINNER_MULTIPLIERS = {"MEV": 0.60, "MAV_high": 0.70, "MRV": 0.65}
ADVANCED_MULTIPLIERS = {"MEV": 1.10, "MAV_high": 1.15, "MRV": 1.10}

TOTAL_WEEKLY_SET_CAPS = {
    "BEGINNER": 80,
    "INTERMEDIATE": 130,
    "ADVANCED": 175,
}

MESOCYCLE_DEFAULTS = {
    "BEGINNER":     {"accumulation_weeks": 8, "deload_weeks": 1, "sets_per_week_increase": 1.5},
    "INTERMEDIATE": {"accumulation_weeks": 4, "deload_weeks": 1, "sets_per_week_increase": 2.0},
    "ADVANCED":     {"accumulation_weeks": 3, "deload_weeks": 1, "sets_per_week_increase": 1.0},
}

DELOAD_PARAMS = {
    "duration_weeks": 1,
    "volume_pct_of_peak": 0.40,    # ~40–50% of peak volume
    "load_pct_of_working": 0.90,   # keep weights at 90%
    "rir_floor": 5,                 # very easy effort
}

RIR_BY_WEEK = {1: 3, 2: 2, 3: 2, 4: 1}  # standard 4-week meso
# For longer mesos: {1: 4, 2: 3, 3: 3, 4: 2, 5: 1}

DOUBLE_PROGRESSION_DEFAULTS = {
    "rep_range_low": 8,
    "rep_range_high": 12,
    "rir_start": 3,
    "rir_end_meso": 1,
    "load_increase_barbell_lbs": 5.0,
    "load_increase_dumbbell_lbs": 5.0,
    "load_increase_pct": 0.025
}
```

### B.5 RIR and Deload Thresholds

```python
# e1RM formulas
RIR_MULTIPLIERS = {0: 1.00, 1: 1.03, 2: 1.06, 3: 1.09, 4: 1.12, 5: 1.15}

# Performance decline thresholds
T_E1RM_SHORT_DECLINE = -0.05    # 5% drop vs. 7-day rolling avg
T_E1RM_LONG_DECLINE = -0.10     # 10% drop vs. 28-day rolling avg
T_CONSECUTIVE_DECLINES = 2      # sessions below threshold
T_RIR_MISS_THRESHOLD = 2        # RIR below target by this amount
T_RIR_MISS_SESSION_PCT = 0.50   # % of sets missing RIR target in a session
T_RIR_MISS_SESSIONS = 2         # consecutive sessions with RIR misses
T_SUBJECTIVE_SESSIONS = 3       # consecutive sessions with poor subjective markers
T_HRV_SUPPRESSION_DAYS = 4      # consecutive days HRV below personal baseline
T_SLEEP_DEBT_DAYS = 4           # consecutive nights poor sleep
T_STAGNATION_SESSIONS = 5       # consecutive sessions with zero progress

# Deload volume reduction
DELOAD_VOLUME_REDUCTION = {
    "low": 0.35,
    "moderate": 0.50,
    "high": 0.70
}
DELOAD_LOAD_REDUCTION = {
    "low": 0.00,
    "moderate": 0.10,
    "high": 0.15
}
DELOAD_RIR_TARGET = (4, 5)
DELOAD_DURATION_DAYS = 7

# Post-deload
POST_DELOAD_VOLUME_RESTART_RATIO = {
    "systemic": 0.70,
    "local": 0.80,
    "scheduled": 0.80
}
POST_DELOAD_DECLINE_SUPPRESSION_DAYS = 7
BEGINNER_RIR_CORRECTION = +1
```

### B.6 Recovery (HRV/RHR/Sleep) Constants

```python
# HRV thresholds
HRV_NORMAL_LOWER_SD_MULT = 0.5    # hrv_30d_mean - 0.5 × SD
HRV_RED_LOWER_SD_MULT = 1.5       # hrv_30d_mean - 1.5 × SD
HRV_MIN_CONSECUTIVE_DAYS_YELLOW = 3
HRV_MIN_CONSECUTIVE_DAYS_RED = 3

# CV (coefficient of variation) thresholds
HRV_CV_STABLE_MAX = 5.0          # % CV (very stable)
HRV_CV_NORMAL_MAX = 10.0         # % CV (normal)
HRV_CV_ELEVATED_MAX = 15.0       # % CV (elevated instability)

# RHR thresholds
RHR_MILD_ELEVATION_BPM = 3.0     # + bpm above baseline
RHR_MODERATE_ELEVATION_BPM = 5.0
RHR_SEVERE_ELEVATION_BPM = 8.0
RHR_MIN_CONSECUTIVE_DAYS = 3

# Sleep thresholds
SLEEP_MINIMUM_HRS = 6.0
SLEEP_TARGET_HRS = 7.5
SLEEP_OPTIMAL_HRS = 8.0
SLEEP_GREEN_HRS = 7.0
SLEEP_EFFICIENCY_GREEN_PCT = 80
SLEEP_EFFICIENCY_YELLOW_PCT = 70

# Sleep debt penalty on composite score
SLEEP_RED_PENALTY = 15.0
SLEEP_YELLOW_PENALTY = 7.5
SLEEP_SEVERE_CHRONIC_PENALTY = 10.0  # additional if <5.5h avg

# Composite score weights
W_HRV = 0.40
W_RHR = 0.30
W_SLEEP = 0.30

# Composite score tier thresholds
COMPOSITE_GREEN_MIN = 55.0
COMPOSITE_YELLOW_MIN = 35.0
COMPOSITE_RED_MAX = 34.9

# Bootstrapping
MINIMUM_DAYS_FOR_BASELINE = 14
OPTIMAL_DAYS_FOR_BASELINE = 30

# Data quality artifact flags
HRV_ARTIFACT_MIN = 10
HRV_ARTIFACT_MAX = 200
RHR_ARTIFACT_MIN = 30
RHR_ARTIFACT_MAX = 120
SLEEP_ARTIFACT_MIN_HRS = 1.0
SLEEP_ARTIFACT_MAX_HRS = 14.0
SPO2_ARTIFACT_MIN = 80
SPO2_ARTIFACT_MAX = 100
SPO2_REFERRAL_THRESHOLD = 92
```

### B.7 Sleep Hygiene Constants

```python
MORNING_LIGHT_WINDOW_MINUTES = 60    # light must occur within this window of wake
MORNING_LIGHT_MIN_DURATION_MIN = 10  # minimum outdoor minutes
MORNING_LIGHT_OVERCAST_MIN = 15      # overcast days: extend

CAFFEINE_HALF_LIFE_HOURS = 5.5
CAFFEINE_CUTOFF_HOURS_BEFORE_BED = 10
CAFFEINE_CUTOFF_STRICT_HOURS = 12

BEDROOM_TEMP_TARGET_F = (65, 68)
BEDROOM_TEMP_TARGET_C = (18.3, 20.0)
WARM_BATH_WINDOW_BEFORE_BED_MIN = (60, 120)

EXERCISE_CUTOFF_HOURS_BEFORE_BED = 4
EXERCISE_LIGHT_CUTOFF_HOURS = 1

WAKE_TIME_CONSISTENCY_THRESHOLD_MIN = 30  # SD < 30 min = consistent
WAKE_TIME_ALERT_THRESHOLD_MIN = 45        # SD > 45 min = trigger coaching

# Supplement doses
MAGNESIUM_DOSE_MG = (300, 400)
LTHEANINE_DOSE_MG = (100, 200)
APIGENIN_DOSE_MG = 50
PRE_SLEEP_PROTEIN_DOSE_G = (30, 40)
SUPPLEMENT_TIMING_MIN_BEFORE_BED = 30

# Phase thresholds
HABIT_COMPLIANCE_THRESHOLD_ADVANCE = 0.70  # 70% compliance to advance phase
HABIT_COMPLIANCE_THRESHOLD_REINFORCE = 0.70
MAX_NEW_HABITS_PER_2_WEEKS = 1
```

### B.8 Programming Constants

```python
MINIMUM_FREQUENCY_PER_MUSCLE_PER_WEEK = 2

REST_PERIODS = {
    "primary_compound": 150,       # seconds
    "secondary_compound": 90,
    "isolation_large_muscle": 75,
    "isolation_small_muscle": 60
}

REP_RANGE_BY_CATEGORY = {
    "primary_compound": "5–8",
    "secondary_compound": "8–12",
    "isolation_large": "10–15",
    "isolation_small": "12–20"
}

RIR_SCALE = {
    "week_1_mesocycle": 4,
    "week_2_mesocycle": 3,
    "week_3_mesocycle": 2,
    "week_4_mesocycle": 1,
    "deload_week": 5
}

SESSION_VOLUME_CAP = {
    2: 24, 3: 18, 4: 15, 5: 12, 6: 10
}

SYSTEMIC_FATIGUE_CAP = {
    "beginner_2day": 50,
    "beginner_3day": 60,
    "intermediate_3day": 80,
    "intermediate_4day": 100,
    "intermediate_5day": 115,
    "intermediate_6day": 130
}

FRACTIONAL_SET_CONTRIBUTIONS = {
    "bench_press": {"triceps": 0.5, "front_delts": 0.25},
    "row": {"biceps": 0.5, "rear_delts": 0.25},
    "squat": {"glutes": 0.3, "hamstrings": 0.3},
    "deadlift": {"hamstrings": 0.5, "glutes": 0.4},
    "pulldown": {"biceps": 0.5}
}

# Session duration estimation
AVG_SET_TIME_SECONDS = 45
WARMUP_TIME_MINUTES = 10

# Split transition thresholds
SPLIT_TRANSITION_TRAINING_AGE_MONTHS = 18
SPLIT_TRANSITION_WEEKLY_SETS_PER_MUSCLE = 20
SPLIT_TRANSITION_SESSION_DURATION_MINUTES = 90
```

---

## APPENDIX C: CITATION INDEX

### C.1 TDEE and Calorie Management (Track 1)

| # | Authors | Title | Journal | Year | URL |
|---|---|---|---|---|---|
| 1 | Mifflin MD et al. | "A new predictive equation for resting energy expenditure in healthy individuals" | Am J Clin Nutr | 1990 | — |
| 2 | Frankenfield D et al. | "Comparison of predictive equations for resting metabolic rate" | J Am Diet Assoc | 2005 | https://pubmed.ncbi.nlm.nih.gov/15883556/ |
| 3 | Roza AM, Shizgal HM | "The Harris Benedict equation reevaluated" | Am J Clin Nutr | 1984 | https://zakboekdietetiek.nl/wp-content/uploads/2015/06/roza-1984.pdf |
| 4 | Cunningham JJ | "A reanalysis of the factors influencing basal metabolic rate in normal adults" | Am J Clin Nutr | 1980 | — |
| 5 | Katch FI, McArdle WD | Nutrition, Weight Control, and Exercise (BMR formula) | — | 1975 | — |
| 6 | Helms ER, Valdez A, Morgan A | The Muscle and Strength Pyramid: Nutrition | 3D Muscle Journey | 2019 | — |
| 7 | Iraki J, Fitschen P, Espinar S, Helms E | "Nutrition Recommendations for Bodybuilders in the Off-Season" | Sports (Basel) | 2019 | — |
| 8 | Trexler ET et al. | "Metabolic adaptation to weight loss: implications for the athlete" | J Int Soc Sports Nutr | 2014 | https://pmc.ncbi.nlm.nih.gov/articles/PMC3943438/ |
| 9 | Rosenbaum M, Leibel RL | "Adaptive thermogenesis in humans" | Int J Obes | 2010 | https://pmc.ncbi.nlm.nih.gov/articles/PMC3673773/ |
| 10 | Aguilar-Navarro M et al. | "Achieving an Optimal Fat Loss Phase in Resistance-Trained Athletes" | Nutrients | 2021 | https://pmc.ncbi.nlm.nih.gov/articles/PMC8471721/ |
| 11 | Flegal KM et al. | "Bias and accuracy of resting metabolic rate equations" | Clin Nutr | 2013 | https://pubmed.ncbi.nlm.nih.gov/23631843/ |
| 12 | Martins C et al. | "Metabolic adaptation is an illusion, only present when participants are in negative energy balance" | Obesity | 2020 | https://pdfs.semanticscholar.org/2625/c7ca159f119ec5d083666198e722c739dd66.pdf |

### C.2 Training Volume and Progression (Tracks 2 & 8)

| # | Authors | Title | Journal | Year | URL |
|---|---|---|---|---|---|
| 1 | Israetel M | "Training Volume Landmarks for Muscle Growth" | RP Strength | 2017/2025 | https://rpstrength.com/blogs/articles/training-volume-landmarks-muscle-growth |
| 2 | Israetel M | "In Defense of Set Increases Within the Hypertrophy Mesocycle" | RP Strength | 2020 | https://rpstrength.com/blogs/articles/in-defense-of-set-increases-within-the-hypertrophy-mesocycle |
| 3 | Schoenfeld BJ, Krieger J | "Dose-response relationship between weekly resistance training volume and increases in muscle mass" | J Sports Sciences | 2017 | https://pubmed.ncbi.nlm.nih.gov/27433992/ |
| 4 | Schoenfeld BJ et al. | "Resistance Training Volume Enhances Muscle Hypertrophy but Not Strength" | MSSE | 2019 | https://pmc.ncbi.nlm.nih.gov/articles/PMC6303131/ |
| 5 | Krieger J | "The King of Volume Metas" | Biolayne | 2024 | https://biolayne.com/reps/issue-31/the-king-of-volume-metas/ |
| 6 | Schoenfeld BJ, Ogborn D, Krieger JW | "Effects of Resistance Training Frequency on Measures of Muscle Hypertrophy" | Sports Medicine | 2016 | https://pubmed.ncbi.nlm.nih.gov/27102172/ |
| 7 | Colquhoun et al. | "Training Volume, Not Frequency, Indicative of Maximal Strength Adaptations" | J Human Kinetics | 2019 | https://pmc.ncbi.nlm.nih.gov/articles/PMC6724585/ |
| 8 | Ramos-Campo et al. | "Split and full-body produce equivalent hypertrophy" | Einstein | 2021 | https://pmc.ncbi.nlm.nih.gov/articles/PMC8372753/ |
| 9 | Fonseca RM et al. | "Changes in exercises are more effective than in loading schemes" | PubMed | 2014 | https://pubmed.ncbi.nlm.nih.gov/24832974/ |
| 10 | Schoenfeld BJ, Pope ZK et al. | "Longer Interset Rest Periods Enhance Muscle Strength and Hypertrophy" | JSCR | 2016 | Via Brookbush Institute |

### C.3 RIR Autoregulation and Deloads (Track 3)

| # | Authors | Title | Journal | Year | URL |
|---|---|---|---|---|---|
| 1 | Zourdos MC et al. | "Novel Resistance Training–Specific Rating of Perceived Exertion Scale" | JSCR | 2016 | https://pubmed.ncbi.nlm.nih.gov/26049792/ |
| 2 | Helms ER et al. | "Application of the Repetitions in Reserve-Based RPE Scale" | Strength Cond J | 2016 | https://pmc.ncbi.nlm.nih.gov/articles/PMC4961270/ |
| 3 | Helms ER et al. | "RPE vs. Percentage 1RM Loading in Periodized Programs" | Front Physiol | 2018 | https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2018.00247/full |
| 4 | Graham T, Cleather DJ | "Autoregulation by RIR Leads to Greater Improvements in Strength" | JSCR | 2019 | https://pubmed.ncbi.nlm.nih.gov/31009432/ |
| 5 | Ogasawara R et al. | "Comparison of Muscle Hypertrophy Following 6-Month of Continuous and Periodic Strength Training" | Eur J Appl Physiol | 2013 | https://pubmed.ncbi.nlm.nih.gov/23053130/ |
| 6 | Pritchard HJ et al. | "Higher- Versus Lower-Intensity Strength-Training Taper" | — | 2019 | https://pubmed.ncbi.nlm.nih.gov/30204523/ |
| 7 | Bell et al. | "Integrating Deloading into Strength and Physique Sports Training Programmes" | Sports Med Open | 2023 | https://pmc.ncbi.nlm.nih.gov/articles/PMC10511399/ |
| 8 | Bell et al. | "A Practical Approach to Deloading" | NSCA Strength Cond J | 2025 | https://doras.dcu.ie/31501/1/a_practical_approach_to_deloading__recommendations.203(2).pdf |
| 9 | Coleman et al. | "Gaining More From Doing Less?" | PeerJ | 2024 | https://pmc.ncbi.nlm.nih.gov/articles/PMC10809978/ |

### C.4 Recovery — HRV, RHR, Sleep, Nocebo (Track 4)

| # | Authors | Title | Journal | Year | URL |
|---|---|---|---|---|---|
| 1 | Kiviniemi AM et al. | "Endurance training guided individually by daily HRV measurements" | Eur J Appl Physiol | 2007 | https://pubmed.ncbi.nlm.nih.gov/17849143/ |
| 2 | Plews DJ | "HRV methodology for endurance athletes" (interview) | Scientific Triathlon EP#42 | — | https://scientifictriathlon.com/tts42/ |
| 3 | — | "HRV-Guided Training Protocol for Professional Endurance Athletes" | IJERPH | 2020 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7432021/ |
| 4 | — | "HRV-Guided Training Meta-Analysis" | IJERPH | 2021 | https://pmc.ncbi.nlm.nih.gov/articles/PMC8507742/ |
| 5 | Gavriloff D et al. | "Sham sleep feedback delivered via actigraphy biases daytime symptom reports" | J Sleep Research | 2018 | https://drjameshewitt.com/can-sleep-tracking-be-bad-for-your-performance/ |
| 6 | Rosman L et al. | Wearable devices and health anxiety in Afib patients | JAHA | 2024 | https://www.med.unc.edu/medicine/news/wearable-devices-can-increase-health-anxiety-could-they-adversely-affect-health/ |
| 7 | Roberts AJ et al. | Sleep extension and restriction effects on cyclists | HiitScience | — | https://hiitscience.com/sleep-endurance-performance/ |
| 8 | — | "Sleep Interventions in Athletic Performance" | Sports Med Open | 2023 | https://pmc.ncbi.nlm.nih.gov/articles/PMC10354314/ |

### C.5 Ad Libitum Dieting (Track 5)

| # | Authors | Title | Journal | Year | URL |
|---|---|---|---|---|---|
| 1 | Weigle DS et al. | "A high-protein diet induces sustained reductions in appetite, ad libitum caloric intake, and body weight" | Am J Clin Nutr | 2005 | https://pubmed.ncbi.nlm.nih.gov/16002798/ |
| 2 | Antonio J et al. | "The effects of consuming a high protein diet (4.4 g/kg/d) on body composition" | JISSN | 2014 | https://www.semanticscholar.org/paper/The-effects-of-consuming-a-high-protein-diet-(4.4-g-Antonio-Peacock/c1cf452b1de175b4774397fc3f1153f9e74bc2bd |
| 3 | Antonio J et al. | "A high protein diet (3.4 g/kg/d) combined with heavy resistance training" | JISSN | 2015 | https://pubmed.ncbi.nlm.nih.gov/26500462/ |
| 4 | Hall KD et al. | "Ultra-processed diets cause excess calorie intake and weight gain" | Cell Metabolism | 2019 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7946062/ |
| 5 | Leidy HJ et al. | "The effects of consuming frequent, higher protein meals on appetite and satiety" | Obesity | 2011 | https://pubmed.ncbi.nlm.nih.gov/20847729/ |
| 6 | Paddon-Jones D et al. | "Important Concepts in Protein Nutrition, Aging, and Skeletal Muscle" | J Nutr | 2023 | https://pmc.ncbi.nlm.nih.gov/articles/PMC10196581/ |
| 7 | Sheeran P et al. | "Self-Determination Theory Interventions for Health Behavior Change: Meta-analysis of 65 RCTs" | Health Psychology | 2020 | https://selfdeterminationtheory.org/wp-content/uploads/2020/11/2020_SheeranWrightEtAl_SDTInterventions.pdf |
| 8 | Jayawardena R et al. | "Effects of plate model as part of dietary intervention for cardio-vascular disease" | CVD Diagn Ther | 2019 | https://pmc.ncbi.nlm.nih.gov/articles/PMC6511685/ |

### C.6 Sleep Hygiene (Track 6)

| # | Authors | Title | Journal | Year | URL |
|---|---|---|---|---|---|
| 1 | Lamon S et al. | "One night of sleep deprivation reduces muscle protein synthesis by 18%" | Physiological Reports | 2021 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7785053/ |
| 2 | Leproult R, Van Cauter E | "Effect of 1 Week of Sleep Restriction on Testosterone Levels" | JAMA | 2011 | DOI: 10.1001/jama.2011.710 |
| 3 | Nedeltcheva AV et al. | Sleep curtailment during caloric restriction reduces fat loss 55% | Ann Intern Med | 2010 | https://pmc.ncbi.nlm.nih.gov/articles/PMC2951287/ |
| 4 | Leota J et al. | Late exercise and sleep outcomes (n=15,000) | Nature Comm | 2025 | https://www.nature.com/articles/s41467-025-58271-x |
| 5 | Hausenblas HA et al. | "Magnesium threonate improves objective and subjective sleep quality" | Sleep Medicine: X | 2024 | https://pmc.ncbi.nlm.nih.gov/articles/PMC11381753/ |
| 6 | — | "L-Theanine + Mg: GABA receptors, delta waves, sleep latency" | Front Nutr | 2022 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9017334/ |
| 7 | — | "Chamomile/apigenin: 9/10 trials effective for anxiety" (systematic review) | CNR | 2024 | https://e-cnr.org/DOIx.php?id=10.7762%2Fcnr.2024.13.2.139 |
| 8 | van Loon LJC lab | "Pre-sleep 40g casein: 22–37% higher overnight MPS" | GSSI | 2022 | https://www.gssiweb.org/research/article/resistance-exercise-augments-postprandial-overnight-muscle-protein-synthesis-rates |
| 9 | Rasch B et al. | "SWS enhancement increased GH by 400%+" | Comm Biology | 2022 | https://www.nature.com/articles/s42003-022-03643-y |
| 10 | Landolt HP et al. | "Caffeine delays melatonin onset ~40 min" | J Sleep Res | 2022 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9541543/ |

### C.7 Protein Targets and Phase Management (Track 7)

| # | Authors | Title | Journal | Year | URL |
|---|---|---|---|---|---|
| 1 | Morton RW et al. | "A systematic review and meta-analysis of protein supplementation on RT-induced gains" | BJSM | 2018 | https://bjsm.bmj.com/lookup/doi/10.1136/bjsports-2017-097608 |
| 2 | Henselmans M | "The myth of 1 g/lb: Optimal protein intake for bodybuilders" | MennoHenselmans.com | 2012 | https://mennohenselmans.com/the-myth-of-1glb-optimal-protein-intake-for-bodybuilders/ |
| 3 | Henselmans M | "You DON'T need more protein in energy deficit" | MennoHenselmans.com | 2024 | https://mennohenselmans.com/you-dont-need-more-protein-in-energy-deficit/ |
| 4 | Helms ER, Aragon AA, Fitschen PJ | "Evidence-based recommendations for natural bodybuilding contest preparation" | JISSN | 2014 | https://pmc.ncbi.nlm.nih.gov/articles/PMC4033492/ |
| 5 | Schoenfeld BJ, Aragon AA | "How much protein can the body use in a single meal for muscle-building?" | JISSN | 2018 | https://pubmed.ncbi.nlm.nih.gov/29497353/ |
| 6 | Antonio J et al. | "A High Protein Diet Has No Harmful Effects: A One-Year Crossover Study" | J Nutr Metab | 2016 | https://pmc.ncbi.nlm.nih.gov/articles/PMC5078648/ |
| 7 | Helms ER, Iraki J et al. | "Nutrition Recommendations for Bodybuilders in the Off-Season" | Sports | 2019 | https://pmc.ncbi.nlm.nih.gov/articles/PMC6680710/ |
| 8 | Barakat C et al. | "Body Recomposition: Can Trained Individuals Build Muscle and Lose Fat at the Same Time?" | SCJ | 2020 | https://journals.lww.com/10.1519/SSC.0000000000000584 |
| 9 | Byrne NM et al. | "Intermittent energy restriction improves weight loss efficiency (MATADOR)" | Int J Obes | 2018 | https://pmc.ncbi.nlm.nih.gov/articles/PMC5803575/ |
| 10 | Campbell BI et al. | "Effects of Intermittent Diet Breaks during 25% Energy Restriction" | J Human Kinetics | 2023 | https://pmc.ncbi.nlm.nih.gov/articles/PMC10170537/ |
| 11 | Ruiz-Castellano C et al. | "Achieving an Optimal Fat Loss Phase in Resistance-Trained Athletes" | Nutrients | 2021 | https://pmc.ncbi.nlm.nih.gov/articles/PMC8471721/ |

---

*End of Milo Master Research Document*  
*Version 1.0 — Compiled 2026-03-05*  
*All formulas, pseudocode, thresholds, and constants are preserved from source tracks unchanged.*  
*This document is the single source of truth for Milo backend algorithm development.*
