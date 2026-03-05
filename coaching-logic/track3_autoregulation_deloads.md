# Track 3: RIR-Based Autoregulation & Reactive Deload Protocols
## Milo AI Fitness Coaching System — Backend Logic Reference

**Document Type:** Research Synthesis for AI Backend Consumption  
**Target Population:** Male beginner-to-intermediate lifters  
**Primary Intensity Metric:** RIR (Reps in Reserve)  
**Deload Model:** Reactive (signal-triggered), not fixed-schedule  

---

## Table of Contents
1. [RIR-Based Intensity Prescription](#1-rir-based-intensity-prescription)
2. [Performance Tracking & Fatigue Detection](#2-performance-tracking--fatigue-detection)
3. [Reactive Deload Triggers](#3-reactive-deload-triggers)
4. [Deload Protocol](#4-deload-protocol)
5. [Post-Deload Progression](#5-post-deload-progression)
6. [Variable Index](#6-variable-index)

---

## 1. RIR-Based Intensity Prescription

### 1.1 Definitions

**RIR (Reps in Reserve):** The number of additional repetitions a lifter could perform before reaching momentary muscular failure. A set with RIR = 2 means the lifter could have completed exactly 2 more reps before failing.

**RPE (Rating of Perceived Exertion):** Zourdos et al. (2016) formalized the resistance-training-specific RPE scale where each RPE value maps to a concrete RIR count:

```
RPE = 10 - RIR
```

| RPE | RIR | Descriptor |
|-----|-----|------------|
| 10  | 0   | True max — no further reps possible |
| 9.5 | 0   | Could not do another rep, but could add tiny load |
| 9   | 1   | 1 rep left in the tank |
| 8.5 | 1–2 | 1–2 reps in reserve |
| 8   | 2   | 2 reps in reserve |
| 7.5 | 2–3 | 2–3 reps in reserve |
| 7   | 3   | 3 reps in reserve |
| 6   | 4   | 4 reps in reserve |
| 5   | 5   | 5 reps in reserve |
| ≤4  | 6+  | Light-to-moderate effort |

**Source:** Zourdos et al. (2016). "Novel Resistance Training–Specific Rating of Perceived Exertion Scale Measuring Repetitions in Reserve." *Journal of Strength and Conditioning Research*, 30: 267–275. https://pubmed.ncbi.nlm.nih.gov/26049792/

### 1.2 Evidence for RIR-Based Training Effectiveness

**Key Evidence:**

1. **Zourdos et al. (2016)** — Established that RPE values mapped to RIR show a strong inverse relationship with average concentric velocity in both experienced squatters (r = -0.88, p < 0.001) and novice squatters (r = -0.77, p = 0.001). This validates RIR as an objective intensity proxy tied to real neuromuscular output. Source: https://pubmed.ncbi.nlm.nih.gov/26049792/

2. **Helms et al. (2018 / Frontiers in Physiology)** — RCT comparing RPE-based versus percentage-1RM-based loading (matched sets, reps, exercises). The RPE group trained at significantly higher average relative intensity (84.14% vs 78.70% of 1RM for bench press, p < 0.001) and accumulated greater volume-load. Both groups increased strength and hypertrophy, with the RPE group showing a higher probability of superior strength gains. Conclusion: "RPE-based loading may provide a small 1RM strength advantage in a majority of individuals." Source: https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2018.00247/full

3. **Graham & Cleather (2019 / JSCR)** — "Autoregulation by 'Repetitions in Reserve' Leads to Greater Improvements in Strength Over a 12-Week Training Program Than Fixed Loading." RIR autoregulation produced superior strength adaptations vs. fixed loading over 12 weeks. Source: https://pubmed.ncbi.nlm.nih.gov/31009432/

4. **Lovegrove et al. (2022 / JSCR)** — Confirmed RIR is a reliable tool for prescribing resistance training load for deadlift and bench press (test-retest reliability confirmed). Source: https://www.semanticscholar.org/paper/Repetitions-in-Reserve-Is-a-Reliable-Tool-for-Load-Lovegrove-Hughes/ac62b53daaffc4520b757c2c00ffac61f578a6c2

5. **Helms et al. (2016 / Strength and Conditioning Journal)** — "Application of the Repetitions in Reserve-Based Rating of Perceived Exertion Scale" — foundational application paper establishing practical use for load prescription. Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC4961270/

### 1.3 RIR Targets by Training Phase

```
VARIABLE: phase_rir_target [int]
  -- The prescribed RIR range for the current mesocycle phase
  -- Used to set loading and progression ceilings
```

| Mesocycle Phase | Week Position | RIR Target | RPE Equivalent | Rationale |
|-----------------|---------------|------------|----------------|-----------|
| Early meso (intro) | Weeks 1–2 | 3–4 | RPE 6–7 | Acclimatization, technique, low fatigue accumulation |
| Mid meso | Weeks 3–4 | 2–3 | RPE 7–8 | Stimulus ascending, manageable fatigue |
| Late meso | Weeks 5–6+ | 1–2 | RPE 8–9 | Near-failure stimuli, fatigue accumulation peak |
| Deload | N/A | 4–5 | RPE 5–6 | Active recovery, technique maintenance |

**Theoretical Basis:** Israetel (RP Strength), Helms et al. (2016). Starting a mesocycle at RIR 3 corresponds to the "just barely effective" threshold where stimuli reliably produce hypertrophy without excessive fatigue. As the meso progresses, proximity to failure increases, which raises training stimulus magnitude. This creates a predictable fatigue arc from MEV (minimum effective volume) toward MRV (maximum recoverable volume). Source: https://rpstrength.com/blogs/articles/in-defense-of-set-increases-within-the-hypertrophy-mesocycle

```python
# Pseudocode: Phase RIR Target Assignment
def get_phase_rir_target(week_in_meso: int, meso_length: int) -> tuple[int, int]:
    """
    Returns (rir_min, rir_max) for current week.
    Assumes a standard 4–6 week mesocycle.
    """
    progress_ratio = week_in_meso / meso_length  # 0.0 → 1.0

    if progress_ratio <= 0.33:           # Early meso
        return (3, 4)
    elif progress_ratio <= 0.67:         # Mid meso
        return (2, 3)
    else:                                # Late meso
        return (1, 2)

def get_deload_rir_target() -> tuple[int, int]:
    return (4, 5)
```

### 1.4 RIR Targets by Exercise Type

Different exercises warrant different RIR floors due to injury risk, technical complexity, and fatigue generation:

| Exercise Category | Examples | Recommended Minimum RIR | Notes |
|-------------------|----------|--------------------------|-------|
| High-complexity compound | Squat, Deadlift, Olympic lifts | ≥2 (never go to true 0 RIR) | High injury risk, high systemic fatigue cost |
| Low-complexity compound | Bench press, OHP, Row | 1–2 in late meso | Moderately high fatigue, more controllable |
| Isolation / machine | Leg curl, lat pulldown, cable fly | 0–1 in late meso | Low systemic fatigue, failure more acceptable |

**Rationale:** For compound lifts, technique degrades near failure, raising injury risk. For power-dominant training at >80% 1RM, Helms et al. (2016) recommend performing sets at RIR 2–3, stopping well short of failure to preserve bar speed and CNS recovery. For isolation work, sets closer to or at failure are acceptable because systemic fatigue impact is minimal. Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC4961270/

```python
# Pseudocode: Exercise-Type RIR Floor
def get_exercise_rir_floor(exercise_type: str, phase: str) -> int:
    """
    Returns absolute minimum allowed RIR for a given exercise and phase.
    Even in late meso, RIR cannot go below this floor.
    """
    floors = {
        "high_complexity_compound": 2,
        "low_complexity_compound": 1,
        "isolation": 0
    }
    base_floor = floors.get(exercise_type, 1)
    
    # During deload, all floors increase by 2
    if phase == "deload":
        return base_floor + 2
    return base_floor
```

### 1.5 Beginner RIR Accuracy and Handling

**Evidence:**

- **Accuracy in general:** Most trainees are accurate to within ~1 repetition on average. The mean underprediction (thinking they have fewer reps left than they actually do) is approximately 0.95–1.1 reps. Standard deviation of error is ~1.45 reps. Source: https://www.strongerbyscience.com/reps-in-reserve/

- **When accuracy is higher:** Accuracy improves significantly when: (a) fewer than 12 reps are performed per set, (b) predictions are made later in the set rather than at the start, and (c) the set is closer to failure. Source: https://www.strongerbyscience.com/reps-in-reserve/

- **Training status:** Contrary to intuition, training status does NOT significantly improve RIR accuracy in controlled studies. Novice and experienced lifters show similar average error magnitudes. However, experienced lifters may be more consistent at gauging RIR as they approach failure (lower SD of scores at 90%+ intensity). Source: Zourdos et al. (2016) https://pubmed.ncbi.nlm.nih.gov/26049792/

- **Practical implication for novices:** Helms et al. (2016) specifically note that "novice lifters should practice recording RIR, but likely not base training intensity or progression solely on the RIR-based scale until increased accuracy is achieved." Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC4961270/

**Milo Implementation Rules for Beginners:**

```python
# Pseudocode: RIR Correction for Beginner Lifters
BEGINNER_RIR_CORRECTION = +1  # Add 1 RIR buffer for lifters < 12 months experience

def apply_beginner_correction(
    reported_rir: int,
    training_age_months: int,
    reps_performed: int
) -> int:
    """
    Adjusts reported RIR upward for beginners to compensate for systematic
    underprediction and to provide a safety buffer on compound movements.
    Correction is reduced for sets ≤8 reps (better accuracy) and removed
    after 12 months of logged training.
    """
    if training_age_months < 12:
        correction = BEGINNER_RIR_CORRECTION
        if reps_performed <= 8:
            correction = max(0, correction - 1)  # Less correction needed near failure
        return reported_rir + correction
    return reported_rir
```

**Practical Guidance:**
- For beginners in weeks 1–4, Milo should use a conservative RIR target of 4–5 to ensure actual proximity to failure is ~3, accounting for systematic underprediction.
- Recommend tracking calibration: System should log predicted RIR vs. actual performance data to build a user-specific correction factor over time.

---

## 2. Performance Tracking & Fatigue Detection

### 2.1 Session-to-Session Performance Tracking

The primary tracking unit is the **Estimated 1 Repetition Maximum (e1RM)** computed from each working set.

**Key Variables:**
```
VARIABLE: session_date           [date]       -- Date of training session
VARIABLE: exercise_id            [string]     -- Canonical exercise name
VARIABLE: set_number             [int]        -- Ordinal set within session
VARIABLE: load_kg                [float]      -- Absolute load lifted (kg)
VARIABLE: reps_completed         [int]        -- Total reps performed
VARIABLE: reported_rir           [int]        -- RIR as reported by lifter
VARIABLE: adjusted_rir           [int]        -- RIR after beginner correction
VARIABLE: e1rm                   [float]      -- Calculated estimated 1RM
VARIABLE: session_e1rm           [float]      -- Top-set or best e1RM per exercise per session
VARIABLE: rolling_e1rm_7d        [float]      -- 7-day average e1RM per exercise
VARIABLE: rolling_e1rm_28d       [float]      -- 28-day average e1RM per exercise
VARIABLE: e1rm_pct_change        [float]      -- % change vs. prior session's e1RM
VARIABLE: consecutive_decline_ct [int]        -- Count of consecutive sessions with e1RM drop
```

### 2.2 e1RM Formulas

#### Primary: Epley Formula (simplest, best for compound lifts at 1–10 reps)
```
e1RM = load × (1 + reps / 30)
```
- Developed by Boyd Epley (1985). Assumes linear rep-strength relationship. Best accuracy for 2–10 reps. Source: https://maxcalculator.com/guides/epley-formula

#### Alternative: Brzycki Formula (slightly more accurate for higher rep sets)
```
e1RM = load / (1.0278 − 0.0278 × reps)
```
Source: https://www.strengthjourneys.xyz/articles/how-do-i-calculate-my-e1rm-estimated-one-rep-max

#### RPE-Adjusted e1RM (recommended for Milo — incorporates effort level)
When RIR data is available, the e1RM should be adjusted for effort level. The conceptual formula:

```
e1RM_adjusted = e1RM_epley × RPE_adjustment_factor
```

Where `RPE_adjustment_factor` is derived from RTS/Tuchscherer-style percentage charts. At RPE 10 (RIR 0), adjustment = 1.00. At RPE 8 (RIR 2), adjustment ≈ 1.05–1.07 (meaning estimated max is ~5-7% higher than what was lifted). Source: https://www.verrotraining.com/blog/maximize-your-training-accuracy-the-verro-e1rm-formula

**Simplified Milo Implementation:**
```python
# Pseudocode: e1RM Calculation

def calc_e1rm_epley(load: float, reps: int) -> float:
    """Standard Epley formula. Best for 1-10 reps."""
    if reps == 1:
        return load
    return load * (1 + reps / 30)

def calc_e1rm_rir_adjusted(load: float, reps: int, rir: int) -> float:
    """
    RPE/RIR-adjusted e1RM. Accounts for effort level.
    When RIR = 0 (RPE 10), no adjustment needed.
    When RIR > 0, the true max is higher than what was lifted.
    
    Adjustment table (based on RTS charts, approximated):
    RIR 0  → multiplier 1.00
    RIR 1  → multiplier 1.03
    RIR 2  → multiplier 1.06
    RIR 3  → multiplier 1.09
    RIR 4  → multiplier 1.12
    RIR 5  → multiplier 1.15
    """
    RIR_MULTIPLIERS = {0: 1.00, 1: 1.03, 2: 1.06, 3: 1.09, 4: 1.12, 5: 1.15}
    base_e1rm = calc_e1rm_epley(load, reps)
    multiplier = RIR_MULTIPLIERS.get(rir, 1.00 + (rir * 0.03))
    return base_e1rm * multiplier

def get_session_e1rm(sets: list[dict]) -> float:
    """
    Returns the best (highest) e1RM from all working sets in a session.
    Only uses sets with reps ≤ 10 for Epley accuracy.
    sets: list of {'load': float, 'reps': int, 'rir': int}
    """
    valid_sets = [s for s in sets if s['reps'] <= 10 and s['reps'] >= 1]
    if not valid_sets:
        return None
    return max(calc_e1rm_rir_adjusted(s['load'], s['reps'], s['rir']) 
               for s in valid_sets)
```

### 2.3 What Constitutes Performance Decline vs. Normal Variation

Normal day-to-day e1RM fluctuation is expected. The challenge is distinguishing noise from signal.

**Normal variation range:** ±2–3% session-to-session is within expected biological variance for trained individuals. Beginner lifters may show ±5% due to skill variance.

**Performance decline signal:** A meaningful decline is flagged when e1RM drops **>5% from the 7-day rolling average** on key compound lifts. A **>10% drop** from the 28-day rolling average is a strong systemic fatigue indicator. Source: Progressive Rehab & Strength https://www.progressiverehabandstrength.com/articles/calculating-and-tracking-rpe-e1rm-for-barbell-strength-training

**Supporting metric — RPE drift:** When sets are performed at the same load and reps but RPE/difficulty is reported as higher (RIR decreasing despite no load change), this signals accumulating fatigue even before absolute e1RM drops. This RPE uncoupling from external load is a leading indicator of fatigue.

```python
# Pseudocode: Performance Change Detection

def calc_e1rm_pct_change(current_e1rm: float, reference_e1rm: float) -> float:
    """
    Returns percent change as a decimal.
    Negative value = decline, positive = improvement.
    """
    if reference_e1rm is None or reference_e1rm == 0:
        return 0.0
    return (current_e1rm - reference_e1rm) / reference_e1rm

def is_performance_declining(
    current_e1rm: float,
    rolling_7d_e1rm: float,
    rolling_28d_e1rm: float
) -> dict:
    """
    Returns diagnostic dict with decline flags.
    """
    short_term_change = calc_e1rm_pct_change(current_e1rm, rolling_7d_e1rm)
    long_term_change = calc_e1rm_pct_change(current_e1rm, rolling_28d_e1rm)

    return {
        "short_term_decline": short_term_change < -0.05,   # >5% drop vs 7-day avg
        "long_term_decline": long_term_change < -0.10,    # >10% drop vs 28-day avg
        "short_term_pct": short_term_change,
        "long_term_pct": long_term_change,
        "severity": "high" if long_term_change < -0.10 
                    else "moderate" if short_term_change < -0.05 
                    else "none"
    }
```

### 2.4 Fatigue Threshold for Deload Flagging

**Core threshold:** If e1RM drops **>5–10% on key lifts (squat, deadlift, bench press) across 2 or more consecutive sessions**, this constitutes a fatigue flag. Source: Progressive Rehab & Strength https://www.progressiverehabandstrength.com/articles/calculating-and-tracking-rpe-e1rm-for-barbell-strength-training

```
THRESHOLD_SHORT_TERM_DECLINE_PCT  = 0.05   (5%)
THRESHOLD_LONG_TERM_DECLINE_PCT   = 0.10  (10%)
THRESHOLD_CONSECUTIVE_DECLINES    = 2     (sessions)
```

### 2.5 Systemic vs. Local Muscle Group Fatigue

This distinction is critical for deciding whether to deload the entire program or just modify a single lift.

| Signal Pattern | Interpretation | Response |
|----------------|----------------|----------|
| e1RM drops on 1 lift, others unaffected | Local muscle group fatigue OR technique issue | Reduce volume/intensity on that movement only; do not full deload |
| e1RM drops on 2+ major compound lifts simultaneously | Systemic/CNS fatigue | Trigger full reactive deload |
| RPE elevating across all lifts but no load drop yet | Systemic fatigue early signal | Increase monitoring; consider early deload |
| Joint pain + soreness localized to one area | Local structural fatigue/overuse | Remove the offending movement; investigate form |
| Subjective markers (motivation, sleep, mood) degraded + ≥1 lift declining | Systemic fatigue (likely CNS + hormonal) | Trigger reactive deload |

```python
# Pseudocode: Systemic vs. Local Fatigue Classification

def classify_fatigue_type(
    declining_lifts: list[str],  # List of key lifts showing >5% e1rm decline
    total_key_lifts: int,        # Total number of tracked key lifts
    systemic_symptoms: bool      # RPE drift, sleep/HRV signals, motivation
) -> str:
    """
    Returns 'systemic', 'local', or 'none'.
    Systemic fatigue triggers full deload; local triggers targeted adjustment.
    """
    proportion_declining = len(declining_lifts) / total_key_lifts
    
    if len(declining_lifts) == 0:
        return "none"
    elif proportion_declining >= 0.5 or systemic_symptoms:
        return "systemic"
    else:
        return "local"
```

---

## 3. Reactive Deload Triggers

### 3.1 Evidence-Based Trigger Categories

Sources: Israetel (RP Strength), Helms et al. (2016), Bell et al. (2022/2023 — "A Practical Approach to Deloading" / NSCA, "Integrating Deloading into Strength and Physique Sports Training Programmes" / Sports Medicine — Open)

#### Trigger Category 1: Objective Performance Stagnation or Regression
- **Signal:** e1RM drops ≥5% on ≥2 key compound lifts across ≥2 consecutive sessions
- **Threshold:** `consecutive_decline_ct >= 2` AND `e1rm_pct_change <= -0.05` on ≥2 lifts
- **Evidence:** Breaking Muscle reactive deload heuristic: "two consecutive training sessions of reduced performance (e.g., unintentional drop in session volume-load)." Source: https://breakingmuscle.com/deload-week/

#### Trigger Category 2: Inability to Hit Prescribed RIR Targets
- **Signal:** Sets feel harder than prescribed RIR target despite no load increase; RIR reporting drift (regularly coming in 2+ RIR below target)
- **Threshold:** `reported_rir < (prescribed_rir - 2)` on ≥50% of sets in a session, for ≥2 consecutive sessions
- **Interpretation:** If a lifter is prescribed RIR 2 but consistently achieving only RIR 0, the accumulated fatigue is masking strength expression. Source: Helms et al. (2016) https://pmc.ncbi.nlm.nih.gov/articles/PMC4961270/

#### Trigger Category 3: Subjective Fatigue Accumulation
- **Signal:** User self-reports: persistent soreness, poor motivation, reduced enthusiasm, general heaviness
- **Threshold:** ≥3 consecutive sessions reporting high subjective fatigue OR ≥3 consecutive poor motivation reports
- **Evidence:** "Three consecutive training sessions with poor motivation to train" / "Four consecutive nights of poor sleep quality." Source: Breaking Muscle https://breakingmuscle.com/deload-week/

#### Trigger Category 4: Recovery Metric Deterioration (HRV/Sleep)
- **Signal:** HRV trending below personal baseline, resting HR drift upward, sleep quality degradation
- **Threshold:**
  - HRV suppressed below personal baseline for 4+ consecutive days → red trigger
  - Resting HR drift upward for 3+ days with other symptoms → amber/trigger
  - Sleep debt accumulating over 4+ nights with poor subjective recovery → red trigger
- **Evidence:** SensAI data-driven deload framework; Morpheus HRV deload guidance. The principle of trigger clustering: fire deload when ≥2 domains are negative. Source: https://www.sensai.fit/blog/data-driven-deload-week-hrv-sleep-training-load

#### Trigger Category 5: Performance Stagnation (No Progress for Extended Period)
- **Signal:** 5 consecutive sessions with no ability to progress (same load, same reps, same RPE)
- **Evidence:** Breaking Muscle "one-to-five" rule: "Five consecutive workouts with no ability to progress." Source: https://breakingmuscle.com/deload-week/

#### Trigger Category 6: Pain / Excessive Soreness
- **Signal:** User reports joint pain, sharp pain during movement, or extreme DOMS preventing normal ROM
- **Threshold:** Any report of joint pain = immediate trigger (zero tolerance rule)
- **Response:** Immediate deload + investigation of offending movement pattern

### 3.2 Specific Thresholds and Decision Logic

```
# Global Thresholds (constants)
T_E1RM_SHORT_DECLINE   = -0.05   # 5% e1RM drop vs 7-day rolling avg
T_E1RM_LONG_DECLINE    = -0.10   # 10% e1RM drop vs 28-day rolling avg
T_CONSECUTIVE_DECLINES = 2       # Consecutive sessions below threshold
T_RIR_MISS_THRESHOLD   = 2       # RIR below target by this amount = miss
T_RIR_MISS_SESSION_PCT = 0.50    # % of sets missing RIR target in a session
T_RIR_MISS_SESSIONS    = 2       # Consecutive sessions with RIR misses
T_SUBJECTIVE_SESSIONS  = 3       # Consecutive sessions with poor subjective markers
T_HRV_SUPPRESSION_DAYS = 4       # Consecutive days HRV below personal baseline
T_SLEEP_DEBT_DAYS      = 4       # Consecutive nights poor sleep
T_STAGNATION_SESSIONS  = 5       # Consecutive sessions with zero progress
```

### 3.3 Deload Decision Tree (Pseudocode)

```python
# Pseudocode: Full Reactive Deload Decision Engine

def evaluate_deload_trigger(
    # Performance metrics
    key_lift_declines: list[bool],          # Per-lift decline flags (≥5%)
    consecutive_decline_counts: list[int],  # Per-lift consecutive decline count
    rir_miss_rate_sessions: list[float],    # Per session: fraction of sets missing RIR target by ≥2
    consecutive_rir_miss_sessions: int,     # Sessions in a row with ≥50% RIR misses
    
    # Subjective metrics
    consecutive_poor_motivation: int,       # Sessions with poor motivation reported
    joint_pain_reported: bool,             # Any joint pain this session
    
    # Recovery metrics (cross-ref Track 4)
    hrv_suppressed_days: int,              # Days HRV below personal baseline
    sleep_debt_days: int,                  # Consecutive nights poor sleep
    
    # Progress metrics
    consecutive_stagnation: int            # Sessions with zero progression
) -> dict:
    """
    Returns deload decision and primary trigger reason.
    Returns: {
        'trigger': bool,
        'urgency': 'immediate' | 'recommended' | 'monitor',
        'reason': str,
        'fatigue_type': 'systemic' | 'local' | 'none'
    }
    """
    
    # RULE 1: Immediate trigger — joint pain
    if joint_pain_reported:
        return {
            'trigger': True,
            'urgency': 'immediate',
            'reason': 'joint_pain_reported',
            'fatigue_type': 'local'
        }
    
    # RULE 2: Systemic performance regression
    declining_lift_count = sum(
        1 for i, declining in enumerate(key_lift_declines)
        if declining and consecutive_decline_counts[i] >= T_CONSECUTIVE_DECLINES
    )
    if declining_lift_count >= 2:
        return {
            'trigger': True,
            'urgency': 'immediate',
            'reason': 'multi_lift_e1rm_decline',
            'fatigue_type': 'systemic'
        }
    
    # RULE 3: Single lift consecutive decline (local, not systemic)
    if any(c >= T_CONSECUTIVE_DECLINES and d 
           for c, d in zip(consecutive_decline_counts, key_lift_declines)):
        if declining_lift_count == 1:
            return {
                'trigger': False,  # Not a full deload, but targeted reduction
                'urgency': 'monitor',
                'reason': 'single_lift_local_decline',
                'fatigue_type': 'local'
            }
    
    # RULE 4: RIR target chronically missed
    if consecutive_rir_miss_sessions >= T_RIR_MISS_SESSIONS:
        return {
            'trigger': True,
            'urgency': 'recommended',
            'reason': 'rir_target_missed_repeatedly',
            'fatigue_type': 'systemic'
        }
    
    # RULE 5: Performance stagnation
    if consecutive_stagnation >= T_STAGNATION_SESSIONS:
        return {
            'trigger': True,
            'urgency': 'recommended',
            'reason': 'performance_stagnation',
            'fatigue_type': 'systemic'
        }
    
    # RULE 6: Recovery metric cluster trigger
    recovery_signals_red = sum([
        hrv_suppressed_days >= T_HRV_SUPPRESSION_DAYS,
        sleep_debt_days >= T_SLEEP_DEBT_DAYS,
        consecutive_poor_motivation >= T_SUBJECTIVE_SESSIONS
    ])
    if recovery_signals_red >= 2:
        return {
            'trigger': True,
            'urgency': 'recommended',
            'reason': 'recovery_signal_cluster',
            'fatigue_type': 'systemic'
        }
    
    # RULE 7: Moderate signals — monitor mode
    recovery_signals_amber = sum([
        hrv_suppressed_days >= 2,
        sleep_debt_days >= 2,
        consecutive_poor_motivation >= 2,
        declining_lift_count >= 1
    ])
    if recovery_signals_amber >= 2:
        return {
            'trigger': False,
            'urgency': 'monitor',
            'reason': 'multiple_amber_signals',
            'fatigue_type': 'potential_systemic'
        }
    
    return {
        'trigger': False,
        'urgency': 'none',
        'reason': 'no_fatigue_signals',
        'fatigue_type': 'none'
    }
```

### 3.4 Consecutive Sessions of Decline Before Triggering

| Scenario | Required Consecutive Sessions | Evidence Source |
|----------|-------------------------------|-----------------|
| e1RM drop ≥5% on 2+ lifts | 2 | Progressive Rehab & Strength; Helms et al. 2016 |
| RIR target missed by ≥2 reps | 2 | Helms/Israetel RP roundtable discussion |
| Poor motivation / subjective fatigue | 3 | Breaking Muscle "one-to-five" rule |
| Performance zero progress | 5 | Breaking Muscle "one-to-five" rule |
| Joint pain | 0 (immediate) | Clinical safety standard |

Source: https://breakingmuscle.com/deload-week/

---

## 4. Deload Protocol

### 4.1 Evidence on Optimal Deload Structure

**Primary consensus findings (Bell et al. 2022/2023 — Delphi consensus with expert coaches):**
- Universal agreement: training volume MUST decrease during deloading
- Training intensity (load) can either decrease or be maintained
- Frequency generally remains unchanged
- Duration: 5–7 days is standard
- Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC10511399/

**Bosquet taper meta-analysis (endurance, n=27 studies):** Volume reduction of 41–60% produced the largest effect size (0.72 ± 0.36, p<0.001) while maintaining intensity/frequency. This dosage principle transfers to resistance training deload design. Source cited in: https://www.sensai.fit/blog/data-driven-deload-week-hrv-sleep-training-load

**Juggernaut Training Systems (Chad Wesley Smith / Israetel principle):** "When you put on the brakes, put them on hard." Anything above ~50% of normal volume+effort combination during a deload is likely "extra work you could be not doing." The deload should be aggressive, not gradual. Source: https://www.jtsstrength.com/fatigue-explained/

### 4.2 Deload Variables

```
VARIABLE: deload_volume_reduction_pct  [float]  -- Target % reduction from pre-deload volume
VARIABLE: deload_intensity_target      [float]  -- Target % of normal working loads
VARIABLE: deload_rir_target            [int]    -- RIR floor during deload (4–5)
VARIABLE: deload_duration_days         [int]    -- Length of deload (default 7)
VARIABLE: deload_set_count             [int]    -- Actual sets per session during deload
VARIABLE: deload_load_pct              [float]  -- % of pre-deload working loads
```

### 4.3 Volume Reduction: Quantified

**Standard recommendation:** Reduce training volume by **40–60%** relative to the preceding training phase.

| Recovery Needs Assessment | Volume Reduction | Sets Remaining |
|---------------------------|------------------|----------------|
| Low (mild fatigue) | 25–45% | ~55–75% of normal |
| Moderate (typical deload) | 40–60% | ~40–60% of normal |
| High (severe accumulated fatigue) | 60–90% | ~10–40% of normal |

**How to reduce volume:** Preferentially reduce the NUMBER OF SETS rather than the number of exercises or reps per set. Evidence from Juggernaut and Israetel suggests volume is the primary driver of fatigue accumulation, so cutting sets is the most efficient lever. Source: https://www.jtsstrength.com/fatigue-explained/

**Practical set targets (moderate recovery deload):**
- If pre-deload weekly sets per muscle group = 16 → deload target = 8 (50% cut)
- Per-session sets per exercise: reduce from e.g. 4 sets → 2 sets

### 4.4 Intensity Handling: Should Load Be Maintained or Reduced?

**Evidence-based recommendation:** Maintain load (intensity) while cutting volume. Do NOT cut load while maintaining volume. This is the most common error in deloading.

**Rationale from Juggernaut (Israetel/Smith):** "Intensity (weight on the bar) is the primary savior of training gains in a deload, dropping the weights and upping the volumes is exactly the OPPOSITE of what you want to do." Source: https://www.jtsstrength.com/fatigue-explained/

**Pritchard et al. (2019 — "Higher- vs. Lower-Intensity Strength-Training Taper"):** A taper with ~70% volume reduction and maintained or slightly higher intensity produced greater improvements in CMJ force and strength than a lower-intensity taper. The higher-intensity condition produced effect-size improvements in isometric midthigh-pull force, CMJ height, and flight time:contraction time. Source: https://pubmed.ncbi.nlm.nih.gov/30204523/

**Bell et al. (Practical Approach to Deloading, NSCA):**
- Standard deload: reduce load by ~10% of 1RM while maintaining reps (i.e., a slight intensity reduction) OR increase RIR by 2–3 (stopping further from failure with the same load)
- Intensity maintenance recommendation: maintain ≥85% 1RM when neuromuscular adaptations are a priority
- Volume reduction: 40–60%
- Source: https://doras.dcu.ie/31501/1/a_practical_approach_to_deloading__recommendations.203(2).pdf

**Practical Milo rule:**
- PRIMARY lever: cut sets by 50%
- SECONDARY lever: increase RIR target to 4–5 (sets stop further from failure)
- TERTIARY option only if high recovery needs: reduce load by 10–15%

```python
# Pseudocode: Deload Session Prescription

def generate_deload_session(
    pre_deload_sets_per_exercise: dict,   # {exercise_id: int (set count)}
    pre_deload_working_loads: dict,       # {exercise_id: float (kg)}
    recovery_needs: str,                  # 'low', 'moderate', 'high'
    pre_deload_rep_ranges: dict           # {exercise_id: (min_reps, max_reps)}
) -> dict:
    """
    Returns deload session prescription.
    """
    volume_reduction = {
        'low': 0.35,       # Cut 35% of sets
        'moderate': 0.50,  # Cut 50% of sets
        'high': 0.70       # Cut 70% of sets
    }[recovery_needs]
    
    load_reduction = {
        'low': 0.00,       # No load reduction (maintain)
        'moderate': 0.10,  # Reduce load by 10%
        'high': 0.15       # Reduce load by 15%
    }[recovery_needs]

    deload_prescription = {}
    for exercise_id in pre_deload_sets_per_exercise:
        original_sets = pre_deload_sets_per_exercise[exercise_id]
        original_load = pre_deload_working_loads[exercise_id]
        
        deload_prescription[exercise_id] = {
            'sets': max(1, round(original_sets * (1 - volume_reduction))),
            'load': original_load * (1 - load_reduction),
            'rir_target': (4, 5),           # Deload RIR target
            'reps': pre_deload_rep_ranges[exercise_id]  # Keep same rep range
        }
    
    return deload_prescription
```

### 4.5 Ogasawara et al. (2013) on Periodic Detraining-Retraining Cycles

**Ogasawara et al. (2013)** — "Comparison of Muscle Hypertrophy Following 6-Month of Continuous and Periodic Strength Training" (*Eur J Appl Physiol* 113:975–985):

- 14 young men: continuous training (CTR) vs. periodic training (PTR: 3 cycles of 6-week training + 3-week detraining)
- Protocol: bench press, 75% 1RM, 3 sets × 10 reps, 3 days/week for 24 weeks
- **Key finding:** Overall improvements in muscle CSA and 1-RM strength were SIMILAR between groups after 24 weeks, even though the PTR group had **25% fewer total training sessions** and **33.5% lower total volume** (CTR: 96,942 kg vs PTR: 64,509 kg total)
- Mechanism: During retraining after detraining, muscle adaptation rates returned to early-phase levels (higher sensitivity). The rate of increase in muscle CSA and strength during second retraining cycle was significantly HIGHER in PTR than CTR.
- **Implication for Milo:** Aggressive 1-week deloads (reduced training stress, not total cessation) are unlikely to cost meaningful muscle or strength. They allow re-sensitization of muscle to training stimuli. Complete training cessation for 3 weeks does cause ~2–3% 1RM decline, but this is rapidly recovered. Source: https://pubmed.ncbi.nlm.nih.gov/23053130/

**Coleman et al. (2024 / PeerJ)** — "Gaining More From Doing Less?":
- 1-week deload (complete cessation) at midpoint of 9-week program: similar hypertrophy to continuous training, but slightly inferior strength gains
- Key implication: **active deload (reduced volume, maintained movement)** is preferable to complete cessation for strength sports, as it preserves neuromuscular skill and avoids full detraining. Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC10809978/

### 4.6 Duration

- **Standard deload:** 7 days (1 full training week)
- **Extended deload (severe fatigue/injury):** 10–14 days with 2–5 days of complete rest embedded at the start
- **Mini-deload:** A single deload session (reduce volume/intensity for one workout) — appropriate for localized fatigue on one lift
- Source: Bell et al. (NSCA), https://doras.dcu.ie/31501/1/a_practical_approach_to_deloading__recommendations.203(2).pdf

---

## 5. Post-Deload Progression

### 5.1 Return-to-Training Criteria

**Do not end a deload based on motivation alone.** Exit criteria should be objective:

| Exit Criterion | Signal |
|----------------|--------|
| HRV trending back toward personal baseline | Recovery metric normalized |
| Resting HR drift resolved | Autonomic recovery |
| Sleep debt stabilized | Acute recovery |
| First quality session completed without strain | Performance signal |
| e1RM on first session ≥ 95% of pre-deload baseline | Strength retention confirmed |

**Timeline:** Recovery signals typically normalize within 5–7 days of proper deloading. Source: https://support.trainwithmorpheus.com/support/solutions/articles/4000226140-how-to-use-hrv-trends-to-plan-deload-or-maintenance-weeks

### 5.2 Post-Deload Performance Expectations

**Commonly observed pattern after deload:**
- Week 1 post-deload: Strength may be slightly below pre-deload peak (especially if deload involved some load reduction). This is normal.
- Weeks 2–3: Performance typically returns to or exceeds pre-deload baseline
- Weeks 3–4+: Supercompensation effect — strength expression may exceed any previous level as fatigue fully dissipates

**Source:** Community experience confirmed by Israetel / Helms discussions; Ogasawara 2013 showing retraining rate equals early training rate. Source: https://rpstrength.com/blogs/articles/return-to-gym-guide

```
NOTE FOR MILO BACKEND: Do NOT flag performance as "decline" during the first
week post-deload. Suppress decline detection for 7 days post-deload end.
Post-deload performance baseline should be updated only after 2 full training weeks.
```

### 5.3 Should the System Restart the Mesocycle or Continue?

**Recommended approach: Restart mesocycle at early-meso RIR targets with adjusted baseline volume.**

**Rationale:**
1. The fatigue that triggered the deload indicates the previous mesocycle reached (or exceeded) the lifter's MRV. Resuming at the same intensity/volume that caused the deload would likely cause rapid re-accumulation of fatigue.
2. Starting a new mesocycle at MEV (minimum effective volume) with RIR 3–4 resets the progression arc optimally.
3. Ogasawara (2013) data shows that retraining after even 3-week detraining returns to equivalent hypertrophic rates as the initial training phase. A 1-week active deload does not require extensive "re-acclimatization."

**Exception:** If the deload was triggered by a single local issue (one lift, joint pain, etc.) and all other lifts were unaffected, the system may continue the mesocycle for unaffected muscle groups while restarting the affected movement at early-meso targets.

### 5.4 Post-Deload Volume and Intensity Baselines

**Rule: Start post-deload at 70–80% of peak pre-deload volume.**

```python
# Pseudocode: Post-Deload Volume Baseline

def calc_post_deload_baseline(
    pre_deload_peak_sets: dict,     # {exercise_id: int} — peak sets before deload
    deload_triggered_by: str,       # 'systemic', 'local', 'scheduled'
    e1rm_week1_post_deload: dict,   # {exercise_id: float} — first session post-deload
    e1rm_pre_deload_peak: dict      # {exercise_id: float} — peak e1RM before deload
) -> dict:
    """
    Returns recommended starting sets and load targets for new mesocycle.
    
    Volume restart rule:
    - Systemic fatigue deload: restart at 70% of pre-deload peak sets
    - Local fatigue deload: restart affected lifts at 70%, others at 85%
    - Scheduled deload: restart at 80% of pre-deload peak sets
    """
    restart_ratio = {
        'systemic': 0.70,
        'local': 0.80,      # Averaged; affected lifts lower
        'scheduled': 0.80
    }[deload_triggered_by]
    
    prescriptions = {}
    for exercise_id, peak_sets in pre_deload_peak_sets.items():
        restart_sets = max(2, round(peak_sets * restart_ratio))
        
        # Load: use first post-deload session e1RM to set new working load
        # Target RIR 3-4 (early meso) at post-deload strength level
        current_e1rm = e1rm_week1_post_deload.get(exercise_id, 
                        e1rm_pre_deload_peak.get(exercise_id, 0))
        
        prescriptions[exercise_id] = {
            'sets': restart_sets,
            'target_rir': (3, 4),       # Early meso prescription
            'load_basis': current_e1rm,  # Load from this e1RM, not pre-deload peak
            'mesocycle_week': 1,
            'progression_note': 'Reset. Progress from current performance baseline.'
        }
    
    return prescriptions
```

### 5.5 Ramp-Up Protocol After Deload

**10–14 Day Ramp-Back (moderate recovery needs):**

| Days Post-Deload | Volume Target | Intensity/RIR |
|------------------|---------------|---------------|
| 1–4 (Week 1) | 70–75% of pre-deload peak | RIR 3–4 (early meso) |
| 5–9 (Week 2) | 80–85% if markers stable | RIR 2–3 (mid meso entry) |
| 10–14 (Week 2–3) | Return to pre-deload levels if markers aligned | Follow new meso schedule |

**Source:** SensAI data-driven return-to-load framework; RP Strength return-to-gym guidelines. https://www.sensai.fit/blog/data-driven-deload-week-hrv-sleep-training-load | https://rpstrength.com/blogs/articles/return-to-gym-guide

---

## 6. Variable Index

All variables used in this document, formatted for backend implementation:

| Variable Name | Data Type | Description | Units/Range |
|---------------|-----------|-------------|-------------|
| `rir_reported` | `int` | RIR as reported by lifter post-set | 0–10 |
| `rir_adjusted` | `int` | RIR after beginner correction factor | 0–10 |
| `rpe_reported` | `float` | RPE equivalent (10 - RIR) | 1.0–10.0 |
| `rir_target_min` | `int` | Minimum RIR for current phase | 0–5 |
| `rir_target_max` | `int` | Maximum RIR for current phase | 0–6 |
| `rir_floor` | `int` | Absolute minimum RIR for exercise type | 0–3 |
| `load_kg` | `float` | Weight lifted in kg | >0 |
| `reps_completed` | `int` | Reps performed | 1–30 |
| `e1rm` | `float` | Estimated 1RM from set | kg |
| `e1rm_rir_adjusted` | `float` | e1RM with effort-level correction | kg |
| `session_e1rm` | `float` | Best e1RM for an exercise in one session | kg |
| `rolling_e1rm_7d` | `float` | 7-day rolling average session_e1rm | kg |
| `rolling_e1rm_28d` | `float` | 28-day rolling average session_e1rm | kg |
| `e1rm_pct_change` | `float` | % change in e1RM vs reference | -1.0 to +1.0 |
| `consecutive_decline_ct` | `int` | Consecutive sessions with e1RM decline | 0–N |
| `consecutive_stagnation_ct` | `int` | Consecutive sessions with zero progress | 0–N |
| `consecutive_rir_misses` | `int` | Consecutive sessions failing RIR target | 0–N |
| `consecutive_poor_motivation_ct` | `int` | Consecutive sessions with poor motivation | 0–N |
| `joint_pain_reported` | `bool` | User reported joint pain this session | true/false |
| `hrv_suppressed_days` | `int` | Days HRV below personal baseline | 0–N |
| `sleep_debt_days` | `int` | Consecutive days poor sleep | 0–N |
| `deload_trigger_status` | `enum` | Deload decision: none/monitor/recommended/immediate | — |
| `deload_active` | `bool` | Whether system is currently in deload week | true/false |
| `deload_start_date` | `date` | Date deload was initiated | ISO date |
| `deload_trigger_reason` | `string` | Primary reason deload was triggered | — |
| `fatigue_type` | `enum` | systemic / local / none | — |
| `recovery_needs` | `enum` | low / moderate / high | — |
| `mesocycle_week` | `int` | Current week within mesocycle (1-indexed) | 1–8 |
| `meso_length` | `int` | Planned mesocycle duration in weeks | 3–8 |
| `training_age_months` | `int` | Months of consistent resistance training | 0–N |
| `post_deload_flag` | `bool` | Flag: within 14 days of deload end | true/false |
| `post_deload_days` | `int` | Days since deload ended | 0–14 |
| `exercise_type` | `enum` | high_complexity_compound / low_complexity_compound / isolation | — |
| `volume_reduction_pct` | `float` | Deload volume reduction fraction | 0.25–0.90 |
| `deload_sets` | `int` | Prescribed sets during deload | 1–3 |
| `deload_load_kg` | `float` | Prescribed load during deload | kg |

---

## Threshold Summary Reference

| Threshold | Value | Trigger |
|-----------|-------|---------|
| Short-term e1RM decline | ≥5% below 7-day rolling avg | Fatigue flag |
| Long-term e1RM decline | ≥10% below 28-day rolling avg | Strong fatigue signal |
| Multi-lift consecutive decline | 2+ sessions, 2+ lifts | Systemic deload trigger |
| RIR below target | ≥2 RIR under target on ≥50% of sets | Fatigue flag |
| Consecutive RIR misses | 2 sessions | Deload trigger |
| Subjective fatigue | 3 consecutive sessions | Deload trigger |
| Performance stagnation | 5 consecutive sessions, no progress | Deload trigger |
| HRV suppression | 4+ days below personal baseline | Deload trigger (with clustering) |
| Sleep debt | 4+ consecutive nights poor sleep | Deload trigger (with clustering) |
| Signal cluster threshold | ≥2 amber/red domains simultaneously | Deload trigger |
| Deload volume reduction | 40–60% (moderate needs) | Standard deload |
| Deload RIR target | 4–5 | All deload sessions |
| Deload duration | 7 days | Standard |
| Post-deload decline suppression window | 7 days | No decline alerts |
| Post-deload volume restart | 70–80% of pre-deload peak | New mesocycle Week 1 |
| New mesocycle RIR target | 3–4 | Week 1–2 restart |

---

## Primary Sources

1. Zourdos et al. (2016). "Novel Resistance Training–Specific Rating of Perceived Exertion Scale Measuring Repetitions in Reserve." *JSCR* 30:267–275. https://pubmed.ncbi.nlm.nih.gov/26049792/

2. Helms et al. (2016). "Application of the Repetitions in Reserve-Based Rating of Perceived Exertion Scale." *Strength and Conditioning Journal*. https://pmc.ncbi.nlm.nih.gov/articles/PMC4961270/

3. Helms et al. (2018). "RPE vs. Percentage 1RM Loading in Periodized Programs." *Frontiers in Physiology*. https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2018.00247/full

4. Graham & Cleather (2019). "Autoregulation by RIR Leads to Greater Improvements in Strength." *JSCR* 35:2451–2456. https://pubmed.ncbi.nlm.nih.gov/31009432/

5. Ogasawara et al. (2013). "Comparison of Muscle Hypertrophy Following 6-Month of Continuous and Periodic Strength Training." *Eur J Appl Physiol* 113:975–985. https://pubmed.ncbi.nlm.nih.gov/23053130/

6. Pritchard et al. (2019). "Higher- Versus Lower-Intensity Strength-Training Taper." *PubMed*. https://pubmed.ncbi.nlm.nih.gov/30204523/

7. Bell et al. (2023). "Integrating Deloading into Strength and Physique Sports Training Programmes." *Sports Medicine - Open*. https://pmc.ncbi.nlm.nih.gov/articles/PMC10511399/

8. Bell et al. (2025). "A Practical Approach to Deloading." *Strength and Conditioning Journal (NSCA)*. https://doras.dcu.ie/31501/1/a_practical_approach_to_deloading__recommendations.203(2).pdf

9. Coleman et al. (2024). "Gaining More From Doing Less? Effects of a One-Week Deload." *PeerJ*. https://pmc.ncbi.nlm.nih.gov/articles/PMC10809978/

10. Lovegrove et al. (2022). "Repetitions in Reserve Is a Reliable Tool for Prescribing Resistance Training Load." *JSCR* 36(10):2696–2700.

11. Progressive Rehab & Strength. "Calculating and Tracking RPE & E1RM." https://www.progressiverehabandstrength.com/articles/calculating-and-tracking-rpe-e1rm-for-barbell-strength-training

12. Stronger by Science. "How to Perfect Your Ability to Predict Repetitions in Reserve." https://www.strongerbyscience.com/reps-in-reserve/

13. Israetel, M. & Helms, E. (2020). "Optimal Volume, Fatigue Accumulation and More" (Roundtable discussion). https://www.youtube.com/watch?v=DLZyMcH9y8s

14. Juggernaut Training Systems. "Fatigue Explained." https://www.jtsstrength.com/fatigue-explained/

15. SensAI. "Data-Driven Deload Weeks: HRV, Sleep Debt, and Training Load." https://www.sensai.fit/blog/data-driven-deload-week-hrv-sleep-training-load
