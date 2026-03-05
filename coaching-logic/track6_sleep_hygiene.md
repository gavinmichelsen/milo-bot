# Track 6: Sleep Hygiene Protocols for Muscle Recovery and Performance
## Milo AI Coaching System — Backend Logic Reference Document

**Document Type:** Research Synthesis + Actionable Coaching Rules  
**Target Audience:** Backend AI agent building Milo coaching logic  
**User Profile:** Male beginner-to-intermediate lifters, Telegram-based coaching  
**Last Updated:** March 2026  

---

## TABLE OF CONTENTS

1. [Andrew Huberman's Sleep Optimization Protocols](#1-andrew-hubermans-sleep-optimization-protocols)
2. [Menno Henselmans' Sleep and Recovery Recommendations](#2-menno-henselmans-sleep-and-recovery-recommendations)
3. [Sleep Duration and Resistance Training Evidence](#3-sleep-duration-and-resistance-training-evidence)
4. [Actionable Coaching Rules for Milo](#4-actionable-coaching-rules-for-milo)
5. [Sleep Metrics Integration (Whoop)](#5-sleep-metrics-integration-whoop)
6. [Supplement Protocols](#6-supplement-protocols)
7. [Master Sleep Hygiene Score Checklist](#7-master-sleep-hygiene-score-checklist)
8. [Telegram Message Templates](#8-telegram-message-templates)

---

## 1. ANDREW HUBERMAN'S SLEEP OPTIMIZATION PROTOCOLS

### 1.1 Morning Sunlight Exposure

**Protocol:** 5–10 minutes of outdoor sunlight exposure within 30–60 minutes of waking. On overcast days, extend to 15–20 minutes.

**Mechanism:**  
Specialized retinal cells called **intrinsically photosensitive retinal ganglion cells (ipRGCs)** contain the photopigment **melanopsin**. These cells detect the blue-yellow contrast of low-angle morning sunlight and transmit signals directly to the **suprachiasmatic nucleus (SCN)**, the brain's master circadian clock. The SCN then triggers:
- A cortisol spike (promotes alertness and immune function)
- Suppression of melatonin (signals daytime has started)
- Dopamine and serotonin modulation via a secondary pathway to the ventromedial prefrontal cortex (mood regulation, independent of the circadian pathway)

The SCN is a photon-summing system — it integrates light exposure over time rather than being triggered by a single moment. This is why brief, low-quality indoor light cannot replicate outdoor sun exposure.

**Evidence:**
- Melanopsin ipRGC function first documented by David Berson's lab at Brown University (landmark visual neuroscience)
- Observational study of 1,762 adults: each additional 30 minutes of morning sunlight shifted sleep midpoint 23 minutes earlier ([NSDR.co summary](https://nsdr.co/post/morning-sunlight-for-sleep-why-it-works-how-to-do-it))
- Samer Hattar (NIMH) research identifies a separate light-to-mood pathway from ipRGCs to the ventromedial prefrontal cortex, distinct from the circadian pathway ([Peter Attia / Huberman Journal Club](https://peterattiamd.com/andrewhuberman3/))
- Indoor lighting delivers 200–500 lux; circadian system requires ≥10,000 lux; outdoor sunlight on overcast winter day delivers ~8,000 lux

**Critical Notes for Milo:**
- Sunglasses block the photons needed for circadian entrainment; advise against wearing them during morning light exposure
- Prescription lenses and contact lenses do NOT reduce efficacy — acceptable to wear
- Windows filter >50% of photons relevant to melanopsin activation; indoor window viewing is 1/50th to 1/100th as effective as direct outdoor exposure
- Consistent timing is more important than duration; works even on cloudy days

**Priority:** HIGHEST — downstream effects on cortisol, melatonin, dopamine, and the entire hormonal cascade for the next 16 hours depend on this single morning input

**Rule Variable:**
```
MORNING_LIGHT_DONE = true/false
MINUTES_OUTDOOR = integer
WAKE_TIME = HH:MM
LIGHT_WITHIN_60MIN = (MORNING_LIGHT_TIME - WAKE_TIME <= 60 minutes)
```

---

### 1.2 Evening Light Reduction and Blue Light Management

**Protocol:** Reduce artificial bright light exposure after sunset. Use dim, warm-toned (amber/red) lighting after 9 PM. Avoid overhead fluorescent or LED lights in the 2 hours before bed.

**Mechanism:**  
The same melanopsin ipRGCs that detect morning sunlight also respond to artificial bright light at night. Even 15 seconds of bright light exposure at night can meaningfully suppress melatonin. The key distinction: these cells are tuned to the blue-yellow contrast of sunlight at a low solar angle — moonlight, candlelight, and firelight do NOT trigger false daytime signals because they are insufficient in intensity and lack the blue-yellow contrast. Modern LED overhead lighting, screens, and fluorescent lighting do exceed the threshold.

Caffeine consumed in the evening can independently delay the endogenous melatonin rhythm by approximately 40 minutes — nearly half the delay caused by bright light exposure at bedtime ([Journal of Sleep Research, Burke et al. 2015, as cited in Landolt et al., 2022, PMC9541543](https://pmc.ncbi.nlm.nih.gov/articles/PMC9541543/)).

**Evidence:**
- Blue light (from screens and LED overhead lights) suppresses melatonin more potently than red/amber light spectra
- Huberman protocol (sourced from circadian biology): dim all overhead lights after sunset; use floor lamps, candles, or firelight-spectrum bulbs

**Actionable Rules:**
```
EVENING_LIGHT_CUTOFF = 21:00 (local)
SCREEN_DIMMED = true/false (after 20:00)
OVERHEAD_LIGHTS_OFF = true/false (after 21:00)
BLUE_LIGHT_GLASSES = optional (lower priority than behavioral light reduction)
```

**Priority:** HIGH

---

### 1.3 Temperature Regulation

**Protocol:**
- Sleep in a cool environment: 65–68°F (18–20°C) ideal
- Take a warm shower or bath 1–2 hours before bed (counterintuitively promotes sleep onset)
- Avoid cold exposure late in the evening (can phase-delay the circadian clock)

**Mechanism:**  
Core body temperature follows a circadian rhythm: lowest ~4 AM, peaks in the late afternoon (4–6 PM). Sleep onset is tightly coupled to a drop in core temperature. A warm bath or shower raises skin temperature, which causes peripheral vasodilation and heat dissipation — accelerating the core temperature drop required for sleep onset. Cold exposure early in the day (e.g., cold shower in the morning) can phase-advance the clock (shift wake time earlier). Late-day heat exposure or hot baths after 8 PM may phase-delay the clock.

**Evidence:**
- Circadian temperature rhythm: well-documented in sleep research; core temperature minimum ~4 AM is a key anchor point for the biological clock ([Huberman Lab / Shortform summary](https://www.shortform.com/podcast/episode/huberman-lab-2024-11-28-episode-summary-essentials-using-science-to-optimize-sleep-learning-metabolism))
- Warm bath before bed: meta-analyses show warm water immersion 1–2 hours before bed reduces sleep onset latency and improves deep sleep quality (Haghayegh et al., 2019, *Sleep Medicine Reviews*)

**Actionable Rules:**
```
BEDROOM_TEMP_TARGET = 65–68°F (18.3–20°C)
WARM_BATH_TIMING = 60–120 min before bedtime
COLD_SHOWER_TIMING = within first 2 hours of waking (phase-advance benefit)
```

**Priority:** HIGH

---

### 1.4 Caffeine Timing and Adenosine Management

**Protocol:**
- Delay first caffeine intake to 90–120 minutes after waking
- Last caffeine intake: no later than 12–14 hours before bedtime (e.g., 10 AM cutoff for a 10 PM bedtime)
- Practical target: no caffeine after 1–2 PM for most users

**Mechanism:**  
Caffeine is an adenosine receptor antagonist. Adenosine is the primary sleep pressure molecule — it accumulates during waking hours and signals drowsiness by binding A1 and A2A adenosine receptors. Caffeine blocks these receptors without clearing adenosine; when caffeine's half-life expires, the accumulated adenosine "crashes" onto the receptors simultaneously — the caffeine crash.

**Caffeine pharmacokinetics:**
- **Half-life: 5–6 hours** (Matthew Walker, as cited by Huberman); some individuals metabolize faster or slower based on CYP1A2 enzyme genetics
- **Quarter-life: 10–12 hours** — 25% of caffeine remains active 10–12 hours after ingestion
- 200 mg of caffeine ingested in the early evening delayed endogenous melatonin onset by ~40 minutes ([Landolt et al., 2022, Journal of Sleep Research, PMC9541543](https://pmc.ncbi.nlm.nih.gov/articles/PMC9541543/), citing Burke et al. 2015)
- Caffeine at bedtime prolongs sleep latency, reduces sleep efficiency, reduces Stage 4 NREM sleep, and suppresses slow-wave activity (delta power) ([Nature, Landolt et al.](https://www.nature.com/articles/1380255.pdf))
- Chronic daily caffeine intake leads to upregulation of adenosine receptors (neuroadaptation), creating caffeine dependence and withdrawal-related sleep disruption upon cessation

**Nuance on "wait to caffeinate":**  
The rationale that adenosine continues clearing for 90–120 minutes post-waking is physiologically questionable — adenosine drops sharply at sleep onset, not across the first hours of waking. However, delaying caffeine does meaningfully align intake with the natural cortisol awakening response (CAR), which peaks 30–45 minutes post-waking, potentially extending afternoon alertness and reducing the crash timing. The bottom line: the last-caffeine cutoff (8–10 AM) matters far more than the delay at the start of the day.

**Actionable Rules:**
```
CAFFEINE_MORNING_DELAY = 60–90 min post-waking (recommended)
CAFFEINE_CUTOFF_HOURS_BEFORE_BED = 10  // conservative
CAFFEINE_CUTOFF_HOURS_BEFORE_BED_STRICT = 12  // for poor sleepers
CAFFEINE_HALF_LIFE_HOURS = 5.5  // default estimate
CAFFEINE_CUTOFF_TIME = BEDTIME_TARGET - 10h
```

**Priority:** VERY HIGH (high compliance barrier → strong behavior change leverage)

---

### 1.5 Consistent Wake Time as the Primary Anchor

**Protocol:** Fix a consistent wake time every day, including weekends, regardless of when you went to sleep.

**Mechanism:**  
The circadian clock is entrained primarily by **light exposure** and **wake time consistency**. Irregular wake times create a form of chronic social jet lag, dampening the circadian amplitude and disrupting the timing of cortisol, melatonin, core temperature rhythms, and anabolic hormone secretion. A consistent wake time, combined with morning light, is the single most powerful behavioral anchor for circadian stability.

**Evidence:**
- Circadian biology consensus: the sleep homeostatic system (Process S, adenosine) and the circadian timing system (Process C, SCN) interact; consistent wake time builds reliable sleep pressure by bedtime
- Irregular sleep schedules correlate with worse HRV, metabolic markers, and performance in athletes

**Actionable Rules:**
```
WAKE_TIME_CONSISTENCY = |today_wake - 7day_avg_wake| <= 30min  // "consistent"
WAKE_TIME_CONSISTENCY_SCORE = rolling 7-day SD of wake time (minutes)
CONSISTENCY_THRESHOLD = SD < 30 min → "consistent"
CONSISTENCY_ALERT = SD > 45 min → trigger coaching message
```

**Priority:** VERY HIGH — the single most underrated lever for sleep quality

---

### 1.6 Exercise Timing

**Protocol:**
- Morning or afternoon exercise: ideal for circadian alignment
- High-intensity/high-strain exercise: complete at least 4 hours before bedtime
- Light exercise (yoga, walk, stretching): acceptable within 1–2 hours of bedtime
- Avoid maximal-effort training within 2 hours of sleep onset

**Mechanism:**  
High-intensity exercise activates the sympathetic nervous system (raises heart rate, core body temperature, and alertness). Sleep onset requires parasympathetic dominance — the reverse state. Large cohort study (n ≈ 15,000, ~4 million person-nights) using wearable data ([Leota et al., Nature Communications, 2025](https://www.nature.com/articles/s41467-025-58271-x)) found dose-response relationships:
- Maximal exercise ending 2h before habitual sleep onset: 36-minute delay in sleep onset, 22-minute shorter total sleep, 14% lower HRV
- Maximal exercise occurring after habitual sleep onset: 80-minute delay, 43-minute shorter sleep
- Exercise ending ≥6 hours before sleep onset: no measurable negative impact; high-strain training at this window was associated with slightly earlier sleep onset ([Whoop research summary](https://www.whoop.com/us/en/thelocker/fact-or-fiction-does-exercise-close-to-bedtime-harm-sleep-quality/))

**Actionable Rules:**
```
EXERCISE_CUTOFF_HOURS_BEFORE_BED = 4  // high-strain
EXERCISE_CUTOFF_HOURS_BEFORE_BED_LIGHT = 1  // light strain (yoga, walk)
EXERCISE_TIMING_WARNING = if (exercise_end_time > (bedtime - 4h) AND strain = "high")
```

**Priority:** MEDIUM-HIGH (most beginners train at moderate strain; still important to establish rule)

---

## 2. MENNO HENSELMANS' SLEEP AND RECOVERY RECOMMENDATIONS

### 2.1 Core Position: Sleep Is Not Optional for Hypertrophy

Henselmans explicitly positions sleep optimization as a **Tier 1 priority** — equivalent to macro tracking and programming, not an afterthought like supplements:

> "Sleep and stress are up there with counting your macros, getting your protein in, doing a good lifting program."  
> — Menno Henselmans ([mennohenselmans.com](https://mennohenselmans.com/these-are-the-top-2-underrated-factors-killing-your-gains/))

He considers sleep and stress the **top 2 underrated factors limiting gains** in most trainees.

### 2.2 Sleep Duration and Nutrient Partitioning

Henselmans cites and endorses two key studies demonstrating that even moderate sleep restriction causes dramatic worsening of body composition outcomes:

**Study 1 — Nedeltcheva et al. (2010):**
- Sleeping 5 hours vs. 7.5 hours per night during caloric restriction:
  - >50% reduction in the proportion of weight lost as fat
  - >50% increase in fat-free mass lost (muscle loss)
- Source: [PMC2951287, Annals of Internal Medicine](https://pmc.ncbi.nlm.nih.gov/articles/PMC2951287/)

**Study 2 (cited by Henselmans):**
- Sleeping 40 minutes less mid-week: increased proportion of weight loss that was fat-free mass from 20% → 80%
- (Statistical caveats acknowledged; Henselmans contacted authors directly)

**Study 3 — Jåbekk et al. (10-week intervention):**
- Sleep-optimization group: lost 1.8 kg fat, gained 1.7 kg lean mass (near-perfect recomposition)
- Control group (no sleep intervention): gained 0.8 kg fat, gained 1.3 kg lean mass
- Statistically significant fat loss difference; lean mass difference trending but not significant

### 2.3 Sleep vs. Training Trade-off

Henselmans' nuanced position on the training-vs.-sleep trade-off:

> "If training time directly subtracts from sleep time... in most cases, I think it is best to train unless you're already at a very high training volume and recovery capacity is genuinely the limiting factor. Get the workout in, only when you're already pushing MRV levels — at that point you're probably better off getting more sleep."  
> — [Menno Henselmans 100K Q&A](https://mennohenselmans.com/100k-qa-training-tips-my-workouts-personal-life/)

**Decision Rule for Milo:**
```python
if user_weekly_sets < MRV_estimate:
    priority = "complete_training_even_if_slightly_tired"
else:  # near MRV
    priority = "prioritize_sleep_over_extra_volume"
```

### 2.4 Recovery Capacity as a Variable

Henselmans emphasizes that recovery capacity (and thus sleep's role) varies by:
- Training volume (sets/week per muscle group)
- Life stress (work, family, sleep deprivation amplifies perceived stress)
- Caloric status (deficit dramatically increases sleep's importance for muscle retention)
- Age (older trainees → sleep quality declines, recovery slower)

**Variable Definitions for Milo:**
```
RECOVERY_CAPACITY_MODIFIERS = {
  "caloric_deficit": HIGH_IMPACT,       // doubles sleep importance
  "high_weekly_volume": HIGH_IMPACT,    // near MRV → sleep becomes limiting
  "high_life_stress": MEDIUM_IMPACT,
  "age_over_35": MEDIUM_IMPACT
}
```

---

## 3. SLEEP DURATION AND RESISTANCE TRAINING EVIDENCE

### 3.1 Muscle Protein Synthesis — Direct Evidence

**Key Finding:** A single night of total sleep deprivation reduces muscle protein synthesis (MPS) by **18%** in young, healthy males and females, accompanied by a 21% increase in cortisol and a 24% decrease in testosterone.

- Source: Lamon et al. (2021), *Physiological Reports*, [PMC7785053](https://pmc.ncbi.nlm.nih.gov/articles/PMC7785053/)
- Five consecutive nights of 4h sleep restriction similarly reduced myofibrillar protein synthesis (Saner et al., 2020, cited in Lamon et al.)
- Mechanism: sleep deprivation creates **anabolic resistance** — muscles lose sensitivity to dietary protein's anabolic signal
- Additional mechanism: catabolic gene signature in skeletal muscle observed after one night of total sleep deprivation (Cedernaes et al., 2018)

### 3.2 Testosterone and Sleep — Leproult & Van Cauter (2011)

**Key Finding:** Five hours of sleep per night for one week reduced testosterone levels by **10–15%** in healthy young men (mean age 24) — equivalent to 10–15 years of aging.

- Source: Leproult R, Van Cauter E. "Effect of 1 Week of Sleep Restriction on Testosterone Levels in Young Healthy Men." *JAMA*, 2011; 305(21): 2173. DOI: 10.1001/jama.2011.710 ([ScienceDaily summary](https://www.sciencedaily.com/releases/2011/05/110531162142.htm), [UChicago Medicine](https://www.uchicagomedicine.org/forefront/news/2011/may/sleep-loss-lowers-testosterone-in-healthy-young-men))
- Lowest testosterone levels occurred in the afternoons (2–10 PM) on sleep-restricted days
- Testosterone is critical for muscle protein synthesis, bone density, and well-being

**Nuance (important for Milo):** A subsequent RCT (Ramasamy et al., *Sleep Health*, 2019, [PMC6917985](https://pmc.ncbi.nlm.nih.gov/articles/PMC6917985/)) found that chronic mild sleep restriction via **delayed bedtime** (rather than earlier wake time) may not significantly reduce testosterone. The Leproult finding involved earlier wake times. The practical take: **truncating sleep at the wake end** (alarm-forcing early wake) is more damaging to testosterone than staying up late. A consistent, sufficient total sleep duration is the priority.

### 3.3 Body Composition During Caloric Deficit — Nedeltcheva et al. (2010)

**Study Design:** Randomized, 2-period crossover; 10 overweight adults; 14 days of caloric restriction with either 8.5h or 5.5h time-in-bed.

**Findings:**
| Outcome | 8.5h Sleep | 5.5h Sleep |
|---------|-----------|-----------|
| Fat lost (kg) | 1.4 | 0.6 |
| Fat-free mass lost (kg) | 1.5 | 2.4 |
| % weight loss as fat | 56% | 25% |
| Hunger increase | — | Significantly higher |
| Ghrelin (acylated) | — | Significantly elevated |
| Resting metabolic rate | — | Significantly lower |

**Conclusion:** Sleep curtailment decreased the fraction of weight lost as fat by **55%** and increased fat-free mass loss by **60%**. Sleep deprivation during a caloric deficit creates a catabolic, muscle-wasting state.

- Source: Nedeltcheva AV et al., *Annals of Internal Medicine*, 2010. [PMC2951287](https://pmc.ncbi.nlm.nih.gov/articles/PMC2951287/) / [PubMed 20921542](https://pubmed.ncbi.nlm.nih.gov/20921542/)

**Milo Application:** For any user in a caloric deficit (cut phase), sleep hygiene moves to CRITICAL priority. Failure to sleep adequately during a cut results in disproportionate muscle loss.

### 3.4 Growth Hormone Secretion

**Key Facts:**
- The major daily GH pulse is a **sleep onset-associated pulse** occurring during the **first phase of slow-wave sleep (SWS, Stages III/IV)**
- 70% of daily GH is released during deep sleep
- GH secretion tracks closely with SWS duration: more SWS = more GH
- Hypnotic deepening of SWS increased GH levels by >400% vs. control in experimental conditions ([Nature, Communications Biology, 2022](https://www.nature.com/articles/s42003-022-03643-y))
- GH drives muscle protein synthesis, tissue regeneration, fat oxidation, and bone density

**Implications for Sleep Architecture:**
- Behaviors that fragment SWS (alcohol, late caffeine, elevated core temperature, late exercise) directly suppress GH release
- The first 3–4 hours of sleep contain the most SWS and thus the most GH
- Chronically shorting sleep cuts the tail end of sleep, losing REM — but going to bed too late also reduces the SWS window in the first half of the night

**Milo Rules:**
```
SWS_PRIORITY_BEHAVIORS = [
  "consistent_bedtime",
  "cool_bedroom",
  "no_alcohol",
  "caffeine_cutoff_enforced",
  "no_late_high_intensity_exercise"
]
```

### 3.5 Minimum and Optimal Sleep Duration

| Category | Duration | Evidence Level |
|----------|----------|----------------|
| Minimum effective (survival/basic recovery) | ≥6h | Low-moderate |
| Minimum for testosterone maintenance | ≥7h | Moderate (Leproult 2011) |
| Minimum for muscle protein synthesis optimization | ≥7h | Moderate (Lamon 2021) |
| **Optimal for hypertrophy-focused trainees** | **7.5–9h** | **Moderate-high** |
| Elite athlete recommendation | 8–10h | Observational |

**Evidence Summary:**
- National Sleep Foundation: 7–9 hours for adults
- Multiple MPS studies used ≥7h as inclusion criterion (adequate sleep control)
- Jåbekk intervention used sleep optimization (duration + quality); outcomes aligned with ~8h targets
- Henselmans' cited studies show harm beginning at 5h and trending negative at <7.5h

**Milo Target:**
```
SLEEP_DURATION_TARGET_HOURS = 7.5  // default
SLEEP_DURATION_TARGET_OPTIMAL = 8.5  // for trainees in caloric deficit or high volume
SLEEP_DURATION_MINIMUM = 7.0       // below this → coaching intervention
SLEEP_DURATION_CRITICAL = 6.0      // below this → flag for immediate attention
```

---

## 4. ACTIONABLE COACHING RULES FOR MILO

### 4.1 Prioritized Habit Stack

Habits ranked by: (1) Strength of evidence, (2) Impact magnitude, (3) Ease of implementation.

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

---

### 4.2 Phased Implementation Protocol

**Phase 1 — Foundation (Weeks 1–2): Pick 2 habits**

Focus on the two highest-leverage, zero-cost habits:
1. **Consistent wake time** (anchor the entire circadian system)
2. **Caffeine cutoff** (most users are already violating this; high ROI)

Coaching prompt trigger: new user onboarding OR user reports poor sleep for 3+ consecutive days

---

**Phase 2 — Light Hygiene (Weeks 3–4): Add 1–2 habits**

1. **Morning sunlight** (add to Phase 1 habits)
2. **Dim lights after 9 PM** (pairs naturally with winding down)

Coaching prompt trigger: Phase 1 habits confirmed at ≥70% compliance over 7 days

---

**Phase 3 — Environment (Weeks 5–6): Add 1–2 habits**

1. **Bedroom temperature** (cooldown protocol)
2. **Consistent bedtime** (add after wake time is locked in)
3. **Warm shower timing** (optional, easy win)

Coaching prompt trigger: Phase 2 habits confirmed at ≥70% compliance over 7 days

---

**Phase 4 — Exercise Timing Refinement (Weeks 7–8)**

1. **Exercise timing check** (review Whoop data: are late workouts hurting HRV/sleep?)
2. **Alcohol awareness** (flag if user journals alcohol consumption near bedtime)

Coaching prompt trigger: Whoop data shows ≥2 nights per week with elevated nocturnal HR and reduced HRV correlated with late workouts

---

**Phase 5 — Supplements (Weeks 9+)**

1. **Magnesium** (high safety, accessible, modest evidence)
2. **L-Theanine** (if stress/anxiety is a reported barrier to sleep)
3. **Apigenin** (only if Phases 1–4 are optimized)

Coaching prompt trigger: Whoop sleep score <70 despite behavioral habits optimized; user explicitly interested in supplements

---

### 4.3 Decision Logic Tree (When to Deploy Each Recommendation)

```python
def sleep_coaching_decision(user_data):
    
    # CRITICAL: Always check these first
    if user_data["avg_sleep_hours"] < 6.0:
        return URGENT: "insufficient sleep — duration intervention BEFORE anything else"
    
    if user_data["wake_time_sd_7day"] > 60:  # minutes
        return PHASE_1: "wake_time_consistency"
    
    if user_data["last_caffeine_hours_before_bed"] < 8:
        return PHASE_1: "caffeine_cutoff"
    
    if user_data["morning_light_compliance_7day"] < 0.5:
        return PHASE_2: "morning_sunlight"
    
    if user_data["evening_light_compliance"] < 0.5:
        return PHASE_2: "evening_light_reduction"
    
    if user_data["bedroom_temp"] > 22:  # Celsius
        return PHASE_3: "bedroom_temperature"
    
    if user_data["bedtime_sd_7day"] > 60:
        return PHASE_3: "bedtime_consistency"
    
    if user_data["late_exercise_nights_per_week"] >= 2:
        return PHASE_4: "exercise_timing"
    
    # Supplements only if above is optimized
    if user_data["sleep_score_avg_14day"] < 70 AND behavioral_habits_optimized:
        return PHASE_5: "supplement_protocol"
    
    return "reinforce_existing_habits"
```

---

## 5. SLEEP METRICS INTEGRATION (WHOOP)

### 5.1 Relevant Whoop Metrics for Milo

| Metric | Whoop Variable | Relevant Threshold | What It Signals |
|--------|---------------|-------------------|-----------------|
| Sleep Performance % | `sleep_performance_pct` | <70% = poor | Total sleep vs. needed |
| Time in SWS (slow-wave sleep) | `sws_minutes` | <60 min = low | GH secretion window |
| Time in REM | `rem_minutes` | <90 min = low | Memory, hormone regulation |
| Sleep Consistency | `sleep_consistency_score` | <70% = irregular | Circadian stability |
| Nocturnal HRV | `hrv_ms` | trend decline = stress | CNS recovery status |
| Nocturnal RHR | `rhr_bpm` | elevated vs. baseline | Sympathetic load |
| Sleep Latency | `sleep_latency_min` | >30 min = problematic | Arousal/caffeine/stress |
| Recovery Score | `recovery_score_pct` | <33% = red | Systemic readiness |
| 7-Day HRV trend | `hrv_7d_trend` | declining = overreach | Cumulative fatigue |

**Note:** Whoop's HRV and RHR measurements are validated against laboratory standards. A University of Connecticut / Korey Stringer Institute study confirmed Whoop accurately measured RHR, HRV, and SWS metrics in collegiate athletes ([Whoop Research Blog](https://www.whoop.com/us/en/thelocker/study-rhr-hrv-sleep-collegiate-athletes/)).

---

### 5.2 Assessment Windows

**Weekly Assessment (every 7 days):**
- Calculate 7-day rolling average of: sleep duration, sleep performance %, recovery score, HRV
- Compare to user's personal baseline (first 2 weeks = baseline calibration period)
- Flag if any metric drops >15% below personal baseline for 3+ consecutive days

**Bi-Weekly Assessment (every 14 days):**
- Assess compliance with active hygiene habits
- Compare sleep performance to 14 days prior
- If improvement: advance to next habit phase
- If flat/worse: reinforce current phase, don't add new habits

**Monthly Assessment (every 30 days):**
- Full sleep hygiene audit against checklist
- Cross-reference sleep scores with training performance (weight moved, RPE trend)
- Adjust targets if user has made lifestyle changes (travel, shift work, etc.)

---

### 5.3 Whoop Data → Coaching Trigger Rules

```python
WHOOP_TRIGGERS = {
    
    # High-priority alerts
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
        "condition": "wake_time_sd_7d > 45",  # minutes
        "priority": "HIGH",
        "action": "consistency_coaching"
    },
    
    "high_latency": {
        "condition": "sleep_latency_avg_7d > 25",  # minutes
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

---

### 5.4 When to Introduce New Habits vs. Reinforce Existing Ones

**Introduce new habit IF:**
- Current active habit has ≥70% compliance over the past 7 days
- Sleep performance score improved by ≥5 percentage points over past 2 weeks
- User explicitly requests new information (curiosity signal)

**Reinforce existing habit IF:**
- Compliance < 70% on any active habit
- Sleep score flat or declining despite habit engagement
- User reports difficulty with current habit

**Never add more than 1 new habit per 2-week window.** Behavior change science (implementation intention research; Gollwitzer 1999) shows that habit stacking beyond 2–3 concurrent habits dramatically reduces compliance.

---

## 6. SUPPLEMENT PROTOCOLS

### 6.1 Magnesium Threonate (MgT) or Bisglycinate

**Huberman Recommendation:** 300–400 mg magnesium threonate OR magnesium bisglycinate, taken 30–60 minutes before bed.

**Evidence:**
- RCT (Hausenblas et al., 2024, *Sleep Medicine: X*, [PMC11381753](https://pmc.ncbi.nlm.nih.gov/articles/PMC11381753/)): 1g MgT/day for 21 days improved deep sleep score (Oura Ring objective measurement; p<0.001), REM sleep score (p=0.02), readiness score, and daily activity vs. placebo. Effects continued improving through 3 weeks, unlike placebo which plateaued at week 1.
- [AJMC summary](https://www.ajmc.com/view/study-magnesium-l-threonate-improves-objective-subjective-sleep-quality): "improved self-reported post-awakening behavior, mental alertness, and moods compared to placebo"
- Strong placebo effect observed — this is relevant: perceived sleep improvement may exceed objective improvement, which is still meaningful for user adherence
- Magnesium deficiency is common in Western diets; athletes/lifters have higher magnesium needs due to sweat losses

**Mechanism:** Magnesium is a natural NMDA receptor antagonist and GABA agonist. The threonate form crosses the blood-brain barrier more efficiently than other forms. MgT increases GABAergic activity, serotonergic receptor expression, and melatonin levels.

**Dose for Milo:** 300–400 mg elemental magnesium (as threonate or bisglycinate) 30–60 min before bed.

**Safety:** Generally safe; very high doses may cause loose stools (use bisglycinate if GI issues).

---

### 6.2 L-Theanine

**Huberman Recommendation:** 100–200 mg before bed (often combined with magnesium).

**Evidence:**
- L-theanine increases GABAergic and serotonergic receptor expression, reduces sleep latency, increases slow-wave (delta) brain activity ([Frontiers in Nutrition, 2022, PMC9017334](https://pmc.ncbi.nlm.nih.gov/articles/PMC9017334/))
- Mg-L-theanine complexes showed superior sleep-promoting effects vs. L-theanine alone in preclinical models (same study above)
- Reduces anxiety-driven sleep difficulty; does not cause grogginess or tolerance
- Note: Most human L-theanine sleep evidence is preclinical or small-sample; stronger evidence exists for its anxiolytic effects (which in turn benefit sleep onset)

**Mechanism:** Promotes alpha brain wave activity (relaxed alertness); reduces excitatory glutamate activity; increases inhibitory GABA.

**Dose for Milo:** 100–200 mg, 30–60 min before bed.

**Best for:** Users who report difficulty winding down mentally; racing thoughts at bedtime.

---

### 6.3 Apigenin

**Huberman Recommendation:** 50 mg apigenin before bed (standardized chamomile extract or pure apigenin).

**Evidence:**
- Apigenin binds GABA-A receptors (same target as benzodiazepines but with far weaker affinity → no dependence risk)
- Systematic review of 10 clinical trials: 9/10 concluded chamomile (primary apigenin source) effective in reducing anxiety ([Clinical Nutrition Research, 2024](https://e-cnr.org/DOIx.php?id=10.7762%2Fcnr.2024.13.2.139))
- In insomnia patients, 540 mg chamomile extract trended toward improved daytime function (not statistically significant in that trial)
- Reduces generalized anxiety (which is the primary mechanism for sleep benefit in most lifters)

**Mechanism:** Partial agonist at GABA-A receptors; anxiolytic effect reduces the physiological arousal that delays sleep onset.

**Dose for Milo:** 50 mg apigenin (standardized), 30–60 min before bed.

**Cautions:**
- Allergic to ragweed? → Chamomile/apigenin may cross-react; advise caution
- Avoid combining with prescription sedatives or blood thinners without medical guidance
- Avoid during pregnancy

**Priority note:** Behavioral interventions (Phases 1–4) have far stronger evidence than supplements. Introduce supplements only once behavioral habits are established.

---

### 6.4 Pre-Sleep Protein (Bonus — Synergistic with Sleep)

**Not a sleep hygiene supplement, but directly relevant:**

- 40g of casein protein ingested before sleep increases overnight myofibrillar protein synthesis by 22–37% vs. placebo ([van Loon lab, GSSI, 2022](https://www.gssiweb.org/research/article/resistance-exercise-augments-postprandial-overnight-muscle-protein-synthesis-rates))
- Evening resistance training further augments the overnight MPS response to pre-sleep protein ([Nutrients, 2016, PMC5188418](https://pmc.ncbi.nlm.nih.gov/articles/PMC5188418/))
- At least 40g protein needed to show robust overnight MPS effect (30g is subthreshold in acute protocols)

**Milo Rule:**
```
PRE_SLEEP_PROTEIN_TRIGGER = (training_day = true AND protein_goal_met_before_dinner = false)
PRE_SLEEP_PROTEIN_DOSE = 30–40g casein or slow-digesting protein
TIMING = 30–60 min before bed
```

---

## 7. MASTER SLEEP HYGIENE SCORE CHECKLIST

Milo uses this as a daily/weekly scoring tool. Each habit has a binary (done/not done) status or a measured value.

### Daily Sleep Hygiene Checklist (0–10 Score)

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
| **BONUS** | Pre-sleep protein (training day) | `pre_sleep_protein = true` | 0.5 (bonus) |

**Scoring:**
```
SLEEP_SCORE = sum(points for completed habits)
SLEEP_SCORE_GRADE = {
    9–10: "Excellent",
    7–8.9: "Good",
    5–6.9: "Moderate — 1–2 habits to improve",
    <5: "Needs attention — prioritize foundation habits"
}
```

**7-Day Rolling Sleep Score:**
```
WEEKLY_SLEEP_SCORE = avg(daily_sleep_scores, last_7_days)
```

---

## 8. TELEGRAM MESSAGE TEMPLATES

### 8.1 Onboarding — Introducing Sleep as a Priority

```
MESSAGE_ONBOARDING_SLEEP_INTRO:

"Before we dive into training, I want to talk about something that most people overlook — sleep.

Here's why it matters for your gains: one night of poor sleep reduces muscle protein synthesis by 18%. And sleeping just 5 hours instead of 7.5 hours can cut your fat loss by more than half, while simultaneously causing you to lose muscle instead.

Sleep isn't recovery time. It's when growth actually happens.

We're going to track two simple things this week:
1. Your wake time (same time every morning, even weekends)
2. Your last caffeine of the day

What time do you usually wake up? And what time do you usually have your last coffee or energy drink?"
```

---

### 8.2 Phase 1 — Consistent Wake Time Introduction

```
MESSAGE_WAKE_TIME_INTRO:

"First habit I want you to lock in: a consistent wake time.

Your body's internal clock (circadian rhythm) controls when testosterone peaks, when growth hormone is released, and how deeply you sleep. The single best thing you can do to stabilize it is wake up at the same time every day — within 30 minutes, including weekends.

Action for this week: Pick a wake time you can realistically hit 7 days a week and tell me what it is. We'll track it together.

(If you're currently all over the place on weekends, just pick a time that's 30–60 min later than your weekday time as a compromise.)"
```

---

### 8.3 Phase 1 — Caffeine Cutoff Introduction

```
MESSAGE_CAFFEINE_CUTOFF_INTRO:

"Second habit this week: your caffeine cutoff.

Caffeine blocks the adenosine receptors in your brain — adenosine is what makes you feel sleepy. Here's the issue: caffeine has a half-life of about 5–6 hours. So if you have a coffee at 3 PM, 25% of that caffeine is still active at 11 PM.

That caffeine doesn't just keep you up — it actively reduces the depth of your sleep, which is when 70% of your growth hormone is released.

Rule: no caffeine after [CALCULATED_CUTOFF_TIME — 10h before target bedtime].

What's your usual bedtime goal? I'll calculate your cutoff."
```

---

### 8.4 Phase 2 — Morning Sunlight Introduction

```
MESSAGE_MORNING_LIGHT_INTRO:

"New habit to add: 10 minutes of morning sunlight, within the first hour of waking.

This isn't just about vitamin D. The cells in your eyes (melanopsin retinal ganglion cells) respond to the blue-yellow contrast of morning sunlight and send a signal to your brain's master clock — locking in your circadian rhythm for the day.

This single habit sets the timing for your cortisol, testosterone, and melatonin for the next 16 hours.

How to do it: Step outside (no sunglasses) within 60 minutes of waking. 10 minutes is enough. You can walk, stretch, eat breakfast, whatever — just be outside.

If it's raining or you're somewhere with no access to natural light, I'll tell you how to adapt."
```

---

### 8.5 Phase 3 — Bedroom Temperature

```
MESSAGE_BEDROOM_TEMP:

"One of the easiest sleep upgrades: cool your bedroom down.

Your body needs to drop its core temperature to initiate and maintain deep sleep. The target is 65–68°F (18–20°C). If your room is warm, your body can't make that drop efficiently — you get lighter, more fragmented sleep and less growth hormone.

Quick wins:
- Set your AC or fan to your target temp
- Keep the room dark (temperature and darkness work together)
- Take a warm shower 60–90 minutes before bed — this pulls heat to your skin surface and accelerates the temperature drop when you get out

What does your bedroom temperature look like? Do you have control over it?"
```

---

### 8.6 Weekly Sleep Check-In

```
MESSAGE_WEEKLY_CHECKIN:

"Quick sleep check-in for the week 🔍

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

---

### 8.7 Red Alert — Insufficient Sleep During Cut

```
MESSAGE_SLEEP_CRITICAL_DEFICIT:

"⚠️ I need to flag something important.

You're in a caloric deficit right now — and your sleep has been averaging [X] hours this week.

Here's the problem: a study in the *Annals of Internal Medicine* found that sleeping 5.5 hours instead of 8.5 hours during a diet cut your fat loss by 55% and increased the amount of muscle you lost by 60%.

Right now, your sleep is working against your cut. It's not a minor issue — it's potentially the biggest factor limiting your results.

For this week, I'd like to prioritize sleep above everything else. Let's troubleshoot what's cutting your sleep short.

Is it: (1) going to bed too late, (2) waking up too early, (3) waking up in the night, or (4) just not enough hours in the day?"
```

---

### 8.8 Supplement Introduction (Phase 5)

```
MESSAGE_SUPPLEMENT_INTRO:

"You've built solid sleep habits — nice work. Here's an optional add-on if you want to go further.

**Magnesium** (threonate or bisglycinate): A recent placebo-controlled study using an Oura Ring found that magnesium threonate improved deep sleep and REM sleep after 2–3 weeks. Most lifters are mildly deficient anyway due to sweat losses.

**Dose:** 300–400 mg, 30 minutes before bed.

I'd start here before anything else. It's cheap, safe, and has real evidence behind it.

If your main issue is a racing mind at bedtime, **L-Theanine (100–200 mg)** pairs well with magnesium — it promotes relaxed alertness without grogginess.

Any supplements you're already taking that I should know about?"
```

---

### 8.9 Follow-Up / Compliance Reinforcement

```
MESSAGE_HABIT_FOLLOW_UP:

"How's the [HABIT_NAME] going?

A quick reminder of why it matters: [1-sentence evidence rationale].

If you're struggling with it, tell me the specific barrier — I can usually find a workaround.

Remember, consistency beats perfection. 5 out of 7 days is genuinely meaningful. We're not going for zero-to-perfect, we're building a system."
```

---

## APPENDIX: KEY CITATION INDEX

| Claim | Citation | DOI / URL |
|-------|----------|-----------|
| Morning sunlight shifts sleep midpoint 23 min per 30 min of sun | Observational study, 1762 adults | https://nsdr.co/post/morning-sunlight-for-sleep-why-it-works-how-to-do-it |
| Melanopsin ipRGC circadian mechanism | Berson et al. (Brown University); Huberman/Hattar | https://peterattiamd.com/andrewhuberman3/ |
| Caffeine half-life 5–6 hours | Walker & Huberman | https://www.youtube.com/watch?v=bFdBJ2v6sps |
| Caffeine delays melatonin ~40 min | Burke et al. 2015, cited in Landolt 2022 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9541543/ |
| Caffeine suppresses delta/SWS at bedtime | Landolt et al., Nature | https://www.nature.com/articles/1380255.pdf |
| Sleep deprivation reduces MPS by 18% | Lamon et al. 2021, Physiological Reports | https://pmc.ncbi.nlm.nih.gov/articles/PMC7785053/ |
| 5h sleep → 10–15% testosterone drop (10–15 year aging equivalent) | Leproult & Van Cauter, JAMA 2011 | DOI: 10.1001/jama.2011.710 |
| Sleep curtailment during deficit: 55% less fat loss, 60% more LBM loss | Nedeltcheva et al. 2010, Annals Internal Medicine | https://pmc.ncbi.nlm.nih.gov/articles/PMC2951287/ |
| GH secreted primarily during first SWS phase | Physiology of GH/Sleep | https://www.scirp.org/journal/paperinformation?paperid=135754 |
| SWS enhancement increased GH by 400%+ | Rasch et al. 2022, Communications Biology | https://www.nature.com/articles/s42003-022-03643-y |
| Late exercise (high-strain, <4h): 36-min sleep delay | Leota et al. 2025, Nature Communications | https://www.nature.com/articles/s41467-025-58271-x |
| Magnesium threonate improves deep sleep (Oura) | Hausenblas et al. 2024, Sleep Medicine: X | https://pmc.ncbi.nlm.nih.gov/articles/PMC11381753/ |
| L-Theanine + Mg: GABA receptors, delta waves, sleep latency | Frontiers in Nutrition 2022 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9017334/ |
| Chamomile/apigenin: 9/10 trials effective for anxiety | Systematic review, CNR 2024 | https://e-cnr.org/DOIx.php?id=10.7762%2Fcnr.2024.13.2.139 |
| Pre-sleep 40g casein: 22–37% higher overnight MPS | van Loon lab, GSSI 2022 | https://www.gssiweb.org/research/article/resistance-exercise-augments-postprandial-overnight-muscle-protein-synthesis-rates |
| Sleep optimization → 1.7kg lean mass gained, 1.8kg fat lost | Jåbekk et al. (Henselmans citation) | https://mennohenselmans.com/these-are-the-top-2-underrated-factors-killing-your-gains/ |
| Whoop HRV/sleep validated in collegiate athletes | UConn / Korey Stringer Institute | https://www.whoop.com/us/en/thelocker/study-rhr-hrv-sleep-collegiate-athletes/ |
| High-strain exercise <4h of bed: Whoop dose-response data | Whoop internal + Leota study | https://www.whoop.com/us/en/thelocker/fact-or-fiction-does-exercise-close-to-bedtime-harm-sleep-quality/ |

---

## APPENDIX: VARIABLE DICTIONARY (For Backend Implementation)

```python
# === SLEEP TRACKING VARIABLES ===
wake_time                   # HH:MM string
wake_time_target            # HH:MM string (user-set)
wake_time_deviation_min     # abs(wake_time - wake_time_target) in minutes
wake_time_sd_7d             # standard deviation of wake times over 7 days (minutes)

bedtime                     # HH:MM string
bedtime_target              # HH:MM string
bedtime_deviation_min       # abs(bedtime - bedtime_target) in minutes
bedtime_sd_7d               # SD of bedtimes over 7 days

sleep_onset                 # HH:MM (when user actually fell asleep per Whoop)
sleep_duration_hours        # float
sleep_performance_pct       # Whoop metric: 0–100
sws_minutes                 # minutes in slow-wave sleep
rem_minutes                 # minutes in REM
sleep_latency_min           # minutes to fall asleep

hrv_ms                      # nightly HRV (ms)
hrv_7d_avg                  # 7-day rolling average HRV
hrv_baseline                # established during first 14 days onboarding
rhr_bpm                     # nocturnal resting heart rate
recovery_score_pct          # Whoop recovery score: 0–100

# === HABITS TRACKING VARIABLES ===
morning_light_done          # bool
morning_light_minutes       # int
morning_light_timing_min    # minutes after wake
caffeine_last_time          # HH:MM
caffeine_last_hours_before_bed  # float
caffeine_cutoff_met         # bool
evening_lights_dimmed       # bool (after 21:00)
bedroom_temp_celsius        # float
exercise_end_time           # HH:MM
exercise_strain             # enum: light/moderate/high/maximal
exercise_cutoff_met         # bool
alcohol_last_drink_hours_before_bed  # float
pre_sleep_protein_done      # bool (training days only)
warm_shower_timing_min      # minutes before bed (if taken)

# === SUPPLEMENT VARIABLES ===
magnesium_taken             # bool
theanine_taken              # bool
apigenin_taken              # bool
supplement_phase_active     # enum: none/magnesium/theanine/apigenin/combo

# === COACHING STATE VARIABLES ===
active_habit_phase          # int: 1–5
habits_in_phase             # list of habit identifiers
habit_compliance_7d         # dict: {habit_id: compliance_rate (0-1)}
last_new_habit_introduced   # date
days_since_last_new_habit   # int
sleep_hygiene_score         # float: 0–10 (daily)
sleep_hygiene_score_7d_avg  # float
user_in_caloric_deficit     # bool (HIGH importance multiplier)
user_training_phase         # enum: bulk/cut/maintain/recomp
```

---

*End of Track 6: Sleep Hygiene Protocols*  
*Document prepared for Milo AI coaching system backend logic*
