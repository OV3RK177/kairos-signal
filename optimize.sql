-- 1. Turn on the TimescaleDB Extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- 2. Ensure it is a Hypertable (Migrate existing data if necessary)
-- This organizes data by time chunks (1 day per chunk)
SELECT create_hypertable('live_metrics', 'time', 
    chunk_time_interval => INTERVAL '1 day', 
    if_not_exists => TRUE, 
    migrate_data => TRUE
);

-- 3. Configure Compression Settings
-- We group by 'project' and 'metric' to crush repetitive text
ALTER TABLE live_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'project, metric',
    timescaledb.compress_orderby = 'time DESC'
);

-- 4. Enable Automatic Compression Policy
-- This tells the DB: "If data is older than 3 days, crush it."
-- We use a DO block to handle cases where the policy might already exist.
DO $$
BEGIN
    PERFORM add_compression_policy('live_metrics', INTERVAL '3 days');
EXCEPTION WHEN unique_violation THEN
    RAISE NOTICE 'Compression policy already exists.';
WHEN OTHERS THEN
    RAISE NOTICE 'Note: %', SQLERRM;
END $$;

-- 5. Verify
SELECT hypertable_name, compression_enabled FROM timescaledb_information.hypertables;
