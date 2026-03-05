# Track 1: TDEE & Calorie Algorithms
## Milo AI Fitness Coaching System — Backend Logic Reference

**Version:** 1.0  
**Date:** 2026-03-05  
**Scope:** Male beginner-to-intermediate lifters, hypertrophy/strength and fat loss goals  
**Adjustment Cadence:** Biweekly (every 14 days)  
**Audience:** AI backend agent, not a human coach

---

## Table of Contents

1. [TDEE Estimation Models](#1-tdee-estimation-models)
2. [Adaptive TDEE Calibration From Weight Data](#2-adaptive-tdee-calibration-from-weight-data)
3. [Calorie Adjustment Algorithms](#3-calorie-adjustment-algorithms)
4. [Metabolic Adaptation Modeling](#4-metabolic-adaptation-modeling)
5. [Variable Reference Table](#5-variable-reference-table)
6. [Decision Logic Master Flow](#6-decision-logic-master-flow)

---

## 1. TDEE Estimation Models

### 1.1 Overview and Model Selection Logic

TDEE is calculated as:

```
TDEE = BMR × activity_multiplier
```

Where BMR (Basal Metabolic Rate) is estimated from one of four equations depending on data availability.

**Primary model selection rule:**

```
if body_fat_pct is known:
    use Katch-McArdle (preferred) OR Cunningham (for athletes)
else:
    use Mifflin-St Jeor (primary fallback)
    // Harris-Benedict (Roza-Shizgal) is secondary fallback only
```

---

### 1.2 Equation Formulas

All weight inputs in **kilograms (kg)**, height in **centimeters (cm)**, age in **years (yr)**, LBM in **kg**.

---

#### 1.2.1 Mifflin-St Jeor (1990) — PRIMARY when BF% unknown

**Source:** Mifflin MD, St Jeor ST, Hill LA, Scott BJ, Daugherty SA, Koh YO. "A new predictive equation for resting energy expenditure in healthy individuals." *Am J Clin Nutr.* 1990;51(2):241–247.

```
// For males (Milo target population):
BMR_mifflin = (10 × weight_kg) + (6.25 × height_cm) − (5 × age_yr) + 5

// For completeness — females:
BMR_mifflin_female = (10 × weight_kg) + (6.25 × height_cm) − (5 × age_yr) − 161
```

**Variables:**
| Variable | Type | Unit | Description |
|---|---|---|---|
| `weight_kg` | float | kg | Current body weight |
| `height_cm` | float | cm | Standing height |
| `age_yr` | int | years | Age in whole years |
| `BMR_mifflin` | float | kcal/day | Resting metabolic rate output |

**Validation:**
- Designated by the Academy of Nutrition and Dietetics (AND) as the evidence-based standard in 2005 (Frankenfield et al., 2005, *J Am Diet Assoc* 105:775–789, [PubMed](https://pubmed.ncbi.nlm.nih.gov/15883556/))
- Predicts RMR within ±10% of measured in **82% of non-obese** and **75% of obese** individuals
- Lowest bias of all tested equations: 95% CI −26 to +8 kcal/day (Flegal et al., 2013, [PubMed](https://pubmed.ncbi.nlm.nih.gov/23631843/))
- Accuracy rate: 82% non-obese vs. 79% for next-best (Livingston equation)
- Harris-Benedict (1919) overestimated energy expenditure by 7–24% in women and 9.2% in men under 50, making Mifflin-St Jeor meaningfully superior for modern populations

**Recommended default:** Use for all users where BF% is unavailable.

---

#### 1.2.2 Harris-Benedict Revised (Roza & Shizgal, 1984) — SECONDARY FALLBACK

**Source:** Roza AM, Shizgal HM. "The Harris Benedict equation reevaluated: resting energy requirements and the body cell mass." *Am J Clin Nutr.* 1984;40(1):168–182. [PDF source](https://zakboekdietetiek.nl/wp-content/uploads/2015/06/roza-1984.pdf)

```
// Males:
BMR_hb_male = 88.362 + (13.397 × weight_kg) + (4.799 × height_cm) − (5.677 × age_yr)

// Females:
BMR_hb_female = 447.593 + (9.247 × weight_kg) + (3.098 × height_cm) − (4.330 × age_yr)
```

**Variables:**
| Variable | Type | Unit | Description |
|---|---|---|---|
| `BMR_hb_male` | float | kcal/day | Male RMR via revised H-B |

**Notes on original vs. revised:**
- Original Harris-Benedict (1919) male: `66.473 + (13.7516 × weight_kg) + (5.0033 × height_cm) − (6.755 × age_yr)`
- The Roza-Shizgal (1984) revision is what should be used; the original consistently overestimates RMR in modern populations
- 95% confidence limits for revised equation: ±213 kcal/day (men), ±201 kcal/day (women)
- Academy of Nutrition and Dietetics recommends Mifflin-St Jeor over this equation; include only as secondary fallback

**Decision rule:**

```
if mifflin_failed OR mifflin_cannot_be_calculated:
    use harris_benedict_revised
```

---

#### 1.2.3 Katch-McArdle (1975) — PRIMARY when BF% is known

**Source:** Katch FI, McArdle WD. "Prediction of body density from simple anthropometric measurements in college-age men and women." *Hum Biol.* 1973;45(3):445–454. Formula widely cited in sports nutrition literature.

```
// Step 1: Calculate Lean Body Mass
LBM_kg = weight_kg × (1 − (body_fat_pct / 100))

// Step 2: Calculate BMR
BMR_katch = 370 + (21.6 × LBM_kg)
```

**Variables:**
| Variable | Type | Unit | Description |
|---|---|---|---|
| `body_fat_pct` | float | % | Body fat percentage (0–60) |
| `LBM_kg` | float | kg | Lean body mass |
| `BMR_katch` | float | kcal/day | BMR output |

**Notes:**
- Accounts for body composition; more accurate for individuals with atypical body composition (muscular athletes, very lean individuals)
- **Does not account for age** — a limitation compared to Mifflin-St Jeor; however, for hypertrophy-focused athletes, LBM is the dominant predictor
- Requires accurate BF% input; errors in BF% estimation propagate directly into BMR error
- Appropriate for Milo users who have DEXA, InBody, or caliper-based BF% measurements

**Recommended default when BF% available:** Use Katch-McArdle for all users with a BF% measurement (any source with confidence >±3%).

---

#### 1.2.4 Cunningham (1980) — PREFERRED for lean/athletic users when BF% is known

**Source:** Cunningham JJ. "A reanalysis of the factors influencing basal metabolic rate in normal adults." *Am J Clin Nutr.* 1980;33(11):2372–2374.

```
// Step 1: Calculate Lean Body Mass (same as Katch-McArdle)
LBM_kg = weight_kg × (1 − (body_fat_pct / 100))

// Step 2: Calculate RMR
RMR_cunningham = 500 + (22 × LBM_kg)
```

**Variables:**
| Variable | Type | Unit | Description |
|---|---|---|---|
| `RMR_cunningham` | float | kcal/day | RMR output |

**Notes:**
- Produces higher estimates than Katch-McArdle (~150–200 kcal/day higher for the same LBM) due to the higher constant (500 vs. 370) and coefficient (22 vs. 21.6)
- Validated specifically for **muscular physique athletes** and resistance-trained individuals; yields more accurate predictions in this population than Katch-McArdle ([Strength Coach Tutor reference](https://www.thestrengthcoachtutor.com/post/the-cunningham-equation))
- Example: 80 kg male, 12% BF → LBM = 70.4 kg → RMR_cunningham = 500 + (22 × 70.4) = **2,049 kcal/day**
- Compared to Katch-McArdle for same individual: 370 + (21.6 × 70.4) = **1,891 kcal/day**

**Decision rule for Milo's target population (male beginner-to-intermediate lifters):**

```
if body_fat_pct is known AND user is resistance_training:
    if user_category == "athletic" OR body_fat_pct < 15:
        use Cunningham
    else:
        use Katch-McArdle
else:
    use Mifflin_St_Jeor
```

---

### 1.3 Equation Comparison Summary

| Equation | Year | Inputs | Best For | Avg Error | Accuracy (±10%) |
|---|---|---|---|---|---|
| Mifflin-St Jeor | 1990 | Weight, Height, Age, Sex | General population, no BF% | −26 to +8 kcal/day | 82% non-obese |
| Harris-Benedict (Roza-Shizgal) | 1984 | Weight, Height, Age, Sex | Secondary fallback only | ±213 kcal (men) | ~70–80% |
| Katch-McArdle | 1975 | LBM (from BF%) | BF% available, non-athletic | N/A | Better than H-B for lean users |
| Cunningham | 1980 | LBM (from BF%) | Resistance-trained/athletic | ~±100–150 kcal | Highest for athletes |

**Recommendation hierarchy for Milo:**
1. **Cunningham** — if BF% known and user is resistance-training (default for Milo's population)
2. **Katch-McArdle** — if BF% known, lower activity/less muscular user
3. **Mifflin-St Jeor** — if BF% unknown (most common at onboarding)
4. **Harris-Benedict (Roza-Shizgal)** — last resort only

---

### 1.4 Activity Multiplier Table (TDEE = BMR × multiplier)

These multipliers originate from the FAO/WHO/UNU 1985 physical activity level (PAL) framework, commonly applied alongside Mifflin-St Jeor and the LBM-based equations.

| Activity Level | Label | Multiplier | Description |
|---|---|---|---|
| Sedentary | `SEDENTARY` | 1.2 | Desk job, no exercise, <2,000 steps/day |
| Lightly Active | `LIGHTLY_ACTIVE` | 1.375 | Light exercise 1–3 days/week |
| Moderately Active | `MODERATELY_ACTIVE` | 1.55 | Moderate exercise 3–5 days/week |
| Very Active | `VERY_ACTIVE` | 1.725 | Hard exercise 6–7 days/week or physical job |
| Extremely Active | `EXTREMELY_ACTIVE` | 1.9 | Hard daily exercise + physical job OR 2× daily training |

**Milo default for target population (male lifter, 3–5 training days/week):**
```
default_activity_multiplier = 1.55  // MODERATELY_ACTIVE
```

**Note on activity multiplier accuracy:**  
Activity multipliers are population-level estimates with high inter-individual variance. Mifflin-St Jeor multiplied by activity factor has a real-world error range of ±200–400 kcal/day at the individual level. This is exactly why Milo's adaptive TDEE calibration (Section 2) is critical — equation-based TDEE is only the starting estimate.

**Pseudocode for initial TDEE calculation:**

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
        BMR = (10 * weight_kg) + (6.25 * height_cm) - (5 * age_yr) + 5  # Mifflin-St Jeor (male)
        equation_used = "Mifflin-St Jeor"
    
    # Apply activity multiplier
    multiplier_map = {
        "SEDENTARY": 1.2,
        "LIGHTLY_ACTIVE": 1.375,
        "MODERATELY_ACTIVE": 1.55,
        "VERY_ACTIVE": 1.725,
        "EXTREMELY_ACTIVE": 1.9
    }
    
    multiplier = multiplier_map.get(activity_level, 1.55)  # default: MODERATELY_ACTIVE
    
    TDEE_estimated = BMR * multiplier
    
    return {
        "TDEE_estimated": round(TDEE_estimated),
        "BMR": round(BMR),
        "equation_used": equation_used,
        "activity_multiplier": multiplier,
        "LBM_kg": LBM_kg if body_fat_pct is not None else None
    }
```

---

## 2. Adaptive TDEE Calibration From Weight Data

### 2.1 Rationale

Static equations predict TDEE with ~±200–400 kcal/day individual error. Over time, real-world weight tracking provides empirical data to calibrate the actual TDEE for a specific individual. This "adaptive TDEE" becomes Milo's primary signal after sufficient data accumulation.

**Core principle (from Helms, Valdez & Morgan, "The Muscle and Strength Pyramid: Nutrition," 3D Muscle Journey, 2019):**  
Track weekly weight averages. Compare average weight this week to average weight last week. A change in average weight of ±1 kg reflects approximately ±7,700 kcal of energy imbalance over that period.

---

### 2.2 Rolling Weight Average Calculation

To eliminate daily noise (water retention, glycogen, sodium, bowel contents), use a rolling N-day average:

```python
def rolling_weight_average(weight_log: list[tuple[date, float]], window_days: int = 7) -> float:
    """
    weight_log: list of (date, weight_kg) tuples sorted ascending by date
    window_days: number of days to average (7 or 14)
    Returns: average weight in kg for the window
    """
    if len(weight_log) < window_days:
        # Insufficient data — use available readings
        weights = [w for _, w in weight_log]
    else:
        # Most recent N days
        recent = weight_log[-window_days:]
        weights = [w for _, w in recent]
    
    return sum(weights) / len(weights)
```

**Helms' recommendation:** Use 7-day averages and compare week-to-week rather than looking at day-to-day fluctuations. For biweekly adjustment cycles, compare the 7-day average of the most recent week to the 7-day average of the week 14 days prior.

```python
def get_biweekly_weight_trend(weight_log: list[tuple[date, float]]) -> dict:
    """
    For a 14-day window: compute 7-day average at beginning vs. end.
    Returns weight_delta_kg and rate_of_change_pct_per_week.
    """
    if len(weight_log) < 10:  # minimum data threshold
        return {"insufficient_data": True}
    
    # First 7 days of the 14-day window
    week1_weights = [w for _, w in weight_log[:7]]
    week1_avg = sum(week1_weights) / len(week1_weights)
    
    # Last 7 days of the 14-day window
    week2_weights = [w for _, w in weight_log[-7:]]
    week2_avg = sum(week2_weights) / len(week2_weights)
    
    weight_delta_kg = week2_avg - week1_avg          # positive = gained weight
    rate_pct_per_week = (weight_delta_kg / week1_avg) * 100  # percent of body weight per week
    
    return {
        "week1_avg_kg": round(week1_avg, 2),
        "week2_avg_kg": round(week2_avg, 2),
        "weight_delta_kg": round(weight_delta_kg, 3),
        "rate_pct_per_week": round(rate_pct_per_week, 3)
    }
```

---

### 2.3 Back-Calculating Actual TDEE

Once calorie intake is being tracked (logged via the app), actual TDEE can be back-calculated from weight change data:

**Core formula:**

```
actual_TDEE = avg_daily_calories_consumed + (weight_change_kg × 7700 / days_in_period)
```

Where:
- `weight_change_kg` is **positive** if weight decreased (fat/mass was burned = net energy deficit)
- `weight_change_kg` is **negative** if weight increased (net energy surplus)

Wait — let's be precise with sign convention:

```
// SIGN CONVENTION:
// weight_delta_kg > 0  →  gained weight  →  was in surplus
// weight_delta_kg < 0  →  lost weight    →  was in deficit

energy_balance_kcal = weight_delta_kg × 7700  
// 7700 kcal ≈ energy content of 1 kg of mixed body tissue (fat + lean)
// Note: pure fat ≈ 9,000 kcal/kg; mixed tissue ~7,700 kcal/kg (Hall et al. model)

actual_TDEE = avg_daily_calories - (energy_balance_kcal / days_in_period)
```

**Pseudocode:**

```python
KCAL_PER_KG_TISSUE = 7700  # mixed tissue energy value; use 7700 as default

def calculate_adaptive_TDEE(avg_daily_calories: float, 
                              weight_delta_kg: float, 
                              days_in_period: int) -> float:
    """
    Back-calculates actual TDEE from logged calorie intake and weight change.
    
    weight_delta_kg: positive = weight gained; negative = weight lost
    avg_daily_calories: average kcal/day consumed during the period
    days_in_period: number of days in measurement window (14 for biweekly)
    
    Returns: adaptive_TDEE in kcal/day
    """
    daily_energy_balance = (weight_delta_kg * KCAL_PER_KG_TISSUE) / days_in_period
    # Positive daily_energy_balance = user was in surplus (consumed > burned)
    # Negative daily_energy_balance = user was in deficit (consumed < burned)
    
    adaptive_TDEE = avg_daily_calories - daily_energy_balance
    
    return round(adaptive_TDEE)
```

**Example calculation:**
- User logs average 2,400 kcal/day for 14 days
- Weight went from 82.4 kg → 81.9 kg (delta = −0.5 kg)
- Energy balance = (−0.5 × 7700) / 14 = −275 kcal/day
- Adaptive TDEE = 2,400 − (−275) = **2,675 kcal/day**

This means the user was burning 2,675 kcal/day despite eating only 2,400 kcal/day, producing a deficit of 275 kcal/day.

---

### 2.4 Reliability Timeline: Minimum Data Requirements

| Weeks of data | Reliability status | Action |
|---|---|---|
| 0–1 weeks | `INSUFFICIENT` | Use equation-based estimate only |
| 2 weeks | `LOW_CONFIDENCE` | Adaptive TDEE available but noisy; blend 30% adaptive + 70% equation |
| 3–4 weeks | `MODERATE_CONFIDENCE` | Blend 60% adaptive + 40% equation |
| 5+ weeks | `HIGH_CONFIDENCE` | Use adaptive TDEE as primary; equation as sanity check |

**Pseudocode for TDEE blending:**

```python
def get_working_TDEE(equation_TDEE: float, 
                      adaptive_TDEE: float | None, 
                      weeks_of_data: int) -> dict:
    """
    Returns the working TDEE to use for calorie targets.
    Blends equation-based and adaptive TDEE based on data maturity.
    """
    
    if adaptive_TDEE is None or weeks_of_data < 2:
        return {
            "working_TDEE": equation_TDEE,
            "confidence": "INSUFFICIENT",
            "source": "equation_only"
        }
    
    elif weeks_of_data < 3:
        # 30/70 blend
        working_TDEE = (0.3 * adaptive_TDEE) + (0.7 * equation_TDEE)
        confidence = "LOW_CONFIDENCE"
    
    elif weeks_of_data < 5:
        # 60/40 blend
        working_TDEE = (0.6 * adaptive_TDEE) + (0.4 * equation_TDEE)
        confidence = "MODERATE_CONFIDENCE"
    
    else:
        # Adaptive TDEE dominates
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

**Important:** The adaptive TDEE is only reliable when:
1. Calorie logging is consistent (≥80% of days logged in the period)
2. No major perturbations (illness, travel, extreme sodium or alcohol intake) distorted the weight readings
3. At least 7 valid weight readings exist in the 14-day window

---

### 2.5 Handling Water Weight Fluctuations and Noise

Daily weight fluctuations of ±1–3 kg are normal and do not reflect fat or muscle changes. Sources of noise:
- Glycogen storage changes (each gram of glycogen binds ~3g water)
- Sodium intake / water retention
- Menstrual cycle (not applicable to Milo's male target population)
- Bowel contents
- Hydration status

**Noise filtering rules:**

```python
def is_weight_reading_valid(weight_kg: float, 
                              user_weight_history: list[float],
                              max_single_day_delta_kg: float = 2.5) -> bool:
    """
    Flags outlier weight readings for exclusion from 7-day averages.
    """
    if len(user_weight_history) < 3:
        return True  # insufficient history to detect outliers
    
    recent_avg = sum(user_weight_history[-7:]) / min(len(user_weight_history), 7)
    delta = abs(weight_kg - recent_avg)
    
    if delta > max_single_day_delta_kg:
        return False  # likely water/sodium spike — exclude from average
    
    return True
```

**Minimum readings per 7-day window:**
```
if valid_readings_in_window < 4:
    flag_as "LOW_DATA_QUALITY"
    use previous window's average as fallback
```

**Recommendation (from Helms, Muscle & Strength Pyramid Nutrition):**  
Weigh every morning, fasted, post-void. Use 7-day rolling average. Compare weekly averages, not individual daily readings. Only act on a 2-week trend, not a single week's data.

---

## 3. Calorie Adjustment Algorithms

### 3.1 Goal Phase Detection

Before any calorie adjustment, identify the user's active goal phase:

```python
GoalPhase = Enum("GoalPhase", ["CUTTING", "BULKING", "MAINTENANCE"])
```

Phase determines target rate of weight change, adjustment direction, and adjustment magnitude.

---

### 3.2 Target Rates of Weight Change

#### Fat Loss Phase (CUTTING)

**Target:** 0.5–1.0% of body weight lost per week to maximize fat-free mass retention.

**Source:** Helms et al. (2014), "Evidence-based recommendations for natural bodybuilding contest preparation." *J Int Soc Sports Nutr.* 11:20. Also corroborated by [Aguilar-Navarro et al. (2021), *Nutrients*](https://pmc.ncbi.nlm.nih.gov/articles/PMC8471721/): "Caloric intake should be set based on a target BW loss of 0.5–1.0%/week to maximize fat-free mass retention."

```python
# Fat loss rate targets
CUTTING_RATE_MIN_PCT_PER_WEEK = 0.5   # % of body weight per week (lower bound)
CUTTING_RATE_MAX_PCT_PER_WEEK = 1.0   # % of body weight per week (upper bound)
CUTTING_RATE_TARGET_PCT_PER_WEEK = 0.75  # midpoint default

# Absolute kcal deficit implied:
# At 80 kg: 0.5% = 400g/week = 4.4 kg/month → ~440 kcal/day deficit
# At 80 kg: 1.0% = 800g/week → ~880 kcal/day deficit
# Practical ceiling: deficit should not exceed 750 kcal/day to preserve LBM

MAX_CUTTING_DEFICIT_KCAL_PER_DAY = 750
```

**Decision rules for loss rate:**
```python
if current_loss_rate_pct_per_week < 0.5:
    status = "LOSS_TOO_SLOW"
    action = "reduce_calories"

elif current_loss_rate_pct_per_week > 1.0:
    status = "LOSS_TOO_FAST"
    action = "increase_calories"  # risk of LBM loss

else:
    status = "LOSS_ON_TARGET"
    action = "hold_calories"
```

**Evidence:** Aguilar-Navarro et al. (2021) report that weekly weight losses of 0.5% of BW show meaningfully greater FFM retention than losses of 0.7% or 1.0% BW/week, where LBM loss reached 42.8% of total weight lost in the most aggressive group.

RP Strength / Mike Israetel recommends aiming for ~1 lb/week for most of a cut, dropping to ~0.5 lbs/week near end of cut when BF% is very low. Maximum deficit ≤500 kcal/day for muscle-preserving cuts.

---

#### Lean Bulk Phase (BULKING)

**Target:** 0.25–0.5% of body weight gained per month for intermediates.

**Source:** Iraki J, Fitschen P, Espinar S, Helms E. "Nutrition Recommendations for Bodybuilders in the Off-Season: A Narrative Review." *Sports (Basel).* 2019;7(7):154. Dr. Helms is a co-author. Referenced in [Bony to Beastly analysis](https://bonytobeastly.com/how-fast-to-gain-weight-bulking/): "he recommends that more advanced lifters gain no more than 0.25% of their body weight per week."

```python
# Lean bulk rate targets (as % body weight per MONTH)
BULKING_RATE_MIN_PCT_PER_MONTH = 0.25   # intermediates (lower bound)
BULKING_RATE_MAX_PCT_PER_MONTH = 1.0    # beginners (upper bound)
BULKING_RATE_INTERMEDIATE_PCT = 0.5     # default for intermediate lifters

# As % body weight per WEEK (for biweekly comparison):
BULKING_RATE_MIN_PCT_PER_WEEK = 0.0625  # 0.25% per month / 4 weeks
BULKING_RATE_MAX_PCT_PER_WEEK = 0.25    # 1.0% per month / 4 weeks

# Calorie surplus implied:
# At 80 kg intermediate: 0.5% per month = 400g → ~215 kcal/day surplus
# At 80 kg beginner: 1.0% per month = 800g → ~430 kcal/day surplus

# Eric Helms guidance from YouTube (2024): 10-20% above maintenance
# Slower end (10%): ~200-250 kcal surplus
# Faster end (20%): ~400-500 kcal surplus
```

**Beginner vs. intermediate distinction:**

```python
def get_target_bulk_rate_pct_per_week(experience_level: str) -> dict:
    """
    Returns target rate of weight gain per week as % of body weight.
    """
    rates = {
        "BEGINNER":      {"min": 0.25/4, "target": 0.5/4, "max": 2.0/4},
        "INTERMEDIATE":  {"min": 0.25/4, "target": 0.25/4, "max": 0.5/4},  # Iraki/Helms 2019
        "ADVANCED":      {"min": 0.0,    "target": 0.125/4, "max": 0.25/4}
    }
    return rates.get(experience_level, rates["INTERMEDIATE"])
```

**Source for beginner rate (Daniel Weiss Coaching / Helms):**  
Beginners: up to 2% total body weight/month; Intermediates: up to 1.5%/month; Advanced: up to 1.0%/month. For Milo's male beginner-to-intermediate population, the appropriate range is 1–2% per month at the start, converging toward 0.5–1% as the user gains experience.

---

### 3.3 Biweekly Calorie Adjustment Protocol

**Adjustment trigger:** Every 14 days (biweekly), compare 7-day weight average at end of period vs. 7-day weight average at start. Based on deviation from target rate, adjust calories.

**Adjustment amounts:**

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

**Source for 100–200 kcal adjustment magnitude:**  
JC Fitness (citing Eric Helms directly): "Eric Helms recommends a deficit of 100 calories if the predicted weight loss is less than 0.5% per week." This conservative adjustment avoids overreaction to noise while ensuring progress.

---

**Full biweekly adjustment pseudocode:**

```python
def biweekly_calorie_adjustment(goal_phase: GoalPhase,
                                 current_calories: int,
                                 rate_pct_per_week: float,  # actual rate observed
                                 body_weight_kg: float,
                                 experience_level: str,
                                 consecutive_stall_periods: int = 0) -> dict:
    """
    Computes new calorie target based on 14-day weight trend.
    
    rate_pct_per_week: positive = gaining, negative = losing
    consecutive_stall_periods: how many consecutive biweekly periods with same issue
    
    Returns: new calorie target + reason code
    """
    
    adjustment = 0
    reason = "ON_TARGET"
    
    if goal_phase == GoalPhase.CUTTING:
        
        if rate_pct_per_week > -0.5:  # not losing fast enough (or gaining)
            # Stall or insufficient deficit
            if rate_pct_per_week >= 0:  # weight stable or increasing
                adjustment = -200
                reason = "CUTTING_STALLED"
            else:  # losing but slower than target
                adjustment = -100
                reason = "CUTTING_TOO_SLOW"
            
            # If stall has persisted 2+ cycles, apply full 200 kcal reduction
            if consecutive_stall_periods >= 2:
                adjustment = -200
                reason = "CUTTING_PERSISTENT_STALL"
        
        elif rate_pct_per_week < -1.0:  # losing too fast — LBM risk
            adjustment = +150
            reason = "CUTTING_TOO_FAST_LBM_RISK"
        
        else:
            reason = "CUTTING_ON_TARGET"
    
    elif goal_phase == GoalPhase.BULKING:
        
        # Get target rates for experience level
        target_rates = get_target_bulk_rate_pct_per_week(experience_level)
        
        if rate_pct_per_week < target_rates["min"]:
            # Not gaining enough
            adjustment = +200
            reason = "BULKING_TOO_SLOW"
            
            if consecutive_stall_periods >= 2:
                adjustment = +200  # maintain full adjustment
                reason = "BULKING_PERSISTENT_STALL"
        
        elif rate_pct_per_week > target_rates["max"]:
            # Gaining too fast — excess fat accumulation
            adjustment = -150
            reason = "BULKING_TOO_FAST"
        
        else:
            reason = "BULKING_ON_TARGET"
    
    elif goal_phase == GoalPhase.MAINTENANCE:
        
        if rate_pct_per_week > 0.25:  # gaining weight unintentionally
            adjustment = -100
            reason = "MAINTENANCE_GAINING"
        
        elif rate_pct_per_week < -0.25:  # losing weight unintentionally
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

---

### 3.4 Maintenance Detection Logic

Maintenance is detected when weight is stable within a specified tolerance window over 14 days:

```python
MAINTENANCE_WINDOW_PCT = 0.25  # ± 0.25% of body weight per week

def detect_maintenance(rate_pct_per_week: float, 
                        current_calories: int,
                        goal_phase: GoalPhase) -> dict:
    """
    Detects if user is effectively at maintenance.
    """
    
    is_stable = abs(rate_pct_per_week) < MAINTENANCE_WINDOW_PCT
    
    if is_stable and goal_phase == GoalPhase.MAINTENANCE:
        return {
            "status": "AT_MAINTENANCE",
            "maintenance_calories_estimate": current_calories,
            "confidence": "HIGH"
        }
    
    elif is_stable and goal_phase == GoalPhase.CUTTING:
        return {
            "status": "CUTTING_STALLED_AT_MAINTENANCE",
            "maintenance_calories_estimate": current_calories,
            "recommendation": "reduce_calories_by_100_to_200"
        }
    
    elif is_stable and goal_phase == GoalPhase.BULKING:
        return {
            "status": "BULKING_STALLED_AT_MAINTENANCE",
            "maintenance_calories_estimate": current_calories,
            "recommendation": "increase_calories_by_100_to_200"
        }
    
    return {"status": "WEIGHT_CHANGING", "rate_pct_per_week": rate_pct_per_week}
```

---

### 3.5 Calorie Floor and Ceiling Constraints

Hard limits to prevent unsafe extremes:

```python
# Minimum intake floor
CALORIE_FLOOR_MALE = 1500  # kcal/day; below this, muscle loss risk increases dramatically
CALORIE_FLOOR_ABSOLUTE = 1200  # never go below this regardless of circumstances

# Maximum cut depth (% below TDEE)
MAX_DEFICIT_PCT_OF_TDEE = 0.25  # 25% below TDEE; beyond this, metabolic adaptation worsens

# Maximum surplus (for bulking)
MAX_SURPLUS_KCAL = 600  # kcal/day above TDEE; beyond this, excess fat accumulation likely

def apply_calorie_bounds(target_calories: int, 
                          working_TDEE: int, 
                          goal_phase: GoalPhase) -> int:
    """
    Enforces safety floors and ceilings on calorie targets.
    """
    
    # Apply minimum floor
    if target_calories < CALORIE_FLOOR_MALE:
        target_calories = CALORIE_FLOOR_MALE
    
    # Apply phase-specific ceiling
    if goal_phase == GoalPhase.CUTTING:
        min_allowed = int(working_TDEE * (1 - MAX_DEFICIT_PCT_OF_TDEE))
        target_calories = max(target_calories, min_allowed, CALORIE_FLOOR_MALE)
    
    elif goal_phase == GoalPhase.BULKING:
        max_allowed = working_TDEE + MAX_SURPLUS_KCAL
        target_calories = min(target_calories, max_allowed)
    
    return target_calories
```

---

## 4. Metabolic Adaptation Modeling

### 4.1 Definition and Evidence

**Metabolic adaptation** (also called adaptive thermogenesis) is the decline in TDEE that exceeds what would be predicted from changes in body composition alone during caloric deficit. It represents the body's defense mechanism against weight loss.

**Key evidence sources:**

1. **Trexler ET, Smith-Ryan AE, Norton LE.** "Metabolic adaptation to weight loss: implications for the athlete." *J Int Soc Sports Nutr.* 2014;11:7. [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC3943438/)  
   — Confirmed that TDEE declines beyond what body mass loss alone predicts  
   — Adaptive thermogenesis and decreased EE persist **after the active weight loss period**, even in subjects who have maintained reduced body weight for >1 year  
   — Adaptive thermogenesis includes: decreased BMR, decreased NEAT, decreased EAT (exercise activity thermogenesis), decreased TEF, and increased skeletal muscle efficiency

2. **Rosenbaum M & Leibel RL.** "Adaptive thermogenesis in humans." *Int J Obes.* 2010;34(Suppl 1):S47–S55. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3673773/)  
   — Maintenance of ≥10% body weight reduction is accompanied by ~20–25% decline in 24-hour energy expenditure  
   — This decrease is **10–15% below** what would be predicted solely from changes in fat and lean mass  
   — The excess reduction is mostly from NREE (non-resting EE), accounting for 85–90% of the unexplained decline

3. **Martins et al. (2020).** "Metabolic adaptation is an illusion, only present when participants are in negative energy balance." *Obesity.*  
   — After a 14 kg (~13%) weight loss: adaptation of −92 kcal/day immediately post-weight loss, reduced to −38 kcal/day after 4 weeks of weight stabilization  
   — Under true energy balance conditions, metabolic adaptation at the RMR level ≈ **~50 kcal/day** (much smaller than often claimed)  
   — Metabolic adaptation does NOT persist at 1-year follow-up if weight is stabilized

---

### 4.2 Magnitude of Adaptation

**Key data points for Milo's modeling:**

| Study / Source | Weight Loss | Adaptation at RMR | Total TDEE Decline Beyond Prediction |
|---|---|---|---|
| Leibel et al. 1995 | 10% body weight | −137 kcal/day (immediately) | −10–15% below predicted |
| Martins et al. 2020 | 13–14 kg | −92 kcal/day (immediate); −38 kcal/day (stable) | — |
| Rosenbaum & Leibel 2010 | ≥10% body weight | 10–15% of decline at REE | 85–90% from NREE |
| Trexler et al. 2014 | Various (athletes) | Significant; persists >1 year | Full TDEE drops exceed composition-based prediction |

**Conservative model for Milo:**

```python
def estimate_metabolic_adaptation(
        weeks_in_deficit: int,
        pct_body_weight_lost: float,   # cumulative % BW lost since cut started
        is_weight_stabilized: bool = False
) -> float:
    """
    Conservative estimate of metabolic adaptation below predicted TDEE.
    Returns kcal/day that TDEE is below what composition changes would predict.
    
    Based on: Rosenbaum & Leibel (2010), Martins et al. (2020), Trexler et al. (2014)
    """
    
    # Base adaptation rate: ~50 kcal/day per 5% BW lost (when weight-stable)
    # Acute (during active deficit): higher, ~100-150 kcal/day per 5% BW lost
    
    if pct_body_weight_lost < 3:
        adaptation_kcal = 0  # minimal adaptation at early stages
    
    elif pct_body_weight_lost < 7:
        base = 50  # kcal/day conservative baseline
        if not is_weight_stabilized:
            base = 100  # acute phase — larger apparent adaptation
        adaptation_kcal = base
    
    elif pct_body_weight_lost < 12:
        base = 100
        if not is_weight_stabilized:
            base = 150
        adaptation_kcal = base
    
    else:  # ≥12% BW lost — significant adaptation territory
        base = 150
        if not is_weight_stabilized:
            base = 200
        adaptation_kcal = base
    
    # Apply duration modifier: adaptation builds over time
    duration_factor = min(1.0, 0.5 + (weeks_in_deficit / 20))
    
    return round(adaptation_kcal * duration_factor)
```

**Key design decision:** Do not pre-emptively reduce calorie targets to account for adaptation. The adaptive TDEE calculation (Section 2.3) already captures adaptation in the real-world data — the adaptive TDEE will naturally fall as adaptation occurs. Separate adaptation modeling would double-count the adjustment.

---

### 4.3 Modeling Adaptation Conservatively: Do Not Over-Adjust

**The problem with aggressive pre-emptive adjustments:**  
If Milo assumes large metabolic adaptation and proactively reduces calories significantly, it will push the user into an excessively low intake — especially if the user's actual adaptation is mild (as Martins et al. 2020 suggest in weight-stable individuals, where adaptation was only ~50 kcal/day at RMR level).

**Conservative approach for Milo:**

```python
METABOLIC_ADAPTATION_BUFFER_KCAL = 50   # kcal/day to account for adaptation when
                                          # relying on equation-based TDEE only
                                          # (not needed when using adaptive TDEE)

# Only apply adaptation buffer when:
# 1. User has < 2 weeks of tracking data (equation-based only)
# 2. User is > 6 weeks into a cut
# 3. Weight loss has been ≥ 7% of starting body weight

def apply_adaptation_buffer(equation_TDEE: float,
                              weeks_in_deficit: int,
                              cumulative_weight_loss_pct: float,
                              using_adaptive_TDEE: bool) -> float:
    """
    Applies a conservative downward correction to equation-based TDEE
    to partially account for metabolic adaptation.
    
    NOT applied when using adaptive TDEE (which already captures real-world adaptation).
    """
    
    if using_adaptive_TDEE:
        return equation_TDEE  # no correction needed — adaptive TDEE accounts for it
    
    if weeks_in_deficit < 6 or cumulative_weight_loss_pct < 7:
        return equation_TDEE  # no significant adaptation yet
    
    # Apply conservative 50–100 kcal buffer
    if cumulative_weight_loss_pct < 12:
        buffer = 75
    else:
        buffer = 125
    
    return equation_TDEE - buffer
```

---

### 4.4 Cut Duration: When to Transition to Maintenance

**Duration-based trigger:**

Prolonged deficits (>12–16 weeks) increase the risk of significant metabolic adaptation, muscle loss, hormonal disruption (decreased leptin, testosterone, T3; increased cortisol, ghrelin), and psychological fatigue.

```python
# Duration limits for continuous cutting
CUT_DURATION_WARNING_WEEKS = 12    # issue advisory, monitor closely
CUT_DURATION_MAX_WEEKS = 16        # recommend transitioning to maintenance
CUT_DURATION_ABSOLUTE_MAX_WEEKS = 20  # force maintenance phase regardless of goal

def check_cut_duration(weeks_in_active_deficit: int,
                        cumulative_weight_loss_pct: float) -> dict:
    """
    Monitors cut duration and recommends phase transitions.
    """
    
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

**Rate-based trigger:**

If weight loss has stalled for ≥3 consecutive biweekly cycles AND calorie reduction has already been applied (calories are already at the CALORIE_FLOOR or TDEE × 0.80), this signals significant metabolic adaptation and should trigger a maintenance phase rather than further reduction.

```python
def check_rate_based_transition(consecutive_stall_cycles: int,
                                  current_calories: int,
                                  working_TDEE: int,
                                  goal_phase: GoalPhase) -> dict:
    """
    Rate-based trigger for phase transitions during cutting.
    """
    
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
    
    return {
        "status": "ADJUSTABLE",
        "consecutive_stalls": consecutive_stall_cycles,
        "deficit_pct": round(current_deficit_pct * 100, 1)
    }
```

---

### 4.5 NEAT Suppression Warning

A major component of metabolic adaptation is unconscious reduction in NEAT (non-exercise activity thermogenesis) — fidgeting, spontaneous movement, posture, etc. This can account for 85–90% of the TDEE decline beyond what composition changes explain (Rosenbaum & Leibel, 2010).

This cannot be directly measured in Milo's system, but the adaptive TDEE calculation will implicitly capture it. If the user is experiencing unusually rapid adaptive TDEE decline (>200 kcal/day below equation-based TDEE at same body weight), it may indicate significant NEAT suppression.

**Flag for monitoring:**

```python
NEAT_SUPPRESSION_THRESHOLD_KCAL = 200  # kcal/day below equation-based TDEE

def flag_neat_suppression(equation_TDEE: float, 
                           adaptive_TDEE: float,
                           current_weight_kg: float,
                           baseline_weight_kg: float) -> dict:
    """
    Flags potential significant NEAT suppression.
    Compares adaptive TDEE to expected TDEE adjusted for weight change.
    """
    
    # Adjust equation TDEE for weight loss (expected reduction from body mass alone)
    # Rough estimate: ~20-22 kcal/kg lost
    weight_loss_kg = baseline_weight_kg - current_weight_kg
    expected_TDEE_reduction = weight_loss_kg * 21  # kcal/kg of weight lost
    
    adjusted_equation_TDEE = equation_TDEE - expected_TDEE_reduction
    adaptation_kcal = adjusted_equation_TDEE - adaptive_TDEE
    
    if adaptation_kcal > NEAT_SUPPRESSION_THRESHOLD_KCAL:
        return {
            "flag": "SIGNIFICANT_NEAT_SUPPRESSION_SUSPECTED",
            "adaptation_magnitude_kcal": round(adaptation_kcal),
            "action": "Consider mandatory maintenance phase or activity increase"
        }
    
    return {
        "flag": "WITHIN_NORMAL_RANGE",
        "adaptation_kcal": round(adaptation_kcal)
    }
```

---

## 5. Variable Reference Table

| Variable | Type | Unit | Default | Source |
|---|---|---|---|---|
| `weight_kg` | float | kg | — | User input |
| `height_cm` | float | cm | — | User input |
| `age_yr` | int | years | — | User input |
| `body_fat_pct` | float | % | None | Optional user input |
| `LBM_kg` | float | kg | Computed | `weight_kg × (1 − BF%)` |
| `BMR` | float | kcal/day | Computed | Selected equation |
| `activity_multiplier` | float | — | 1.55 | Moderately Active default |
| `TDEE_estimated` | float | kcal/day | Computed | `BMR × activity_multiplier` |
| `adaptive_TDEE` | float | kcal/day | None until 2 weeks data | Back-calculated |
| `working_TDEE` | float | kcal/day | Computed | Blended (equation + adaptive) |
| `target_calories` | int | kcal/day | Computed | `working_TDEE ± goal_adjustment` |
| `weight_delta_kg` | float | kg | Computed | 7-day avg week2 − 7-day avg week1 |
| `rate_pct_per_week` | float | %/week | Computed | `(weight_delta / body_weight) × 100` |
| `KCAL_PER_KG_TISSUE` | int | kcal/kg | 7700 | Mixed tissue energy constant |
| `consecutive_stall_cycles` | int | cycles | 0 | Counter |
| `weeks_in_deficit` | int | weeks | 0 | Counter |
| `cumulative_weight_loss_pct` | float | % | 0 | `(start_weight − current_weight) / start_weight × 100` |
| `CUTTING_RATE_TARGET_PCT_PER_WEEK` | float | %/week | 0.75 | Helms et al. 2014 |
| `MAX_DEFICIT_PCT_OF_TDEE` | float | — | 0.25 | Safety bound |
| `CUT_DURATION_MAX_WEEKS` | int | weeks | 16 | Conservative clinical guideline |
| `CALORIE_FLOOR_MALE` | int | kcal/day | 1500 | Minimum safe intake |

---

## 6. Decision Logic Master Flow

```
START BIWEEKLY ADJUSTMENT CYCLE
│
├── Input: 14-day weight log, 14-day calorie log, current goal_phase
│
├── STEP 1: Data Quality Check
│   ├── valid_weight_readings >= 8 of 14 days?
│   │   ├── YES → proceed
│   │   └── NO → flag LOW_DATA_QUALITY; hold current calories; request more data
│   │
│   └── calorie_logging_completeness >= 80%?
│       ├── YES → proceed with adaptive TDEE calculation
│       └── NO → use equation-based TDEE only; log_warning("Insufficient calorie data")
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
│   │   └── FORCE_MAINTENANCE? → override goal_phase to MAINTENANCE
│   │
│   ├── rate_based_transition_check(consecutive_stall_cycles, current_calories)
│   │   └── TRANSITION_RECOMMENDED? → flag for maintenance suggestion
│   │
│   └── neat_suppression_flag(equation_TDEE, adaptive_TDEE)
│       └── SIGNIFICANT? → advisory notification
│
├── STEP 5: Compute Calorie Adjustment
│   ├── IF goal_phase == CUTTING:
│   │   ├── rate_pct_per_week > −0.5 (not losing fast enough)?
│   │   │   └── adjustment = −100 to −200 kcal
│   │   ├── rate_pct_per_week < −1.0 (losing too fast)?
│   │   │   └── adjustment = +100 to +200 kcal
│   │   └── ELSE → adjustment = 0
│   │
│   ├── IF goal_phase == BULKING:
│   │   ├── rate_pct_per_week < target_min?
│   │   │   └── adjustment = +100 to +200 kcal
│   │   ├── rate_pct_per_week > target_max?
│   │   │   └── adjustment = −100 to −200 kcal
│   │   └── ELSE → adjustment = 0
│   │
│   └── IF goal_phase == MAINTENANCE:
│       ├── rate_pct_per_week > 0.25? → adjustment = −100 kcal
│       ├── rate_pct_per_week < −0.25? → adjustment = +100 kcal
│       └── ELSE → adjustment = 0
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

## References

1. Mifflin MD, St Jeor ST, Hill LA, Scott BJ, Daugherty SA, Koh YO. "A new predictive equation for resting energy expenditure in healthy individuals." *Am J Clin Nutr.* 1990;51(2):241–247.

2. Frankenfield D, Roth-Yousey L, Compher C. "Comparison of predictive equations for resting metabolic rate in healthy nonobese and obese adults: a systematic review." *J Am Diet Assoc.* 2005;105(5):775–789. [PubMed](https://pubmed.ncbi.nlm.nih.gov/15883556/)

3. Roza AM, Shizgal HM. "The Harris Benedict equation reevaluated: resting energy requirements and the body cell mass." *Am J Clin Nutr.* 1984;40(1):168–182. [PDF](https://zakboekdietetiek.nl/wp-content/uploads/2015/06/roza-1984.pdf)

4. Cunningham JJ. "A reanalysis of the factors influencing basal metabolic rate in normal adults." *Am J Clin Nutr.* 1980;33(11):2372–2374.

5. Katch FI, McArdle WD. *Nutrition, Weight Control, and Exercise.* 1975. (Katch-McArdle BMR formula: BMR = 370 + 21.6 × LBM_kg)

6. Helms ER, Valdez A, Morgan A. *The Muscle and Strength Pyramid: Nutrition.* 2nd ed. 3D Muscle Journey; 2019. — Biweekly weight averaging, TDEE calibration from tracking, calorie adjustment protocols.

7. Iraki J, Fitschen P, Espinar S, Helms E. "Nutrition Recommendations for Bodybuilders in the Off-Season: A Narrative Review." *Sports (Basel).* 2019;7(7):154. — 0.25–0.5% BW/month lean bulk rate for intermediates.

8. Trexler ET, Smith-Ryan AE, Norton LE. "Metabolic adaptation to weight loss: implications for the athlete." *J Int Soc Sports Nutr.* 2014;11:7. [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC3943438/)

9. Rosenbaum M, Leibel RL. "Adaptive thermogenesis in humans." *Int J Obes.* 2010;34(Suppl 1):S47–S55. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3673773/)

10. Rosenbaum M, Hirsch J, Gallagher DA, Leibel RL. "Long-term persistence of adaptive thermogenesis in subjects who have maintained a reduced body weight." *Am J Clin Nutr.* 2008;88(4):906–912.

11. Aguilar-Navarro M, et al. "Achieving an Optimal Fat Loss Phase in Resistance-Trained Athletes." *Nutrients.* 2021;13(9):3255. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8471721/) — 0.5–1.0% BW/week fat loss recommendation with FFM retention data.

12. Flegal KM, et al. "Bias and accuracy of resting metabolic rate equations in non-obese and obese adults." *Clin Nutr.* 2013. [PubMed](https://pubmed.ncbi.nlm.nih.gov/23631843/) — Mifflin-St Jeor validated unbiased in 337 community-living adults.

13. Martins C, et al. "Metabolic adaptation is an illusion, only present when participants are in negative energy balance." *Obesity.* 2020. [Semantic Scholar PDF](https://pdfs.semanticscholar.org/2625/c7ca159f119ec5d083666198e722c739dd66.pdf) — ~50 kcal/day adaptation at weight-stable RMR; adaptation reduced to zero at 1-year follow-up.

14. Leibel RL, Rosenbaum M, Hirsch J. "Changes in energy expenditure resulting from altered body weight." *N Engl J Med.* 1995;332:621–628.

---

*Document prepared for Milo AI backend system. Variables and pseudocode intended for direct implementation. All formulas use SI units (kg, cm) unless otherwise specified.*
