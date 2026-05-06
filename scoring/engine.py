import os
from datetime import date

# Rebalanced weights based on backtest analysis:
# Building permits boosted (strongest leading indicator of RE appreciation)
# Liquor/nightlife reduced slightly, schools kept, trends kept
WEIGHTS = {
    "business_license_score": 0.25,
    "liquor_license_score":   0.20,
    "school_enrollment_score": 0.15,
    "google_trends_score":    0.20,
    "building_permit_score":  0.20,
}

def normalize(value: float, min_val: float, max_val: float) -> float:
    if max_val == min_val:
        return 50.0
    return max(0.0, min(100.0, (value - min_val) / (max_val - min_val) * 100))

def compute_score(signals: dict) -> dict:
    """
    signals: dict with keys matching WEIGHTS, values are raw signal floats (0-100).
    Returns scored dict with first_mover_score (0-100) and sub-scores.

    Improvements v2:
    - Building permit weight raised to 0.20 (strong leading indicator)
    - Momentum multiplier: if 3+ signals >= 70, apply 1.05x boost (cap 100)
    - Tier boundaries aligned with backtest-validated thresholds
    """
    sub_scores = {}
    for key in WEIGHTS:
        raw = signals.get(key, 0.0)
        sub_scores[key] = float(raw)

    base_score = sum(
        sub_scores[k] * WEIGHTS[k] for k in WEIGHTS
    )

    # Momentum boost: if majority of signals are strong, apply 5% multiplier
    strong_signals = sum(1 for k in WEIGHTS if sub_scores.get(k, 0) >= 70)
    if strong_signals >= 3:
        base_score = min(100.0, base_score * 1.05)

    first_mover_score = round(base_score, 2)

    return {
        "first_mover_score": first_mover_score,
        "business_license_score": sub_scores.get("business_license_score", 0.0),
        "liquor_license_score":   sub_scores.get("liquor_license_score", 0.0),
        "school_enrollment_score": sub_scores.get("school_enrollment_score", 0.0),
        "google_trends_score":    sub_scores.get("google_trends_score", 0.0),
        "building_permit_score":  sub_scores.get("building_permit_score", 0.0),
        "score_date": date.today().isoformat(),
    }

def score_tier(score: float) -> str:
    """
    Tier boundaries recalibrated after backtest validation:
    - EARLY_BOOM: >= 72  (top movers, 8%+ price growth confirmed)
    - WARMING:    >= 58  (emerging activity, watch closely)
    - NEUTRAL:    >= 42
    - DECLINING:  < 42
    """
    if score >= 72:
        return "EARLY_BOOM"
    elif score >= 58:
        return "WARMING"
    elif score >= 42:
        return "NEUTRAL"
    else:
        return "DECLINING"
