from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os, io, csv, requests
from scoring.engine import compute_score
from backtest.api import router as backtest_router

load_dotenv()

app = FastAPI(title="ZoneIQ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(backtest_router, prefix="/backtest", tags=["Backtest"])

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "zoneiq2026")
ALERT_THRESHOLD = int(os.getenv("ALERT_THRESHOLD", "15"))

engine = create_engine(DATABASE_URL) if DATABASE_URL else None

CITY_MAP = {
    '30005': 'Alpharetta', '30009': 'Alpharetta', '30022': 'Johns Creek',
    '30024': 'Suwanee', '30033': 'Decatur', '30040': 'Cumming',
    '30041': 'Cumming', '30043': 'Lawrenceville', '30044': 'Lawrenceville',
    '30062': 'Marietta', '30066': 'Marietta', '30067': 'Marietta',
    '30068': 'Marietta', '30075': 'Roswell', '30076': 'Roswell',
    '30092': 'Peachtree Corners', '30096': 'Duluth', '30097': 'Duluth',
    '30101': 'Acworth', '30102': 'Acworth', '30114': 'Canton',
    '30115': 'Canton', '30127': 'Powder Springs', '30132': 'Dallas',
    '30144': 'Kennesaw', '30152': 'Kennesaw', '30188': 'Woodstock',
    '30189': 'Woodstock', '30213': 'Fairburn', '30228': 'Hampton',
    '30238': 'Jonesboro', '30260': 'Morrow', '30269': 'Peachtree City',
    '30277': 'Sharpsburg', '30281': 'Stockbridge', '30291': 'Union City',
    '30294': 'Ellenwood', '30301': 'Atlanta', '30306': 'Atlanta-VH',
    '30307': 'Atlanta-Inman', '30308': 'Atlanta-Midtown',
    '30309': 'Atlanta-Midtown', '30316': 'Atlanta-EAV', '30317': 'Kirkwood',
    '30318': 'Atlanta-W'
}

# Socrata endpoints for business license data
SOCRATA_SOURCES = [
    {
        "url": "https://data.fultoncountyga.gov/resource/qzwm-k9p9.json",
        "zip_field": "zip_code",
        "name_field": "business_name",
        "type_field": "license_type",
        "date_field": "issue_date",
        "zips": ["303"]
    },
    {
        "url": "https://opendata.atlantaga.gov/resource/businesses.json",
        "zip_field": "zip",
        "name_field": "business_name",
        "type_field": "license_type",
        "date_field": "issue_date",
        "zips": ["303"]
    },
    {
        "url": "https://data.gwinnettcounty.com/resource/business-licenses.json",
        "zip_field": "zip_code",
        "name_field": "business_name",
        "type_field": "license_type",
        "date_field": "issue_date",
        "zips": ["300"]
    }
]

def get_db():
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
    with engine.connect() as conn:
        yield conn

@app.get("/health")
def health():
    return {"status": "ok", "service": "ZoneIQ API"}

@app.get("/scores/top")
def get_top_scores(limit: int = 20, db=Depends(get_db)):
    rows = db.execute(text(
        "SELECT zip_code, city, state, first_mover_score, business_license_score, "
        "liquor_license_score, school_enrollment_score, google_trends_score, "
        "building_permit_score, score_date FROM zip_scores "
        "ORDER BY first_mover_score DESC LIMIT :limit"
    ), {"limit": limit}).fetchall()
    scores = []
    for r in rows:
        city = r.city or CITY_MAP.get(r.zip_code, '')
        scores.append({
            "zip_code": r.zip_code,
            "city": city,
            "state": r.state,
            "first_mover_score": float(r.first_mover_score or 0),
            "business_license_score": float(r.business_license_score or 0),
            "liquor_license_score": float(r.liquor_license_score or 0),
            "school_enrollment_score": float(r.school_enrollment_score or 0),
            "google_trends_score": float(r.google_trends_score or 0),
            "building_permit_score": float(r.building_permit_score or 0),
            "score_date": str(r.score_date),
        })
    return {"scores": scores, "total": len(scores)}

@app.get("/businesses/{zip_code}")
def get_businesses(zip_code: str):
    """Fetch recent business license records for a given zip code from public Socrata APIs."""
    businesses = []
    for source in SOCRATA_SOURCES:
        if not any(zip_code.startswith(p) for p in source["zips"]):
            continue
        try:
            params = {
                "$where": f"{source['zip_field']}='{zip_code}'",
                "$limit": 25,
                "$order": f"{source['date_field']} DESC"
            }
            resp = requests.get(source["url"], params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                for item in data:
                    name = item.get(source["name_field"], "").strip()
                    if not name:
                        continue
                    businesses.append({
                        "name": name,
                        "type": item.get(source["type_field"], "N/A"),
                        "date": item.get(source["date_field"], "")[:10] if item.get(source["date_field"]) else "N/A"
                    })
        except Exception:
            continue
        if businesses:
            break
    # Deduplicate by name
    seen = set()
    unique = []
    for b in businesses:
        if b["name"] not in seen:
            seen.add(b["name"])
            unique.append(b)
    return {"zip_code": zip_code, "businesses": unique[:20], "total": len(unique[:20])}

@app.get("/explain/{zip_code}")
def explain_zip(zip_code: str, db=Depends(get_db)):
    row = db.execute(text(
        "SELECT zip_code, city, state, first_mover_score, business_license_score, "
        "liquor_license_score, school_enrollment_score, google_trends_score, "
        "building_permit_score, score_date FROM zip_scores WHERE zip_code = :zip"
    ), {"zip": zip_code}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Zip {zip_code} not found")
    city = row.city or CITY_MAP.get(row.zip_code, '')
    score = float(row.first_mover_score or 0)
    tier = 'early_boom' if score >= 75 else 'warming' if score >= 60 else 'neutral' if score >= 40 else 'declining'
    return {
        "zip_code": row.zip_code,
        "city": city,
        "tier": tier,
        "scores": {
            "first_mover_score": score,
            "business_license_score": float(row.business_license_score or 0),
            "liquor_license_score": float(row.liquor_license_score or 0),
            "school_enrollment_score": float(row.school_enrollment_score or 0),
            "google_trends_score": float(row.google_trends_score or 0),
            "building_permit_score": float(row.building_permit_score or 0),
        },
        "score_date": str(row.score_date),
    }

@app.post("/fix-cities")
def fix_cities(x_admin_secret: str = Header(None), db=Depends(get_db)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized")
    updated = 0
    for zip_code, city in CITY_MAP.items():
        result = db.execute(text(
            "UPDATE zip_scores SET city = :city WHERE zip_code = :zip AND (city IS NULL OR city = '')"
        ), {"city": city, "zip": zip_code})
        updated += result.rowcount
    db.commit()
    return {"updated_rows": updated, "message": f"Fixed city names for {updated} zip codes"}

@app.post("/run-pipeline")
def run_pipeline(x_admin_secret: str = Header(None), db=Depends(get_db)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized")
    results = []
    for zip_code, city in CITY_MAP.items():
        score_data = compute_score(zip_code)
        db.execute(text(
            "INSERT INTO zip_scores (zip_code, city, first_mover_score, business_license_score, "
            "liquor_license_score, school_enrollment_score, google_trends_score, building_permit_score, score_date) "
            "VALUES (:zip, :city, :fms, :bls, :lls, :ses, :gts, :bps, CURRENT_DATE) "
            "ON CONFLICT (zip_code) DO UPDATE SET "
            "city = EXCLUDED.city, first_mover_score = EXCLUDED.first_mover_score, "
            "business_license_score = EXCLUDED.business_license_score, "
            "liquor_license_score = EXCLUDED.liquor_license_score, "
            "school_enrollment_score = EXCLUDED.school_enrollment_score, "
            "google_trends_score = EXCLUDED.google_trends_score, "
            "building_permit_score = EXCLUDED.building_permit_score, "
            "score_date = EXCLUDED.score_date"
        ), {
            "zip": zip_code, "city": city,
            "fms": score_data.get("first_mover_score", 50),
            "bls": score_data.get("business_license_score", 50),
            "lls": score_data.get("liquor_license_score", 50),
            "ses": score_data.get("school_enrollment_score", 50),
            "gts": score_data.get("google_trends_score", 50),
            "bps": score_data.get("building_permit_score", 50),
        })
        results.append({"zip": zip_code, "score": score_data.get("first_mover_score", 50)})
    db.commit()
    return {"processed": len(results), "results": results}

@app.get("/alerts")
def get_alerts(limit: int = 50, db=Depends(get_db)):
    rows = db.execute(text(
        "SELECT zip_code, score_jump, prev_score, new_score, fired_at "
        "FROM alerts ORDER BY fired_at DESC LIMIT :limit"
    ), {"limit": limit}).fetchall()
    return {"alerts": [{"zip_code": r.zip_code, "score_jump": float(r.score_jump or 0), "prev_score": float(r.prev_score or 0), "new_score": float(r.new_score or 0), "fired_at": str(r.fired_at)} for r in rows]}

@app.get("/export/csv")
def export_csv(db=Depends(get_db)):
    rows = db.execute(text(
        "SELECT zip_code, city, first_mover_score, business_license_score, "
        "liquor_license_score, school_enrollment_score, google_trends_score, "
        "building_permit_score, score_date FROM zip_scores ORDER BY first_mover_score DESC"
    )).fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["zip_code","city","first_mover_score","business_license_score",
                     "liquor_license_score","school_enrollment_score","google_trends_score",
                     "building_permit_score","score_date"])
    for r in rows:
        writer.writerow([r.zip_code, r.city or CITY_MAP.get(r.zip_code,''), r.first_mover_score,
                         r.business_license_score, r.liquor_license_score, r.school_enrollment_score,
                         r.google_trends_score, r.building_permit_score, r.score_date])
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode()), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=zoneiq_scores.csv"})
