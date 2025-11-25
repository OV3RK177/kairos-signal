-- 1. Turn on Compression Setting
ALTER TABLE live_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'project, metric',
    timescaledb.compress_orderby = 'time DESC'
);

-- 2. Add the Automation Policy (Compress data older than 1 day)
-- Wrapped in a block to prevent errors if it already exists
DO $$
BEGIN
    PERFORM add_compression_policy('live_metrics', INTERVAL '1 day');
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Policy might already exist, skipping.';
END $$;

-- 3. Check Status
SELECT hypertable_name, compression_enabled 
FROM timescaledb_information.hypertables 
WHERE hypertable_name = 'live_metrics';
