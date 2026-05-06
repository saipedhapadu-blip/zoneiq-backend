import requests
import random

ATLANTA_ZIP_CITY_MAP = {
    "30005": "alpharetta", "30009": "alpharetta", "30022": "johns_creek",
    "30024": "suwanee", "30033": "decatur", "30040": "cumming",
    "30041": "cumming", "30043": "lawrenceville", "30044": "lawrenceville",
    "30075": "roswell", "30076": "roswell", "30092": "peachtree_corners",
    "30306": "atlanta", "30307": "atlanta", "30308": "atlanta", "30309": "atlanta"
}


def fetch_business_license_score(zip_code: str) -> float:
    """
    Fetches new business license filings for a zip code.
    Uses Fulton County Open Data (Socrata) where available.
    Falls back to simulated normalized score (0-100) for other zips.
    """
    try:
        # Attempt Fulton County open data (30301-30319 range)
        if zip_code.startswith("303"):
            url = "https://data.fultoncountyga.gov/resource/business-licenses.json"
            params = {"$where": f"zip_code='{zip_code}'", "$limit": 100}
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                count = len(data)
                # Normalize: 0 licenses = 20, 50+ licenses = 95
                score = min(95.0, 20.0 + (count / 50.0) * 75.0)
                return round(score, 2)
    except Exception:
        pass
    # Fallback: return a stable simulated score based on zip
    seed = sum(ord(c) for c in zip_code)
    random.seed(seed)
    return round(random.uniform(45.0, 90.0), 2)
