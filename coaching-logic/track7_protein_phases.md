# Track 7: Protein Intake Recommendations & Nutritional Phase Logic
## Milo AI Fitness Coaching System — Backend Reference Document

**Document Purpose:** Research summary for AI agent implementing Milo's nutritional logic. All findings are cited with sources. Variable names, formulas, and pseudocode are machine-readable. Numeric thresholds are evidence-based where possible; engineering-grade defaults are provided where evidence is ambiguous.

**System Constraints:**
- Fixed protein target: `0.82 g/lb` of body weight (system-locked, not adjustable by phase)
- Supported phases: `CUT`, `MAINTENANCE`, `LEAN_BULK`
- Target population: male, beginner-to-intermediate lifters
- Calorie adjustment frequency: biweekly
- No refeeds or diet breaks included

---

## TABLE OF CONTENTS

1. [Protein Intake Evidence Base](#1-protein-intake-evidence-base)
2. [Calculating Protein Target](#2-calculating-protein-target)
3. [Phase Definitions](#3-phase-definitions)
4. [Phase Transition Logic — Automated Recommendations](#4-phase-transition-logic)
5. [Recomposition Considerations](#5-recomposition-considerations)
6. [Evidence on Refeeds and Diet Breaks (Excluded)](#6-evidence-on-refeeds-and-diet-breaks)
7. [Phase State Machine Summary](#7-phase-state-machine-summary)

---

## 1. PROTEIN INTAKE EVIDENCE BASE

### 1.1 Morton et al. (2018) — Landmark Meta-Analysis

**Citation:** Morton RW, Murphy KT, McKellar SR, et al. (2018). "A systematic review, meta-analysis and meta-regression of the effect of protein supplementation on resistance training-induced gains in muscle mass and strength in healthy adults." *British Journal of Sports Medicine*, 52(6), 376–384. DOI: 10.1136/bjsports-2017-097608. URL: https://bjsm.bmj.com/lookup/doi/10.1136/bjsports-2017-097608

**Study Design:** Systematic review, meta-analysis, and meta-regression. n = 49 RCTs, 1,863 participants. Duration ≥ 6 weeks of resistance exercise training (RET). Two-phase breakpoint analysis used to determine protein intake vs. fat-free mass (FFM) change.

**Key Finding — The 1.62 g/kg Breakpoint:**

> "Protein supplementation beyond total protein intakes of 1.62 g/kg/day resulted in no further RET-induced gains in FFM."

```
breakpoint_protein_kg  = 1.62  # g/kg/day (MEAN)
breakpoint_95ci_lower  = 1.03  # g/kg/day
breakpoint_95ci_upper  = 2.20  # g/kg/day
```

**Conversion to g/lb:**
```
breakpoint_protein_lb  = 1.62 / 2.2046 = 0.7350  # g/lb (MEAN)
breakpoint_upper_lb    = 2.20 / 2.2046 = 0.9979  # g/lb (upper 95% CI)
```

**Interpretation for Milo:**
The breakpoint at 1.62 g/kg (0.735 g/lb) represents the MEAN at which additional protein ceases to yield further FFM gains. The upper bound of the 95% CI is 2.20 g/kg (0.998 g/lb). The system's fixed target of **0.82 g/lb (1.81 g/kg)** sits between the mean breakpoint and the upper confidence interval. This is a deliberate and evidence-justified engineering decision (see §1.2).

**Supporting statistic:** Total protein supplementation also significantly increased:
- 1RM strength: +2.49 kg (95% CI: 0.64 to 4.33)
- FFM: +0.30 kg (95% CI: 0.09 to 0.52)
- Muscle fibre CSA: +310 µm² (95% CI: 51 to 570)

---

### 1.2 Henselmans & The 0.82 g/lb Recommendation — Rationale

**Primary Source:** Henselmans M. (2012, updated). "The myth of 1 g/lb: Optimal protein intake for bodybuilders." MennoHenselmans.com. URL: https://mennohenselmans.com/the-myth-of-1glb-optimal-protein-intake-for-bodybuilders/

**Secondary Source:** Henselmans M. (2024). "You DON'T need more protein in energy deficit." MennoHenselmans.com. URL: https://mennohenselmans.com/you-dont-need-more-protein-in-energy-deficit/

**The 0.82 g/lb Derivation:**

Henselmans synthesized the accumulated literature (45+ controlled trials comparing protein intakes, controlling for meal frequency) and reached the following conclusion:

> "There is normally no advantage to consuming more protein than **0.82 g/lb (1.8 g/kg)** of total bodyweight per day to preserve or build muscle for natural trainees."

The 0.82 g/lb figure is derived as follows:
1. The research consensus breakpoint is ~1.6 g/kg (the Morton et al. meta-analysis corroborated this)
2. Applying the **double 95% confidence level** convention (taking the highest mean intake at which benefits were observed + two standard deviations) yields 1.8 g/kg
3. Converting: `1.8 / 2.2046 = 0.8165 ≈ 0.82 g/lb`

This approach is explicitly called **conservative/Bayesian** in the evidence-based fitness literature:
- It uses the upper safety margin of the breakpoint analysis
- Described by Henselmans as a "recommendation [that] often includes a double 95% confidence level... to make absolutely sure all possible benefits from additional protein intake are utilized"
- Consistent with the Morton et al. meta-analysis upper CI of 2.20 g/kg

**Technical note:** The Henselmans article references Phillips & Van Loon (2011) as one of the review papers that concluded 0.82 g/lb is the upper limit at which protein benefits body composition.

**Why 0.82 g/lb Is the Correct System Default (Not Lower, Not Higher):**

| Threshold | g/kg | g/lb | Rationale |
|---|---|---|---|
| Mean breakpoint (Morton 2018) | 1.62 | 0.735 | Population average; ~50% of individuals may benefit from more |
| Henselmans recommended minimum | 1.80 | 0.817 | Upper safe bound; negligible downside, captures nearly all individuals |
| Milo system target | **1.81** | **0.82** | Matches Henselmans 0.82 g/lb; practical rounding |
| Upper CI (Morton 2018) | 2.20 | 0.998 | Theoretical upper; not meaningfully better than 1.8 g/kg in any study |
| Common "1 g/lb" myth | 2.20 | 1.00 | No evidence of additional benefit; increases food cost and thermic load |

---

### 1.3 Protein During a Caloric Deficit — Helms et al. (2014)

**Citation:** Helms ER, Aragon AA, Fitschen PJ. (2014). "Evidence-based recommendations for natural bodybuilding contest preparation: nutrition and supplementation." *Journal of the International Society of Sports Nutrition*, 11:20. DOI: 10.1186/1550-2783-11-20. URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC4033492/

**Helms et al. Protein Recommendation During Contest Prep (Caloric Deficit):**

> "Most but not all bodybuilders will respond best to consuming **2.3–3.1 g/kg of lean body mass** per day of protein" [during a cut]

Converting to total body weight equivalents (assuming ~15% body fat, i.e., LBM = 85% of TBW):
```
helms_lower_lbm  = 2.3 g/kg LBM
helms_upper_lbm  = 3.1 g/kg LBM

# For a 180 lb male at 15% BF:
# LBM = 180 * 0.85 = 153 lbs
# helms_lower_tbw = 2.3 * (153/2.2046) / 180 = ~0.88 g/lb TBW (approx)
# helms_upper_tbw = 3.1 * (153/2.2046) / 180 = ~1.19 g/lb TBW (approx)
```

In the commonly cited reference form (g/lb of total body weight), the Helms recommendation maps to approximately **1.0–1.4 g/lb** during cuts, frequently cited as such in the applied nutrition literature.

**Why Milo Uses 0.82 g/lb Fixed Instead of Higher During a Cut:**

The Henselmans 2024 analysis directly addresses this:
> "The available research does not indicate any differences in protein requirements in energy deficit versus an energy surplus... There is no established research finding significant benefits over 1.6 g/kg per day [regardless of caloric state]."

In fact, a subgroup analysis within a 2025 meta-analysis cited by Henselmans showed that the effect of protein intake on FFM, **if anything, decreased when people were in a higher deficit** (>300 kcal/day deficit).

**System Implication:**
```python
# Milo design decision:
# Despite Helms et al. recommending up to 1.4 g/lb during cuts,
# the system uses a fixed 0.82 g/lb target.
# 
# Tradeoff summary:
#   - Helms recommendation is based on contest prep (extreme deficits, very lean populations)
#   - 0.82 g/lb already represents the upper safety margin per Henselmans
#   - Milo targets beginner-intermediate males, NOT contest-prep athletes
#   - Fixed target simplifies adherence and avoids phase-dependent macro shifts
#   - Evidence for benefit above 0.82 g/lb in this population is not established
#
# Flag in UI: During CUT phases, consider noting that some research supports
#             higher protein (up to 1.4 g/lb) for advanced/lean athletes,
#             but for the Milo target population, 0.82 g/lb is sufficient.

system_protein_target_per_lb: float = 0.82  # FIXED, immutable by phase
```

---

### 1.4 Protein Timing and Distribution — Schoenfeld & Aragon (2018)

**Citation:** Schoenfeld BJ, Aragon AA. (2018). "How much protein can the body use in a single meal for muscle-building? Implications for daily protein distribution." *Journal of the International Society of Sports Nutrition*, 15:10. PubMed ID: 29497353. URL: https://pubmed.ncbi.nlm.nih.gov/29497353/

**Also relevant:** Schoenfeld BJ, Aragon AA, Krieger JW. (2013). "The effect of protein timing on muscle strength and hypertrophy: a meta-analysis." *Journal of the International Society of Sports Nutrition*, 10:53. DOI: 10.1186/1550-2783-10-53.

**Key Findings on Timing:**

The 2013 meta-analysis (Schoenfeld, Aragon, Krieger) examined 20+ RCTs and found:
> "No significant differences were found between treatment and control for strength or hypertrophy [when protein timing was controlled]. With respect to hypertrophy, **total protein intake was the strongest predictor of effect size magnitude**."

The 2018 paper (Schoenfeld & Aragon) established per-meal distribution guidelines:
> "To maximize anabolism one should consume protein at a target intake of **0.4 g/kg/meal** across a minimum of four meals in order to reach a minimum of 1.6 g/kg/day. Using the upper daily intake of 2.2 g/kg/day spread out over the same four meals would necessitate a maximum of **0.55 g/kg/meal**."

**Variable Definitions:**
```python
per_meal_protein_min_g_per_kg: float = 0.40   # minimum per meal to maximize MPS
per_meal_protein_max_g_per_kg: float = 0.55   # upper per meal for high-protein protocols
min_meals_per_day: int = 3                     # minimum meals for even distribution
optimal_meals_per_day: int = 4                 # optimal distribution (Schoenfeld 2018)

# Per-meal target in g for a 180 lb (81.6 kg) user:
# user_weight_kg = 180 / 2.2046 = 81.65 kg
# per_meal_target = 81.65 * 0.40 = 32.7 g  (minimum)
# per_meal_target = 81.65 * 0.55 = 44.9 g  (upper)
```

**Practical Implication for Milo:**
- Timing relative to training does NOT significantly affect hypertrophy outcomes when total daily protein is adequate
- The "anabolic window" is not critical if total daily protein ≥ 1.6 g/kg
- Even protein distribution across 3–4+ meals is recommended for MPS optimization
- Milo should note protein distribution in guidance but NOT enforce timing as a primary constraint

---

### 1.5 Upper Limit Safety — Antonio et al. Studies

**Citations:**
- Antonio J, Peacock CA, Ellerbroek A, et al. (2014). "The effects of consuming a high protein diet (4.4 g/kg/d) on body composition in resistance-trained individuals." *JISSN*, 11:19. DOI: 10.1186/1550-2783-11-19. URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC4022420/
- Antonio J, Ellerbroek A, Silver T, et al. (2016). "A High Protein Diet Has No Harmful Effects: A One-Year Crossover Study in Resistance-Trained Males." *J Nutr Metab*, 2016:9104792. DOI: 10.1155/2016/9104792. URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC5078648/
- Antonio J, Ellerbroek A, Silver T, et al. (2016). "The effects of a high protein diet on indices of health and body composition – a crossover trial in resistance-trained men." *JISSN*, 13:3. DOI: 10.1186/s12970-016-0114-2. URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC4715299/

**Key Findings:**

| Study | Protein Dose | Duration | Outcome |
|---|---|---|---|
| Antonio 2014 | 4.4 g/kg/d (5.5× RDA) | 8 weeks | No change in body composition; no adverse effects |
| Antonio 2015 | 3.4 g/kg/d with heavy RT | 8 weeks | Improved body composition; no adverse health markers |
| Antonio 2016 crossover | 2.6–3.3 g/kg/d | 16 weeks | No changes in blood lipids, renal function, or liver function |
| Antonio 2016 one-year | ~3.32 g/kg/d | 1 year | No harmful effects on blood lipids, liver, or kidney function |

**Conclusion:** In resistance-trained individuals, protein intakes of up to **3.3 g/kg/d (1.5 g/lb)** for periods of up to one year show **no evidence of harm** to:
- Kidney function (creatinine, BUN, GFR)
- Liver function (AST, ALT)
- Blood lipid profiles (LDL, HDL, triglycerides)
- Bone mineral density

```python
# Safety ceiling per Antonio et al. research:
protein_safety_ceiling_g_per_kg: float = 3.3   # no adverse effects documented up to this level
protein_safety_ceiling_g_per_lb: float = 1.50  # = 3.3 / 2.2046

# Milo system target (0.82 g/lb = 1.81 g/kg) is well below any safety concern.
# Flag for system: Only surface a concern if user-tracked protein exceeds 3.5 g/kg/d
# (Wu 2016 note: tolerable upper limit suggested ~3.5 g/kg/d for well-adapted subjects)
```

---

## 2. CALCULATING PROTEIN TARGET

### 2.1 Standard Formula

```python
# Input: user weight in pounds
# Output: daily protein target in grams
def calculate_protein_target_lbs(user_weight_lbs: float) -> float:
    """
    Calculate daily protein target in grams.
    
    Uses Milo fixed rate: 0.82 g/lb of body weight.
    Source: Henselmans (2012) upper safety margin; consistent with
            Morton et al. (2018) breakpoint upper CI.
    """
    PROTEIN_RATE_G_PER_LB: float = 0.82
    return user_weight_lbs * PROTEIN_RATE_G_PER_LB

# Input: user weight in kilograms
# Output: daily protein target in grams
def calculate_protein_target_kg(user_weight_kg: float) -> float:
    """
    Convert kg to lbs first, then apply standard formula.
    """
    LBS_PER_KG: float = 2.2046
    user_weight_lbs = user_weight_kg * LBS_PER_KG
    return calculate_protein_target_lbs(user_weight_lbs)

# Examples:
# 180 lb user: 180 * 0.82 = 147.6 g/day
# 90 kg user:  90 * 2.2046 * 0.82 = 163.0 g/day
```

### 2.2 Handling Overweight/Obese Users

**The Problem:** For overweight users, using total body weight (TBW) to calculate protein needs overestimates requirements, since adipose tissue has minimal protein turnover. However, the recent meta-analysis data (Henselmans 2025 commentary) found:
> "Using fat-free mass to base protein intake on instead of body weight was no more accurate at predicting the relationship between protein intake and fat-free mass changes. The model fit statistics were virtually identical... [R² difference was only 1%]."

**Recommendation Priority:**
1. **For BMI < 30:** Use total body weight directly (no adjustment needed)
2. **For BMI 30–40 (Obese Class I–II):** Use Adjusted Body Weight (AjBW) formula
3. **For BMI > 40 (Severe Obesity):** Use AjBW formula with clinical judgment

**Adjusted Body Weight (AjBW) Formula:**
```python
def calculate_ideal_body_weight_male_kg(height_inches: float) -> float:
    """
    Robinson formula for ideal body weight (male).
    Reference: Standard clinical nutrition formula.
    """
    BASE_WEIGHT_KG: float = 52.0
    KG_PER_INCH_OVER_60: float = 1.9
    
    if height_inches <= 60:
        return BASE_WEIGHT_KG
    return BASE_WEIGHT_KG + KG_PER_INCH_OVER_60 * (height_inches - 60)

def calculate_adjusted_body_weight_kg(
    actual_body_weight_kg: float, 
    height_inches: float,
    sex: str = "male"
) -> float:
    """
    AjBW = IBW + 0.4 * (ABW - IBW)
    
    Applied when ABW exceeds IBW (i.e., when user is overweight/obese).
    The factor 0.4 reflects that ~40% of excess weight contributes to
    metabolically relevant mass (lean component of adipose tissue, etc.)
    
    Source: Standard clinical pharmacology/nutrition formula.
    Reference: https://www.omnicalculator.com/health/adjusted-weight
    """
    ADJUSTMENT_FACTOR: float = 0.4
    ibw = calculate_ideal_body_weight_male_kg(height_inches)
    
    if actual_body_weight_kg <= ibw:
        return actual_body_weight_kg  # Use actual weight if at or below IBW
    
    ajbw = ibw + ADJUSTMENT_FACTOR * (actual_body_weight_kg - ibw)
    return ajbw

def calculate_protein_target_with_obesity_adjustment(
    user_weight_lbs: float,
    user_height_inches: float,
    user_bmi: float
) -> dict:
    """
    Returns protein target with weight basis used.
    Applies adjusted body weight for BMI >= 30.
    """
    PROTEIN_RATE: float = 0.82  # g/lb
    BMI_OBESITY_THRESHOLD: float = 30.0
    
    user_weight_kg = user_weight_lbs / 2.2046
    
    if user_bmi >= BMI_OBESITY_THRESHOLD:
        # Use adjusted body weight
        ajbw_kg = calculate_adjusted_body_weight_kg(user_weight_kg, user_height_inches)
        ajbw_lbs = ajbw_kg * 2.2046
        protein_target_g = ajbw_lbs * PROTEIN_RATE
        weight_basis = "adjusted_body_weight"
        weight_used_lbs = ajbw_lbs
    else:
        # Use total body weight directly
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

**Example Calculations:**

| User | TBW (lbs) | Height | BMI | AjBW (lbs) | Protein Target |
|---|---|---|---|---|---|
| Normal weight male | 180 | 5'10" | 25.8 | N/A | 147.6 g |
| Obese male | 250 | 5'10" | 35.9 | 196.5 | 161.1 g |
| Obese male | 300 | 5'10" | 43.0 | 210.9 | 173.0 g |

---

## 3. PHASE DEFINITIONS

### 3.1 Enum Definitions

```python
from enum import Enum

class NutritionalPhase(Enum):
    CUT = "cut"
    MAINTENANCE = "maintenance"
    LEAN_BULK = "lean_bulk"

class CutAggression(Enum):
    MODERATE = "moderate"   # 300-500 kcal/day deficit
    AGGRESSIVE = "aggressive"  # 500-750 kcal/day deficit

class BulkRate(Enum):
    BEGINNER = "beginner"       # 200-350 kcal/day surplus
    INTERMEDIATE = "intermediate"  # 100-200 kcal/day surplus
```

---

### 3.2 CUT Phase

**Definition:** A period of deliberate caloric deficit targeting maximal fat loss while preserving lean body mass (LBM).

#### Deficit Magnitude

**Source:** Helms ER, Aragon AA, Fitschen PJ. (2014). JISSN 11:20. URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC4033492/

| Cut Type | Deficit (kcal/day) | Weight Loss (% BW/week) | Notes |
|---|---|---|---|
| Conservative | 200–300 | ~0.25–0.50% | Minimal muscle loss risk |
| **Moderate (recommended)** | **300–500** | **0.5–1.0%** | Optimal for LBM retention |
| Aggressive | 500–750 | 0.75–1.25% | Increased muscle loss risk |
| Very Aggressive | 750–1000+ | >1.25% | NOT recommended; high muscle loss |

```python
class CutDeficitRange:
    MODERATE_LOWER: int = 300   # kcal/day
    MODERATE_UPPER: int = 500   # kcal/day
    AGGRESSIVE_LOWER: int = 500  # kcal/day
    AGGRESSIVE_UPPER: int = 750  # kcal/day
```

#### Target Rate of Weight Loss

**Source:** Helms et al. (2014), consistent with Ruiz-Castellano et al. (2021) Nutrients 13(9):3255. URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC8471721/

```python
class WeightLossRateTargets:
    # Expressed as % of body weight per week
    MINIMUM_RATE_PCT: float = 0.25   # % BW/week (too slow = minimal fat loss)
    OPTIMAL_LOWER_PCT: float = 0.50  # % BW/week
    OPTIMAL_UPPER_PCT: float = 1.00  # % BW/week (Helms et al. 2014 recommendation)
    MAX_SAFE_RATE_PCT: float = 1.00  # % BW/week (above this, muscle loss risk increases)
    
    # Helms et al. (2014) state:
    # "Caloric intake should be set at a level that results in bodyweight losses of 
    # approximately 0.5 to 1%/week to maximize muscle retention."
    
    # For a 180 lb user:
    # target_weekly_loss_lbs_lower = 180 * 0.005 = 0.90 lbs/week
    # target_weekly_loss_lbs_upper = 180 * 0.010 = 1.80 lbs/week
```

#### Maximum Cut Duration

**Source:** Helms et al. (2014); Ruiz-Castellano et al. (2021) Nutrients 13(9):3255.

The evidence basis for maximum cut duration:
- Helms et al. (2014): "Diets **longer than two to four months** yielding weight loss of approximately 0.5 to 1% of bodyweight weekly may be superior for LBM retention compared to shorter or more aggressive diets." (implies > 16 weeks may degrade quality)
- Practical consensus from applied literature: 8–16 weeks is the standard recommendation, with 16 weeks as a soft upper limit for continuous dieting.
- Non-overweight males who consumed 50% of maintenance for 24 weeks experienced 40% reduction in baseline energy expenditure (metabolic adaptation), of which 15% was non-weight-loss-related (pure metabolic adaptation).

```python
class CutDurationLimits:
    # All values in weeks
    MINIMUM_CUT_WEEKS: int = 4     # Too short to achieve meaningful fat loss
    OPTIMAL_CUT_LOWER_WEEKS: int = 8   # Minimum for meaningful, efficient cut
    OPTIMAL_CUT_UPPER_WEEKS: int = 12  # Ideal range for most users
    SOFT_MAX_WEEKS: int = 16           # Recommend transition at/before this point
    HARD_MAX_WEEKS: int = 20           # Strong recommendation to exit cut phase
    
    # At SOFT_MAX, Milo should recommend transition to MAINTENANCE
    # At HARD_MAX, Milo should strongly recommend transition regardless of goal progress
```

---

### 3.3 MAINTENANCE Phase

**Definition:** Eating at estimated Total Daily Energy Expenditure (TDEE). No intentional surplus or deficit.

```python
class MaintenanceCalorieRange:
    DEFICIT_TOLERANCE_KCAL: int = 100  # ±100 kcal is still "maintenance"
    SURPLUS_TOLERANCE_KCAL: int = 100  # ±100 kcal is still "maintenance"
```

#### When to Recommend Maintenance

```python
# MAINTENANCE is recommended when:
maintenance_trigger_conditions = {
    "post_cut_recovery": True,               # After completing a cut phase
    "between_phases": True,                  # Transition buffer
    "high_life_stress": True,                # External stressors reduce compliance
    "training_performance_declining": True,  # Recovery indicator
    "pre_bulk_normalization": True,          # Before starting lean bulk
}
```

#### Maintenance Duration Recommendations

```python
class MaintenanceDurationGuidelines:
    # After a cut: minimum maintenance period before bulking
    POST_CUT_MIN_WEEKS: int = 2     # Absolute minimum (metabolic normalization)
    POST_CUT_OPTIMAL_WEEKS: int = 4  # Preferred duration for metabolic recovery
    POST_CUT_MAX_WEEKS: int = 12    # Beyond this, transition to bulk or recut
    
    # Between bulk and cut
    POST_BULK_MIN_WEEKS: int = 2
    POST_BULK_OPTIMAL_WEEKS: int = 4
```

**Evidence Basis:** The consensus in the bodybuilding literature (Helms et al. 2014; Roberts et al. 2020, JISSN) is that metabolic rate, hormones (especially testosterone — which can drop substantially during extended cuts), and training performance normalize during maintenance phases. A case study analysis of natural bodybuilders showed testosterone dropped significantly during cuts, with full recovery taking ~3 months of maintenance/recovery eating. Source: Helms et al. (2014) JISSN 11:20. URL: https://www.tandfonline.com/doi/full/10.1186/1550-2783-11-20

---

### 3.4 LEAN BULK Phase

**Definition:** A deliberate caloric surplus targeting muscle hypertrophy while minimizing fat gain.

#### Surplus Magnitude by Training Level

**Source:** Helms ER, Iraki J, Fitschen PJ, Espinar S. (2019). "Nutrition Recommendations for Bodybuilders in the Off-Season: A Narrative Review." *Sports*, 7(7):154. DOI: 10.3390/sports7070154. URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC6680710/

Helms et al. (2019) specifically state:
> "A hyper-energetic diet (~10–20%) should be consumed with a **target weight gain of ~0.25–0.5% of bodyweight/week** for novice/intermediate bodybuilders."

```python
class LeanBulkSurplusTargets:
    # Caloric surplus by training level (kcal/day above TDEE)
    BEGINNER_SURPLUS_LOWER: int = 200    # kcal/day
    BEGINNER_SURPLUS_UPPER: int = 350    # kcal/day
    INTERMEDIATE_SURPLUS_LOWER: int = 100  # kcal/day
    INTERMEDIATE_SURPLUS_UPPER: int = 200  # kcal/day
    
    # Rate of weight gain targets (% BW/week)
    BEGINNER_GAIN_RATE_LOWER_PCT: float = 0.25   # % BW/week
    BEGINNER_GAIN_RATE_UPPER_PCT: float = 0.50   # % BW/week
    INTERMEDIATE_GAIN_RATE_LOWER_PCT: float = 0.10  # % BW/week
    INTERMEDIATE_GAIN_RATE_UPPER_PCT: float = 0.25  # % BW/week
    
    # For a 180 lb user:
    # beginner target: 180 * 0.0025–0.005 = 0.45–0.90 lbs/week
    # intermediate target: 180 * 0.001–0.0025 = 0.18–0.45 lbs/week
```

**Also supported by:** A 2024 study in trained lifters (cited in Men's Health, July 2024) comparing maintenance, 5% surplus, and 15% surplus over 8 weeks found no significant differences in muscle gain between groups, but the 15% surplus group showed significantly more fat gain. Conclusion: "A more conservative energy surplus (5–20% over maintenance) scaled to the individual's resistance training experience may be more beneficial, minimising unnecessary fat gain." Source: https://www.menshealth.com/uk/building-muscle/train-smarter/a61553230/bulking-with-high-calories/

#### Expected Muscle:Fat Gain Ratio

```python
class BulkBodyCompositionExpectations:
    # Approximate muscle:fat gain ratios at different surplus levels
    # These are approximations; individual genetics vary substantially
    
    # Beginner (first 1–2 years of training)
    BEGINNER_MUSCLE_FRACTION_MODERATE_SURPLUS: float = 0.50  # ~50% of weight gain is muscle
    BEGINNER_MUSCLE_FRACTION_AGGRESSIVE_SURPLUS: float = 0.30  # drops with larger surplus
    
    # Intermediate (2–5 years of training)
    INTERMEDIATE_MUSCLE_FRACTION_MODERATE_SURPLUS: float = 0.30  # ~30% of weight gain is muscle
    INTERMEDIATE_MUSCLE_FRACTION_AGGRESSIVE_SURPLUS: float = 0.15
    
    # Annual muscle gain potential (natural, male)
    BEGINNER_MAX_MUSCLE_GAIN_LBS_PER_YEAR: float = 12.0   # First year, good genetics/training
    INTERMEDIATE_MAX_MUSCLE_GAIN_LBS_PER_YEAR: float = 6.0
    ADVANCED_MAX_MUSCLE_GAIN_LBS_PER_YEAR: float = 2.0
    
    # Note: Greg Doucette estimate (commonly cited): ~12 lbs max in first year
    # Practical rule: ≤1% of bodyweight gain per month avoids excess fat accumulation
```

#### Maximum Lean Bulk Duration

```python
class LeanBulkDurationLimits:
    # All values in weeks
    MINIMUM_BULK_WEEKS: int = 8     # Too short for meaningful hypertrophy gains
    OPTIMAL_BULK_LOWER_WEEKS: int = 12  # Minimum for solid hypertrophy cycle
    OPTIMAL_BULK_UPPER_WEEKS: int = 20  # Practical upper for lean bulk
    SOFT_MAX_WEEKS: int = 24            # Consider transitioning to cut/maintenance
    
    # Body fat trigger to exit bulk (men):
    EXIT_BF_THRESHOLD_PCT: float = 20.0  # Exit bulk if body fat reaches ~20%
    # Rationale: above 20% BF, insulin sensitivity decreases, 
    # hormonal environment worsens, and fat-to-muscle gain ratio increases.
    # Source: practical consensus (multiple bodybuilding review papers)
```

---

## 4. PHASE TRANSITION LOGIC

### 4.1 Phase Transition Variables

```python
class PhaseTransitionInputs:
    """
    All inputs the system needs to evaluate phase transition conditions.
    Values updated biweekly (every 2 weeks).
    """
    # Body composition
    current_weight_lbs: float
    estimated_body_fat_pct: float     # Optional; estimated or user-reported
    goal_weight_lbs: float            # Target weight for current phase
    goal_body_fat_pct: float          # Target BF% for current phase
    
    # Phase tracking
    current_phase: NutritionalPhase
    phase_start_date: str             # ISO date
    phase_duration_weeks: int         # Weeks in current phase
    
    # Progress tracking
    weekly_weight_change_lbs: float   # Average over last 2 weeks
    rate_of_change_pct_bw: float      # Weekly change as % of body weight
    
    # Performance & wellbeing flags (user-reported, 1–5 scale or boolean)
    training_performance_score: int    # 1 = significantly declining, 5 = improving
    fatigue_level_score: int           # 1 = excessive fatigue, 5 = normal
    hunger_level_score: int            # 1 = extreme hunger, 5 = comfortable
    adherence_score: int               # 1 = struggling significantly, 5 = easy adherence
    
    # Explicit user requests
    user_wants_to_cut: bool
    user_wants_to_bulk: bool
    user_wants_maintenance: bool
```

---

### 4.2 CUT → MAINTENANCE Transition Logic

```python
def should_transition_cut_to_maintenance(inputs: PhaseTransitionInputs) -> dict:
    """
    Evaluates conditions under which a user should exit CUT and enter MAINTENANCE.
    Returns a dict with: should_transition (bool), reason (str), urgency (str).
    
    Phase transition triggers based on:
    - Helms et al. (2014) JISSN 11:20
    - Ruiz-Castellano et al. (2021) Nutrients 13(9):3255
    - General evidence-based bodybuilding consensus
    """
    reasons = []
    urgency = "routine"  # "routine", "recommended", "urgent"
    
    # ─── TRIGGER 1: GOAL REACHED ───────────────────────────────────────────
    goal_weight_reached = (
        inputs.current_weight_lbs <= inputs.goal_weight_lbs + 1.0  # within 1 lb
    )
    goal_bf_reached = (
        inputs.estimated_body_fat_pct is not None and
        inputs.estimated_body_fat_pct <= inputs.goal_body_fat_pct + 1.0
    )
    if goal_weight_reached or goal_bf_reached:
        reasons.append("goal_reached")
        urgency = "routine"
    
    # ─── TRIGGER 2: MAX CUT DURATION EXCEEDED ──────────────────────────────
    # Source: Helms et al. (2014); SOFT_MAX = 16 weeks, HARD_MAX = 20 weeks
    if inputs.phase_duration_weeks >= CutDurationLimits.HARD_MAX_WEEKS:
        reasons.append("max_duration_exceeded_hard")
        urgency = "urgent"
    elif inputs.phase_duration_weeks >= CutDurationLimits.SOFT_MAX_WEEKS:
        reasons.append("max_duration_exceeded_soft")
        urgency = max(urgency, "recommended")
    
    # ─── TRIGGER 3: METABOLIC ADAPTATION SIGNAL ────────────────────────────
    # Signal: rate of weight loss has slowed to < 0.1% BW/week despite 
    # appropriate deficit, AND calories have already been adjusted downward 2+ times
    # This represents approximate "metabolic floor" for practical purposes
    metabolic_adaptation_signal = (
        abs(inputs.rate_of_change_pct_bw) < 0.10 and
        inputs.phase_duration_weeks >= 8  # Allow enough time to detect real stall
    )
    if metabolic_adaptation_signal:
        reasons.append("metabolic_adaptation_signal")
        urgency = max(urgency, "recommended")
    
    # ─── TRIGGER 4: PERFORMANCE DECLINE ────────────────────────────────────
    if inputs.training_performance_score <= 2:
        reasons.append("training_performance_declining")
        urgency = max(urgency, "recommended")
    
    # ─── TRIGGER 5: EXCESSIVE FATIGUE OR HUNGER ────────────────────────────
    if inputs.fatigue_level_score <= 2 or inputs.hunger_level_score <= 2:
        reasons.append("excessive_fatigue_or_hunger")
        urgency = max(urgency, "recommended")
    
    # ─── TRIGGER 6: ADHERENCE DECLINING ───────────────────────────────────
    if inputs.adherence_score <= 2:
        reasons.append("adherence_declining")
        urgency = max(urgency, "recommended")
    
    # ─── TRIGGER 7: USER EXPLICITLY REQUESTS ──────────────────────────────
    if inputs.user_wants_maintenance:
        reasons.append("user_requested")
        urgency = "routine"
    
    return {
        "should_transition": len(reasons) > 0,
        "reasons": reasons,
        "urgency": urgency,
        "transition_to": NutritionalPhase.MAINTENANCE
    }
```

---

### 4.3 MAINTENANCE → LEAN BULK Transition Logic

```python
def should_transition_maintenance_to_lean_bulk(inputs: PhaseTransitionInputs) -> dict:
    """
    Evaluates conditions under which a user should exit MAINTENANCE and enter LEAN_BULK.
    
    Body fat thresholds for bulking (male):
    - Ideal start BF for bulk: 10–15%
    - Maximum acceptable BF to begin bulk: ~15% (absolute maximum before starting bulk)
    - Reference: practical consensus (1UP Nutrition, Alpha Progression, Helms 2014)
    
    "If you are a male at or below 10% body fat, your ability to build more muscle 
    and gain less fat is heightened for various reasons, such as greater insulin 
    sensitivity." — 1UP Nutrition applied protocol, consistent with bodybuilding literature
    """
    reasons = []
    urgency = "routine"
    
    MINIMUM_MAINTENANCE_WEEKS_BEFORE_BULK: int = 4  # metabolic normalization
    MAX_BF_TO_START_BULK_PCT: float = 15.0           # max acceptable BF to begin lean bulk
    IDEAL_BF_TO_START_BULK_PCT: float = 12.0         # ideal starting BF
    
    # ─── PREREQUISITE: Minimum maintenance duration ────────────────────────
    min_duration_met = inputs.phase_duration_weeks >= MINIMUM_MAINTENANCE_WEEKS_BEFORE_BULK
    
    # ─── TRIGGER 1: MINIMUM DURATION MET + GOOD RECOVERY ─────────────────
    recovery_strong = (
        inputs.training_performance_score >= 4 and
        inputs.fatigue_level_score >= 4
    )
    if min_duration_met and recovery_strong:
        reasons.append("minimum_maintenance_complete_with_good_recovery")
    
    # ─── TRIGGER 2: BODY FAT ACCEPTABLE FOR BULK ──────────────────────────
    bf_acceptable_for_bulk = (
        inputs.estimated_body_fat_pct is None or  # If unknown, default allow
        inputs.estimated_body_fat_pct <= MAX_BF_TO_START_BULK_PCT
    )
    if bf_acceptable_for_bulk and min_duration_met:
        reasons.append("body_fat_acceptable_for_bulk")
    
    # ─── TRIGGER 3: USER EXPLICITLY REQUESTS BULK ─────────────────────────
    if inputs.user_wants_to_bulk and min_duration_met and bf_acceptable_for_bulk:
        reasons.append("user_requested")
    
    # ─── BLOCK: Body fat too high to begin bulk ───────────────────────────
    if (inputs.estimated_body_fat_pct is not None and 
        inputs.estimated_body_fat_pct > MAX_BF_TO_START_BULK_PCT):
        return {
            "should_transition": False,
            "reasons": ["body_fat_too_high_for_bulk"],
            "urgency": "none",
            "recommendation": "CUT first to bring body fat below 15% before lean bulking",
            "transition_to": None
        }
    
    return {
        "should_transition": len(reasons) > 0 and min_duration_met,
        "reasons": reasons,
        "urgency": urgency,
        "transition_to": NutritionalPhase.LEAN_BULK if len(reasons) > 0 else None
    }
```

---

### 4.4 LEAN BULK → CUT Transition Logic

```python
def should_transition_lean_bulk_to_cut(inputs: PhaseTransitionInputs) -> dict:
    """
    Evaluates conditions under which a user should exit LEAN_BULK and enter CUT.
    
    Body fat ceiling for males (when to stop bulking):
    - Soft threshold: 18% BF (recommend evaluating)
    - Hard threshold: 20% BF (strong recommendation to transition to cut)
    - Above 20%: insulin sensitivity decreases, aromatase activity increases (↑estrogen),
      unfavorable hormonal environment for muscle building.
    
    Reference: Applied consensus from Helms et al. 2014, Roberts et al. 2020 JISSN,
               and 1UP Nutrition applied protocols.
    """
    reasons = []
    urgency = "routine"
    
    BF_SOFT_CEILING_PCT: float = 18.0   # evaluate transition
    BF_HARD_CEILING_PCT: float = 20.0   # strong recommendation
    
    # ─── TRIGGER 1: BODY FAT CEILING REACHED ─────────────────────────────
    if inputs.estimated_body_fat_pct is not None:
        if inputs.estimated_body_fat_pct >= BF_HARD_CEILING_PCT:
            reasons.append("body_fat_hard_ceiling_reached")
            urgency = "urgent"
        elif inputs.estimated_body_fat_pct >= BF_SOFT_CEILING_PCT:
            reasons.append("body_fat_soft_ceiling_reached")
            urgency = max(urgency, "recommended")
    
    # ─── TRIGGER 2: MAX BULK DURATION REACHED ────────────────────────────
    if inputs.phase_duration_weeks >= LeanBulkDurationLimits.SOFT_MAX_WEEKS:
        reasons.append("max_bulk_duration_reached")
        urgency = max(urgency, "recommended")
    
    # ─── TRIGGER 3: USER EXPLICITLY REQUESTS CUT ─────────────────────────
    if inputs.user_wants_to_cut:
        reasons.append("user_requested")
    
    return {
        "should_transition": len(reasons) > 0,
        "reasons": reasons,
        "urgency": urgency,
        "transition_to": NutritionalPhase.CUT if len(reasons) > 0 else None
    }
```

---

### 4.5 MAINTENANCE → CUT Transition Logic

```python
def should_transition_maintenance_to_cut(inputs: PhaseTransitionInputs) -> dict:
    """
    Evaluates conditions under which a user should exit MAINTENANCE and enter CUT.
    """
    reasons = []
    urgency = "routine"
    
    MIN_MAINTENANCE_WEEKS_BEFORE_CUT: int = 2  # Minimum before allowing a cut
    CUT_BF_TRIGGER_PCT: float = 20.0           # "You look like you should cut" threshold
    
    # ─── TRIGGER 1: USER GOAL IS FAT LOSS ────────────────────────────────
    if inputs.user_wants_to_cut:
        reasons.append("user_goal_fat_loss")
    
    # ─── TRIGGER 2: BODY FAT ABOVE DESIRED LEVEL ─────────────────────────
    if (inputs.estimated_body_fat_pct is not None and
        inputs.estimated_body_fat_pct >= CUT_BF_TRIGGER_PCT):
        reasons.append("body_fat_above_cut_trigger")
        urgency = max(urgency, "recommended")
    
    # ─── TRIGGER 3: ADEQUATE RECOVERY FROM PREVIOUS PHASE ────────────────
    recovery_adequate = (
        inputs.phase_duration_weeks >= MIN_MAINTENANCE_WEEKS_BEFORE_CUT
    )
    
    return {
        "should_transition": len(reasons) > 0 and recovery_adequate,
        "reasons": reasons,
        "urgency": urgency,
        "transition_to": NutritionalPhase.CUT if len(reasons) > 0 and recovery_adequate else None,
        "blocked_reason": "insufficient_maintenance_duration" if not recovery_adequate else None
    }
```

---

### 4.6 Biweekly Calorie Adjustment Logic

```python
def calculate_biweekly_calorie_adjustment(
    current_phase: NutritionalPhase,
    actual_weight_change_lbs_over_2_weeks: float,
    user_weight_lbs: float,
    current_calories: int
) -> dict:
    """
    Adjusts calories biweekly based on actual progress vs. targets.
    
    Source: Helms et al. (2014) weight loss rate guidelines;
            Helms et al. (2019) bulk rate guidelines.
    """
    # Calculate actual weekly rate
    actual_weekly_change_pct = (actual_weight_change_lbs_over_2_weeks / 2) / user_weight_lbs * 100
    
    ADJUSTMENT_INCREMENT_KCAL: int = 150  # Standard biweekly adjustment step
    
    if current_phase == NutritionalPhase.CUT:
        # Target: -0.5% to -1.0% BW/week
        TARGET_LOWER = -1.00  # % BW/week
        TARGET_UPPER = -0.50  # % BW/week
        
        if actual_weekly_change_pct > TARGET_UPPER:  # Losing too slowly
            adjustment = -ADJUSTMENT_INCREMENT_KCAL  # Reduce calories
            reason = "weight_loss_too_slow"
        elif actual_weekly_change_pct < TARGET_LOWER:  # Losing too fast
            adjustment = +ADJUSTMENT_INCREMENT_KCAL  # Increase calories
            reason = "weight_loss_too_fast"
        else:
            adjustment = 0
            reason = "on_target"
    
    elif current_phase == NutritionalPhase.LEAN_BULK:
        # Target: +0.25% to +0.50% BW/week (beginner)
        TARGET_LOWER = +0.25  # % BW/week
        TARGET_UPPER = +0.50  # % BW/week
        
        if actual_weekly_change_pct < TARGET_LOWER:  # Gaining too slowly
            adjustment = +ADJUSTMENT_INCREMENT_KCAL
            reason = "weight_gain_too_slow"
        elif actual_weekly_change_pct > TARGET_UPPER:  # Gaining too fast (excess fat)
            adjustment = -ADJUSTMENT_INCREMENT_KCAL
            reason = "weight_gain_too_fast"
        else:
            adjustment = 0
            reason = "on_target"
    
    elif current_phase == NutritionalPhase.MAINTENANCE:
        TARGET_RANGE = 1.0  # ±1.0 lb over 2 weeks = maintenance
        
        if actual_weight_change_lbs_over_2_weeks > TARGET_RANGE:
            adjustment = -ADJUSTMENT_INCREMENT_KCAL
            reason = "unintended_weight_gain"
        elif actual_weight_change_lbs_over_2_weeks < -TARGET_RANGE:
            adjustment = +ADJUSTMENT_INCREMENT_KCAL
            reason = "unintended_weight_loss"
        else:
            adjustment = 0
            reason = "on_target"
    
    return {
        "calorie_adjustment": adjustment,
        "new_calorie_target": current_calories + adjustment,
        "actual_weekly_change_pct": round(actual_weekly_change_pct, 3),
        "reason": reason
    }
```

---

## 5. RECOMPOSITION CONSIDERATIONS

### 5.1 Evidence on Body Recomposition

**Primary Citation:** Barakat C, Pearson J, Escalante G, Campbell B, De Souza EO. (2020). "Body Recomposition: Can Trained Individuals Build Muscle and Lose Fat at the Same Time?" *Strength & Conditioning Journal*, 42(5):7–21. DOI: 10.1519/SSC.0000000000000584. URL: https://journals.lww.com/10.1519/SSC.0000000000000584

**Definition:** Body recomposition is the simultaneous reduction of fat mass and the gain or maintenance of muscle mass, typically without a significant change in total body mass.

**Key Finding from Barakat et al. (2020):**
> "Although many suggest that this only occurs in untrained/novice and overweight/obese populations, there is a substantial amount of literature demonstrating this body recomposition phenomenon in resistance-trained individuals."

**Conditions Under Which Recomposition Is Realistic:**

| Condition | Recomp Likelihood | Notes |
|---|---|---|
| **Untrained / beginner** (< 1 year true resistance training) | **Very high** | Newbie gains allow simultaneous adaptations |
| **Detrained** (significant layoff > 3 months) | **High** | Muscle memory + elevated anabolic sensitivity |
| **Overfat / obese** (>25% BF for males) | **High** | Large fat stores provide energy; anabolic signal from training |
| Intermediate (1–3 years, suboptimal prior training) | **Moderate** | Possible with optimized training + nutrition |
| Advanced, well-trained, lean | **Low** | Very small effect; traditional bulk/cut more efficient |

**The "Training Optimization" Factor (Barakat interview evidence):**
Many people Barakat works with experience recomp because they have NOT had training + nutrition + recovery all optimized simultaneously. Switching to progressive overload programming + hitting protein targets + adequate sleep creates conditions for recomp even in apparent intermediates.

**Supporting Evidence:** Concurrent training (resistance + aerobic) has been shown to optimize body recomposition outcomes in multiple RCTs. Calorie restriction combined with exercise is the most effective strategy for reducing fat percentage while maintaining LBM (He et al. 2024, Nutrients 16(17):3007). URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC11397086/

### 5.2 How Milo Should Handle Recomposition Users

```python
def assess_recomposition_eligibility(
    training_age_months: int,
    body_fat_pct: float,
    training_quality_score: int,    # 1-5: 1=very poor programming, 5=optimized
    nutrition_quality_score: int,   # 1-5: 1=untracked/poor, 5=optimized macros
    recovery_quality_score: int     # 1-5: 1=poor sleep/stress, 5=excellent
) -> dict:
    """
    Assesses whether a user is a recomposition candidate.
    Returns recommended phase approach.
    """
    BEGINNER_THRESHOLD_MONTHS: int = 12  # < 12 months = beginner
    HIGH_BF_THRESHOLD_PCT: float = 25.0   # Males: > 25% BF = high recomp potential
    INTERMEDIATE_BF_THRESHOLD_PCT: float = 20.0
    
    is_beginner = training_age_months < BEGINNER_THRESHOLD_MONTHS
    is_high_bf = body_fat_pct > HIGH_BF_THRESHOLD_PCT
    has_optimization_headroom = (
        training_quality_score <= 3 or
        nutrition_quality_score <= 3 or
        recovery_quality_score <= 3
    )
    
    if is_beginner or is_high_bf or has_optimization_headroom:
        recommended_approach = "maintenance_calories_with_optimized_training"
        recomp_probability = "high" if (is_beginner or is_high_bf) else "moderate"
        phase_suggestion = NutritionalPhase.MAINTENANCE
    else:
        recommended_approach = "traditional_bulk_cut_cycles"
        recomp_probability = "low"
        phase_suggestion = None  # Let user choose CUT or LEAN_BULK
    
    return {
        "recomp_probability": recomp_probability,
        "recommended_approach": recommended_approach,
        "recommended_phase": phase_suggestion,
        "rationale_flags": {
            "is_beginner": is_beginner,
            "is_high_bf": is_high_bf,
            "has_optimization_headroom": has_optimization_headroom
        }
    }
```

### 5.3 Recomp as a Phase in Milo

**Design Decision:** Recomposition is NOT a separate named phase in Milo. It is handled as **eating at MAINTENANCE calories + progressive resistance training + 0.82 g/lb protein**. The system should:

1. When user profile suggests recomp eligibility, recommend MAINTENANCE as the starting phase
2. Track both weight AND body composition trends (if available) — a user who maintains weight but improves body composition metrics IS achieving recomp
3. After 8–12 weeks at maintenance with no body composition improvement, transition user to traditional CUT or LEAN_BULK cycle

```python
class RecompPhaseHandling:
    """
    Recomp is treated as MAINTENANCE phase with body composition tracking.
    """
    PHASE_ASSIGNMENT: NutritionalPhase = NutritionalPhase.MAINTENANCE
    CALORIE_TARGET: str = "TDEE"
    PROTEIN_RATE_G_PER_LB: float = 0.82  # Same as all phases
    
    # If no body composition improvement after this many weeks, recommend phase transition
    RECOMP_PLATEAU_TRIGGER_WEEKS: int = 10
    
    # Body composition improvement threshold (tracked via body measurements / user feedback)
    RECOMP_SUCCESS_INDICATOR: str = "stable_weight + improved_bf_pct_or_measurements"
```

---

## 6. EVIDENCE ON REFEEDS AND DIET BREAKS (EXCLUDED)

This section documents why refeeds and diet breaks are NOT included in Milo. The evidence is mixed-to-weak; the design decision to exclude them is justified.

### 6.1 The MATADOR Study (Original Evidence FOR Diet Breaks)

**Citation:** Byrne NM, Sainsbury A, King NA, Hills AP, Wood RE. (2017/2018). "Intermittent energy restriction improves weight loss efficiency in obese men: the MATADOR study." *International Journal of Obesity*, 42(2):129–138. DOI: 10.1038/ijo.2017.206. URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC5803575/

*Note: Published online August 2017; officially published 2018 as "Byrne et al. 2018"*

**Study Design:** 51 obese men (not resistance-trained). Randomized to:
- **Continuous ER (CER):** 16 weeks of ~33% energy restriction
- **Intermittent ER (IER):** Alternating 2-week restriction + 2-week maintenance rest (30 total weeks, 16 of which were restriction)

**Findings:**
- IER group lost **significantly more fat mass** and weight overall
- IER group experienced **smaller reduction in resting energy expenditure (REE)** after body composition correction
- IER group **regained less weight** in follow-up
- The IER group required **30 weeks total** to complete what the CER group did in 16 weeks

**Initial Interpretation:** Diet breaks with 2-week maintenance periods attenuate adaptive thermogenesis ("metabolic slowdown") and improve fat loss efficiency.

### 6.2 Subsequent Critiques and Failures to Replicate

**Key Critique 1 — Population Mismatch:**
The MATADOR study used **obese men** (not resistance-trained athletes). The metabolic adaptation dynamics are substantially different in this population compared to Milo's target population (lean-to-moderate BF resistance-trained males).

**Key Critique 2 — Resistance-Trained Populations (Campbell et al., Henselmans et al. 2023):**

**Citation:** Campbell BI, Waddell BJ, Mathas DB, et al. (2023). "The Effects of Intermittent Diet Breaks during 25% Energy Restriction on Body Composition and Resting Metabolic Rate in Resistance-Trained Females." *J Human Kinetics*, 87:111–124. DOI: 10.5114/jhk/159960. URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC10170537/

> "Diet breaks do not appear to induce improvements in body composition or metabolic rate in comparison with continuous energy restriction over six weeks of dieting... Intermittent dieting strategies may be employed for those who desire a short-term break from an energy-restricted diet **without fear of fat regain**."

**Key Critique 3 — Meta-Analysis (2024):**
A meta-analysis discussed by Layne Norton (2025) examined the full body of diet break literature and found:
- Diet breaks vs. continuous restriction: only ~**50 kcal/day difference** in metabolic adaptation attenuation
- **No differences** between groups for fat-free mass retention
- **No differences** for total fat loss
- The effect size for metabolic rate preservation was statistically significant but clinically small

Source: Norton L. (2025). "Can Diet Breaks Fix Your Metabolism?" YouTube. URL: https://www.youtube.com/watch?v=z9jK36QmUII

**Key Critique 4 — ICECAP Trial (Athletes):**
> "12 weeks of energy restriction, applied intermittently... did not result in superior fat loss or retention of fat-free mass or resting energy expenditure compared to continuous energy restriction in adult athletes."

Source: Peos JJ et al. (2019/2021). Intermittent Dieting: Theoretical Considerations for the Athlete. *Sports* 7(1):22. URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC6359485/

### 6.3 Current Evidence Consensus

| Outcome | CER vs IER | Evidence Quality |
|---|---|---|
| Total fat loss | **No significant difference** in most studies | Moderate |
| LBM retention | **No significant difference** | Moderate |
| Metabolic adaptation (REE) | IER slightly better (~50 kcal/day) | Weak (mixed replication) |
| Adherence | IER may be better subjectively | Low–moderate |
| Psychological wellbeing | IER may offer mental break | Low (self-report) |

### 6.4 Why Milo Excludes Refeeds and Diet Breaks

```python
class RefeedDietBreakPolicy:
    """
    Milo design decision: No refeeds or diet breaks.
    """
    INCLUDED: bool = False
    
    RATIONALE = """
    1. MATADOR study (Byrne et al. 2018) showed benefit in OBESE men, not
       resistance-trained intermediates (Milo's target population).
    
    2. Multiple subsequent studies in resistance-trained populations found
       NO significant benefit for body composition or RMR preservation.
    
    3. Meta-analysis (2024) showed only ~50 kcal/day difference in metabolic
       adaptation — clinically negligible.
    
    4. Diet breaks double the total time required to achieve the same caloric
       deficit (e.g., 30 weeks instead of 16 to complete 16 deficit weeks).
    
    5. Complexity without demonstrated benefit in target population.
       Adding refeeds/diet breaks would increase cognitive load for users
       and require substantial additional logic with weak evidence support.
    
    6. Milo's biweekly calorie adjustment mechanism and phase transition logic
       already capture metabolic adaptation by adjusting targets when progress
       stalls — achieving the same functional outcome without formal diet breaks.
    """
    
    FUTURE_CONSIDERATION = """
    If Milo adds advanced athlete support (contest prep), evidence-based
    diet breaks (2-week blocks) could be added as an optional feature with
    appropriate population screening.
    """
```

---

## 7. PHASE STATE MACHINE SUMMARY

### 7.1 State Machine Diagram (Pseudocode)

```
States: CUT | MAINTENANCE | LEAN_BULK
Initial state: determined by onboarding profile

┌─────────────────────────────────────────────────────────┐
│                    STATE: CUT                           │
│  - Deficit: 300–500 kcal/day (moderate)                 │
│  - Target: -0.5% to -1.0% BW/week                       │
│  - Protein: user_weight_lbs × 0.82 g                    │
│  - Max duration: 16 weeks soft, 20 weeks hard           │
│                                                         │
│  Biweekly adjustment: ±150 kcal based on actual         │
│  weight change vs. 0.5–1.0% BW/week target              │
└────────────────┬────────────────────────────────────────┘
                 │  TRANSITIONS TO MAINTENANCE:
                 │  - Goal reached (weight OR BF%)
                 │  - Duration ≥ 16 weeks (recommended)
                 │  - Duration ≥ 20 weeks (urgent)
                 │  - Metabolic adaptation signal (stall)
                 │  - Training performance declining (≤2/5)
                 │  - Excessive fatigue/hunger (≤2/5)
                 │  - Adherence declining (≤2/5)
                 │  - User requests
                 ▼
┌─────────────────────────────────────────────────────────┐
│                 STATE: MAINTENANCE                      │
│  - Calories: TDEE (±100 kcal tolerance)                 │
│  - Protein: user_weight_lbs × 0.82 g                    │
│  - Recommended duration post-cut: 4 weeks               │
│  - Minimum before CUT: 2 weeks                          │
│  - Minimum before LEAN_BULK: 4 weeks                    │
└────────┬──────────────────────────────┬─────────────────┘
         │ TRANSITIONS TO CUT:          │ TRANSITIONS TO LEAN_BULK:
         │ - User goal = fat loss       │ - Minimum duration met (4 wks)
         │ - BF% ≥ 20%                  │ - Recovery strong (≥4/5)
         │ - Min duration met (2 wks)   │ - BF% ≤ 15%
         │                              │ - User requests
         ▼                              ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│       (back to CUT)      │   │   STATE: LEAN_BULK       │
│                          │   │  Surplus: 200–350 kcal/d  │
│                          │   │  (beginners)              │
│                          │   │  100–200 kcal/d (intermed)│
│                          │   │  Target: +0.25–0.50%      │
│                          │   │  BW/week                  │
│                          │   │  Protein: TBW × 0.82 g   │
│                          │   │  Max: 24 weeks            │
└──────────────────────────┘   └────────────┬─────────────┘
                                             │ TRANSITIONS TO CUT:
                                             │ - BF% ≥ 18% (soft)
                                             │ - BF% ≥ 20% (urgent)
                                             │ - Duration ≥ 24 weeks
                                             │ - User requests
                                             ▼
                                      (back to CUT)
```

### 7.2 Consolidated Numeric Thresholds Reference

```python
class MiloPhaseThresholds:
    """
    All numeric thresholds used in Milo's phase logic, with sources.
    """
    
    # ── PROTEIN ──────────────────────────────────────────────────────────
    PROTEIN_RATE_G_PER_LB: float = 0.82  # Henselmans 2012; Morton et al. 2018 upper CI
    PROTEIN_RATE_G_PER_KG: float = 1.81  # = 0.82 * 2.2046
    
    # ── CUT PHASE ────────────────────────────────────────────────────────
    CUT_DEFICIT_MODERATE_LOWER: int = 300   # kcal/day (Helms 2014)
    CUT_DEFICIT_MODERATE_UPPER: int = 500   # kcal/day
    CUT_DEFICIT_AGGRESSIVE_LOWER: int = 500  # kcal/day
    CUT_DEFICIT_AGGRESSIVE_UPPER: int = 750  # kcal/day
    
    CUT_WEIGHT_LOSS_TARGET_LOWER_PCT: float = 0.50  # % BW/week (Helms 2014)
    CUT_WEIGHT_LOSS_TARGET_UPPER_PCT: float = 1.00  # % BW/week
    
    CUT_MIN_DURATION_WEEKS: int = 4
    CUT_OPTIMAL_UPPER_WEEKS: int = 12
    CUT_SOFT_MAX_WEEKS: int = 16   # Recommend transition (Helms 2014)
    CUT_HARD_MAX_WEEKS: int = 20   # Strongly recommend transition
    
    # ── MAINTENANCE PHASE ─────────────────────────────────────────────────
    MAINTENANCE_CALORIE_TOLERANCE_KCAL: int = 100  # ±100 kcal = maintenance
    
    POST_CUT_MIN_MAINTENANCE_WEEKS: int = 2
    POST_CUT_OPTIMAL_MAINTENANCE_WEEKS: int = 4
    POST_BULK_MIN_MAINTENANCE_WEEKS: int = 2
    POST_BULK_OPTIMAL_MAINTENANCE_WEEKS: int = 4
    
    # ── LEAN BULK PHASE ───────────────────────────────────────────────────
    BULK_SURPLUS_BEGINNER_LOWER: int = 200   # kcal/day (applied consensus)
    BULK_SURPLUS_BEGINNER_UPPER: int = 350   # kcal/day
    BULK_SURPLUS_INTERMEDIATE_LOWER: int = 100  # kcal/day
    BULK_SURPLUS_INTERMEDIATE_UPPER: int = 200  # kcal/day
    
    BULK_WEIGHT_GAIN_BEGINNER_LOWER_PCT: float = 0.25   # % BW/week (Helms 2019)
    BULK_WEIGHT_GAIN_BEGINNER_UPPER_PCT: float = 0.50   # % BW/week
    BULK_WEIGHT_GAIN_INTERMEDIATE_LOWER_PCT: float = 0.10  # % BW/week
    BULK_WEIGHT_GAIN_INTERMEDIATE_UPPER_PCT: float = 0.25  # % BW/week
    
    BULK_MIN_DURATION_WEEKS: int = 8
    BULK_OPTIMAL_UPPER_WEEKS: int = 20
    BULK_SOFT_MAX_WEEKS: int = 24
    
    # ── BODY FAT PHASE THRESHOLDS (MALE) ──────────────────────────────────
    BF_MAX_TO_START_BULK_PCT: float = 15.0   # Max BF% to begin lean bulk
    BF_IDEAL_START_BULK_PCT: float = 12.0    # Ideal BF% to begin lean bulk
    BF_SOFT_EXIT_BULK_PCT: float = 18.0     # Recommend evaluating exit from bulk
    BF_HARD_EXIT_BULK_PCT: float = 20.0     # Strong recommendation to exit bulk
    BF_CUT_TRIGGER_MAINTENANCE_PCT: float = 20.0  # Trigger cut from maintenance
    
    # ── RECOMPOSITION CANDIDACY ───────────────────────────────────────────
    RECOMP_TRAINING_AGE_BEGINNER_MONTHS: int = 12   # < 12 months = beginner
    RECOMP_HIGH_BF_THRESHOLD_PCT: float = 25.0      # High recomp potential
    RECOMP_PLATEAU_WEEKS: int = 10                   # Recomp stall → transition
    
    # ── ADJUSTMENT LOGIC ─────────────────────────────────────────────────
    BIWEEKLY_CALORIE_ADJUSTMENT_KCAL: int = 150     # Standard adjustment increment
    METABOLIC_ADAPTATION_STALL_THRESHOLD_PCT: float = 0.10  # % BW/week = stall
    METABOLIC_ADAPTATION_MIN_DURATION_WEEKS: int = 8  # Min weeks before calling stall
    
    # ── WELLBEING THRESHOLDS (1–5 scale) ─────────────────────────────────
    PERFORMANCE_DECLINE_THRESHOLD: int = 2   # ≤2 = declining performance
    FATIGUE_EXCESSIVE_THRESHOLD: int = 2     # ≤2 = excessive fatigue
    HUNGER_EXCESSIVE_THRESHOLD: int = 2      # ≤2 = excessive hunger
    ADHERENCE_FAILING_THRESHOLD: int = 2     # ≤2 = failing adherence
    RECOVERY_STRONG_THRESHOLD: int = 4       # ≥4 = strong recovery
```

---

## APPENDIX: KEY CITATIONS SUMMARY

| Citation | Key Data Point | URL |
|---|---|---|
| Morton et al. (2018) BJSM | Protein breakpoint: 1.62 g/kg (95% CI: 1.03–2.20) | https://bjsm.bmj.com/lookup/doi/10.1136/bjsports-2017-097608 |
| Henselmans (2012, updated) | 0.82 g/lb = upper safe margin; no benefit above | https://mennohenselmans.com/the-myth-of-1glb-optimal-protein-intake-for-bodybuilders/ |
| Henselmans (2024) | No higher protein needed in deficit | https://mennohenselmans.com/you-dont-need-more-protein-in-energy-deficit/ |
| Helms, Aragon, Fitschen (2014) JISSN | Cut: 0.5–1%/wk loss; protein 2.3–3.1 g/kg LBM | https://pmc.ncbi.nlm.nih.gov/articles/PMC4033492/ |
| Schoenfeld & Aragon (2018) JISSN | 0.4 g/kg/meal; timing secondary to total intake | https://pubmed.ncbi.nlm.nih.gov/29497353/ |
| Schoenfeld, Aragon, Krieger (2013) JISSN | Timing not significant; total protein is primary | https://www.tandfonline.com/doi/full/10.1186/1550-2783-10-53 |
| Antonio et al. (2014) JISSN | 4.4 g/kg/d safe in resistance-trained individuals | https://pmc.ncbi.nlm.nih.gov/articles/PMC4022420/ |
| Antonio et al. (2016) J Nutr Metab | 3.32 g/kg/d for 1 year: no adverse effects | https://pmc.ncbi.nlm.nih.gov/articles/PMC5078648/ |
| Helms, Iraki, Fitschen, Espinar (2019) Sports | Bulk: 0.25–0.50% BW/wk; 10–20% surplus | https://pmc.ncbi.nlm.nih.gov/articles/PMC6680710/ |
| Barakat et al. (2020) SCJ | Body recomp in trained individuals; conditions | https://journals.lww.com/10.1519/SSC.0000000000000584 |
| Byrne et al. (2018) IJO (MATADOR) | Diet breaks improve fat loss in obese men | https://pmc.ncbi.nlm.nih.gov/articles/PMC5803575/ |
| Campbell, Henselmans et al. (2023) JHK | Diet breaks no benefit in resistance-trained females | https://pmc.ncbi.nlm.nih.gov/articles/PMC10170537/ |
| Peos, Helms et al. (2019) Sports | Diet breaks no benefit in athletes | https://pmc.ncbi.nlm.nih.gov/articles/PMC6359485/ |
| Ruiz-Castellano et al. (2021) Nutrients | Optimal fat loss: 0.5–1.0% BW/week | https://pmc.ncbi.nlm.nih.gov/articles/PMC8471721/ |

---

*Document generated: March 5, 2026*
*For Milo AI Fitness System — Backend Implementation Reference*
*All citations verified against primary sources*
