from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import random
import io
import csv
from datetime import date, timedelta
from scoring.engine import compute_score, score_tier

router = APIRouter()

ATLANTA_ZIPS = [
    "30005", "30022", "30092", "30075", "30307", "30306", "30308",
    "30309", "30316", "30317", "30318", "30024", "30040", "30188",
    "30269", "30144", "30096", "30043", "30062", "30033"
]

# Simulated Zillow ZHVI price growth by zip (annual %)
ZHVI_GROWTH = {
    "30307": 0.142, "30306": 0.138, "30308": 0.121, "30309": 0.118,
    "30316": 0.132, "30317": 0.128, "30318": 0.115, "30022": 0.098,
    "30005": 0.092, "30092": 0.105, "30075": 0.088, "30024": 0.095,
    "30040": 0.082, "30188": 0.078, "30269": 0.071, "30144": 0.065,
    "30096": 0.058, "30043": 0.045, "30062": 0.042, "30033": 0.038,
}


def _generate_synthetic_scores(score_date: date) -> list:
    results = []
    for zip_code in ATLANTA_ZIPS:
        seed = sum(ord(c) for c in zip_code) + score_date.toordinal()
        random.seed(seed)
        signals = {
            "business_license_score": random.uniform(40, 90),
            "liquor_license_score": random.uniform(35, 92),
            "school_enrollment_score": random.uniform(30, 88),
            "google_trends_score": random.uniform(38, 85),
            "building_permit_score": random.uniform(40, 80),
        }
        scored = compute_score(signals)
        actual_growth = ZHVI_GROWTH.get(zip_code, 0.05)
        results.append({
            "zip_code": zip_code,
            "score_date": score_date.isoformat(),
            "first_mover_score": scored["first_mover_score"],
            "tier": score_tier(scored["first_mover_score"]),
            "actual_price_growth_pct": round(actual_growth * 100, 2),
            "predicted_boom": scored["first_mover_score"] >= 70,
            "actual_boom": actual_growth >= 0.08,
        })
    return results


@router.get("/single")
def backtest_single(
    score_date: str = None,
    use_synthetic: bool = True
):
    sd = date.fromisoformat(score_date) if score_date else date.today() - timedelta(weeks=78)
    results = _generate_synthetic_scores(sd)
    predicted_boom = [r for r in results if r["predicted_boom"]]
    actual_boom = [r for r in results if r["actual_boom"]]
    tp = [r for r in predicted_boom if r["actual_boom"]]
    precision = len(tp) / len(predicted_boom) if predicted_boom else 0
    recall = len(tp) / len(actual_boom) if actual_boom else 0
    avg_score_hot = sum(r["first_mover_score"] for r in results if r["tier"] == "HOT") / max(1, len([r for r in results if r["tier"] == "HOT"]))
    verdict = "STRONG" if precision >= 0.60 else "GOOD" if precision >= 0.45 else "WEAK"
    return {
        "score_date": sd.isoformat(),
        "total_zips": len(results),
        "predicted_boom_count": len(predicted_boom),
        "actual_boom_count": len(actual_boom),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "verdict": verdict,
        "results": results
    }


@router.get("/summary")
def backtest_summary(use_synthetic: bool = True):
    summaries = []
    base = date.today() - timedelta(weeks=104)
    for week in range(0, 104, 13):
        sd = base + timedelta(weeks=week)
        results = _generate_synthetic_scores(sd)
        predicted_boom = [r for r in results if r["predicted_boom"]]
        actual_boom = [r for r in results if r["actual_boom"]]
        tp = [r for r in predicted_boom if r["actual_boom"]]
        precision = len(tp) / len(predicted_boom) if predicted_boom else 0
        summaries.append({
            "score_date": sd.isoformat(),
            "precision": round(precision, 3),
            "predicted": len(predicted_boom),
            "actual": len(actual_boom),
        })
    avg_precision = sum(s["precision"] for s in summaries) / len(summaries)
    overall_verdict = "STRONG" if avg_precision >= 0.60 else "GOOD" if avg_precision >= 0.45 else "WEAK"
    return {
        "periods_tested": len(summaries),
        "avg_precision": round(avg_precision, 3),
        "overall_verdict": overall_verdict,
        "emoji": "STRONG" if avg_precision >= 0.60 else "GOOD" if avg_precision >= 0.45 else "WEAK",
        "summary": summaries
    }


@router.get("/rolling/csv")
def backtest_rolling_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["score_date", "zip_code", "first_mover_score", "tier",
                     "actual_price_growth_pct", "predicted_boom", "actual_boom"])
    base = date.today() - timedelta(weeks=104)
    for week in range(0, 104, 13):
        sd = base + timedelta(weeks=week)
        for r in _generate_synthetic_scores(sd):
            writer.writerow([r["score_date"], r["zip_code"], r["first_mover_score"],
                             r["tier"], r["actual_price_growth_pct"],
                             r["predicted_boom"], r["actual_boom"]])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=backtest_rolling.csv"})
