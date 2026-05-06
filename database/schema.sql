-- ZoneIQ Database Schema
CREATE TABLE IF NOT EXISTS zip_scores (
    id SERIAL PRIMARY KEY,
    zip_code VARCHAR(10) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(2) DEFAULT 'GA',
    first_mover_score NUMERIC(5,2),
    business_license_score NUMERIC(5,2),
    liquor_license_score NUMERIC(5,2),
    school_enrollment_score NUMERIC(5,2),
    google_trends_score NUMERIC(5,2),
    building_permit_score NUMERIC(5,2),
    score_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_zip_scores_zip ON zip_scores(zip_code);
CREATE INDEX IF NOT EXISTS idx_zip_scores_date ON zip_scores(score_date);
CREATE INDEX IF NOT EXISTS idx_zip_scores_score ON zip_scores(first_mover_score DESC);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    zip_code VARCHAR(10) NOT NULL,
    score_jump NUMERIC(5,2),
    prev_score NUMERIC(5,2),
    new_score NUMERIC(5,2),
    fired_at TIMESTAMP DEFAULT NOW()
);

-- Seed 45 Atlanta Metro zip codes
INSERT INTO zip_scores (zip_code, city, first_mover_score, business_license_score, liquor_license_score, school_enrollment_score, google_trends_score, building_permit_score, score_date) VALUES
('30005', 'Alpharetta', 72.5, 75.0, 68.0, 74.0, 71.0, 75.0, CURRENT_DATE),
('30009', 'Alpharetta', 68.3, 70.0, 65.0, 69.0, 67.0, 71.0, CURRENT_DATE),
('30022', 'Johns Creek', 78.1, 80.0, 75.0, 79.0, 77.0, 80.0, CURRENT_DATE),
('30024', 'Suwanee', 74.6, 76.0, 72.0, 75.0, 74.0, 76.0, CURRENT_DATE),
('30033', 'Decatur', 65.2, 67.0, 70.0, 63.0, 65.0, 61.0, CURRENT_DATE),
('30040', 'Cumming', 71.8, 73.0, 69.0, 72.0, 71.0, 74.0, CURRENT_DATE),
('30041', 'Cumming', 69.4, 71.0, 66.0, 70.0, 69.0, 71.0, CURRENT_DATE),
('30043', 'Lawrenceville', 60.1, 62.0, 58.0, 61.0, 59.0, 61.0, CURRENT_DATE),
('30044', 'Lawrenceville', 58.7, 60.0, 56.0, 59.0, 58.0, 60.0, CURRENT_DATE),
('30062', 'Marietta', 63.5, 65.0, 61.0, 64.0, 62.0, 65.0, CURRENT_DATE),
('30066', 'Marietta', 62.0, 63.0, 59.0, 63.0, 61.0, 64.0, CURRENT_DATE),
('30067', 'Marietta', 59.3, 61.0, 57.0, 60.0, 58.0, 60.0, CURRENT_DATE),
('30068', 'Marietta', 64.8, 66.0, 63.0, 65.0, 64.0, 66.0, CURRENT_DATE),
('30075', 'Roswell', 73.2, 75.0, 71.0, 74.0, 72.0, 74.0, CURRENT_DATE),
('30076', 'Roswell', 70.9, 72.0, 69.0, 71.0, 70.0, 72.0, CURRENT_DATE),
('30092', 'Peachtree Corners', 76.4, 78.0, 74.0, 77.0, 75.0, 78.0, CURRENT_DATE),
('30096', 'Duluth', 67.1, 69.0, 64.0, 68.0, 66.0, 69.0, CURRENT_DATE),
('30097', 'Duluth', 69.8, 71.0, 67.0, 70.0, 69.0, 72.0, CURRENT_DATE),
('30101', 'Acworth', 61.5, 63.0, 59.0, 62.0, 60.0, 63.0, CURRENT_DATE),
('30102', 'Acworth', 59.0, 61.0, 57.0, 60.0, 58.0, 59.0, CURRENT_DATE),
('30114', 'Canton', 66.3, 68.0, 63.0, 67.0, 65.0, 68.0, CURRENT_DATE),
('30115', 'Canton', 64.7, 66.0, 61.0, 65.0, 63.0, 68.0, CURRENT_DATE),
('30127', 'Powder Springs', 57.4, 59.0, 54.0, 58.0, 56.0, 60.0, CURRENT_DATE),
('30132', 'Dallas', 53.2, 55.0, 50.0, 54.0, 52.0, 55.0, CURRENT_DATE),
('30144', 'Kennesaw', 66.9, 68.0, 64.0, 67.0, 66.0, 69.0, CURRENT_DATE),
('30152', 'Kennesaw', 65.1, 67.0, 62.0, 66.0, 64.0, 66.0, CURRENT_DATE),
('30188', 'Woodstock', 70.2, 72.0, 68.0, 71.0, 69.0, 71.0, CURRENT_DATE),
('30189', 'Woodstock', 68.6, 70.0, 66.0, 69.0, 68.0, 70.0, CURRENT_DATE),
('30213', 'Fairburn', 48.5, 50.0, 45.0, 49.0, 47.0, 52.0, CURRENT_DATE),
('30228', 'Hampton', 45.1, 47.0, 42.0, 46.0, 44.0, 46.0, CURRENT_DATE),
('30238', 'Jonesboro', 44.8, 46.0, 42.0, 45.0, 43.0, 48.0, CURRENT_DATE),
('30260', 'Morrow', 43.2, 45.0, 41.0, 44.0, 42.0, 44.0, CURRENT_DATE),
('30269', 'Peachtree City', 72.8, 74.0, 70.0, 73.0, 72.0, 75.0, CURRENT_DATE),
('30277', 'Sharpsburg', 51.3, 53.0, 48.0, 52.0, 50.0, 53.0, CURRENT_DATE),
('30281', 'Stockbridge', 49.7, 51.0, 47.0, 50.0, 48.0, 53.0, CURRENT_DATE),
('30291', 'Union City', 41.5, 43.0, 39.0, 42.0, 40.0, 43.0, CURRENT_DATE),
('30294', 'Ellenwood', 46.3, 48.0, 44.0, 47.0, 45.0, 47.0, CURRENT_DATE),
('30301', 'Atlanta', 55.0, 57.0, 60.0, 53.0, 55.0, 50.0, CURRENT_DATE),
('30306', 'Atlanta-VH', 82.5, 84.0, 88.0, 80.0, 82.0, 79.0, CURRENT_DATE),
('30307', 'Atlanta-Inman', 85.3, 86.0, 90.0, 83.0, 85.0, 82.0, CURRENT_DATE),
('30308', 'Atlanta-Midtown', 80.1, 81.0, 85.0, 78.0, 80.0, 76.0, CURRENT_DATE),
('30309', 'Atlanta-Midtown', 79.4, 80.0, 84.0, 77.0, 79.0, 77.0, CURRENT_DATE),
('30316', 'Atlanta-EAV', 77.8, 79.0, 83.0, 76.0, 77.0, 74.0, CURRENT_DATE),
('30317', 'Kirkwood', 76.2, 78.0, 81.0, 74.0, 76.0, 72.0, CURRENT_DATE),
('30318', 'Atlanta-W', 74.5, 76.0, 79.0, 72.0, 74.0, 71.0, CURRENT_DATE);
