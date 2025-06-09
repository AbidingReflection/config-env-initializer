-- execution_metrics.sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;

-- High-level execution records
CREATE TABLE script_executions (
    execution_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    script_name        TEXT NOT NULL,
    start_ts           INTEGER,
    end_ts             INTEGER,
    duration_ms        INTEGER GENERATED ALWAYS AS ((end_ts - start_ts)) STORED,
    log_file_name      TEXT,
    execution_failed   BOOLEAN DEFAULT 0
);


-- Section-level execution records
CREATE TABLE section_executions (
    execution_id   INTEGER NOT NULL,
    section_name   TEXT NOT NULL,
    start_ts       INTEGER NOT NULL,
    end_ts         INTEGER,
    duration_ms    INTEGER GENERATED ALWAYS AS ((end_ts - start_ts)) STORED,
    FOREIGN KEY(execution_id) REFERENCES script_executions(execution_id)
);

-- Index to speed up section lookups
CREATE INDEX IF NOT EXISTS idx_section_execution_id 
ON section_executions (execution_id);

-- Critical index for fast lookup of latest executions per script
CREATE INDEX IF NOT EXISTS idx_script_name_start_ts 
ON script_executions (script_name, start_ts DESC);
