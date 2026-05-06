# ZoneIQ Backend

Neighborhood Boom Predictor — First Mover Score engine for Atlanta Metro area.

## What It Does

Combines public data signals weekly to score every zip code 0-100:
- Business license filings (new businesses opening)
- Liquor license activity (nightlife / entertainment growth)
- School enrollment trends (family migration)
- Google Trends keyword interest (search momentum)
- Building permits (construction activity)

Outputs a **First Mover Score** with tier: EARLY_BOOM / WARMING / NEUTRAL / DECLINING

## Tech Stack

- Python 3.11
- FastAPI
- PostgreSQL (Supabase or Railway Postgres)
- APScheduler (weekly pipeline)
- Deployed on Railway

## Project Structure

```
zoneiq-backend/
  main.py              # FastAPI app + all API endpoints
  scheduler.py         # Weekly pipeline runner + alert firing
  requirements.txt     # Python dependencies
  Procfile             # Heroku/Railway process config
  .env.example         # Required environment variables
  scoring/
    engine.py          # Weighted scoring model
  ingestion/
    business_licenses.py
    liquor_licenses.py
    school_enrollment.py
    google_trends.py
  database/
    schema.sql         # PostgreSQL schema + Atlanta zip seeds
  backtest/
    api.py             # Backtesting endpoints
```

## Quick Deploy to Railway (Free)

1. Go to https://railway.app and sign in with GitHub
2. Click **New Project** → **Deploy from GitHub Repo**
3. Select `zoneiq-backend`
4. Add a **PostgreSQL** plugin inside the project
5. Set environment variables (see `.env.example`):
   - `DATABASE_URL` — auto-set by Railway Postgres plugin
   - `SECRET_KEY` — any random string
6. Railway auto-detects `Procfile` and deploys
7. Run schema: copy contents of `database/schema.sql` into Railway Postgres console

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/scores` | All latest zip scores |
| GET | `/scores/{zip_code}` | Score for one zip |
| GET | `/scores/top?limit=10` | Top scoring zips |
| GET | `/history/{zip_code}` | Score history |
| GET | `/alerts` | Recent alerts fired |
| GET | `/export/csv` | Download scores as CSV |
| POST | `/pipeline/run` | Manually trigger pipeline |
| GET | `/backtest/single?zip_code=30303` | Backtest one zip |
| GET | `/backtest/summary` | Backtest all zips |
| GET | `/backtest/rolling/csv` | Download rolling backtest CSV |

## Alert Logic

An alert fires when a zip code score increases by 15+ points in one week (configurable via `ALERT_THRESHOLD` env var).

## Configuration

Copy `.env.example` to `.env` and fill in values before deploying.

## Author

Built by saipedhapadu-blip
