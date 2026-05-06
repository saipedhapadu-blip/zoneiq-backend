from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os, io, csv
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


def get_db():
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
    with engine.connect() as conn:
        yield conn


@app.get("/health")
def health(conn=Depends(get_db)):
    conn.execute(text("SELECT 1"))
    return {"status": "connected", "database": "ok"}


@app.get("/score/{zip_code}")
def get_score(zip_code: str, conn=Depends(get_db)):
    row = conn.execute(
        text("SELECT * FROM zip_scores WHERE zip_code=:z ORDER BY score_date DESC LIMIT 1"),
        {"z": zip_code}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"No data for zip {zip_code}")
    return dict(row._mapping)


@app.get("/scores/top")
def top_scores(limit: int = 10, conn=Depends(get_db)):
    rows = conn.execute(
        text("SELECT DISTINCT ON (zip_code) * FROM zip_scores ORDER BY zip_code, score_date DESC, first_mover_score DESC LIMIT :l"),
        {"l": limit}
    ).fetchall()
    return [dict(r._mapping) for r in rows]


@app.get("/scores/history/{zip_code}")
def score_history(zip_code: str, weeks: int = 12, conn=Depends(get_db)):
    rows = conn.execute(
        text("SELECT * FROM zip_scores WHERE zip_code=:z ORDER BY score_date DESC LIMIT :w"),
        {"z": zip_code, "w": weeks}
    ).fetchall()
    return [dict(r._mapping) for r in rows]


@app.get("/alerts")
def get_alerts(conn=Depends(get_db)):
    rows = conn.execute(
        text("SELECT * FROM alerts ORDER BY fired_at DESC LIMIT 50")
    ).fetchall()
    return [dict(r._mapping) for r in rows]


@app.get("/export/csv")
def export_csv(conn=Depends(get_db)):
    rows = conn.execute(
        text("SELECT * FROM zip_scores ORDER BY score_date DESC, first_mover_score DESC LIMIT 500")
    ).fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    if rows:
        writer.writerow(rows[0]._mapping.keys())
        for r in rows:
            writer.writerow(r._mapping.values())
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=zoneiq_scores.csv"})


@app.post("/run-pipeline")
def run_pipeline(x_admin_secret: str = Header(None)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized")
    from scheduler import run_once
    run_once()
    return {"status": "pipeline triggered"}
