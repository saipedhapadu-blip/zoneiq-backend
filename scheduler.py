import os
import logging
from datetime import date
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from apscheduler.schedulers.blocking import BlockingScheduler

from ingestion.business_licenses import fetch_business_license_score
from ingestion.liquor_licenses import fetch_liquor_license_score
from ingestion.school_enrollment import fetch_school_enrollment_score
from ingestion.google_trends import fetch_google_trends_score
from scoring.engine import compute_score

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
ALERT_THRESHOLD = int(os.getenv("ALERT_THRESHOLD", "15"))

ATLANTA_ZIPS = [
    "30005", "30009", "30022", "30024", "30033", "30040", "30041",
    "30043", "30044", "30062", "30066", "30067", "30068", "30075",
    "30076", "30092", "30096", "30097", "30101", "30102", "30114",
    "30115", "30127", "30132", "30144", "30152", "30188", "30189",
    "30213", "30228", "30238", "30260", "30269", "30277", "30281",
    "30291", "30294", "30301", "30306", "30307", "30308", "30309",
    "30316", "30317", "30318"
]


def run_once():
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set")
        return
    engine = create_engine(DATABASE_URL)
    logger.info(f"Pipeline starting for {len(ATLANTA_ZIPS)} zip codes...")
    with engine.connect() as conn:
        for zip_code in ATLANTA_ZIPS:
            try:
                signals = {
                    "business_license_score": fetch_business_license_score(zip_code),
                    "liquor_license_score": fetch_liquor_license_score(zip_code),
                    "school_enrollment_score": fetch_school_enrollment_score(zip_code),
                    "google_trends_score": fetch_google_trends_score(zip_code),
                    "building_permit_score": 50.0,
                }
                scored = compute_score(signals)
                # Get previous score for alert detection
                prev = conn.execute(
                    text("SELECT first_mover_score FROM zip_scores WHERE zip_code=:z ORDER BY score_date DESC LIMIT 1"),
                    {"z": zip_code}
                ).fetchone()
                conn.execute(text("""
                    INSERT INTO zip_scores (zip_code, first_mover_score, business_license_score,
                        liquor_license_score, school_enrollment_score, google_trends_score,
                        building_permit_score, score_date)
                    VALUES (:zip, :fms, :bls, :lls, :ses, :gts, :bps, :sd)
                """), {
                    "zip": zip_code,
                    "fms": scored["first_mover_score"],
                    "bls": scored["business_license_score"],
                    "lls": scored["liquor_license_score"],
                    "ses": scored["school_enrollment_score"],
                    "gts": scored["google_trends_score"],
                    "bps": scored["building_permit_score"],
                    "sd": scored["score_date"],
                })
                # Fire alert if score jumped >= threshold
                if prev:
                    jump = scored["first_mover_score"] - float(prev[0])
                    if jump >= ALERT_THRESHOLD:
                        conn.execute(text("""
                            INSERT INTO alerts (zip_code, score_jump, prev_score, new_score)
                            VALUES (:z, :j, :p, :n)
                        """), {"z": zip_code, "j": jump, "p": float(prev[0]), "n": scored["first_mover_score"]})
                        logger.info(f"ALERT fired for {zip_code}: +{jump:.1f} pts")
                conn.commit()
                logger.info(f"Scored {zip_code}: {scored['first_mover_score']}")
            except Exception as e:
                logger.error(f"Error processing {zip_code}: {e}")
    logger.info("Pipeline complete.")


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(run_once, "cron", day_of_week="mon", hour=6, minute=0)
    logger.info("Scheduler started. Pipeline runs every Monday at 6AM ET.")
    run_once()  # Run immediately on startup
    scheduler.start()
