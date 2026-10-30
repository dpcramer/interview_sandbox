-- One row per school we track.
CREATE TABLE schools (
    school_id   TEXT PRIMARY KEY,
    school_name TEXT NOT NULL
);

-- One row per scrape run (weekly in production). Here: 'previous' and 'current'.
CREATE TABLE snapshots (
    snapshot_id TEXT PRIMARY KEY,
    captured_at TEXT  -- ISO 8601
);

-- Which schools a snapshot actually scraped successfully. A person can only be called a
-- departure if their school is covered; otherwise their status is unknown.
CREATE TABLE snapshot_coverage (
    snapshot_id TEXT NOT NULL REFERENCES snapshots (snapshot_id),
    school_id   TEXT NOT NULL REFERENCES schools (school_id),
    PRIMARY KEY (snapshot_id, school_id)
);

-- Append-only: what one snapshot saw for one person. Raw title is kept next to the
-- normalized one so rules can be re-run over history. staff_id is only set when the
-- source already carries a confirmed identity (the previous snapshot).
CREATE TABLE staff_observations (
    observation_id  TEXT PRIMARY KEY,
    snapshot_id     TEXT NOT NULL REFERENCES snapshots (snapshot_id),
    school_id       TEXT NOT NULL REFERENCES schools (school_id),
    staff_id        TEXT,
    name            TEXT NOT NULL,
    name_key        TEXT NOT NULL,
    title           TEXT,
    title_raw       TEXT,
    email           TEXT,
    phone           TEXT,
    source_provider TEXT NOT NULL,
    source_url      TEXT
);
