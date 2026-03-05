# Track 2: Hypertrophy Volume & Progression Models
**Milo AI Fitness System — Backend Logic Reference**
*Compiled for AI agent consumption. Prioritizes variable definitions, formulas, and decision logic.*

---

## Table of Contents
1. [Volume Landmarks Framework](#1-volume-landmarks-framework)
2. [Volume-Response Relationship](#2-volume-response-relationship)
3. [Volume Distribution & Emphasis Model](#3-volume-distribution--emphasis-model)
4. [Progression Models](#4-progression-models)
5. [Mesocycle Structure](#5-mesocycle-structure)

---

## 1. Volume Landmarks Framework

### 1.1 Definitions

The four volume landmarks are defined by **Dr. Mike Israetel / Renaissance Periodization (RP Strength)**. All values represent **weekly hard sets** (direct/prime-mover sets only; compound contributions are partially discounted). A "hard set" assumes load between 30–85% 1RM, rep range 5–30, and effort 0–4 RIR (Reps in Reserve).

> Source: [Israetel, M. — Training Volume Landmarks for Muscle Growth, RP Strength (2017, updated 2025)](https://rpstrength.com/blogs/articles/training-volume-landmarks-muscle-growth)

```
Variable Name   | Type    | Definition
----------------|---------|------------------------------------------------------------
MV              | int     | Maintenance Volume — weekly sets to PRESERVE current muscle
                |         | mass. Approx ~6 sets/week for most muscles when training 2x/week.
                |         | Remarkably stable regardless of training age.

MEV             | int     | Minimum Effective Volume — lowest weekly sets that produce
                |         | measurable hypertrophic gains. Mesocycle starting point.
                |         | Increases with training age (beginners MEV ≈ MV + 2–4 sets;
                |         | intermediates MEV gap widens).

MAV             | range   | Maximum Adaptive Volume — range between MEV and MRV where
                |         | optimal gains occur. Not a fixed number; a dynamic zone that
                |         | progresses upward as the mesocycle advances and work capacity grows.
                |         | Target average over the mesocycle.

MRV             | int     | Maximum Recoverable Volume — upper weekly set limit beyond
                |         | which recovery is impaired and gains stop. Briefly exceeding
                |         | MRV causes functional overreaching; chronically exceeding
                |         | causes accumulated fatigue and performance decline.
```

**Key relationships:**
```
MV < MEV < MAV_low < MAV_high < MRV
MV is stable across training age (~6 sets/wk for most muscles)
MEV increases with training age
MAV_high approaches MRV in advanced lifters (narrowing window)
```

---

### 1.2 Per-Muscle-Group Volume Landmarks Table

All values represent **weekly direct sets** for an **intermediate male lifter** (1–5 years consistent training). Beginners use the lower bound of MEV/MAV ranges; advanced use upper bounds.

> Primary source: [Israetel / RP Strength per-muscle guides (2018–2024)](https://rpstrength.com/blogs/articles/complete-hypertrophy-training-guide) and [community-compiled RP summary table (r/AdvancedFitness, 2021)](https://www.reddit.com/r/AdvancedFitness/comments/lyney9/summary_of_dr_mike_israetel_and_renaissance/)
> Secondary source: [RP Volume Guide PDF summary (Scribd)](https://www.scribd.com/document/489839887/RP-Volume-Guide)
> Tertiary source: [Arvo MEV/MAV/MRV Calculator (aggregated RP data)](https://arvo.guru/tools/volume-calculator)

```
Muscle Group        | MV    | MEV    | MAV (range) | MRV   | Freq/week | Notes
--------------------|-------|--------|-------------|-------|-----------|-------------------------
Chest               | 4     | 6–8    | 8–18        | 20–22 | 2–3x      | Intermediate values 6–16; advanced up to 24–32 (priority)
Back (lats + upper) | 6     | 10     | 12–20       | 22–25 | 2–4x      | Includes rows + pulldowns
Quads               | 6     | 8      | 10–18       | 20–22 | 2–3x      | High inter-individual variance
Hamstrings          | 3–4   | 4–6    | 8–14        | 16–18 | 2–3x      | Includes hip hinges + leg curls
Glutes              | 0–2   | 4–6    | 8–16        | 20+   | 2–3x      | Often trained via quad/ham work; 0 direct if squatting heavily
Side Delts          | 6     | 8      | 10–22       | 25–26 | 3+x       | High frequency capacity
Rear Delts          | 0     | 6      | 8–16        | 18–26 | 2–5x      | Partial credit from rows
Front Delts         | 0     | 0      | 0–8         | 12–16 | 2–6x      | Pressing work usually sufficient; rarely needs isolation
Biceps              | 4–6   | 8      | 10–18       | 20–26 | 2–3x      | Partial credit from pulling movements
Triceps             | 4     | 6      | 8–16        | 18–20 | 2–6x      | Partial credit from pressing movements
Calves              | 0     | 6–8    | 10–16       | 20+   | 2–6x      | Respond well to high frequency; no compound crossover
Abs                 | 0     | 0–6    | 8–20        | 25+   | 2–6x      | Partial credit from compound movements
Traps               | 0     | 4      | 8–20        | 25+   | 2–6x      | Partial credit from deadlifts, rows, overhead press
```

**Notes on compound set-counting (RP methodology):**
- Volumes above represent DIRECT sets only; compound lifts provide partial credit
- Example: bench press = 1 direct chest set, ~0.5 triceps set, ~0.25 front delt set
- Example: pulldown/row = 1 direct back set, ~0.5 biceps set, ~0.25 rear delt set
- RP reduces MEV/MRV values for smaller muscles to account for this indirect volume
- Do NOT double-count: a barbell row counted as 1 back set should not also be counted as a full biceps set

---

### 1.3 Beginner vs. Intermediate Adjustments

> Source: [RP Strength Chest Guide (2024)](https://rpstrength.com/blogs/articles/chest-hypertrophy-training-tips); [Schoenfeld, B. (2010) evidence-based guidelines PDF via elementssystem.com](https://elementssystem.com/wp-content/uploads/2018/08/Schoenfeld-volumen-review.pdf)

```
training_status: enum { BEGINNER, INTERMEDIATE, ADVANCED }

Beginner (< ~12 months consistent training):
  MEV   = table_value × 0.5 to 0.7   (MEV ≈ MV; gains occur at very low volumes)
  MAV   = table_value × 0.6 to 0.8
  MRV   = table_value × 0.5 to 0.75
  Notes = "Growth occurs at 2–6 sets/muscle/week. Start at lower MEV,
           emphasize technique. 1–3 sets/exercise per ACSM guidelines."

Intermediate (1–5 years consistent training):
  MEV   = table_value (use as published)
  MAV   = table_value (use as published)
  MRV   = table_value (use as published)
  Notes = "Standard landmark values apply. Progressive volume cycling
           across mesocycles appropriate."

Advanced (5+ years consistent training):
  MEV   = table_value × 1.0 to 1.2   (MEV escalates; MAV–MEV window narrows)
  MAV   = table_value × 1.0 to 1.3
  MRV   = table_value × 1.0 to 1.2
  Notes = "MEV–MRV window narrows (e.g., 5–7 sets/session vs 2–8 for beginners).
           May require specialization phases. Outside Milo's primary scope."
```

**Pseudocode: landmark lookup by muscle and status:**
```python
def get_volume_landmark(muscle_group: str, status: TrainingStatus, landmark: str) -> int | tuple:
    base = VOLUME_TABLE[muscle_group][landmark]  # from Section 1.2
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

---

## 2. Volume-Response Relationship

### 2.1 Schoenfeld & Krieger 2017 Meta-Analysis

> Source: [Schoenfeld, B.J. & Krieger, J. (2017). "Dose-response relationship between weekly resistance training volume and increases in muscle mass." *Journal of Sports Sciences*, 35(11), 1073–1082.](https://pubmed.ncbi.nlm.nih.gov/27433992/)
> Also: [Full-text hosted at ageingmuscle.be](https://www.ageingmuscle.be/sites/bams/files/publications/Dose%20response%20relationship%20between%20weekly%20resistance%20training%20volume%20and%20increases.pdf)

**Study parameters:**
- N = 34 treatment groups from 15 studies; 363 subjects
- Measured: muscle cross-sectional area (MRI, ultrasound) and indirect markers
- Independent variable: weekly sets per muscle group (<5, 5–9, 10+)

**Key quantitative findings:**

```
Volume Category    | ES     | % Hypertrophy Gain | P-value
-------------------|--------|--------------------|---------
< 5 sets/week      | 0.307  | 5.4%               | —
5–9 sets/week      | 0.397  | 6.6%               | —
10+ sets/week      | 0.544  | 9.8%               | —
(continuous model) | +0.023 ES per additional set | P=0.002

Higher vs Lower    | ES diff = 0.241 (3.9% greater gain) | P=0.03
(binary model)
```

**Key conclusions:**
1. Clear graded dose-response: more weekly sets → more hypertrophy
2. Each additional weekly set = +0.37% hypertrophic gain (ES +0.023)
3. 10+ sets/week produced significantly greater gains than <10 sets/week
4. The 40% greater ES difference between high and low volume groups is practically significant

### 2.2 Diminishing Returns and Practical Ceiling

> Source: [Krieger, J. (2024) — "The King of Volume Metas," Biolayne (meta-analysis of 67 studies, 2,058 subjects)](https://biolayne.com/reps/issue-31/the-king-of-volume-metas/)
> Source: [Schoenfeld et al. 2019 — Resistance Training Volume Enhances Hypertrophy, *Medicine & Science in Sports & Exercise* (MSSE)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6303131/)
> Source: [Weightology — Set Volume for Muscle Size Evidence Bible (2025)](https://weightology.net/the-members-area/evidence-based-guides/set-volume-for-muscle-size-the-ultimate-evidence-based-bible/)

**Diminishing returns pattern (logarithmic relationship):**
```
Volume Range     | Response
-----------------|------------------------------------------
1–5 sets/week    | Rapid gains; each set provides large marginal return
5–12 sets/week   | Strong gains; dose-response clearly present
12–20 sets/week  | Good gains; diminishing marginal return per set begins
20–30 sets/week  | Some benefit possible; recovery demands rise steeply
30–40 sets/week  | Research (Enes et al., quad specialization) shows further benefit
                 | but systemic recovery constraints limit applicability
40+ sets/week    | Likely impractical; recovery probably exceeds adaptation
```

**Per-session ceiling:**
- Optimal per-session volume: ~**6–8 hard sets per muscle per session** (Weightology meta-analysis, long rest intervals)
- Above ~11 sets/muscle/session: unclear whether additional sets add benefit (Dr. Milo Wolf analysis, 2026)
- Practical rule: **5–10 sets/session/muscle** → add 1 training session frequency per week for each 5–10 additional weekly sets desired

**Practical ceiling for programming (for beginners–intermediates):**
```
10–20 sets/muscle/week = "working range" for most trained individuals
< 10 sets/week         = viable for beginners, time-constrained, or maintenance
> 20 sets/week         = specialization/emphasis phases only; not sustainable for all muscles simultaneously
```

### 2.3 How Training Status Shifts the Volume-Response Curve

> Source: [muscledb.com analysis of Schoenfeld & Krieger 2017](http://www.muscledb.com/papers/resistance-training-volume-meta-analysis/en/)
> Source: [Schoenfeld 2017 evidence-based guidelines PDF](https://elementssystem.com/wp-content/uploads/2018/08/Schoenfeld-volumen-review.pdf)

```
Status              | Minimum Growth Volume | Optimal Starting Volume | Volume Ceiling
--------------------|----------------------|-------------------------|------------------
Untrained/Beginner  | 2–4 sets/muscle/week | 5–10 sets/muscle/week   | ~15 sets/week
(0–12 months)       | (any stimulus grows) | (MEV for novice)        | (low MRV)

Intermediate        | 5–8 sets/muscle/week | 10–15 sets/muscle/week  | ~20–25 sets/week
(1–5 years)         | (MEV established)    | (within MAV)            |

Advanced            | 8–12 sets/muscle/week| 15–20 sets/muscle/week  | ~25–35 sets/week
(5+ years)          | (MEV has risen)      | (high MAV)              | (with periodization)
```

**Mechanism:** Muscles adapt to habitual training doses. As training age increases:
- Fewer molecular signals triggered per set (reduced sensitivity)
- More sets required to cross the MEV threshold
- MRV also rises (but more slowly than MEV), narrowing the productive zone

**Pseudocode: Training status effect on effective volume range:**
```python
def effective_volume_range(muscle: str, status: TrainingStatus) -> dict:
    base_mev = get_volume_landmark(muscle, status, "MEV")
    base_mrv = get_volume_landmark(muscle, status, "MRV")
    return {
        "mev": base_mev,
        "mav_low": base_mev + 2,
        "mav_high": base_mrv - 3,
        "mrv": base_mrv,
        "productive_window": base_mrv - base_mev  # narrows with training age
    }
```

---

## 3. Volume Distribution & Emphasis Model

### 3.1 Principle

Total weekly volume budget is NOT distributed uniformly. Muscles with higher priority (based on user goals, aesthetics preferences, lagging bodyparts) receive MAV-level volume; others receive MEV or MV-level volume.

> Source: [YouTube: "How Much Volume for Each Muscle Group?" (Volume Allocation for Hypertrophy Training, 2021)](https://www.youtube.com/watch?v=NoABJB5_wKM)

### 3.2 Priority Tier System

```
Tier       | Volume Level | Description
-----------|--------------|------------------------------------------------
PRIMARY    | MAV range    | Emphasis muscles. User's priority body parts.
           |              | Target: (MEV + MRV) / 2 to MRV - 3 sets
SECONDARY  | MEV to MAV   | Maintained but not emphasized. Making progress,
           |              | not the focus. Target: MEV to (MEV + MRV) / 2
TERTIARY   | MV to MEV    | Maintenance-only. Preserved while primary grows.
           |              | Target: MV to MEV
```

### 3.3 Variables

```python
emphasis_config: dict = {
    "muscle_group_name": {
        "tier": Tier,              # PRIMARY | SECONDARY | TERTIARY
        "target_weekly_sets": int, # calculated from landmarks + tier
        "current_weekly_sets": int # tracked in real time
    }
}

user_goal_emphasis: enum = {
    BALANCED,           # No preference; equal distribution
    UPPER_BODY,         # Upper > Lower volume
    LOWER_BODY,         # Lower > Upper volume
    ARMS,               # Biceps/Triceps/Shoulders emphasized
    CHEST_AND_BACK,     # Classic V-taper focus
    GLUTES_AND_LEGS,    # Lower body aesthetic focus
    CUSTOM              # Per-muscle priority set by user
}
```

### 3.4 Allocation Algorithm

```python
def assign_tier(muscle: str, user_emphasis: GoalEmphasis, custom_priorities: dict) -> Tier:
    if user_emphasis == CUSTOM:
        return custom_priorities[muscle]  # user-specified per muscle
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
        return SECONDARY  # all muscles get MEV-to-MAV-midpoint volume
    # ... additional presets

def calculate_target_sets(muscle: str, status: TrainingStatus, tier: Tier) -> int:
    landmarks = get_volume_landmark(muscle, status)
    mev = landmarks["MEV"]
    mav_high = landmarks["MAV"][1]
    mrv = landmarks["MRV"]
    mv = landmarks["MV"]

    if tier == PRIMARY:
        return int((mav_high + mrv) / 2)  # upper MAV range
    elif tier == SECONDARY:
        return int((mev + mav_high) / 2)  # MEV to MAV midpoint
    elif tier == TERTIARY:
        return max(mv, mev - 2)            # MV to MEV range
```

### 3.5 Concrete Example Allocation Tables

**Balanced Approach (Intermediate Male):**
```
Muscle Group   | Tier      | MV | MEV | MAV    | MRV | Target Sets
---------------|-----------|----|-----|--------|-----|------------
Chest          | SECONDARY | 4  | 8   | 8–18   | 22  | 12
Back           | SECONDARY | 6  | 10  | 12–20  | 25  | 14
Side Delts     | SECONDARY | 6  | 8   | 10–22  | 26  | 12
Rear Delts     | SECONDARY | 0  | 6   | 8–16   | 26  | 10
Biceps         | SECONDARY | 4  | 8   | 10–18  | 26  | 12
Triceps        | SECONDARY | 4  | 6   | 8–16   | 20  | 10
Quads          | SECONDARY | 6  | 8   | 10–18  | 22  | 12
Hamstrings     | SECONDARY | 4  | 4   | 8–14   | 18  | 10
Glutes         | SECONDARY | 2  | 4   | 8–16   | 20  | 10
Calves         | SECONDARY | 0  | 6   | 10–16  | 20  | 12
Abs            | SECONDARY | 0  | 4   | 8–20   | 25  | 10
TOTAL SETS/WEEK: ~124
```

**Upper Body Emphasis (Intermediate Male):**
```
Muscle Group   | Tier      | Target Sets | Rationale
---------------|-----------|-----------|--------------------------
Chest          | PRIMARY   | 16         | Upper MAV range
Back           | PRIMARY   | 18         | Upper MAV range
Side Delts     | PRIMARY   | 16         | Upper MAV range
Rear Delts     | PRIMARY   | 12         | MAV range
Biceps         | PRIMARY   | 14         | MAV range
Triceps        | PRIMARY   | 12         | MAV range
Quads          | TERTIARY  | 6          | MV level
Hamstrings     | TERTIARY  | 4          | MV level
Glutes         | TERTIARY  | 4          | MV level
Calves         | TERTIARY  | 6          | MV level
Abs            | SECONDARY | 8          | MEV-MAV midpoint
TOTAL SETS/WEEK: ~116
```

**Lower Body Emphasis (Intermediate Male):**
```
Muscle Group   | Tier      | Target Sets | Rationale
---------------|-----------|-----------|--------------------------
Chest          | SECONDARY | 10         | MEV-MAV midpoint
Back           | SECONDARY | 12         | MEV-MAV midpoint
Side Delts     | TERTIARY  | 6          | MV level
Rear Delts     | TERTIARY  | 4          | ~MV level
Biceps         | TERTIARY  | 6          | MV level
Triceps        | TERTIARY  | 4          | MV level
Quads          | PRIMARY   | 16         | Upper MAV range
Hamstrings     | PRIMARY   | 12         | Upper MAV range
Glutes         | PRIMARY   | 14         | Upper MAV range
Calves         | PRIMARY   | 14         | Upper MAV range
Abs            | SECONDARY | 8          | MEV-MAV midpoint
TOTAL SETS/WEEK: ~106
```

**Key constraint: Total systemic fatigue must remain manageable.**
```python
TOTAL_WEEKLY_SETS_LIMIT = {
    BEGINNER: 80,     # ~80 total weekly sets across all muscles
    INTERMEDIATE: 120, # ~100–130 sets typical practical range
    ADVANCED: 160      # with careful periodization
}

# Flag if allocation exceeds limit
if sum(target_sets.values()) > TOTAL_WEEKLY_SETS_LIMIT[status]:
    reduce_tertiary_sets_first()  # drop TERTIARY to MV floor
    reduce_secondary_sets_second()  # reduce SECONDARY toward MEV
```

---

## 4. Progression Models

### 4.1 Overview

Four main progression frameworks are applicable for Milo's target population (beginner–intermediate males, hypertrophy + strength focus):

| Model | Best For | Mechanism | Complexity |
|-------|----------|-----------|------------|
| Linear Progression (LP) | True beginners (0–6 months) | Add load every session | Low |
| Double Progression | Beginners → Intermediates | Add reps → then add load | Low-Med |
| Undulating Periodization (DUP/WUP) | Intermediates | Vary rep range across days/weeks | Medium |
| Block/Mesocycle Periodization | Intermediates | Volume ramps across blocks; deload | Medium-High |

> Source: [Helms, E. & Wolf, M. — "How to Train for Maximum Muscle Growth" (YouTube, 2024)](https://www.youtube.com/watch?v=twOKHMAAR0U)
> Source: [Ripped Body — Autoregulated Double Progression (2025)](https://rippedbody.com/progression/)
> Source: [Helms, E. — Periodization for Hypertrophy (YouTube, 2020)](https://www.youtube.com/watch?v=uL9CHTp4_x4)

---

### 4.2 Model 1: Linear Progression (LP)

**Target:** True beginners (0–6 months training age)

**Mechanism:** Fixed sets and reps; increase absolute load each session or weekly.

**Variables:**
```python
lp_params = {
    "rep_target": int,           # fixed rep target, e.g., 8 reps
    "sets": int,                 # fixed set count, e.g., 3
    "load_increment_barbell": float,  # pounds per session, e.g., 5.0
    "load_increment_dumbbell": float, # pounds per 2-3 sessions, e.g., 5.0
    "stall_threshold": int,      # sessions without progress before adjusting, e.g., 2
}
```

**Progression rule:**
```python
def lp_next_session(exercise, current_load, current_reps, target_reps, status):
    if current_reps >= target_reps:
        next_load = current_load + lp_params["load_increment"]
        next_reps = target_reps  # hold reps constant, increase load
        return (next_load, next_reps)
    else:
        return (current_load, current_reps)  # repeat same load until target reps hit
```

**Stall handling:**
```python
if sessions_stalled >= lp_params["stall_threshold"]:
    # Option 1: Drop rep target by 2 and reset (e.g., 3x8 → 3x6 with new load)
    # Option 2: Switch to double progression model
    switch_to_double_progression()
```

---

### 4.3 Model 2: Double Progression (Autoregulated)

**Target:** Beginners approaching stall on LP; intermediates (primary model)

**Mechanism:** Progress reps within a range at fixed load; once top of range hit across all sets, increase load. Autoregulated via RIR tracking.

> Source: [Helms, E. — Double Progression Method (YouTube, 2024)](https://www.youtube.com/watch?v=twOKHMAAR0U)
> Source: [Ripped Body — Autoregulated Double Progression System (2025)](https://rippedbody.com/progression/)

**Variables:**
```python
double_prog_params = {
    "rep_range_low": int,        # e.g., 8
    "rep_range_high": int,       # e.g., 12
    "rir_target": int,           # e.g., 2 (reps in reserve)
    "rir_tolerance": int,        # e.g., 1 (acceptable RIR window: rir_target ± tolerance)
    "load_increase_pct": float,  # e.g., 0.025 (2.5%)
    "load_increase_abs": float,  # e.g., 5.0 lbs (use smaller of % or abs)
    "sets": int,                 # e.g., 3
}
```

**Session-to-session logic:**
```python
def double_progression_next(exercise, sessions: list[Session]) -> (float, int):
    """
    sessions: list of recent sessions with (load, reps_achieved, rir_reported)
    Returns: (next_load, target_reps)
    """
    current = sessions[-1]
    
    # Check if progression warranted: all sets hit top of rep range at target RIR
    all_sets_hit_top = all(s.reps >= double_prog_params["rep_range_high"] for s in current.sets)
    rir_acceptable = all(
        abs(s.rir - double_prog_params["rir_target"]) <= double_prog_params["rir_tolerance"]
        for s in current.sets
    )
    
    if all_sets_hit_top and rir_acceptable:
        # LOAD PROGRESSION: increase load, reset reps to bottom of range
        load_increase = min(
            current.load * double_prog_params["load_increase_pct"],
            double_prog_params["load_increase_abs"]
        )
        next_load = current.load + load_increase
        next_reps_target = double_prog_params["rep_range_low"]  # reset to low end
        return (next_load, next_reps_target)
    else:
        # REP PROGRESSION: keep load, aim to add 1 rep
        return (current.load, min(current.reps + 1, double_prog_params["rep_range_high"]))
```

**Specific numeric rules (from Israetel/Helms):**
```
Progression trigger: ALL SETS complete rep_range_high at RIR ≤ target_RIR
Load increase rate:
  - Barbell compound (squat, deadlift, row): +5 lbs per increment
  - Barbell isolation (curl, extension): +2.5 lbs per increment
  - Dumbbell (all): +5 lbs per dumbbell per increment (smallest available jump)
  - Machine: smallest available increment (1 plate = typically 5–10 lbs)
  
Typical progression cadence:
  - Beginners: may progress load every 1–2 sessions (weekly)
  - Intermediates: may take 3–6 sessions (2–4 weeks) to hit all reps at target RIR
  - Advanced: may take 5–10+ sessions (4–8+ weeks)
```

---

### 4.4 Model 3: Daily Undulating Periodization (DUP)

**Target:** Intermediates who want variety or strength + hypertrophy blend

**Mechanism:** Rep ranges vary across days within a week (heavy day, moderate day, light day). Volume is equated across conditions; periodization occurs via rep range cycling.

> Source: [Helms, E. — Periodization for Hypertrophy (YouTube, 2020)](https://www.youtube.com/watch?v=uL9CHTp4_x4); Review by Grgic et al. (2017) cited therein: no hypertrophy advantage vs linear if progressive overload occurs.

**Variables:**
```python
dup_rotation = [
    {"day_type": "HEAVY",    "rep_range": (4, 6),  "rir": 2, "rir_end_meso": 1},
    {"day_type": "MODERATE", "rep_range": (8, 12), "rir": 2, "rir_end_meso": 1},
    {"day_type": "LIGHT",    "rep_range": (15, 20),"rir": 2, "rir_end_meso": 1},
]
```

**Note on DUP vs double progression for Milo:**
```
Research finding (Helms, Grgic 2017): DUP provides no superior hypertrophy
vs linear progressive overload IF progressive overload is maintained.
DUP is beneficial for: maintaining strength adaptations during hypertrophy phases,
motor pattern variety, reduced boredom.
RECOMMENDATION for Milo: Default to double progression. Offer DUP as optional
advanced variant for intermediates who also care about strength expression.
```

---

### 4.5 Model 4: Block/Mesocycle Periodization

**Target:** Intermediates (primary model for volume cycling across mesocycles)

**Mechanism:** Each mesocycle cycles volume from MEV → MAV → MRV over accumulation weeks, followed by a deload. Each new mesocycle starts at MEV but with higher baseline capability. See Section 5 for full structure.

**Cross-mesocycle progression rule:**
```python
def calculate_next_meso_starting_volume(muscle: str, prev_meso_avg_volume: int,
                                         prev_meso_performance_change: float) -> int:
    """
    prev_meso_performance_change: % change in strength on benchmark lift
    Positive → growing; increase starting volume
    Zero/negative → stagnant/declining; adjust
    """
    if prev_meso_performance_change > 0.02:  # > 2% strength gain
        # Successful mesocycle: increase MEV starting point by 1–2 sets next meso
        return prev_meso_avg_volume + 1  # slight volume increase meso-over-meso
    elif prev_meso_performance_change <= 0:
        # Performance decline → possible overreaching; reduce next meso starting volume
        return max(MEV_floor[muscle], prev_meso_avg_volume - 2)
    else:
        return prev_meso_avg_volume  # maintain same starting point
```

---

### 4.6 Progression Model Decision Logic

```python
def select_progression_model(status: TrainingStatus, goal: Goal) -> ProgressionModel:
    if status == BEGINNER:
        return LinearProgression  # simplest; fast results
    elif status == INTERMEDIATE:
        if goal == PRIMARILY_HYPERTROPHY:
            return DoubleProgression  # default for intermediates
        elif goal == HYPERTROPHY_AND_STRENGTH:
            return BlockPeriodization  # with DUP or strength blocks
    elif status == ADVANCED:
        return BlockPeriodization  # required for continued progress

# Override: if user has <12 consistent training months, always start LP first.
# Switch to double progression when: LP stalls for 2+ consecutive sessions OR
# user hits 6 months consistent training.
```

---

## 5. Mesocycle Structure

### 5.1 Definitions

```
Variable          | Type  | Definition
------------------|-------|-----------------------------------------------
mesocycle_length  | int   | Weeks of accumulation + 1 deload week.
                  |       | Typical: 4–6 weeks total (3–5 accumulation + 1 deload)
accumulation_weeks| int   | Weeks of progressive training within the mesocycle
deload_week       | int   | 1 week at MV-level volume; always included at end
microcycle        | int   | 1 week of training
macrocycle        | int   | 3–4 mesocycles; ~12–20 weeks; one training phase
```

> Source: [RP Strength — In Defense of Set Increases Within the Hypertrophy Mesocycle (2020)](https://rpstrength.com/blogs/articles/in-defense-of-set-increases-within-the-hypertrophy-mesocycle)
> Source: [Reshape.ai — Periodization for Strength and Hypertrophy (2025)](https://www.reshapeapp.ai/blog/periodization-for-strength-and-hypertrophy)

---

### 5.2 Recommended Mesocycle Length

```
Training Status | Accumulation Weeks | Deload | Total Mesocycle | Rationale
----------------|-------------------|--------|-----------------|---------------------------
Beginner        | 8–12 weeks        | 1 week | 9–13 weeks      | High recovery; slow MRV approach
Intermediate    | 3–5 weeks         | 1 week | 4–6 weeks       | Standard; matches research evidence
Advanced        | 2–4 weeks         | 1 week | 3–5 weeks       | Narrow MEV-MRV window; faster fatigue

Most common for Milo target population (intermediate): 4-week accumulation + 1 deload = 5 weeks total
```

**Mesocycle decision tree:**
```python
def get_mesocycle_length(status: TrainingStatus, fatigue_level: int) -> int:
    """
    fatigue_level: self-reported 1–5 scale (1=fresh, 5=crushed)
    Returns: number of accumulation weeks before mandating deload
    """
    base = {BEGINNER: 10, INTERMEDIATE: 4, ADVANCED: 3}[status]
    
    if fatigue_level >= 4:
        return max(2, base - 2)  # shorten meso; early deload signal
    elif fatigue_level <= 2:
        return min(base + 1, 6)  # potentially extend by 1 week
    else:
        return base  # standard length
```

---

### 5.3 Volume Ramp Across the Mesocycle (MEV → MRV)

**Core principle:** Start each mesocycle at or near MEV. Add sets progressively toward MRV. Reduce RIR targets (increase effort) simultaneously. At MRV (or earlier if recovery signals indicate), take deload.

> Source: [RP Strength — In Defense of Set Increases Within Hypertrophy Mesocycle (Israetel, 2020)](https://rpstrength.com/blogs/articles/in-defense-of-set-increases-within-the-hypertrophy-mesocycle)
> Source: [RP Strength — Training Volume Landmarks (Israetel, 2017/2025)](https://rpstrength.com/blogs/articles/training-volume-landmarks-muscle-growth)

**Example: 5-week mesocycle (4 accumulation + 1 deload), intermediate, chest, MEV=8, MRV=20:**
```
Week | Sets/week | Target RIR | Phase
-----|-----------|------------|----------------------
1    | 8         | 3–4 RIR    | MEV start; resensitization
2    | 10        | 2–3 RIR    | Early MAV; adding volume
3    | 14        | 2 RIR      | Mid MAV; productive zone
4    | 18        | 1 RIR      | Approaching MRV; max stimulus
5    | 4–6       | 4–5 RIR    | DELOAD (MV level, ~50% reduction)
```

**Autoregulated set addition algorithm (from Israetel 2020):**
```python
def should_add_set_next_week(muscle: str, recovery_score: int, 
                              pump_score: int, performance_trend: str) -> bool:
    """
    recovery_score: 1–4 (1=no soreness/full recovery, 4=still sore/impaired)
    pump_score:     1–4 (1=no pump, 4=excellent pump)
    performance_trend: 'improved' | 'maintained' | 'declined'
    
    Set addition scoring (RP autoregulation protocol):
    recovery_score == 1 (no soreness) → +1 point toward adding sets
    recovery_score == 2 (mild soreness gone) → neutral
    recovery_score == 3 (lingering soreness) → -1 point
    recovery_score == 4 (severe soreness) → do not add; may reduce
    """
    score = 0
    
    # Recovery assessment
    if recovery_score == 1: score += 1
    elif recovery_score == 3: score -= 1
    elif recovery_score == 4: return False  # do not add; consider deload
    
    # Stimulus assessment (pump proxy)
    if pump_score >= 3: score += 1
    elif pump_score <= 1: score -= 1
    
    # Performance trend
    if performance_trend == 'improved': score += 1
    elif performance_trend == 'declined': return False  # may be at MRV
    
    # Decision
    if score >= 2: return True   # add 1 set
    elif score <= 0: return False # maintain or reduce
    else: return False  # borderline; do not add this week

def calculate_set_increment(score: int) -> int:
    """
    Based on RP recovery/stimulus scoring:
    Both recovery=1 AND pump score good (+2 total) → add 2–3 sets
    score == 1 → add 1 set
    score == 0 → maintain
    score < 0  → reduce 1 set; consider deload
    """
    if score >= 2: return 2
    elif score == 1: return 1
    elif score == 0: return 0
    else: return -1
```

---

### 5.4 Rate of Volume Increase Per Week

```
Standard rate: +1 to +2 sets per muscle group per week
For advanced in narrow MEV-MRV window: +0.5 to +1 set per week (fractions tracked)
For beginners with wide window: may add +2 to +3 sets per week

Practical formula:
  sets_increase_per_week = (MRV - MEV) / accumulation_weeks
  
  Example (chest, intermediate): (20 - 8) / 4 weeks = 3 sets/week increase
  Example (chest, beginner): (14 - 5) / 6 weeks ≈ 1.5 sets/week increase
  
  Round to nearest whole set; tolerance ±1 set per week
```

---

### 5.5 When to End a Mesocycle and Deload

**Primary triggers (from Israetel RP framework):**

```python
MRV_SIGNAL_THRESHOLDS = {
    "performance_decline": True,    # Can't match previous week's reps at same load
    "persistent_soreness": 4,       # Recovery score stays 4 for 2+ consecutive sessions
    "joint_pain": True,             # Any notable joint discomfort
    "weeks_at_accumulation": 5,     # Hard cap; deload regardless after 5 accumulation weeks
    "sleep_disruption": True,       # Severely disrupted sleep (CNS overload signal)
}

def assess_deload_trigger(performance_data: dict, recovery_data: dict, 
                           weeks_accumulated: int) -> bool:
    """
    Returns True if deload should be initiated NOW (this week).
    """
    # Hard cap
    if weeks_accumulated >= MAX_ACCUMULATION_WEEKS[status]:
        return True
    
    # Performance collapse signal
    if performance_data["reps_at_target_load"] < performance_data["prev_week_reps"] - 2:
        # Check if external factors explain it (sleep, stress)
        if performance_data["confounding_factors"] == False:
            return True  # True MRV signal
    
    # Persistent recovery failure
    if recovery_data["avg_recovery_score"] >= 4:
        return True
    
    # Joint pain
    if recovery_data["joint_pain_flag"] == True:
        return True
    
    return False
```

**Deload protocol:**
```python
deload_params = {
    "duration_weeks": 1,
    "target_volume": "MV",           # Drop to ~6 sets/muscle/week (MV level)
    "volume_reduction_pct": 0.50,    # ~50% of peak volume
    "load_reduction_pct": 0.10,      # Keep load at ~90% of working loads
    "rep_range": "same or slightly wider",  # Same exercises; higher RIR
    "rir_during_deload": 5,          # Very easy; 5+ RIR
}
```

---

### 5.6 Cross-Mesocycle Progression (Macro-Level Volume Cycling)

Each successive mesocycle after a deload should start slightly higher MEV than the previous:

```
Mesocycle   | Start Volume        | End Volume (pre-deload)
------------|---------------------|------------------------
Meso 1      | MEV                 | MEV + (accumulation_weeks × increment)
Meso 2      | MEV + 1             | Meso1_end + 1 (or slightly higher)
Meso 3      | MEV + 2             | Approaching MRV peak
Meso 4+     | Assess: reduce if   | Cycle repeats; exercise rotation
            | performance stagnant|

Example (RP Chest Meso 1→3 progression):
Meso 1 Week 1: 3 sets, 185 lb, 3 RIR → Meso 1 Week 4: 5 sets, 200 lb, 0 RIR
Meso 2 Week 1: 4 sets, 200 lb, 3 RIR → Meso 2 Week 4: 6 sets, 215 lb, 0 RIR  
Meso 3 Week 1: 5 sets, 215 lb, 3 RIR → Meso 3 Week 4: 7 sets, 230 lb, 0 RIR
Source: RP Chest Guide example tables
```

**Exercise rotation rule (between mesocycles):**
```python
def rotate_exercises_for_new_meso(prev_exercises: list, muscle: str) -> list:
    """
    RP principle: Change at least 1–2 exercises per mesocycle to:
    - Re-sensitize to exercise stimulus (prevent SRA curve blunting)
    - Train different portions of strength curve / muscle lengthening
    - Maintain novelty and technique improvement
    Rule: keep 1 core compound (e.g., bench press); rotate 1–2 accessory movements
    """
    core_compounds = COMPOUND_EXERCISES[muscle]  # always keep
    accessories = ACCESSORY_EXERCISES[muscle]    # rotate
    new_accessories = pick_different(prev_exercises, accessories, n=1)
    return core_compounds + new_accessories
```

---

## Summary: Implementation Constants and Key Parameters

```python
# ===== VOLUME LANDMARK TABLE (Intermediate Male Reference) =====
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

# ===== BEGINNER MULTIPLIERS =====
BEGINNER_MULTIPLIERS = {
    "MEV": 0.60,
    "MAV_high": 0.70,
    "MRV": 0.65
}

# ===== PROGRESSION PARAMETERS =====
DOUBLE_PROGRESSION_DEFAULTS = {
    "rep_range_low": 8,
    "rep_range_high": 12,
    "rir_start": 3,
    "rir_end_meso": 1,
    "load_increase_barbell_lbs": 5.0,
    "load_increase_dumbbell_lbs": 5.0,
    "load_increase_pct": 0.025   # 2.5%
}

# ===== MESOCYCLE PARAMETERS =====
MESOCYCLE_DEFAULTS = {
    BEGINNER:     {"accumulation_weeks": 8, "deload_weeks": 1, "sets_per_week_increase": 1.5},
    INTERMEDIATE: {"accumulation_weeks": 4, "deload_weeks": 1, "sets_per_week_increase": 2.0},
    ADVANCED:     {"accumulation_weeks": 3, "deload_weeks": 1, "sets_per_week_increase": 1.0},
}

DELOAD_PARAMS = {
    "duration_weeks": 1,
    "volume_pct_of_peak": 0.40,   # ~40–50% of final accumulation week volume
    "load_pct_of_working": 0.90,  # keep weights at 90%
    "rir_floor": 5,               # very easy effort
}

# ===== RIR PROGRESSION SCHEME (4-week meso) =====
RIR_BY_WEEK = {1: 3, 2: 2, 3: 2, 4: 1}  # standard 4-week
# For longer mesos: {1: 4, 2: 3, 3: 3, 4: 2, 5: 1}

# ===== TOTAL WEEKLY VOLUME CAPS =====
TOTAL_WEEKLY_SET_CAPS = {
    BEGINNER:     80,
    INTERMEDIATE: 130,
    ADVANCED:     175,
}
```

---

## Sources & Citations

1. Israetel, M. (2017, updated 2025). "Training Volume Landmarks for Muscle Growth." *RP Strength*. https://rpstrength.com/blogs/articles/training-volume-landmarks-muscle-growth

2. Israetel, M. (2020). "In Defense of Set Increases Within the Hypertrophy Mesocycle." *RP Strength*. https://rpstrength.com/blogs/articles/in-defense-of-set-increases-within-the-hypertrophy-mesocycle

3. Israetel, M. (2018). "Progressing for Hypertrophy." *RP Strength*. https://rpstrength.com/blogs/articles/progressing-for-hypertrophy

4. Israetel, M. (2024). "Complete Glute Training Guide." *RP Strength*. https://rpstrength.com/blogs/articles/glute-hypertrophy-training-tips

5. Israetel, M. (2024). "Complete Chest Training Guide." *RP Strength*. https://rpstrength.com/blogs/articles/chest-hypertrophy-training-tips

6. Schoenfeld, B.J. & Krieger, J. (2017). "Dose-response relationship between weekly resistance training volume and increases in muscle mass: A systematic review and meta-analysis." *Journal of Sports Sciences*, 35(11), 1073–1082. https://pubmed.ncbi.nlm.nih.gov/27433992/

7. Schoenfeld, B.J., Ogborn, D., & Krieger, J.W. (2019). "Resistance Training Volume Enhances Muscle Hypertrophy but Not Strength in Trained Men." *Medicine & Science in Sports & Exercise*, 51(1), 94–103. https://pmc.ncbi.nlm.nih.gov/articles/PMC6303131/

8. Schoenfeld, B.J. (2017). "Evidence-Based Guidelines for Resistance Training Volume to Maximize Muscle Hypertrophy." *Strength and Conditioning Journal*. https://elementssystem.com/wp-content/uploads/2018/08/Schoenfeld-volumen-review.pdf

9. Krieger, J. (2024). "The King of Volume Metas." *Biolayne*. https://biolayne.com/reps/issue-31/the-king-of-volume-metas/

10. Helms, E. & Wolf, M. (2024). "How to Train for Maximum Muscle Growth." https://www.youtube.com/watch?v=twOKHMAAR0U

11. Helms, E. (2020). "How to Properly Program for Hypertrophy." https://www.youtube.com/watch?v=uL9CHTp4_x4

12. Helms, E. (2016). "Application of the Repetitions in Reserve-Based Rating of Perceived Exertion Scale." *Strength and Conditioning Journal*. https://pmc.ncbi.nlm.nih.gov/articles/PMC4961270/

13. Helms, E. (2021). "Rep Ranges & RIR for Muscle Growth." *Swole Radio Podcast*. https://www.youtube.com/watch?v=QZ4M5t7lLWs

14. Ripped Body. (2025). "How to Make Progress With Your Training." https://rippedbody.com/progression/

15. BostonRAL. (2021). "Summary of Dr. Mike Israetel and RP's Volume Landmarks." *r/AdvancedFitness*. https://www.reddit.com/r/AdvancedFitness/comments/lyney9/

16. Weightology. (2025). "Set Volume for Muscle Size: The Ultimate Evidence Based Bible." https://weightology.net/the-members-area/evidence-based-guides/set-volume-for-muscle-size-the-ultimate-evidence-based-bible/

17. Reshape.ai. (2025). "Periodization for Strength and Hypertrophy." https://www.reshapeapp.ai/blog/periodization-for-strength-and-hypertrophy
