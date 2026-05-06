import os
from datetime import date

WEIGHTS = {
    "business_license_score": 0.25,
    "liquor_license_score": 0.25,
    "school_enrollment_score": 0.20,
    "google_trends_score": 0.20,
    "building_permit_score": 0.10,
}


def normalize(value: float, min_val: float, max_val: float) -> float:
    if max_val == min_val:
        return 50.0
    return max(0.0, min(100.0, (value - min_val) / (max_val - min_val) * 100))


def compute_score(signals: dict) -> dict:
    """
    signals: dict with keys matching WEIGHTS, values are raw signal floats.
    Returns scored dict with first_mover_score (0-100) and sub-scores.
    """
    sub_scores = {}
    for key in WEIGHTS:
        raw = signals.get(key, 0.0)
        # Each signal is assumed pre-normalized 0-100 by ingestion layer
        sub_scores[key] = float(raw)

    first_mover_score = sum(
        sub_scores[k] * WEIGHTS[k] for k in WEIGHTS
    )

    return {
        "first_mover_score": round(first_mover_score, 2),
        "business_license_score": round(sub_scores["business_license_score"], 2),
        "liquor_license_score": round(sub_scores["liquor_license_score"], 2),
        "school_enrollment_score": round(sub_scores["school_enrollment_score"], 2),
        "google_trends_score": round(sub_scores["google_trends_score"], 2),
        "building_permit_score": round(sub_scores["building_permit_score"], 2),
        "score_date": date.today().isoformat(),
    }


def score_tier(score: float) -> str:
    if score >= 80:
        return "HOT"
    elif score >= 60:
        return "WARM"
    elif score >= 40:
        return "NEUTRAL"
    else:
        return "COLD"
