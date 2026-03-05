# Track 8: Full-Body Programming Design, Frequency, and Customizable Volume Distribution
## Milo AI Fitness Coaching System — Backend Logic Reference Document

**Purpose:** This document defines variables, rules, decision logic, and templates for the Milo full-body programming engine. All sections are written for AI agent consumption, not end-user display.

---

## TABLE OF CONTENTS

1. [Training Frequency Evidence](#1-training-frequency-evidence)
2. [Full-Body Programming Advantages and Design](#2-full-body-programming-advantages-and-design)
3. [Exercise Selection Framework](#3-exercise-selection-framework)
4. [Customizable Volume Distribution Model](#4-customizable-volume-distribution-model)
5. [Weekly Template Generation Logic](#5-weekly-template-generation-logic)
6. [Session Structure Templates](#6-session-structure-templates)

---

## 1. TRAINING FREQUENCY EVIDENCE

### 1.1 Core Meta-Analytic Finding: Schoenfeld et al. 2016

**Citation:** Schoenfeld, B.J., Ogborn, D., & Krieger, J.W. (2016). *Effects of Resistance Training Frequency on Measures of Muscle Hypertrophy: A Systematic Review and Meta-Analysis.* Sports Medicine. DOI: 10.1007/s40279-016-0543-8. [PubMed abstract](https://pubmed.ncbi.nlm.nih.gov/27102172/)

**Key results:**
- Binary frequency analysis: higher-frequency groups showed significantly greater hypertrophy effect size (ES = 0.49 ± 0.08) vs. lower-frequency groups (ES = 0.30 ± 0.07), p = 0.002
- Mean percent change for higher frequency: 6.8 ± 0.7%; lower frequency: 3.7 ± 0.5%
- Conclusion: training a muscle group **≥2x/week is superior to 1x/week** on a volume-equated basis
- Insufficient data at the time to determine whether 3x/week was superior to 2x/week

**Implementation variable:**
```
MINIMUM_FREQUENCY_PER_MUSCLE_PER_WEEK = 2  // default; based on Schoenfeld 2016
```

---

### 1.2 Is 3x/Week Better Than 2x/Week?

**Evidence summary (post-2016):**

**Stronger-by-Science meta-analysis (Krieger, 2020):**  
Regression analysis across 19 studies (direct hypertrophy measures) found a roughly **linear relationship between frequency and hypertrophic overperformance**, with each additional training day adding ~0.11% weekly hypertrophy (CI: 0.05–0.16%). However, the absolute effect per extra day is small. Groups training 3x/week essentially performed at par in direct comparisons; groups training 4x+/week overperformed by 0.185%/week. Source: [Stronger by Science](https://www.strongerbyscience.com/frequency-muscle/)

**Schoenfeld 2018 updated meta-analysis:**  
25 studies. Conclusion: "there is strong evidence that resistance training frequency does **not** significantly or meaningfully impact muscle hypertrophy when **volume is equated**." Implication: when volume is fixed, 2x and 3x produce similar results. Higher frequency mainly matters as a mechanism to **accumulate more total volume** within session-size constraints. Source: [Facebook summary of Schoenfeld 2018 meta via Barbell Medicine](https://www.facebook.com/groups/BarbellMedicineGroup/posts/2196804847230769/)

**Colquhoun et al. (2019) — Journal of Human Kinetics:**  
36 resistance-trained men randomized to 2x/week (split, 4 sessions/week) vs. 3x/week (total-body, 3 sessions/week), volume equated over 10 weeks. Result: **no significant difference** in hypertrophy (elbow extensors, quadriceps). Small effect sizes (0.31–0.39) *favored 2x/week* per muscle for all hypertrophy measures (i.e., split training). Conclusion: "training muscle groups either twice or three times per week results in similar increases in muscular strength and hypertrophy." Source: [PMC6724585](https://pmc.ncbi.nlm.nih.gov/articles/PMC6724585/)

**Israetel frequency estimates (qualitative):**  
1x/week = growth factor ~1.0; 2x/week = ~1.5x growth factor; 3x/week = ~1.75x growth factor; beyond 3x/week, diminishing returns. Source: [Reddit AdvancedFitness summary of RP guidelines](https://www.reddit.com/r/AdvancedFitness/comments/lyney9/summary_of_dr_mike_israetel_and_renaissance/)

**Practical interpretation for Milo:**  
- **2x/week per muscle = the evidence-based default.** Volume-matched 3x/week adds modest benefit (~1.75x vs. 1.5x growth factor relative to 1x).
- **3x/week becomes worth targeting only when:** (a) 2x/week volume has reached session MRV limits, requiring volume split across 3 sessions; or (b) the user's recovery allows it without performance degradation.
- **Frequency is primarily a tool to manage per-session volume load**, not an independent driver of growth once volume is equated.

**Decision rule:**
```python
def get_target_muscle_frequency(training_days, muscle_priority):
    """
    Returns target training_frequency (times/week) for a muscle group.
    
    Rules:
    - Default: 2x/week for all major muscles
    - If training_days <= 2: 1–2x/week may be unavoidable for some muscles
    - If training_days >= 5 and muscle_priority == "HIGH": can target 3x/week
    - If muscle's weekly volume target > per_session_MEV * 2: consider 3x split
    """
    if training_days <= 2:
        return 1  # low frequency; compensate with higher per-session volume
    elif training_days in [3, 4]:
        return 2  # standard; achieves 2x/week per muscle via rotation
    elif training_days >= 5:
        if muscle_priority == "HIGH":
            return 3  # high-priority muscle gets extra stimulus
        else:
            return 2  # non-priority muscles maintain 2x
```

---

### 1.3 Weekly Frequency Distribution for Full-Body Training

**Core rule:** Minimum 48 hours of recovery between sessions targeting the same muscle group. Exception: very low-volume "feeder" sessions for smaller muscles (arms, calves) may be performed on consecutive days.

**Frequency distribution by training days:**

| Training Days/Week | Muscle Frequency/Week | Weekly Schedule Pattern |
|---|---|---|
| 2 | 2x all major muscles | Mon + Thu, or any 2 non-consecutive days |
| 3 | 2x (A-B-A / B-A-B rotation) | Mon-Wed-Fri (every other day) |
| 4 | 2–3x depending on rotation | Mon-Tue-Thu-Fri (2-on/1-off pattern) |
| 5 | 2–3x depending on priority | Mon-Tue-Wed-Fri-Sat (1 rest day mid-week) |
| 6 | 2–3x most muscles; 3x priority | Mon-Tue-Wed-Thu-Fri-Sat; or 6-on/1-off |

**Rule: no two sessions targeting the same large compound pattern (e.g., heavy squat) on consecutive days unless session intensity (RIR) is differentiated (e.g., Day 1 = RIR 1–2; Day 2 = RIR 3–4, reduced volume).**

---

## 2. FULL-BODY PROGRAMMING ADVANTAGES AND DESIGN

### 2.1 Evidence Base for Full-Body Training

**Ramos-Campo et al. (2021) — Einstein Journal (PMC8372753):**  
67 untrained subjects randomized to Split Workout Routine (2x/week per muscle, 8 sets/session) vs. Full-Body Routine (4x/week per muscle, 4 sets/session). Both trained 4 sessions/week with identical total weekly volume. Result: **similar gains in bench press 1RM (+18.1% split vs. +17.5% full-body), squat 1RM (+28.2% split vs. +28.6% full-body), and muscle thickness in upper and lower limbs.** Conclusion: both strategies equally effective when volume is equated. Source: [PMC8372753](https://pmc.ncbi.nlm.nih.gov/articles/PMC8372753/)

**Practical advantages of full-body for beginners/intermediates:**
1. **Scheduling resilience:** missing one session doesn't create a gap for any muscle group
2. **Frequency efficiency:** 2x/week per muscle achieved in as few as 2 sessions
3. **Neural reinforcement:** more frequent practice of movement patterns accelerates technique learning for beginners
4. **Lower per-session fatigue accumulation:** volume per muscle group per session is moderate, allowing higher quality sets
5. **Balanced development:** all muscles trained with similar attention; no muscle group neglected

**When to transition to a split:**
```python
def recommend_split_transition(training_age_months, weekly_sets_per_muscle, training_days):
    """
    Returns True if a split is likely warranted.
    
    Criteria for split transition:
    - Training age > 18 months (past beginner-intermediate)
    - Weekly volume needs exceed ~20+ sets/muscle for multiple groups
    - Training days >= 4 AND per-session duration exceeds ~90 min with full-body
    - Performance plateau persists despite volume progression
    """
    if (training_age_months > 18 and 
        max(weekly_sets_per_muscle.values()) > 20 and 
        training_days >= 4):
        return True  # upper/lower split recommended
    return False
```

**Source note:** Mike Israetel distinguishes beginner, intermediate, and advanced by training quality requirements. Beginners and early intermediates make gains easily; full-body is optimal. Source: [RP Strength YouTube — Beginner/Intermediate/Advanced Hypertrophy](https://www.youtube.com/watch?v=2aYrGSPZmpk)

---

### 2.2 Compound-First Principle: Evidence and Rules

**NSCA principle (from NSCA's Guide to Program Design):**  
"Multiple-joint exercises should be performed before single-joint exercises." Exercises performed early yield greater rates of force development, higher rep counts, and heavier loads. Studies show performance of multi-joint exercises declines significantly when preceded by exercises that fatigue overlapping muscles. Source: [Human Kinetics NSCA excerpt](https://us.humankinetics.com/blogs/excerpt/utilize-proper-workout-structure-and-exercise-order)

**Session exercise order rules:**
```
EXERCISE_ORDER_PRIORITY = [
    1: "Primary compound — lower body (squat or hinge variations)",
    2: "Primary compound — upper body pull (row or vertical pull)",
    3: "Primary compound — upper body push (horizontal or vertical press)",
    4: "Secondary compound (lunge, dip, chin-up, secondary row)",
    5: "Isolation — large muscles (leg curls, lateral raises, rear delts)",
    6: "Isolation — small muscles (curls, tricep extensions, calf raises)",
    7: "Core (abs/obliques, if included)"
]
```

**Agonist-antagonist pairing rule:**  
Alternate upper/lower or push/pull within a session to allow partial recovery without extending session duration. Example: squat → row → RDL → press → leg curl → lateral raise.

**Energy conservation rule:**
```python
def check_compound_adjacency(exercise_queue):
    """
    Flag a session where two high-CNS-demand exercises appear consecutively.
    High-CNS exercises: back squat, deadlift, barbell RDL, overhead press (heavy).
    """
    HIGH_CNS = ["back_squat", "deadlift", "rdl_barbell", "ohp_barbell"]
    for i in range(len(exercise_queue) - 1):
        if (exercise_queue[i] in HIGH_CNS and 
            exercise_queue[i+1] in HIGH_CNS):
            return "WARNING: Consecutive CNS-heavy compounds. Reorder or separate."
    return "OK"
```

---

### 2.3 How Many Exercises Per Session by Training Frequency

**Per-session volume capacity constraints:**  
Evidence suggests 6–10 hard sets per muscle per session is the practical ceiling before additional sets primarily generate fatigue without proportional additional growth stimulus. Source: [Reddit naturalbodybuilding — high frequency full-body discussion](https://www.reddit.com/r/naturalbodybuilding/comments/1ogc6ri/high_frequency_full_body_hypertrophy_training_for/)

**Session targets by training frequency:**

| Training Days/Week | Exercises Per Session | Working Sets Per Muscle/Session | Session Duration |
|---|---|---|---|
| 2 | 6–8 | 3–5 | 60–90 min |
| 3 | 5–7 | 2–4 | 50–75 min |
| 4 | 4–6 | 2–3 | 45–65 min |
| 5 | 4–5 | 2–3 | 40–60 min |
| 6 | 3–5 | 1–2 | 35–55 min |

**Rule:** as training frequency increases, per-session exercise count and sets decrease proportionally to maintain total weekly volume within recoverable range.

**5–6 day/week fatigue management rules:**
```
HIGH_FREQUENCY_FATIGUE_RULES = [
    "Alternate session intensity: HIGH (RIR 1-2) and MODERATE (RIR 2-4) days",
    "Limit consecutive high-intensity days to maximum 2 in a row",
    "No heavy bilateral lower-body compound (squat/DL) on consecutive days",
    "Use unilateral or machine substitutes on back-off days for lower body",
    "Weekly session 5-6 should use RIR 3-4 (deload-adjacent intensity)",
    "Deload week every 4-6 weeks: drop to MV-level sets at RIR 4-5"
]
```

---

## 3. EXERCISE SELECTION FRAMEWORK

### 3.1 Exercise Category Taxonomy

```python
EXERCISE_TAXONOMY = {
    
    "PRIMARY_COMPOUNDS": {
        "squat_variations": [
            "back_squat", "front_squat", "goblet_squat", "hack_squat", 
            "box_squat", "safety_bar_squat"
        ],
        "hinge_variations": [
            "conventional_deadlift", "romanian_deadlift", "sumo_deadlift",
            "trap_bar_deadlift", "good_morning"
        ],
        "horizontal_press": [
            "barbell_bench_press", "dumbbell_bench_press", "incline_barbell_press",
            "incline_dumbbell_press", "decline_bench_press"
        ],
        "vertical_press": [
            "barbell_overhead_press", "dumbbell_overhead_press", 
            "seated_db_shoulder_press", "arnold_press"
        ],
        "horizontal_pull": [
            "barbell_bent_over_row", "dumbbell_bent_over_row", "cable_row",
            "chest_supported_row", "pendlay_row", "t_bar_row"
        ],
        "vertical_pull": [
            "pull_up", "chin_up", "lat_pulldown", "neutral_grip_pulldown",
            "assisted_pull_up"
        ]
    },
    
    "SECONDARY_COMPOUNDS": {
        "lower_body": [
            "lunge_dumbbell", "lunge_barbell", "bulgarian_split_squat",
            "leg_press", "step_up", "hip_thrust"
        ],
        "upper_body_push": [
            "dips", "push_up_weighted", "cable_chest_press", "landmine_press"
        ],
        "upper_body_pull": [
            "single_arm_dumbbell_row", "cable_face_pull", "seal_row",
            "inverted_row", "neutral_grip_chin_up"
        ]
    },
    
    "ISOLATION_EXERCISES": {
        "biceps": [
            "dumbbell_curl", "barbell_curl", "hammer_curl", "preacher_curl",
            "incline_curl", "cable_curl"
        ],
        "triceps": [
            "tricep_pushdown_cable", "overhead_tricep_extension", "skull_crusher",
            "close_grip_bench_press", "dumbbell_kickback"
        ],
        "lateral_deltoid": [
            "dumbbell_lateral_raise", "cable_lateral_raise", "machine_lateral_raise"
        ],
        "rear_deltoid": [
            "dumbbell_reverse_fly", "cable_face_pull", "machine_rear_delt_fly",
            "band_pull_apart"
        ],
        "quadriceps": [
            "leg_extension_machine", "sissy_squat"
        ],
        "hamstrings": [
            "leg_curl_lying", "leg_curl_seated", "nordic_hamstring_curl"
        ],
        "glutes": [
            "hip_thrust_barbell", "cable_kickback", "glute_bridge"
        ],
        "calves": [
            "calf_raise_standing", "calf_raise_seated", "leg_press_calf_raise"
        ],
        "abs_core": [
            "crunch", "cable_crunch", "leg_raise", "plank", "ab_wheel_rollout",
            "hanging_knee_raise"
        ]
    }
}
```

**Primary vs. secondary distinction rule:**
```
PRIMARY_COMPOUNDS:
  - Multi-joint, high systemic fatigue cost
  - Train 2–5+ muscle groups simultaneously
  - Placed first in session (slots 1–3)
  - Load measured in absolute weight; progressive overload primary metric

SECONDARY_COMPOUNDS:
  - Multi-joint, moderate fatigue cost
  - Train 1–3 muscle groups primarily
  - Placed mid-session (slots 3–5)

ISOLATION_EXERCISES:
  - Single-joint, low systemic fatigue
  - Target one specific muscle/region
  - Placed last in session (slots 5–7)
  - Critical for: lateral delts, biceps, triceps long head, leg curls, rear delts
```

---

### 3.2 Muscles Requiring Direct Isolation Work

Some muscle groups are NOT adequately stimulated by compound exercises alone and require dedicated isolation:

| Muscle | Why Compounds Insufficient | Required Isolation |
|---|---|---|
| Lateral deltoid | No compound significantly involves shoulder abduction | Lateral raises |
| Biceps (full development) | Rows/pulldowns train supinated curl partially | Curls (various) |
| Triceps long head | Presses train medial/lateral; long head needs shoulder-extended position | Overhead extensions |
| Rear deltoid | Rows involve but don't fully isolate | Reverse flyes, face pulls |
| Hamstrings (knee flexion) | Hinges train hip extension; knee flexion requires additional work | Leg curls |
| Calves | Rarely adequately loaded in compound movements | Calf raises |

**Source:** [House of Hypertrophy — Compound vs. Isolation for Hypertrophy](https://houseofhypertrophy.com/compound-vs-isolation/)

---

### 3.3 Exercise Variety vs. Specificity: The Fonseca Principle

**Fonseca et al. (2014) — PubMed [24832974](https://pubmed.ncbi.nlm.nih.gov/24832974/):**  
Groups varying exercise selection vs. constant exercise. Key finding: groups using varied lower-body exercises developed **more uniform regional hypertrophy** across quadriceps heads (vastus medialis, rectus femoris, vastus intermedius) compared to a group performing only the barbell squat. The squat-only group showed inferior hypertrophy in the vastus medialis and rectus femoris.

**Costa et al. (2021):**  
Varied exercise group (3 different exercises per muscle per week) showed more regional hypertrophy gains across upper, middle, and lower regions of biceps and triceps compared to non-varied group. Source: [PMC6934277 — PLoS ONE](https://pmc.ncbi.nlm.nih.gov/articles/PMC6934277/)

**Practical rules:**
```python
EXERCISE_ROTATION_RULES = {
    "WITHIN_SESSION": "Do not repeat identical exercises within the same session",
    "SESSION_TO_SESSION": "Rotate at least one primary compound variation per muscle group between sessions A and B",
    "MESOCYCLE": "Change primary exercise variations every 4–6 weeks (mesocycle boundary)",
    "MINIMUM_VARIETY": "Target a minimum of 2 different exercise stimuli per muscle per week",
    "ISOLATION_VARIATION": "Allow same isolation exercise to repeat across sessions (consistency for progressive overload)",
    "SPECIFICITY_CONSTRAINT": "Do not vary so frequently that progressive overload tracking is lost (avoid weekly exercise changes)"
}
```

**Session rotation example (3-day / A-B-A rotation):**
```
Session A — Lower: Back Squat | Session B — Lower: Romanian Deadlift
Session A — Pull: Barbell Row | Session B — Pull: Lat Pulldown
Session A — Push: Barbell Bench | Session B — Push: Incline DB Press
```

---

### 3.4 Minimum Exercise Requirements Per Muscle Per Session

```python
MINIMUM_DIRECT_SETS_PER_MUSCLE_PER_SESSION = {
    "chest":          2,   # Working sets minimum
    "back_lats":      2,
    "back_traps":     1,
    "quads":          2,
    "hamstrings":     2,
    "glutes":         1,   # Often covered by squat/hinge compound
    "shoulders_lat":  2,   # Requires direct isolation
    "shoulders_rear": 1,
    "biceps":         1,   # 2+ if arms emphasis
    "triceps":        1,   # 2+ if arms emphasis
    "calves":         2,   # Often skipped; enforce in programming
}

NOTE: "Sets" above refer to working sets (not warm-up sets). Indirect sets from compounds count fractionally.
Fractional set counting rule:
  - Bench press counts as ~0.5 sets of triceps
  - Row counts as ~0.5 sets of biceps
  - Squat counts as ~0.3 sets of glutes and ~0.3 sets of hamstrings
  - Deadlift counts as ~0.5 sets of hamstrings and ~0.4 sets of glutes
```

---

## 4. CUSTOMIZABLE VOLUME DISTRIBUTION MODEL

### 4.1 Volume Landmark Reference Table (Israetel / RP Framework)

These values represent population-average weekly sets per muscle group. Individual values vary by training age, recovery capacity, and genetics.

**Source:** Compiled from [RP Strength volume landmarks article](https://rpstrength.com/blogs/articles/training-volume-landmarks-muscle-growth), [Reddit AdvancedFitness RP summary](https://www.reddit.com/r/AdvancedFitness/comments/lyney9/summary_of_dr_mike_israetel_and_renaissance/), and [FitnessRec volume landmarks guide](https://fitnessrec.com/articles/how-to-program-volume-landmarks-mrv-mav-and-mev-explained-for-optimal-muscle-growth).

| Muscle Group | MV (sets/wk) | MEV (sets/wk) | MAV Range (sets/wk) | MRV (sets/wk) | Default Freq |
|---|---|---|---|---|---|
| Chest | 6 | 10–12 | 14–20 | 20–26 | 2x |
| Back (lats) | 6 | 10–12 | 14–22 | 20–35 | 2–4x |
| Back (traps) | 0 | 0–6 | 12–20 | 26+ | 2–3x |
| Front Deltoid | 0 | 0 | 6–8 | 12 | 2x |
| Lateral Deltoid | 6 | 6–8 | 16–22 | 26 | 2–3x |
| Rear Deltoid | 0 | 6 | 16–22 | 26 | 2–3x |
| Biceps | 4 | 8–10 | 14–20 | 18–26 | 2–4x |
| Triceps | 4 | 8–10 | 10–14 | 18–26 | 2–4x |
| Quads | 6 | 8–10 | 14–20 | 20–28 | 2x |
| Hamstrings | 4 | 6–8 | 12–18 | 18–24 | 2x |
| Glutes | 0 | 0 | 12–20 | 16+ | 2–3x |
| Calves | 6 | 8–10 | 12–16 | 18–24 | 2–4x |
| Abs/Core | 0 | 0 | 8–20 | 25 | 3x |
| Forearms | 0 | 2–8 | 9–19 | 20+ | 2–6x |

**Variables:**
```
MV  = maintenance_volume     # Minimum sets to preserve existing muscle
MEV = minimum_effective_volume  # Minimum sets that produce growth
MAV = maximum_adaptive_volume   # Range where best growth occurs (target zone)
MRV = maximum_recoverable_volume  # Ceiling; chronic exposure causes performance decline
```

---

### 4.2 Emphasis Modes and Volume Multiplier System

**Emphasis Preference Enum:**
```python
class EmphasisMode(Enum):
    BALANCED         = "balanced"
    UPPER_EMPHASIS   = "upper_emphasis"
    LOWER_EMPHASIS   = "lower_emphasis"
    ARMS_EMPHASIS    = "arms_emphasis"
    CUSTOM           = "custom"
```

**Volume Allocation Model:**

The system operates by assigning a volume_multiplier to each muscle group based on the user's emphasis mode. The multiplier is applied against the baseline MAV_MID (midpoint of MAV range) to compute target weekly sets. The constraint is that **no muscle group drops below MEV** and **no muscle group exceeds MRV**. Total weekly session volume (sum of all sets) must remain within systemic fatigue tolerance.

```python
# Baseline: midpoint of MAV range for a beginner-intermediate
BASELINE_MAV_MID = {
    "chest":           12,
    "back_lats":       14,
    "back_traps":      8,
    "front_delts":     4,   # typically covered by pressing
    "lateral_delts":   12,
    "rear_delts":      10,
    "biceps":          10,
    "triceps":         10,
    "quads":           12,
    "hamstrings":      10,
    "glutes":          8,
    "calves":          10,
    "abs":             8
}
```

**Volume Multiplier Matrix by Emphasis Mode:**

| Muscle Group | Balanced | Upper Emphasis | Lower Emphasis | Arms Emphasis | Custom-Upper | Custom-Lower |
|---|---|---|---|---|---|---|
| Chest | 1.0 | 1.3 | 0.7 | 1.0 | 1.5 | 0.6 |
| Back (lats) | 1.0 | 1.3 | 0.7 | 1.0 | 1.5 | 0.6 |
| Lateral Delts | 1.0 | 1.2 | 0.7 | 1.0 | 1.3 | 0.6 |
| Rear Delts | 1.0 | 1.2 | 0.7 | 1.0 | 1.3 | 0.6 |
| Biceps | 1.0 | 1.0 | 0.7 | 1.5 | 0.8 | 0.6 |
| Triceps | 1.0 | 1.0 | 0.7 | 1.5 | 0.8 | 0.6 |
| Quads | 1.0 | 0.7 | 1.3 | 0.7 | 0.6 | 1.5 |
| Hamstrings | 1.0 | 0.7 | 1.3 | 0.7 | 0.6 | 1.5 |
| Glutes | 1.0 | 0.7 | 1.3 | 0.7 | 0.6 | 1.5 |
| Calves | 1.0 | 0.7 | 1.1 | 0.7 | 0.6 | 1.2 |

**Volume clamping rules:**
```python
def compute_target_weekly_sets(muscle, emphasis_mode, user_training_age="beginner"):
    """
    Compute weekly sets target for a muscle group given emphasis mode.
    Always clamped to [MEV, MRV].
    """
    baseline = BASELINE_MAV_MID[muscle]
    multiplier = VOLUME_MULTIPLIER_TABLE[emphasis_mode][muscle]
    raw_target = round(baseline * multiplier)
    
    # Clamp to evidence-based landmarks
    clamped = max(MEV[muscle], min(raw_target, MRV[muscle]))
    return clamped
```

---

### 4.3 Emphasis Modes — Detailed Logic

#### MODE: BALANCED
- All muscles target midpoint of MAV
- No muscle below MEV, no muscle above MAV_MID
- Use case: default for new users, no stated preference

#### MODE: UPPER_EMPHASIS
- Chest, back, shoulders, biceps, triceps → elevated toward MAV upper bound
- Quads, hamstrings, glutes → drop toward MEV (not below)
- Rationale: aesthetics-focused users who want V-taper, arm size, chest width
- Constraint: lower body volume floor = MEV (never drops to zero; structural health maintained)

#### MODE: LOWER_EMPHASIS
- Quads, hamstrings, glutes → elevated toward MAV upper bound  
- Upper body → drops toward MEV
- Rationale: users prioritizing quad sweep, glute development
- Constraint: upper body volume floor = MEV (pressing/pulling patterns maintained)

#### MODE: ARMS_EMPHASIS
- Biceps, triceps → push toward MAV upper bound (close to MRV if tolerance allows)
- Note: arms also receive indirect volume from all pressing (triceps) and pulling (biceps)
- Adjust for indirect volume by subtracting fractional set contributions from compounds before adding direct sets
- Other muscle groups remain at Balanced allocation

#### MODE: CUSTOM
- User specifies 1–2 priority muscle groups (e.g., "chest" and "lateral_delts")
- Priority muscles: multiplier 1.5 (approaching MAV upper bound)
- All other muscles: multiplier 0.7–0.8 (near MEV)
- Constraint: total weekly sets must not exceed SYSTEMIC_FATIGUE_CAP

```python
SYSTEMIC_FATIGUE_CAP = {
    # Total maximum working sets per week across ALL muscles
    # Based on training days and experience level
    "beginner_2day":       50,
    "beginner_3day":       60,
    "intermediate_3day":   80,
    "intermediate_4day":  100,
    "intermediate_5day":  115,
    "intermediate_6day":  130
}
```

---

### 4.4 Concrete Allocation Table Example (3-Day Intermediate, Balanced vs. Emphasis Modes)

Target weekly sets after multiplier application:

| Muscle Group | MEV | Balanced | Upper Emphasis | Lower Emphasis | Arms Emphasis |
|---|---|---|---|---|---|
| Chest | 10 | 12 | 16 | 8 (→MEV=10) | 12 |
| Back (lats) | 10 | 14 | 18 | 10 (MEV) | 14 |
| Lateral Delts | 6 | 12 | 14 | 8 (→MEV=6+) | 12 |
| Rear Delts | 6 | 10 | 12 | 7 (→MEV) | 10 |
| Biceps | 8 | 10 | 10 | 7 (→MEV=8) | 15 |
| Triceps | 8 | 10 | 10 | 7 (→MEV=8) | 15 |
| Quads | 8 | 12 | 8 (→MEV) | 16 | 8 (→MEV) |
| Hamstrings | 6 | 10 | 7 (→MEV) | 13 | 7 (→MEV) |
| Glutes | 0 | 8 | 6 | 10 | 6 |
| Calves | 8 | 10 | 7 (→MEV=8) | 11 | 7 (→MEV=8) |
| **TOTAL** | | **108** | **108** | **100** | **115** |

*Note: "→MEV" = raw calculation was below MEV, so clamped up to MEV. Arms Emphasis total is higher because direct arm isolation volume increases without cutting many other muscles.*

---

## 5. WEEKLY TEMPLATE GENERATION LOGIC

### 5.1 Algorithm: Weekly Plan Generator

**Inputs:**
```python
class WeeklyPlanInputs:
    training_days_per_week: int           # 2–6
    training_day_indices: List[int]       # e.g., [0,2,4] for Mon/Wed/Fri (0=Monday)
    emphasis_mode: EmphasisMode           # see Section 4.2
    priority_muscles: List[str]           # up to 2 muscles (for CUSTOM mode)
    volume_targets: Dict[str, int]        # computed weekly sets per muscle (Section 4.3)
    experience_level: str                 # "beginner" | "intermediate"
    session_duration_limit: int           # minutes; default 60
    rir_target: int                       # current mesocycle RIR target (1–4)
```

**Outputs:**
```python
class WeeklyPlan:
    sessions: List[Session]               # one Session object per training day
    weekly_sets_achieved: Dict[str, int]  # actual sets per muscle after generation
    session_balance_score: float          # measures fatigue parity across sessions

class Session:
    day_index: int                        # 0=Monday ... 6=Sunday
    session_label: str                    # "A", "B", "C" etc.
    exercises: List[ExerciseSlot]
    estimated_duration_minutes: int
    primary_fatigue_type: str             # "lower_dominant" | "upper_dominant" | "balanced"

class ExerciseSlot:
    exercise_name: str
    category: str                         # from EXERCISE_TAXONOMY
    target_muscle: List[str]
    sets: int
    rep_range: str                        # e.g., "8–12"
    rir: int
    rest_seconds: int
    notes: str
```

---

### 5.2 Distribution Algorithm (Pseudocode)

```python
def generate_weekly_plan(inputs: WeeklyPlanInputs) -> WeeklyPlan:
    
    # Step 1: Compute volume targets per muscle
    volume_targets = {}
    for muscle in ALL_MUSCLES:
        volume_targets[muscle] = compute_target_weekly_sets(muscle, inputs.emphasis_mode)
    
    # Step 2: Determine session count and type
    n = inputs.training_days_per_week
    session_labels = assign_session_labels(n)  # ["A", "B"] for 2-day; ["A", "B", "A"] for 3-day; etc.
    
    # Step 3: Distribute volume across sessions
    # Rule: divide total weekly sets by frequency; cap per-session sets using SESSION_VOLUME_CAPS
    session_targets = distribute_volume_to_sessions(volume_targets, n, inputs.emphasis_mode)
    
    # Step 4: Select exercises for each session
    for session_idx, session_label in enumerate(session_labels):
        exercises = select_exercises_for_session(
            session_label=session_label,
            session_targets=session_targets[session_idx],
            available_exercises=EXERCISE_TAXONOMY,
            rotation_rules=EXERCISE_ROTATION_RULES,
            priority_muscles=inputs.priority_muscles
        )
        # Apply ordering: primary compound lower → primary compound upper → secondaries → isolations
        exercises = sort_by_session_order_priority(exercises)
        
        # Step 5: Assign sets, reps, RIR, rest
        for exercise in exercises:
            exercise.sets = calculate_sets(exercise.target_muscle, session_targets, n)
            exercise.rep_range = get_rep_range(exercise.category, inputs.emphasis_mode)
            exercise.rir = inputs.rir_target
            exercise.rest_seconds = get_rest_period(exercise.category)
        
        # Step 6: Estimate duration; enforce session_duration_limit
        estimated_duration = estimate_session_duration(exercises)
        if estimated_duration > inputs.session_duration_limit:
            exercises = trim_exercises(exercises, inputs.session_duration_limit)
    
    return WeeklyPlan(sessions=sessions, weekly_sets_achieved=tally_sets(sessions))
```

---

### 5.3 Volume Distribution Rules

**Per-session volume cap (working sets, total across all muscles):**
```python
SESSION_VOLUME_CAP = {
    2: 24,   # 2-day: higher per-session since less frequent
    3: 18,   # 3-day: moderate per-session
    4: 15,   # 4-day: lower per-session
    5: 12,   # 5-day: low per-session; quality over quantity
    6: 10    # 6-day: minimal per-session; near-daily practice
}
```

**Distribution formula:**
```python
def calculate_sets_per_session(weekly_sets_target, training_days, muscle):
    """
    Returns integer sets per session for a muscle.
    Ensures minimum 2 sets per session when muscle is trained (for adequate stimulus).
    """
    base = weekly_sets_target / training_days  # raw distribution
    if base < 2.0:
        # Don't program a muscle with <2 sets; consolidate into fewer sessions
        sessions_needed = max(1, round(weekly_sets_target / 2))
        sets_per_active_session = round(weekly_sets_target / sessions_needed)
        return sets_per_active_session, sessions_needed
    return round(base), training_days
```

**Session balance rule:**  
No single session should carry >40% of weekly volume for any muscle group. Exception: 2-day programs where 50% per session is expected.

**Systemic fatigue rule:**  
```
CONSECUTIVE_DAY_RULES = {
    "back_squat + conventional_deadlift": "Never on consecutive days",
    "heavy_compound_lower_day 1 + heavy_compound_lower_day_2": "Require ≥48h gap",
    "same_primary_compound_pattern": "Rotate variations if consecutive days unavoidable",
    "5-6_day_programs": "Day 5/6 = reduced intensity (RIR +1 to +2 vs. days 1-4)"
}
```

---

### 5.4 Exercise Ordering Rules Within a Session

```python
def sort_by_session_order_priority(exercises):
    """
    Sort exercises according to evidence-based ordering:
    1. CNS-demanding primary compound lower body
    2. Primary compound upper body pull
    3. Primary compound upper body push
    4. Secondary compound (lower or upper)
    5. Isolation — larger muscles (lateral delts, leg curls)
    6. Isolation — smaller muscles (curls, tricep extensions)
    7. Core
    
    Additional constraint:
    - Avoid back-to-back CNS-heavy movements (see check_compound_adjacency)
    - Priority muscles (custom emphasis) may be moved to slot 2–3 for maximum freshness
    """
    ORDER_WEIGHT = {
        "squat_variation": 1,
        "hinge_variation": 1,
        "vertical_pull": 2,
        "horizontal_pull": 2,
        "horizontal_press": 3,
        "vertical_press": 3,
        "secondary_compound_lower": 4,
        "secondary_compound_upper": 4,
        "isolation_large": 5,
        "isolation_small": 6,
        "core": 7
    }
    return sorted(exercises, key=lambda e: ORDER_WEIGHT[e.category])
```

---

### 5.5 Rep Range and RIR Assignment

```python
REP_RANGE_BY_CATEGORY = {
    "primary_compound":       "5–8",   # Strength-bias for compounds; also hypertrophy
    "secondary_compound":     "8–12",  # Classic hypertrophy range
    "isolation_large":        "10–15",
    "isolation_small":        "12–20"
}

# Within a session, lower rep ranges go with primary compounds earlier in session
# Higher rep ranges naturally appear with isolations later (less fatiguing, more metabolic)

RIR_SCALE = {
    "week_1_mesocycle": 4,  # Comfortable, high technique practice
    "week_2_mesocycle": 3,
    "week_3_mesocycle": 2,
    "week_4_mesocycle": 1,  # Hard, near-failure approach
    "deload_week": 5         # Very comfortable; volume reduced to MV
}
```

---

### 5.6 Rest Period Recommendations

**Evidence base:** Schoenfeld et al. (2016) — *Longer Interset Rest Periods Enhance Muscle Strength and Hypertrophy in Resistance-Trained Men.* J Strength Cond Res 30(7):1805–1812. Longer rest (3 min) produced significantly greater quad thickness (+13.3%) and strength gains vs. 1-min rest. Source: [Brookbush Institute review of Schoenfeld 2016 rest study](https://brookbushinstitute.com/articles/longer-interset-rest-periods-enhance-muscle-strength-hypertrophy-resistance-trained-men)

```python
REST_PERIODS = {
    "primary_compound": 150,       # 2.5 minutes (90–180 second range)
    "secondary_compound": 90,      # 90 seconds
    "isolation_large_muscle": 75,  # 60–90 seconds
    "isolation_small_muscle": 60   # 60 seconds
}

# Session duration estimate formula:
def estimate_session_duration(exercises):
    """
    Total time = sum(sets × (avg_set_time + rest_period)) + warm_up_time
    avg_set_time ≈ 45 seconds for most sets
    warm_up_time ≈ 8–10 minutes
    """
    total_seconds = 600  # 10 min warm-up
    for ex in exercises:
        set_time = 45  # seconds per set (including rep time)
        rest = REST_PERIODS[ex.category]
        total_seconds += ex.sets * (set_time + rest)
    return total_seconds / 60  # return minutes
```

---

## 6. SESSION STRUCTURE TEMPLATES

### 6.1 Warm-Up Protocol

**Standard warm-up template (applies to ALL sessions):**

**Phase 1: General (5 min)**
- 5 minutes light cardio (bike, row, treadmill) OR dynamic mobility (leg swings, arm circles, hip rotations)

**Phase 2: Specific build-up sets for first compound movement:**
```
For compound lifts (squat, deadlift, bench, overhead press):
  Set 1: 40–50% of working weight × 6–8 reps (controlled)
  Set 2: 60–70% of working weight × 4–6 reps
  Set 3: 80–90% of working weight × 1–3 reps (single if needed)
  
  Example (200 lb squat working weight):
    Set 1: 95 lb × 8
    Set 2: 135 lb × 5
    Set 3: 175 lb × 2
    → Working sets begin
```

Source: [Hevy warm-up sets guide](https://www.hevyapp.com/warm-up-sets/), [Animal Pak warm-up protocol](https://www.animalpak.com/blogs/fitness-bodybuilding/hypertrophy-training)

**Rule:** Warm-up sets are NOT counted toward working set totals (do not count toward weekly volume targets).

---

### 6.2 Three-Day Full-Body Program Template (3x/Week)

**Schedule:** Monday – Wednesday – Friday (or any M-W-F equivalent)  
**Session rotation:** A–B–A (Week 1), B–A–B (Week 2)  
**Frequency achieved:** 2x/week per muscle via A/B rotation  
**Default volume target:** ~12–14 sets/week per major muscle group  

#### Session A

| Order | Exercise | Category | Sets | Reps | RIR | Rest |
|---|---|---|---|---|---|---|
| 1 | Back Squat | Primary compound — squat | 3 | 5–8 | 2 | 150s |
| 2 | Barbell Bent-Over Row | Primary compound — horiz. pull | 3 | 6–10 | 2 | 150s |
| 3 | Barbell Bench Press | Primary compound — horiz. press | 3 | 6–10 | 2 | 150s |
| 4 | Romanian Deadlift | Secondary compound — hinge | 3 | 8–12 | 2 | 120s |
| 5 | Dumbbell Lateral Raise | Isolation — lateral delt | 3 | 12–15 | 2 | 60s |
| 6 | Dumbbell Curl | Isolation — biceps | 2 | 10–15 | 2 | 60s |
| 7 | Tricep Pushdown | Isolation — triceps | 2 | 10–15 | 2 | 60s |

**Estimated duration:** ~65–70 min (with warm-up)

#### Session B

| Order | Exercise | Category | Sets | Reps | RIR | Rest |
|---|---|---|---|---|---|---|
| 1 | Romanian Deadlift (heavy) | Primary compound — hinge | 3 | 5–8 | 2 | 150s |
| 2 | Lat Pulldown | Primary compound — vert. pull | 3 | 8–12 | 2 | 120s |
| 3 | Incline Dumbbell Press | Primary compound — horiz. press | 3 | 8–12 | 2 | 120s |
| 4 | Bulgarian Split Squat | Secondary compound — lower | 3 | 8–12 each | 2 | 120s |
| 5 | Cable Row | Secondary compound — horiz. pull | 3 | 10–12 | 2 | 90s |
| 6 | Rear Delt Fly | Isolation — rear delt | 2 | 15–20 | 2 | 60s |
| 7 | Lying Leg Curl | Isolation — hamstrings | 2 | 12–15 | 2 | 60s |

**Estimated duration:** ~65–70 min

**Weekly volume achieved (3-day A-B-A week):**

| Muscle | Session A | Session B | Weekly Total |
|---|---|---|---|
| Quads | 3 (squat) + 2 (split) | 2 (split) | ~9 direct + indirect |
| Hamstrings | 3 (RDL) | 3 (RDL heavy) + 2 (leg curl) | ~10 |
| Back/Lats | 3 (row) | 3 (pulldown) + 3 (cable row) | ~12–14 |
| Chest | 3 (bench) | 3 (incline DB) | ~9 |
| Lateral Delts | 3 (lateral raise) | 0 | ~6 (+ indirect) |
| Biceps | 2 (curl) + 1.5 (indirect from pulls) | 1.5 (indirect) | ~8 |
| Triceps | 2 (pushdown) + 1.5 (indirect from presses) | 1.5 (indirect) | ~8 |

---

### 6.3 Four-Day Full-Body Program Template (4x/Week)

**Schedule:** Mon–Tue–Thu–Fri  
**Session rotation:** A–B–A–B (consistent each week)  
**Frequency achieved:** 2x/week per muscle  
**Default volume target:** ~14–16 sets/week per major muscle group  

Per-session volume is reduced vs. 3-day (fewer sets per exercise) because sets are distributed across 4 sessions.

#### Session A (Monday / Thursday)

| Order | Exercise | Category | Sets | Reps | RIR | Rest |
|---|---|---|---|---|---|---|
| 1 | Back Squat | Primary compound — squat | 3 | 5–8 | 2 | 150s |
| 2 | Barbell Row | Primary compound — horiz. pull | 3 | 6–10 | 2 | 150s |
| 3 | Overhead Dumbbell Press | Primary compound — vert. press | 3 | 8–12 | 2 | 120s |
| 4 | Dumbbell Lateral Raise | Isolation — lateral delt | 3 | 12–15 | 2 | 60s |
| 5 | Tricep Overhead Extension | Isolation — triceps | 2 | 12–15 | 2 | 60s |

**Estimated duration:** ~50–55 min

#### Session B (Tuesday / Friday)

| Order | Exercise | Category | Sets | Reps | RIR | Rest |
|---|---|---|---|---|---|---|
| 1 | Romanian Deadlift | Primary compound — hinge | 3 | 6–10 | 2 | 150s |
| 2 | Incline Dumbbell Bench | Primary compound — horiz. press | 3 | 8–12 | 2 | 120s |
| 3 | Neutral-Grip Lat Pulldown | Primary compound — vert. pull | 3 | 8–12 | 2 | 120s |
| 4 | Bulgarian Split Squat | Secondary compound — lower | 3 | 8–12 each | 2 | 90s |
| 5 | Dumbbell Curl | Isolation — biceps | 2 | 10–15 | 2 | 60s |
| 6 | Lying Leg Curl | Isolation — hamstrings | 2 | 12–15 | 2 | 60s |

**Estimated duration:** ~55–60 min

**Note for 4-day consecutive days (Mon–Tue):** Session A (Mon) is lower-dominant; Session B (Tue) opens with a hinge. Squat on Monday and hinge/RDL on Tuesday is acceptable because (a) different movement patterns, (b) RIR kept at 2 ensures Monday squats don't cause excessive DOMS before Tuesday's hinge. If user reports soreness on Day 2, swap to RIR 3 on Day 1.

---

### 6.4 Five-Day Full-Body Program Template (5x/Week)

**Schedule:** Mon–Tue–Wed–Fri–Sat (Thursday = rest; Sunday = rest)  
**Session rotation:** A–B–C–A–B (so each session appears once per week, A and B appear twice)  
**Frequency achieved:** 2–3x/week depending on muscle group  
**Volume per session:** Lower (~3–4 working sets per primary muscle per session)  

**Fatigue management rule:** Session 5 (Saturday) = moderate intensity day (RIR target +1 vs. days 1–4). Heaviest sessions = Monday and Wednesday.

#### Session A (Monday / Friday)

| Order | Exercise | Category | Sets | Reps | RIR | Rest |
|---|---|---|---|---|---|---|
| 1 | Back Squat | Primary compound | 3 | 5–8 | 2 | 150s |
| 2 | Lat Pulldown | Primary compound | 3 | 8–12 | 2 | 120s |
| 3 | Dumbbell Bench Press | Primary compound | 3 | 8–12 | 2 | 120s |
| 4 | Dumbbell Lateral Raise | Isolation | 2 | 12–15 | 2 | 60s |
| 5 | Dumbbell Curl | Isolation | 2 | 10–15 | 2 | 60s |

**Estimated duration:** ~50 min

#### Session B (Tuesday / Saturday)

| Order | Exercise | Category | Sets | Reps | RIR | Rest |
|---|---|---|---|---|---|---|
| 1 | Romanian Deadlift | Primary compound | 3 | 6–10 | 3 | 150s |
| 2 | Cable Row | Secondary compound | 3 | 10–12 | 3 | 90s |
| 3 | Overhead DB Press | Primary compound | 3 | 8–12 | 3 | 120s |
| 4 | Lying Leg Curl | Isolation | 2 | 12–15 | 3 | 60s |
| 5 | Tricep Pushdown | Isolation | 2 | 12–15 | 3 | 60s |

**Note:** Saturday's Session B uses RIR 3 (one full RIR higher than the corresponding Tuesday session) to reduce cumulative weekly fatigue going into the weekend rest days.

#### Session C (Wednesday)

| Order | Exercise | Category | Sets | Reps | RIR | Rest |
|---|---|---|---|---|---|---|
| 1 | Leg Press | Secondary compound — lower | 3 | 10–15 | 2 | 90s |
| 2 | Incline Dumbbell Press | Primary compound | 3 | 8–12 | 2 | 120s |
| 3 | Single-Arm DB Row | Secondary compound | 3 | 10–12/side | 2 | 90s |
| 4 | Bulgarian Split Squat | Secondary compound | 2 | 10–12/side | 2 | 90s |
| 5 | Rear Delt Fly | Isolation | 2 | 15–20 | 2 | 60s |
| 6 | Calf Raise | Isolation | 3 | 15–20 | 2 | 60s |

**Estimated duration:** ~55 min

---

### 6.5 Two-Day Template (Reference for Minimal Frequency)

**Schedule:** Any 2 non-consecutive days (e.g., Mon + Thu)  
**Session rotation:** A on Day 1, B on Day 2 each week  
**Per-session volume:** Higher (~5 sets per primary muscle) since each session is the only stimulus that week

#### Session A

| Order | Exercise | Category | Sets | Reps | RIR | Rest |
|---|---|---|---|---|---|---|
| 1 | Back Squat | Primary compound | 4 | 5–8 | 2 | 150s |
| 2 | Barbell Bent-Over Row | Primary compound | 4 | 6–10 | 2 | 150s |
| 3 | Barbell Bench Press | Primary compound | 4 | 6–10 | 2 | 150s |
| 4 | Dumbbell Lateral Raise | Isolation | 3 | 12–15 | 2 | 60s |
| 5 | Dumbbell Curl | Isolation | 3 | 10–15 | 2 | 60s |
| 6 | Tricep Pushdown | Isolation | 3 | 10–15 | 2 | 60s |
| 7 | Lying Leg Curl | Isolation | 3 | 12–15 | 2 | 60s |

**Estimated duration:** ~75–80 min

#### Session B

| Order | Exercise | Category | Sets | Reps | RIR | Rest |
|---|---|---|---|---|---|---|
| 1 | Trap Bar Deadlift / RDL | Primary compound | 4 | 5–8 | 2 | 150s |
| 2 | Neutral-Grip Lat Pulldown | Primary compound | 4 | 8–12 | 2 | 120s |
| 3 | Incline Dumbbell Press | Primary compound | 4 | 8–12 | 2 | 120s |
| 4 | Bulgarian Split Squat | Secondary compound | 3 | 8–12/side | 2 | 90s |
| 5 | Cable Row | Secondary compound | 3 | 10–12 | 2 | 90s |
| 6 | Rear Delt Fly | Isolation | 3 | 15–20 | 2 | 60s |
| 7 | Calf Raise | Isolation | 3 | 15–20 | 2 | 60s |

**Estimated duration:** ~80–85 min

---

## APPENDIX A: VARIABLE REFERENCE GLOSSARY

| Variable | Type | Description |
|---|---|---|
| `training_days_per_week` | int (2–6) | Number of sessions per 7-day week |
| `emphasis_mode` | Enum | BALANCED / UPPER_EMPHASIS / LOWER_EMPHASIS / ARMS_EMPHASIS / CUSTOM |
| `priority_muscles` | List[str] | Up to 2 muscles to prioritize in CUSTOM mode |
| `MV` | Dict[str, int] | Maintenance volume (sets/week per muscle) |
| `MEV` | Dict[str, int] | Minimum effective volume (sets/week per muscle) |
| `MAV` | Dict[str, Tuple[int,int]] | Maximum adaptive volume range (sets/week per muscle) |
| `MRV` | Dict[str, int] | Maximum recoverable volume (sets/week per muscle) |
| `volume_multiplier` | float (0.6–1.5) | Scales baseline MAV_MID based on emphasis mode |
| `rir_target` | int (1–5) | Reps in reserve for the current mesocycle week |
| `session_volume_cap` | Dict[int, int] | Max total working sets per session by training_days |
| `systemic_fatigue_cap` | Dict[str, int] | Max total weekly working sets across all muscles |
| `rest_period` | Dict[str, int] | Recommended inter-set rest by exercise category (seconds) |
| `session_label` | str ("A","B","C") | Session variant identifier for rotation tracking |
| `exercise_category` | Enum | PRIMARY_COMPOUND / SECONDARY_COMPOUND / ISOLATION |
| `frequency_per_muscle` | int (1–3) | Times per week a muscle is directly trained |
| `rep_range` | str | e.g., "8–12"; assigned by exercise category |
| `MINIMUM_FREQUENCY_PER_MUSCLE_PER_WEEK` | int | Default = 2 (per Schoenfeld et al. 2016) |

---

## APPENDIX B: DECISION LOGIC FLOWCHART (TEXT)

```
INPUT: user profile (training_days, emphasis_mode, experience_level)
  │
  ▼
STEP 1: Validate training_days (2–6); clamp to range if out of bounds
  │
  ▼
STEP 2: For each muscle_group → compute_target_weekly_sets(muscle, emphasis_mode)
         → apply volume_multiplier
         → clamp to [MEV, MRV]
  │
  ▼
STEP 3: Check systemic_fatigue_cap(training_days, experience_level)
         → if sum(all weekly sets) > cap: reduce non-priority muscles toward MEV
  │
  ▼
STEP 4: Assign session labels (A/B/A for 3-day; A/B/A/B for 4-day; etc.)
  │
  ▼
STEP 5: Distribute weekly sets across sessions
         → compute sets_per_session for each muscle per session
         → enforce minimum 2 sets/session if muscle is trained that day
         → enforce ≤ SESSION_VOLUME_CAP[training_days] total per session
  │
  ▼
STEP 6: Select exercises for each session
         → choose from EXERCISE_TAXONOMY by muscle
         → apply rotation (Session A uses variation 1; Session B uses variation 2)
         → check exercise_adjacency (no consecutive CNS-heavy movements)
  │
  ▼
STEP 7: Order exercises by ORDER_WEIGHT (primary compound lower first → isolations last)
  │
  ▼
STEP 8: Assign rep_range, rir, rest_period per exercise
  │
  ▼
STEP 9: Estimate session duration
         → if > session_duration_limit: trim lowest-priority isolation exercises
  │
  ▼
OUTPUT: WeeklyPlan with List[Session], weekly_sets_achieved, estimated durations
```

---

## APPENDIX C: FULL-BODY TRANSITION THRESHOLDS

When full-body programming becomes impractical and an upper/lower or PPL split is warranted:

| Indicator | Threshold | Action |
|---|---|---|
| Training age | > 18–24 months consistent training | Consider upper/lower split |
| Weekly volume need | Any major muscle > 20 sets/week | Full-body struggles to distribute efficiently |
| Session duration | > 90 min at 3x/week to meet volume | Volume too high for full-body per session |
| Per-session fatigue | User reports systemic fatigue persisting > 48h | Reduce frequency or switch to split |
| Training days | ≥ 5 days with high volume needs | Upper/lower or PPL more efficient |
| Plateau with full-body | No progress after 2+ mesocycles at MRV | Split allows higher focused volume per group |

Source: [A Workout Routine — Full Body Split Guide](https://www.aworkoutroutine.com/full-body-split/), [Hevy — Full Body vs. Split comparison](https://www.hevyapp.com/full-body-workout-vs-split/)

---

## APPENDIX D: KEY CITATIONS SUMMARY

| Citation | Key Finding | URL |
|---|---|---|
| Schoenfeld, Ogborn & Krieger (2016) — Sports Medicine | 2x/week superior to 1x/week for hypertrophy; insufficient data on 3x vs. 2x | https://pubmed.ncbi.nlm.nih.gov/27102172/ |
| Schoenfeld et al. (2018) — systematic review, 25 studies | Volume-equated frequency does not significantly impact hypertrophy | Via Barbell Medicine group summary |
| Colquhoun et al. (2019) — J Human Kinetics | 2x/week and 3x/week produce similar hypertrophy when volume equated; small ES favored 2x | https://pmc.ncbi.nlm.nih.gov/articles/PMC6724585/ |
| Schoenfeld, Pope et al. (2016) — J Strength Cond Res | 3-min rest > 1-min rest for compound exercise hypertrophy | Via Brookbush Institute review |
| Ramos-Campo et al. (2021) — Einstein | Split and full-body produce equivalent hypertrophy in untrained when volume equated | https://pmc.ncbi.nlm.nih.gov/articles/PMC8372753/ |
| Fonseca et al. (2014) — PubMed 24832974 | Exercise variety produces more uniform regional quad hypertrophy vs. squat-only | https://pubmed.ncbi.nlm.nih.gov/24832974/ |
| Costa et al. (2021) — as cited in PMC6934277 | Varied exercise selection promotes growth across more muscle regions | https://pmc.ncbi.nlm.nih.gov/articles/PMC6934277/ |
| Israetel / RP Strength | Volume landmarks (MV, MEV, MAV, MRV) per muscle group | https://rpstrength.com/blogs/articles/training-volume-landmarks-muscle-growth |
| Stronger by Science (Krieger 2020) | Linear frequency-hypertrophy relationship; ~0.11%/week additional gain per extra day | https://www.strongerbyscience.com/frequency-muscle/ |

---

*Document compiled for Milo AI fitness coaching backend, March 2026.*
*All volume landmarks are population averages and should be treated as starting defaults, subject to individual feedback loops (performance tracking, recovery signals, RIR drift).*
