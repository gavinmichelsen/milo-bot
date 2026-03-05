# Track 4: Recovery Integration — HRV, RHR, Sleep, and Nocebo Avoidance
## Milo AI Fitness Coaching System — Backend Logic Specification

**Document Purpose:** Backend implementation reference for recovery monitoring, composite scoring, and nocebo-safe communication via Telegram.  
**Data Sources:** Whoop, Withings  
**Primary Metrics:** HRV (rMSSD/LnrMSSD), Resting Heart Rate (RHR), Sleep Duration, Sleep Quality Score, Strain Score, SpO2  
**Last Updated:** 2026-03-05  

---

## Table of Contents

1. [HRV as a Recovery Metric](#1-hrv-as-a-recovery-metric)
2. [Resting Heart Rate (RHR)](#2-resting-heart-rate-rhr)
3. [Sleep Metrics](#3-sleep-metrics)
4. [Nocebo Effect and Wearable Anxiety](#4-nocebo-effect-and-wearable-anxiety)
5. [Composite Recovery Score Model](#5-composite-recovery-score-model)
6. [Recovery-to-Action Mapping](#6-recovery-to-action-mapping)
7. [Telegram Communication Templates](#7-telegram-communication-templates)
8. [Variable Glossary](#8-variable-glossary)

---

## 1. HRV as a Recovery Metric

### 1.1 Evidence Base

**Kiviniemi et al. (2007)** ([PubMed](https://pubmed.ncbi.nlm.nih.gov/17849143/)) conducted the foundational prospective trial of HRV-guided training. Twenty-six healthy, moderately fit males were randomized to: (a) a predefined 6-day/week training program, or (b) HRV-guided training where session intensity was prescribed daily based on morning HRV measurements. Key result: the HRV-guided group showed significantly greater improvements in maximal running performance (Load_max: +0.9 ± 0.2 vs. +0.5 ± 0.4 km/h, p=0.048). The mechanism is that reducing training intensity on low-HRV days prevents short-term overreaching that would otherwise compromise test performance.

**Plews et al.** ([Scientific Triathlon interview](https://scientifictriathlon.com/tts42/)) extended this work to elite endurance athletes, articulating the core methodological principle: acute (single-day) HRV values are "too varied and cannot really mean much." Rolling averages — specifically 7-day or 10-day windows — provide the stability needed to extract actionable signals. Plews uses a threshold of **0.5 coefficient of variation (CV) over a two-week period** as the boundary for a "substantial change."

A 2021 systematic review and meta-analysis ([International Journal of Environmental Research and Public Health, PMC8507742](https://pmc.ncbi.nlm.nih.gov/articles/PMC8507742/)) pooled all HRV-guided training studies and confirmed: HRV-guided training showed a small but consistent effect size (SMD+ = 0.20, 95% CI = −0.09, 0.48) favoring it over predefined training for vagal modulation, with greater increases in RMSSD/SD1.

### 1.2 Why Single-Day HRV Is Unreliable

Day-to-day HRV variability is well-documented and substantial:

- Between-day CV for RMSSD: **17.88%** in younger adults, **CV for LnRMSSD: 4.42%** ([European Journal of Applied Physiology, PMC11055755](https://pmc.ncbi.nlm.nih.gov/articles/PMC11055755/))
- SDNN between-day CV: up to **18.96%**
- Normal day-to-day fluctuations of **10% one way or the other are not unusual** ([TrainingPeaks](https://www.trainingpeaks.com/coach-blog/explaining-hrv-numbers-age/))
- Contextual confounders: noise exposure, ambient temperature, body position, time of measurement, hydration, alcohol, mental stress — all shift single readings

**Critical design implication:** A single low-HRV reading carries high false-positive risk for indicating overtraining. Signaling users on single-day drops will produce anxiety without actionable information.

### 1.3 Recommended HRV Metric: LnrMSSD

```
Variable: hrv_raw       TYPE: float   UNIT: ms    SOURCE: Whoop/Withings
Variable: hrv_ln        TYPE: float   UNIT: ln(ms) FORMULA: ln(hrv_raw)
```

**Why LnrMSSD?**
- rMSSD is the preferred HRV time-domain metric for vagal modulation monitoring (parasympathetic recovery)
- Log-transformation normalizes the distribution, enabling parametric statistics and stable rolling averages
- Used in all Plews, Kiviniemi, and Javaloyes et al. methodologies
- Whoop measures HRV during slow-wave sleep using rMSSD via photoplethysmography (PPG) ([Whoop accuracy documentation](https://www.whoop.com/us/en/thelocker/how-well-whoop-measures-sleep/))

### 1.4 Rolling Average Windows

#### 7-Day Rolling Average (Primary Signal)

```
Variable: hrv_7d_avg    TYPE: float   UNIT: ln(ms)
Variable: hrv_window    TYPE: integer VALUE: 7
```

**Formula:**
```
hrv_7d_avg[t] = (1/7) × Σ hrv_ln[t-i] for i in {0, 1, 2, 3, 4, 5, 6}
```

**Requirements:**
- Minimum 4 of 7 days must have valid readings to compute; otherwise return NULL
- Applied to LnrMSSD, NOT raw rMSSD (to prevent skewed averages from single outliers)

**Evidence:** This window was operationalized in the [International Journal of Environmental Research and Public Health HRV-guided training protocol (PMC7432021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7432021/) following Plews, Laursen, Kilding, and Buchheit's recommendations. Elite HRV ([help.elitehrv.com](https://help.elitehrv.com/article/355-what-is-the-hrv-7-day-rolling-average-and-coefficient-of-variation)) confirms: "The 7 Day Rolling HRV can be helpful to more easily see weekly HRV trends, especially when there is a lot of daily fluctuation."

#### 30-Day Baseline (Personal Norm)

```
Variable: hrv_30d_mean  TYPE: float   UNIT: ln(ms)
Variable: hrv_30d_sd    TYPE: float   UNIT: ln(ms)
Variable: baseline_window TYPE: integer VALUE: 30
```

**Formula:**
```
hrv_30d_mean[t] = (1/30) × Σ hrv_ln[t-i] for i in {0..29}
hrv_30d_sd[t]   = sqrt( (1/29) × Σ (hrv_ln[t-i] - hrv_30d_mean[t])² for i in {0..29} )
```

**Bootstrapping Rule:** During onboarding (days 1–30), use all available days. Do not generate readiness recommendations until ≥ 14 days of data exist.

### 1.5 Coefficient of Variation (CV) as Stability Indicator

```
Variable: hrv_7d_cv     TYPE: float   UNIT: percentage (%)
```

**Formula:**
```
hrv_7d_cv[t] = (hrv_7d_sd / hrv_7d_mean) × 100
```

where `hrv_7d_sd` is the standard deviation of the 7 LnrMSSD values in the rolling window.

**Interpretation thresholds** ([Elite HRV](https://help.elitehrv.com/article/355-what-is-the-hrv-7-day-rolling-average-and-coefficient-of-variation)):
| CV Range | Interpretation |
|----------|----------------|
| < 5%     | Very stable; well-adapted to current training load |
| 5–10%    | Normal physiological variation; expected during moderate training |
| > 10%    | Elevated instability; increased training stress or other stressors |
| > 15%    | High instability; should increase weight on other recovery signals |

**Note:** Normal day-to-day variation in HRV is typically **5–10% CV**. A CV above 10% in the 7-day window suggests the system is less stable and individual readings are less reliable — reduce confidence in any single HRV-based trigger.

### 1.6 Meaningful Deviation Threshold

**Plews methodology** (confirmed in [PMC7432021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7432021/)): Normal range = `hrv_30d_mean ± 0.5 × hrv_30d_sd`

```
Variable: hrv_normal_upper  = hrv_30d_mean + (0.5 × hrv_30d_sd)
Variable: hrv_normal_lower  = hrv_30d_mean - (0.5 × hrv_30d_sd)
Variable: hrv_below_normal  TYPE: boolean  = (hrv_7d_avg < hrv_normal_lower)
```

**Z-score approach** (for continuous scoring):
```
Variable: hrv_z_score   TYPE: float
hrv_z_score[t] = (hrv_7d_avg[t] - hrv_30d_mean[t]) / hrv_30d_sd[t]
```

| Z-Score Range | Status |
|---------------|--------|
| > +1.0        | Elevated (parasympathetic dominant — green, ready to push) |
| −0.5 to +1.0  | Normal range |
| −1.0 to −0.5  | Mild suppression (watch) |
| −1.5 to −1.0  | Moderate suppression (yellow) |
| < −1.5        | Significant suppression (red) |

**Alternative 1-SD threshold** (HRV4Training app): Substantial change = ±1 SD from rolling mean. Plews' HRV4Coach app uses a more sensitive ±0.5 SD. For Milo, **use ±0.5 SD** as the activation boundary (more conservative = fewer false negatives for coaches).

### 1.7 Decision Logic: When to Flag

**CRITICAL CONSTRAINT: Never flag on a single day. Require sustained trend.**

```python
def compute_hrv_status(hrv_7d_avg_history: list[float], 
                        hrv_30d_mean: float, 
                        hrv_30d_sd: float,
                        min_consecutive_days: int = 3) -> str:
    """
    Returns: 'green', 'yellow', 'red', or 'insufficient_data'
    
    hrv_7d_avg_history: ordered list of hrv_7d_avg values, most recent last
    Requires at least min_consecutive_days entries to evaluate trend
    """
    if len(hrv_7d_avg_history) < min_consecutive_days:
        return 'insufficient_data'
    
    lower_bound = hrv_30d_mean - (0.5 * hrv_30d_sd)
    red_bound   = hrv_30d_mean - (1.5 * hrv_30d_sd)
    
    # Check most recent N days
    recent = hrv_7d_avg_history[-min_consecutive_days:]
    
    days_below_lower = sum(1 for v in recent if v < lower_bound)
    days_below_red   = sum(1 for v in recent if v < red_bound)
    
    if days_below_red >= min_consecutive_days:
        return 'red'
    elif days_below_lower >= min_consecutive_days:
        return 'yellow'
    else:
        return 'green'
```

**Minimum consecutive days before escalation:**
- Yellow trigger: 3 consecutive days of hrv_7d_avg < (hrv_30d_mean − 0.5 SD)
- Red trigger: 3 consecutive days of hrv_7d_avg < (hrv_30d_mean − 1.5 SD)

This prevents single-day noise events from triggering alerts while catching real sustained suppression within a week.

---

## 2. Resting Heart Rate (RHR)

### 2.1 Evidence Base

RHR elevation is an established early marker of overreaching and overtraining. Key evidence:

- **A study on recreational runners** ([Runners Connect](https://runnersconnect.net/overtraining-in-runners/)) found that when runners entered overreaching, average nighttime heart rate rose approximately **3%**, with statistical significance separating overreached from adapted runners within **9–10 days** of increased training load.
- **TrainingPeaks** clinical guidance ([The 4 Signs of Overtraining](https://www.trainingpeaks.com/coach-blog/the-4-signs-of-overtraining/)): "An RHR 5 bpm above their average indicates they need more recovery time." If elevated for multiple weeks, suspect overtraining or illness.
- **Runners Connect** ([Overtraining Symptoms in Runners](https://runnersconnect.net/overtraining-in-runners/)): "A sustained increase of 3–5 beats per minute above your baseline for several days is one of the most reliable objective markers of accumulating fatigue."
- Combined model ([Running Explained](https://www.runningexplained.com/post/overtraining-in-runners-signs-metrics-prevention)): Combining night heart rate + readiness to train + HR/effort index correctly identified overreaching with **>90% accuracy**.

### 2.2 Variables

```
Variable: rhr_daily         TYPE: float   UNIT: bpm   SOURCE: Whoop/Withings
Variable: rhr_14d_mean      TYPE: float   UNIT: bpm
Variable: rhr_30d_mean      TYPE: float   UNIT: bpm
Variable: rhr_30d_sd        TYPE: float   UNIT: bpm
Variable: rhr_z_score       TYPE: float
Variable: rhr_delta_bpm     TYPE: float   UNIT: bpm   (current − baseline)
```

### 2.3 Baseline Establishment

Use a **30-day rolling average** as the personal baseline (consistent with HRV approach):

```
rhr_30d_mean[t] = (1/N) × Σ rhr_daily[t-i]  for i in {0..N-1}
                  where N = min(available_days, 30)

rhr_30d_sd[t]   = sqrt( (1/(N-1)) × Σ (rhr_daily[t-i] - rhr_30d_mean[t])² )
```

A 14-day baseline is acceptable as a minimum during onboarding.

### 2.4 Meaningful Elevation Thresholds

```
rhr_delta_bpm   = rhr_7d_avg - rhr_30d_mean
rhr_z_score     = (rhr_7d_avg - rhr_30d_mean) / rhr_30d_sd
```

| Elevation | Interpretation |
|-----------|----------------|
| < +3 bpm  | Normal fluctuation — no action |
| +3–5 bpm  | Mild elevation — watch; combine with HRV and sleep |
| > +5 bpm  | Significant elevation — recovery concern (yellow/red) |
| > +8 bpm  | Severe elevation — likely illness or acute overreaching (red) |

**Note:** A **single-day** spike of 5–8 bpm after an unusually hard workout is expected and is NOT a flag. Flagging requires sustained elevation (see Section 2.5).

### 2.5 Decision Logic

```python
def compute_rhr_status(rhr_7d_avg_history: list[float],
                        rhr_30d_mean: float,
                        rhr_30d_sd: float,
                        min_consecutive_days: int = 3) -> str:
    """
    Returns: 'green', 'yellow', 'red', 'insufficient_data'
    """
    if len(rhr_7d_avg_history) < min_consecutive_days:
        return 'insufficient_data'
    
    recent = rhr_7d_avg_history[-min_consecutive_days:]
    
    mild_upper = rhr_30d_mean + 3.0   # bpm
    mod_upper  = rhr_30d_mean + 5.0   # bpm
    sev_upper  = rhr_30d_mean + 8.0   # bpm
    
    days_mild     = sum(1 for v in recent if v > mild_upper)
    days_moderate = sum(1 for v in recent if v > mod_upper)
    days_severe   = sum(1 for v in recent if v > sev_upper)
    
    if days_severe >= 2:
        return 'red'
    elif days_moderate >= min_consecutive_days:
        return 'red'
    elif days_mild >= min_consecutive_days:
        return 'yellow'
    else:
        return 'green'
```

### 2.6 RHR × HRV Interaction

The combination of both metrics provides a more reliable signal than either alone:

```python
def combined_hrv_rhr_status(hrv_status: str, rhr_status: str) -> str:
    """
    Combined status: takes the worse of the two signals,
    but requires BOTH to be non-green to elevate to red.
    """
    status_rank = {'green': 0, 'yellow': 1, 'red': 2, 'insufficient_data': -1}
    
    if hrv_status == 'insufficient_data' and rhr_status == 'insufficient_data':
        return 'insufficient_data'
    
    # If only one metric available, use it but downgrade severity
    valid_statuses = [s for s in [hrv_status, rhr_status] 
                      if s != 'insufficient_data']
    
    if len(valid_statuses) == 1:
        # Single metric: cap at yellow (less confident without corroboration)
        return 'yellow' if valid_statuses[0] == 'red' else valid_statuses[0]
    
    ranks = [status_rank[s] for s in valid_statuses]
    
    if max(ranks) == 2 and min(ranks) >= 1:
        # Both yellow or red → escalate to red
        return 'red'
    elif max(ranks) == 2 and min(ranks) == 0:
        # One red, one green → yellow (conflicting signals)
        return 'yellow'
    else:
        return valid_statuses[status_rank.index(max(ranks))]
```

**Physiological rationale:** HRV drops and RHR rises when the autonomic nervous system is sympathetically dominant (under-recovered). When both metrics move in the same direction simultaneously over multiple days, the signal reliability approaches >90% ([Running Explained](https://www.runningexplained.com/post/overtraining-in-runners-signs-metrics-prevention)).

---

## 3. Sleep Metrics

### 3.1 Evidence Base

**Sleep and training recovery:**
- Sleep restriction to ~5 hours/night impairs endurance performance by ~3%, and the impairment compounds with each additional night of restriction ([HiitScience / Roberts et al.](https://hiitscience.com/sleep-endurance-performance/))
- Sleep extension to >8 hours improves time-trial performance by ~3% ([Roberts et al.](https://hiitscience.com/sleep-endurance-performance/))
- Partial sleep restriction (4 hours) negatively affects muscle power, strength, and endurance in elite athletes ([Sports Medicine Open, PMC10354314](https://pmc.ncbi.nlm.nih.gov/articles/PMC10354314/))
- Sleep deprivation reduces protein synthesis and impairs muscle damage repair ([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0024320519307623))
- The American Academy of Sleep Medicine recommends **≥7 hours** for adults; active individuals should target **7–9 hours**, with highly trained athletes benefiting from **8–10 hours** ([Marathon Handbook](https://marathonhandbook.com/sleep-to-recover-after-training/))
- Elite athletes self-report needing ~**8.3 hours** to feel rested, but on average sleep only 6.8 ± 1.1 hours ([Sports Medicine Open](https://pmc.ncbi.nlm.nih.gov/articles/PMC10354314/))
- Resistance training group in a UCLA study gained **40 minutes of additional sleep** per night compared to other exercise modalities ([UCLA Health](https://www.uclahealth.org/news/article/new-study-suggests-resistance-training-helps-sleep))

### 3.2 Variables

```
Variable: sleep_duration_hrs    TYPE: float   UNIT: hours   SOURCE: Whoop
Variable: sleep_efficiency_pct  TYPE: float   UNIT: %       SOURCE: Whoop (time asleep / time in bed × 100)
Variable: sleep_perf_score      TYPE: float   UNIT: 0–100   SOURCE: Whoop Sleep Performance Score
Variable: sleep_consistency     TYPE: float   UNIT: 0–1     SOURCE: Whoop (timing vs. prior 4 nights)
Variable: sleep_hrv_rmssd       TYPE: float   UNIT: ms      SOURCE: Whoop (measured during SWS)
Variable: spo2_avg              TYPE: float   UNIT: %       SOURCE: Whoop/Withings
```

### 3.3 Whoop Sleep Performance Score — Components

Per [Whoop's published methodology](https://www.whoop.com/us/en/thelocker/how-well-whoop-measures-sleep/), Sleep Performance comprises:
1. **Sleep Sufficiency** (hours obtained vs. hours needed)
2. **Sleep Consistency** (timing vs. prior 4 nights)
3. **Sleep Efficiency** (% time in bed actually asleep)
4. **Sleep Stress** (time in high-stress state overnight)

The Whoop Recovery Score weightings reported by third-party analysis ([Plait.fit](https://www.plait.fit/blog/recovery-score-drops-after-good-sleep.html)):
- HRV: ~40% of recovery score
- RHR: ~30% of recovery score
- Sleep Performance: ~20% of recovery score
- Respiratory Rate: ~10% of recovery score

**Note for Milo:** Milo will NOT use Whoop's raw recovery score as a passthrough to users — it carries nocebo risk (see Section 4). Instead, use raw input metrics.

### 3.4 Sleep Duration Thresholds

```
Variable: sleep_minimum_hrs     TYPE: float   VALUE: 6.0   # Below this = deficit
Variable: sleep_optimal_hrs     TYPE: float   VALUE: 8.0   # Optimal for athletes
Variable: sleep_target_hrs      TYPE: float   VALUE: 7.5   # Reasonable nightly target
```

| Duration | Status |
|----------|--------|
| ≥ 8.0 h  | Optimal (green) |
| 7.0–7.9 h | Adequate (green-yellow) |
| 6.0–6.9 h | Suboptimal (yellow) |
| < 6.0 h  | Deficit (yellow → red based on trend) |
| < 5.0 h  | Acute deficit (red — same-day modifier) |

### 3.5 Rolling Average Approach

```
Variable: sleep_7d_avg_hrs      TYPE: float   UNIT: hours
Variable: sleep_7d_avg_eff      TYPE: float   UNIT: %
Variable: sleep_7d_avg_score    TYPE: float   UNIT: 0–100

sleep_7d_avg_hrs[t] = (1/N) × Σ sleep_duration_hrs[t-i]   for i in {0..6}, N = valid readings
sleep_7d_avg_eff[t] = (1/N) × Σ sleep_efficiency_pct[t-i] for i in {0..6}
```

### 3.6 Sleep Status Decision Logic

```python
def compute_sleep_status(sleep_7d_avg_hrs: float,
                          sleep_7d_avg_eff: float,
                          sleep_duration_history: list[float],
                          min_consecutive_days: int = 3) -> str:
    """
    Returns: 'green', 'yellow', 'red', 'insufficient_data'
    
    sleep_duration_history: daily values, most recent last
    """
    if sleep_7d_avg_hrs is None:
        return 'insufficient_data'
    
    # Rolling average bands
    if sleep_7d_avg_hrs >= 7.0 and sleep_7d_avg_eff >= 80:
        avg_status = 'green'
    elif sleep_7d_avg_hrs >= 6.0 and sleep_7d_avg_eff >= 70:
        avg_status = 'yellow'
    else:
        avg_status = 'red'
    
    # Acute signal: check last N consecutive nights < 6h
    if len(sleep_duration_history) >= min_consecutive_days:
        recent = sleep_duration_history[-min_consecutive_days:]
        acute_deficit_days = sum(1 for d in recent if d < 6.0)
        if acute_deficit_days >= min_consecutive_days:
            # Override to red regardless of weekly average
            return 'red'
    
    return avg_status


def apply_sleep_modifier(composite_score: float, 
                          sleep_status: str,
                          sleep_7d_avg_hrs: float) -> float:
    """
    Applies sleep debt penalty to composite score.
    Returns modified composite score (0–100 scale).
    """
    if sleep_status == 'red':
        penalty = 15.0
    elif sleep_status == 'yellow':
        penalty = 7.5
    else:
        penalty = 0.0
    
    # Additional penalty for severe chronic sleep restriction
    if sleep_7d_avg_hrs < 5.5:
        penalty += 10.0
    
    return max(0.0, composite_score - penalty)
```

### 3.7 When Sleep Should Influence Training Recommendations

```
SLEEP MODIFIER RULES:
─────────────────────────────────────────────────────
Condition                        → Training Influence
─────────────────────────────────────────────────────
Single night < 6h                → No change (single-day noise)
2 consecutive nights < 6h        → Suggest avoiding max-effort sessions
3+ consecutive nights < 6h       → Recommend reduced intensity (-20% load)
7-day avg < 6h                   → Deload recommendation regardless of HRV/RHR
7-day avg < 5.5h                 → Rest/recovery-only recommendation
Sleep efficiency < 70% (3 days)  → Flag for investigation, not training change
─────────────────────────────────────────────────────
```

---

## 4. Nocebo Effect and Wearable Anxiety

### 4.1 Core Research

**The Gavriloff 2018 Study** ([Journal of Sleep Research](https://drjameshewitt.com/can-sleep-tracking-be-bad-for-your-performance/)):
- Participants with clinically significant insomnia were given wearables programmed to deliver **false** sleep efficiency feedback
- Negative feedback group (told they slept "very poorly" at 61.4% efficiency):
  - **Decreased alertness** and **increased sleepiness**
  - **Greater subjective fatigue**
  - Impaired cognitive performance — caused by feedback, not actual sleep
- Positive feedback group (told they slept "very well" at 91.4% efficiency):
  - Increased positive mood and alertness
  - Reduced sleepiness and fatigue
- **Implication:** What users are *told* about their recovery influences their actual performance, independent of true physiological state.

**Orthosomnia** — coined by scientists at Rush Medical College and Feinberg School of Medicine ([GoodTherapy](https://www.goodtherapy.org/blog/health-tracking-anxiety-wearable-obsession), [ABC News](https://www.goodmorningamerica.com/wellness/story/orthosomnia-obsession-wearable-tech-impact-sleep-123990784)):
- Defined as obsessive pursuit of optimal sleep driven by tracker data
- Sleep specialists began identifying this pattern in 2017
- The harder patients try to control sleep after seeing bad scores, the worse it gets
- Dr. Rebecca Robbins (Harvard/Brigham and Women's Hospital): "The information they receive stresses them out, and then it causes them to struggle the next night"

**Wearable-induced health anxiety** ([University of Copenhagen / Futurity](https://www.futurity.org/fitness-trackers-watches-anxiety-2416592/)):
- Study of 27 heart patients using Fitbit for 6 months (66 qualitative interviews)
- Patients began treating Fitbit data "just as they would use a doctor" without clinical context
- When metrics failed expectations → unnecessary anxiety, fear, guilt
- Author Tariq Osman Andersen: "They don't get help interpreting their watch data. This makes them unnecessarily anxious, or they may learn something that is far from reality."

**UNC School of Medicine (2024)** ([UNC Medicine](https://www.med.unc.edu/medicine/news/wearable-devices-can-increase-health-anxiety-could-they-adversely-affect-health/)):
- 172 Afib patients: wearable users showed significantly higher rates of anxiety about symptoms
- **1 in 5** wearable-using Afib patients experienced intense fear in response to irregular rhythm notifications
- Wearable users more likely to contact doctors on normal measurement variation

**Smartwatch anxiety cycle** ([Dodgson Psychology](https://www.dodgsonpsychology.ca/smartwatch-anxiety-orthosomnia/)):
- "When you see a negative metric, your brain interprets this as a threat"
- Anxiety about data causes cortisol release → lowers HRV → watch 'confirms' stress
- The anxiety about the data **proves the watch right** — self-fulfilling nocebo loop

### 4.2 The Case Against Raw Daily Score Sharing

| Practice | Problem |
|----------|---------|
| Show raw recovery score every morning | Triggers nocebo loop on normal low days |
| Alert user to every HRV dip | Creates anxiety from expected post-workout variation |
| Frame output as "your recovery is 45%" | User interprets as personal failure or illness |
| Show sleep stage detail nightly | Orthosomnia risk; staging accuracy ~60–75% ([GoodTherapy](https://www.goodtherapy.org/blog/health-tracking-anxiety-wearable-obsession)) |

**Milo must NOT expose:**
- Raw Whoop recovery score (0–100)
- Raw HRV ms values
- Sleep stage breakdowns (SWS/REM percentages)
- Single-day Z-scores
- "Your HRV dropped 12% today" language

### 4.3 Design Principles for Nocebo-Safe Communication

1. **Trend-based, never single-day** — only surface recovery signals when a 3+ day trend is established
2. **Action-forward framing** — always tell the user what to *do*, not what is *wrong*
3. **Positive default** — most days, users receive an affirmative "ready to train" message
4. **Suppress suppression language** — replace "low recovery" with "your body is working on adapting"
5. **No alarming colors or emoji** — avoid red warning language unless truly warranted
6. **Contextual attribution** — when flagging, offer benign explanations ("high training load this week," "travel/time zone adjustment")
7. **Silent by default** — only send a Telegram message if there is an actionable recommendation; do not message on normal-green days unless user requests daily check-in

---

## 5. Composite Recovery Score Model

### 5.1 Weighting Evidence

Based on Whoop's internal algorithm (HRV ~40%, RHR ~30%, Sleep ~20%, Respiratory rate ~10%) and academic composite readiness models (Alan Couzens neural network approach, [alancouzens.com](https://alancouzens.com/TP/athletes.cgi/blog/readiness)), the following weights are supported:

```
Variable: w_hrv    TYPE: float   VALUE: 0.40   # HRV (LnrMSSD 7-day Z-score)
Variable: w_rhr    TYPE: float   VALUE: 0.30   # RHR (7-day Z-score, inverted)
Variable: w_sleep  TYPE: float   VALUE: 0.30   # Sleep score (combines duration + efficiency)
```

*Note: SpO2 is excluded from the primary composite unless SpO2_avg < 94% for 3+ days, which triggers a medical referral flag separate from training recommendations.*

### 5.2 Score Calculation

**Step 1: Z-score each metric**

```
hrv_z    = (hrv_7d_avg   - hrv_30d_mean)   / hrv_30d_sd       # positive = better
rhr_z    = -1 × (rhr_7d_avg  - rhr_30d_mean)   / rhr_30d_sd   # inverted: elevated RHR = negative z
sleep_z  = (sleep_7d_avg_score - sleep_score_30d_mean) / sleep_score_30d_sd
```

**Step 2: Compute raw composite**

```
composite_z = (w_hrv × hrv_z) + (w_rhr × rhr_z) + (w_sleep × sleep_z)
```

**Step 3: Convert to 0–100 scale**

Z-scores are bounded to [−3, +3] and linearly mapped to [0, 100]:

```
composite_z_clamped  = max(-3.0, min(3.0, composite_z))
composite_score_raw  = 50 + (composite_z_clamped / 3.0) × 50
composite_score      = max(0.0, min(100.0, composite_score_raw))
```

**Step 4: Apply sleep debt modifier** (from Section 3.6)

```
composite_score_final = apply_sleep_modifier(composite_score, sleep_status, sleep_7d_avg_hrs)
```

### 5.3 Handling Missing Data

```python
def compute_composite(hrv_z: float | None, 
                       rhr_z: float | None,
                       sleep_z: float | None,
                       w_hrv: float = 0.40,
                       w_rhr: float = 0.30,
                       w_sleep: float = 0.30) -> float | None:
    """
    Returns composite score 0–100 or None if insufficient data.
    Reweights dynamically if metrics are missing.
    """
    available = {k: v for k, v in 
                 {'hrv': (hrv_z, w_hrv), 
                  'rhr': (rhr_z, w_rhr), 
                  'sleep': (sleep_z, w_sleep)}.items() 
                 if v[0] is not None}
    
    if len(available) == 0:
        return None
    
    # Reweight to sum to 1.0
    total_weight = sum(w for _, w in available.values())
    
    composite_z = sum((z * w / total_weight) 
                      for z, w in available.values())
    
    composite_z_clamped = max(-3.0, min(3.0, composite_z))
    return 50.0 + (composite_z_clamped / 3.0) * 50.0
```

### 5.4 Tier System: Green / Yellow / Red

```
Variable: composite_score_final  TYPE: float   UNIT: 0–100
```

| Tier   | Score Range | Conditions |
|--------|-------------|------------|
| GREEN  | 55–100      | composite_score_final ≥ 55 AND no individual metric in red |
| YELLOW | 35–54       | composite_score_final 35–54 OR one metric in yellow for 3+ days |
| RED    | 0–34        | composite_score_final < 35 OR two+ metrics in yellow/red simultaneously for 3+ days |

**Additional escalation rule:** A single metric hitting red-level threshold for 5+ consecutive days escalates to system-level RED regardless of composite score.

```python
def classify_tier(composite_score: float | None,
                   hrv_status: str,
                   rhr_status: str,
                   sleep_status: str) -> str:
    """
    Returns: 'green', 'yellow', 'red', 'insufficient_data'
    """
    if composite_score is None:
        return 'insufficient_data'
    
    # Count individual metric warnings
    statuses = [hrv_status, rhr_status, sleep_status]
    red_count    = sum(1 for s in statuses if s == 'red')
    yellow_count = sum(1 for s in statuses if s == 'yellow')
    
    # Score-based primary classification
    if composite_score >= 55 and red_count == 0 and yellow_count < 2:
        score_tier = 'green'
    elif composite_score >= 35 and red_count < 2:
        score_tier = 'yellow'
    else:
        score_tier = 'red'
    
    # Multi-metric escalation rule
    if red_count >= 2 or (red_count >= 1 and yellow_count >= 1):
        return 'red'
    
    return score_tier
```

### 5.5 Continuous vs. Categorical Output

**Recommendation: Use categorical tiers for user communication, continuous score for internal logging.**

Rationale:
- Continuous scores (e.g., "your recovery is 67/100") invite daily obsession and comparison
- Categorical tiers are actionable: "go hard," "go moderate," "go easy"
- Research supports that what users are told about their scores shapes how they feel and perform (Gavriloff 2018)
- Internally, store the continuous composite_score_final for trend analysis and model improvement

---

## 6. Recovery-to-Action Mapping

### 6.1 Tier Definitions and Thresholds

#### TIER GREEN — "Ready to Train as Programmed"

```
Conditions (ALL must be true):
  composite_score_final ≥ 55
  hrv_status  = 'green'  OR  hrv_z_score > -0.5
  rhr_status  = 'green'  OR  rhr_delta_bpm < 3
  sleep_7d_avg_hrs ≥ 7.0
  sleep_status = 'green'
  No individual metric declining for 3+ days
  No concurrent SpO2 < 94%
```

**Training directive:** Execute session as programmed. No modifications needed.

#### TIER YELLOW — "Consider Reducing Intensity"

```
Conditions (ANY of the following):
  35 ≤ composite_score_final < 55
  hrv_7d_avg below normal range (< hrv_30d_mean - 0.5×SD) for 3+ days
  rhr_7d_avg elevated 3–5 bpm above baseline for 3+ days
  sleep_7d_avg_hrs between 6.0–6.9h
  sleep_7d_avg_eff between 70–79%
  hrv_status = 'yellow' AND (rhr_status = 'yellow' OR sleep_status = 'yellow')
  
  MUST persist for: ≥ 3 consecutive days before triggering Telegram message
```

**Training directive:** Reduce training intensity by 20–30%. Maintain movement/skill work. Avoid new personal records or maximum effort sets. Prioritize sleep hygiene tonight.

#### TIER RED — "Recommend Deload or Rest"

```
Conditions (ANY of the following):
  composite_score_final < 35
  hrv_7d_avg below (hrv_30d_mean - 1.5×SD) for 3+ days
  rhr_7d_avg elevated > 5 bpm above baseline for 3+ days
  sleep_7d_avg_hrs < 6.0h for 5+ days
  Two or more individual metrics in 'yellow' or 'red' simultaneously for 3+ days
  Any single metric in 'red' for 5+ consecutive days
  
  MUST persist for: ≥ 3 consecutive days (or 2 days if metrics are severely depressed)
```

**Training directive:** Full deload or rest. Active recovery only (light walk, stretching). If RED persists > 7 days without identifiable cause (race prep, travel, known illness), flag for coach/professional review.

### 6.2 Escalation Timer Logic

```python
def compute_tier_with_persistence(
    tier_history: list[str],   # daily tier classifications, most recent last
    current_composite: float,
    current_individual_statuses: dict,
    min_days_yellow: int = 3,
    min_days_red: int = 3
) -> tuple[str, bool]:
    """
    Returns: (communicated_tier, should_send_telegram_message)
    
    Only escalates tier AND sends message if trend persists for minimum days.
    Default output is 'green' with no message unless threshold met.
    """
    if len(tier_history) < min_days_yellow:
        return ('green', False)  # Insufficient history, default quiet
    
    recent = tier_history[-min_days_red:]
    
    yellow_streak = sum(1 for t in recent if t in ('yellow', 'red'))
    red_streak    = sum(1 for t in recent if t == 'red')
    
    if red_streak >= min_days_red:
        return ('red', True)
    elif yellow_streak >= min_days_yellow:
        return ('yellow', True)
    else:
        return ('green', False)  # Green is silent by default
```

**Key principle:** GREEN days send no recovery message unless the user has opted in to daily check-ins. This prevents habituating users to daily data anxiety.

### 6.3 Specific Numeric Thresholds Summary Table

| Metric | Green | Yellow | Red | Min Days to Trigger |
|--------|-------|--------|-----|---------------------|
| HRV 7d avg vs baseline | Within ±0.5 SD | −0.5 to −1.5 SD | < −1.5 SD | 3 days |
| RHR 7d avg vs baseline | < +3 bpm | +3 to +5 bpm | > +5 bpm | 3 days |
| Sleep duration (7d avg) | ≥ 7.0 h | 6.0–6.9 h | < 6.0 h | 3 days for yellow, 5 for red |
| Sleep efficiency (7d avg) | ≥ 80% | 70–79% | < 70% | 3 days |
| Composite score | ≥ 55 | 35–54 | < 35 | 3 days |
| SpO2 avg | ≥ 95% | 92–94% | < 92% | 2 days → refer |

---

## 7. Telegram Communication Templates

### 7.1 Core Principles for Message Design

1. **Never mention raw scores** ("your HRV is 42ms" or "recovery score: 38/100")
2. **Always lead with the action**, not the data
3. **Frame decline as body adapting**, not failing
4. **Positive framing for green** — affirm, don't diagnose
5. **Offer choice in yellow** — suggest, never mandate
6. **Use warmth in red** — empathy, not alarm

### 7.2 Message Templates by Tier

#### GREEN — No message (silent default)

*Optional daily check-in message (user opt-in only):*
```
"Looking good for today's session — your body's been adapting well this week. 
Your workout is programmed and ready. Go get it. 💪"
```

#### GREEN — Pre-workout reminder (user requests coaching)
```
"Based on your recent trend, today's a solid day to hit your programmed session. 
Your body has been recovering well — [insert today's workout]. 
Let me know how it goes!"
```

#### YELLOW — First trigger (Day 3 of sustained decline)
```
"Your body's working through a heavier adaptation period this week — 
that's a normal part of building fitness. 

Today I'd suggest keeping the session a bit lighter: 
[modified session description — 20-30% intensity reduction].

Nothing to worry about — just let your system catch up. 
A bit more sleep tonight would also go a long way. 🙌"
```

#### YELLOW — Subsequent days (Day 4–6)
```
"Still in an adaptation phase — your body's doing what it should after 
a demanding training block. 

Keep this week's effort dialed back a bit. 
[session recommendation]. 

Prioritize sleep and nutrition, and you'll come out of this stronger."
```

#### RED — First trigger
```
"Your body's been sending consistent signals that it needs a recovery focus 
right now — this happens to every athlete, especially after periods of hard work.

Today's recommendation: skip the structured session and do something 
restorative instead — a 20-30 min walk, light stretching, or just rest.

This isn't a setback. Recovery IS training. 
How are you feeling overall this week?"
```

#### RED — Sustained (Day 5+)
```
"We're now several days into a recovery phase. If you haven't already, 
this is a good time to check in on sleep, stress levels, and nutrition 
to help your body get back on track.

A full deload week (lighter movement only) is the right call. 
I'll check back in as we track how things progress. 

If this pattern continues much longer, it might be worth a conversation 
with your coach or doctor — just to rule out illness or other factors."
```

#### SpO2 Flag (< 92% for 2 days)
```
"Just flagging something worth attention: 
your overnight oxygen levels have been a bit low over the last two nights.

This doesn't necessarily mean anything serious, but it's worth monitoring — 
and if you're feeling unusually fatigued or short of breath, 
a check-in with your doctor would be a good idea.

Training today: keep it light, easy effort only."
```

### 7.3 Anti-Patterns (Do Not Use)

```
❌ "Your recovery score is red today."
❌ "WARNING: HRV is significantly below baseline."
❌ "You are under-recovered."
❌ "Your sleep was poor last night."
❌ "You should not train today."
❌ "Your body battery is critically low."
```

---

## 8. Variable Glossary

| Variable | Type | Unit | Source | Description |
|----------|------|------|--------|-------------|
| `hrv_raw` | float | ms | Whoop | Raw rMSSD reading |
| `hrv_ln` | float | ln(ms) | Derived | Natural log of hrv_raw |
| `hrv_7d_avg` | float | ln(ms) | Derived | 7-day rolling mean of hrv_ln |
| `hrv_7d_sd` | float | ln(ms) | Derived | 7-day rolling SD of hrv_ln |
| `hrv_7d_cv` | float | % | Derived | 7-day coefficient of variation |
| `hrv_30d_mean` | float | ln(ms) | Derived | 30-day rolling mean (personal baseline) |
| `hrv_30d_sd` | float | ln(ms) | Derived | 30-day rolling SD |
| `hrv_z_score` | float | — | Derived | (hrv_7d_avg − hrv_30d_mean) / hrv_30d_sd |
| `hrv_normal_lower` | float | ln(ms) | Derived | hrv_30d_mean − 0.5 × hrv_30d_sd |
| `hrv_normal_upper` | float | ln(ms) | Derived | hrv_30d_mean + 0.5 × hrv_30d_sd |
| `hrv_status` | string | — | Derived | 'green', 'yellow', 'red', 'insufficient_data' |
| `rhr_daily` | float | bpm | Whoop/Withings | Resting heart rate (overnight) |
| `rhr_7d_avg` | float | bpm | Derived | 7-day rolling mean of rhr_daily |
| `rhr_30d_mean` | float | bpm | Derived | 30-day rolling mean (personal baseline) |
| `rhr_30d_sd` | float | bpm | Derived | 30-day rolling SD |
| `rhr_delta_bpm` | float | bpm | Derived | rhr_7d_avg − rhr_30d_mean |
| `rhr_z_score` | float | — | Derived | (rhr_7d_avg − rhr_30d_mean) / rhr_30d_sd |
| `rhr_status` | string | — | Derived | 'green', 'yellow', 'red', 'insufficient_data' |
| `sleep_duration_hrs` | float | hours | Whoop | Total sleep time (TST) |
| `sleep_efficiency_pct` | float | % | Whoop | TST / TIB × 100 |
| `sleep_perf_score` | float | 0–100 | Whoop | Whoop Sleep Performance Score |
| `sleep_7d_avg_hrs` | float | hours | Derived | 7-day rolling mean of sleep_duration_hrs |
| `sleep_7d_avg_eff` | float | % | Derived | 7-day rolling mean of sleep_efficiency_pct |
| `sleep_score_30d_mean` | float | 0–100 | Derived | 30-day mean of sleep_perf_score |
| `sleep_score_30d_sd` | float | 0–100 | Derived | 30-day SD of sleep_perf_score |
| `sleep_status` | string | — | Derived | 'green', 'yellow', 'red', 'insufficient_data' |
| `spo2_avg` | float | % | Whoop/Withings | Average overnight SpO2 |
| `composite_score` | float | 0–100 | Derived | Weighted Z-score composite (pre-sleep modifier) |
| `composite_score_final` | float | 0–100 | Derived | composite_score after sleep debt penalty |
| `composite_tier` | string | — | Derived | 'green', 'yellow', 'red', 'insufficient_data' |
| `tier_history` | list[string] | — | Stored | Daily tier classifications for trend detection |
| `days_baseline` | integer | days | Computed | Number of days of valid data available |
| `baseline_ready` | boolean | — | Computed | True when days_baseline ≥ 14 |

---

## 9. Implementation Notes

### 9.1 Bootstrapping / Cold Start

```python
MINIMUM_DAYS_FOR_BASELINE = 14   # Can compute, but lower confidence
OPTIMAL_DAYS_FOR_BASELINE = 30   # Full baseline established

if days_baseline < 7:
    # No recommendations; collect data silently
    communication_mode = 'silent'
    
elif days_baseline < 14:
    # Use available data; acknowledge uncertainty
    # Use 1.0 SD thresholds instead of 0.5 SD (wider tolerance)
    hrv_normal_lower = hrv_available_mean - (1.0 × hrv_available_sd)
    communication_mode = 'limited'
    
else:
    # Full operational mode
    communication_mode = 'full'
```

### 9.2 Data Quality Flags

```
if hrv_raw < 10 or hrv_raw > 200:
    flag 'hrv_artifact' → exclude from rolling average

if rhr_daily < 30 or rhr_daily > 120:
    flag 'rhr_artifact' → exclude from rolling average

if sleep_duration_hrs < 1.0 or sleep_duration_hrs > 14.0:
    flag 'sleep_artifact' → exclude from rolling average

if spo2_avg < 80 or spo2_avg > 100:
    flag 'spo2_artifact' → exclude
```

### 9.3 Key Timing Requirements

- Compute rolling averages once per day, after Whoop/Withings data sync (typically morning)
- Store tier classification with daily timestamp
- Evaluate tier persistence BEFORE determining whether to send Telegram message
- Update 30-day baseline nightly (rolling window, exclude flagged artifacts)

### 9.4 Interaction With Training Program

```
Recovery tier feeds into Milo's training prescription logic:

GREEN  → Execute programmed session (e.g., Track 2 strength or Track 3 cardio)
YELLOW → Apply intensity modifier: reduce load by 20–30%, maintain skill work
RED    → Override session: substitute with active recovery template
         OR prompt user via Telegram to choose: rest or light movement
```

### 9.5 User Opt-In Levels

```
LEVEL 0 (default):   Only send Telegram messages on YELLOW/RED triggers
LEVEL 1 (opt-in):    Daily green confirmation + workout summary
LEVEL 2 (opt-in):    Weekly trend summary (no daily scores, only trend narrative)

NEVER available:     Raw metric dashboard, daily recovery score
```

---

## 10. Sources

1. Kiviniemi et al. (2007). "Endurance training guided individually by daily heart rate variability measurements." *European Journal of Applied Physiology.* [PubMed: 17849143](https://pubmed.ncbi.nlm.nih.gov/17849143/)

2. Plews, D. Interview on HRV methodology for endurance athletes. *Scientific Triathlon, EP#42.* [scientifictriathlon.com](https://scientifictriathlon.com/tts42/)

3. HRV-Guided Training Protocol for Professional Endurance Athletes. (2020). *International Journal of Environmental Research and Public Health.* [PMC7432021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7432021/)

4. Systematic Review and Meta-Analysis: HRV-Guided Training vs. Predefined Training. (2021). *IJERPH.* [PMC8507742](https://pmc.ncbi.nlm.nih.gov/articles/PMC8507742/)

5. Inter-day reliability of heart rate complexity and variability metrics. (2023). *European Journal of Applied Physiology.* [PMC11055755](https://pmc.ncbi.nlm.nih.gov/articles/PMC11055755/)

6. Elite HRV. "What is the HRV 7 Day Rolling Average and Coefficient of Variation?" [help.elitehrv.com](https://help.elitehrv.com/article/355-what-is-the-hrv-7-day-rolling-average-and-coefficient-of-variation)

7. TrainingPeaks. "The 4 Signs of Overtraining." [trainingpeaks.com](https://www.trainingpeaks.com/coach-blog/the-4-signs-of-overtraining/)

8. Runners Connect. "Overtraining Symptoms in Runners." [runnersconnect.net](https://runnersconnect.net/overtraining-in-runners/)

9. Running Explained. "Overtraining in Runners: 3 Metrics That Reveal If You're Doing Too Much." [runningexplained.com](https://www.runningexplained.com/post/overtraining-in-runners-signs-metrics-prevention)

10. Roberts et al. — Sleep extension and restriction effects on endurance cyclists. *HiitScience.* [hiitscience.com](https://hiitscience.com/sleep-endurance-performance/)

11. Sleep Interventions in Athletic Performance. (2023). *Sports Medicine - Open.* [PMC10354314](https://pmc.ncbi.nlm.nih.gov/articles/PMC10354314/)

12. Sleep deprivation reduces muscle injury recovery. (2019). *Life Sciences.* [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0024320519307623)

13. UCLA Health. "New study suggests resistance training helps sleep." (2022). [uclahealth.org](https://www.uclahealth.org/news/article/new-study-suggests-resistance-training-helps-sleep)

14. Gavriloff D, Sheaves B, Juss A, Espie CA, Miller CB, Kyle SD. (2018). "Sham sleep feedback delivered via actigraphy biases daytime symptom reports in people with insomnia." *Journal of Sleep Research*, 27(6). [via Dr. James Hewitt](https://drjameshewitt.com/can-sleep-tracking-be-bad-for-your-performance/)

15. Andersen TO et al. Fitbit anxiety study — heart patients and wearable data interpretation. *University of Copenhagen / Futurity.* [futurity.org](https://www.futurity.org/fitness-trackers-watches-anxiety-2416592/)

16. Rosman L et al. (2024). Wearable devices and health anxiety in Afib patients. *Journal of the American Heart Association.* [UNC Medicine](https://www.med.unc.edu/medicine/news/wearable-devices-can-increase-health-anxiety-could-they-adversely-affect-health/)

17. Orthosomnia — obsessive pursuit of optimal sleep from tracker data. *ABC News / Good Morning America.* [goodmorningamerica.com](https://www.goodmorningamerica.com/wellness/story/orthosomnia-obsession-wearable-tech-impact-sleep-123990784)

18. Dodgson Psychology. "Smartwatch Anxiety: A Psychologist's Guide to Data Stress." (2026). [dodgsonpsychology.ca](https://www.dodgsonpsychology.ca/smartwatch-anxiety-orthosomnia/)

19. Whoop. "Sleep Accuracy: How WHOOP Measures and Scores Sleep." [whoop.com](https://www.whoop.com/us/en/thelocker/how-well-whoop-measures-sleep/)

20. Plait. "Why Your WHOOP Recovery Score Drops After Good Sleep." (2024). [plait.fit](https://www.plait.fit/blog/recovery-score-drops-after-good-sleep.html)

21. Alan Couzens. "Some brief thoughts on readiness scores." [alancouzens.com](https://alancouzens.com/TP/athletes.cgi/blog/readiness)

22. Shaffer F, Ginsberg JP. (2017). "An Overview of Heart Rate Variability Metrics and Norms." *Frontiers in Public Health.* [PMC5624990](https://pmc.ncbi.nlm.nih.gov/articles/PMC5624990/)

23. Wearable Sleep Technology in Clinical and Research Settings. *Medicine and Science in Sports and Exercise.* [PMC6579636](https://pmc.ncbi.nlm.nih.gov/articles/PMC6579636/)
