-- execute from task 1 directory
-- docker compose exec -T timescaledb psql -U postgres -d fitbit_data < "../Task 3/db_optimizations/heart_rate_aggregations/heart_rate_aggregations.sql"

-- Drop existing objects with improved error handling
DO $$

DECLARE
    view_name TEXT;
    ts_info_exists BOOLEAN;
BEGIN
    -- Check if TimescaleDB information schema is available
    SELECT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE schemaname = 'timescaledb_information'
        AND tablename = 'continuous_aggregates'
    ) INTO ts_info_exists;

    -- If TimescaleDB information schema exists, try to remove policies
    IF ts_info_exists THEN
        BEGIN
            FOR view_name IN (
                SELECT view_name 
                FROM timescaledb_information.continuous_aggregate_policies
                WHERE view_name LIKE 'heart_rate_%'
            ) LOOP
                BEGIN
                    EXECUTE FORMAT('SELECT remove_continuous_aggregate_policy(%L, if_exists => true)', view_name);
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'Error removing policy for %: %', view_name, SQLERRM;
                END;
            END LOOP;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Could not access continuous aggregate policies: %', SQLERRM;
        END;
    END IF;

    -- Drop materialized views directly (more reliable method)
    FOR view_name IN (
        SELECT table_name FROM information_schema.tables
        WHERE table_name LIKE 'heart_rate_%'
        AND (table_name = 'heart_rate_1m' OR 
             table_name = 'heart_rate_1h' OR 
             table_name = 'heart_rate_1d' OR 
             table_name = 'heart_rate_1w' OR 
             table_name = 'heart_rate_1mo')
    ) LOOP
        BEGIN
            EXECUTE format('DROP MATERIALIZED VIEW IF EXISTS %I CASCADE', view_name);
            RAISE NOTICE 'Dropped view: %', view_name;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Error dropping %: %', view_name, SQLERRM;
        END;
    END LOOP;
END $$;
-- Create heart rate aggregation views
CREATE OR REPLACE FUNCTION create_heart_rate_aggregations() RETURNS VOID AS $$
BEGIN
    -- Minutely: continuous aggregate (from hypertable)
CREATE MATERIALIZED VIEW IF NOT EXISTS heart_rate_1m WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', timestamp) AS bucket,
    user_id,
    device_id,
    AVG(value) AS avg_heart_rate,
    MIN(value) AS min_heart_rate,
    MAX(value) AS max_heart_rate,
    COUNT(*) AS sample_count,
    AVG(resting_heart_rate) AS avg_resting_heart_rate
FROM heart_rate
GROUP BY bucket, user_id, device_id
WITH NO DATA;

-- Hourly: regular materialized view (from minutely)
CREATE MATERIALIZED VIEW IF NOT EXISTS heart_rate_1h AS
SELECT
    time_bucket('1 hour', bucket) AS bucket,
    user_id,
    device_id,
    AVG(avg_heart_rate) AS avg_heart_rate,
    MIN(min_heart_rate) AS min_heart_rate,
    MAX(max_heart_rate) AS max_heart_rate,
    SUM(sample_count) AS sample_count,
    AVG(avg_resting_heart_rate) AS avg_resting_heart_rate
FROM heart_rate_1m
GROUP BY bucket, user_id, device_id
WITH NO DATA;

-- Daily: regular materialized view (from hourly)
CREATE MATERIALIZED VIEW IF NOT EXISTS heart_rate_1d AS
SELECT
    time_bucket('1 day', bucket) AS bucket,
    user_id,
    device_id,
    AVG(avg_heart_rate) AS avg_heart_rate,
    MIN(min_heart_rate) AS min_heart_rate,
    MAX(max_heart_rate) AS max_heart_rate,
    SUM(sample_count) AS sample_count,
    AVG(avg_resting_heart_rate) AS avg_resting_heart_rate
FROM heart_rate_1h
GROUP BY bucket, user_id, device_id
WITH NO DATA;

-- Weekly: regular materialized view (from daily)
CREATE MATERIALIZED VIEW IF NOT EXISTS heart_rate_1w AS
SELECT
    time_bucket('7 days', bucket) AS bucket,
    user_id,
    device_id,
    AVG(avg_heart_rate) AS avg_heart_rate,
    MIN(min_heart_rate) AS min_heart_rate,
    MAX(max_heart_rate) AS max_heart_rate,
    SUM(sample_count) AS sample_count,
    AVG(avg_resting_heart_rate) AS avg_resting_heart_rate
FROM heart_rate_1d
GROUP BY bucket, user_id, device_id
WITH NO DATA;

-- Monthly: regular materialized view (from weekly)
CREATE MATERIALIZED VIEW IF NOT EXISTS heart_rate_1mo AS
SELECT
    time_bucket('30 days', bucket) AS bucket,
    user_id,
    device_id,
    AVG(avg_heart_rate) AS avg_heart_rate,
    MIN(min_heart_rate) AS min_heart_rate,
    MAX(max_heart_rate) AS max_heart_rate,
    SUM(sample_count) AS sample_count,
    AVG(avg_resting_heart_rate) AS avg_resting_heart_rate
FROM heart_rate_1w
GROUP BY bucket, user_id, device_id
WITH NO DATA;

    -- Set up refresh policies
    PERFORM create_heart_rate_refresh_policies();

    RAISE NOTICE 'Created all heart rate continuous aggregates';
END;
$$ LANGUAGE PLPGSQL;

-- Set up refresh policies for heart rate aggregations
CREATE OR REPLACE FUNCTION create_heart_rate_refresh_policies() RETURNS VOID AS $$
BEGIN
    -- Minutely aggregation policy
    BEGIN
        EXECUTE 'SELECT add_continuous_aggregate_policy(''heart_rate_1m'', 
                    start_offset => INTERVAL ''2 days'',
                    end_offset => INTERVAL ''1 hour'',
                    schedule_interval => INTERVAL ''1 hour'', 
                    if_not_exists => true)';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Policy for heart_rate_1m already exists or error: %', SQLERRM;
    END;

    -- Hourly aggregation policy
    BEGIN
        EXECUTE 'SELECT add_continuous_aggregate_policy(''heart_rate_1h'', 
                    start_offset => INTERVAL ''7 days'',
                    end_offset => INTERVAL ''1 hour'',
                    schedule_interval => INTERVAL ''6 hours'', 
                    if_not_exists => true)';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Policy for heart_rate_1h already exists or error: %', SQLERRM;
    END;

    -- Daily aggregation policy
    BEGIN
        EXECUTE 'SELECT add_continuous_aggregate_policy(''heart_rate_1d'', 
                    start_offset => INTERVAL ''30 days'',
                    end_offset => INTERVAL ''1 hour'',
                    schedule_interval => INTERVAL ''1 day'', 
                    if_not_exists => true)';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Policy for heart_rate_1d already exists or error: %', SQLERRM;
    END;

    -- Weekly aggregation policy
    BEGIN
        EXECUTE 'SELECT add_continuous_aggregate_policy(''heart_rate_1w'', 
                    start_offset => INTERVAL ''90 days'',
                    end_offset => INTERVAL ''1 day'',
                    schedule_interval => INTERVAL ''7 days'', 
                    if_not_exists => true)';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Policy for heart_rate_1w already exists or error: %', SQLERRM;
    END;

    -- Monthly aggregation policy
    BEGIN
        EXECUTE 'SELECT add_continuous_aggregate_policy(''heart_rate_1mo'', 
                    start_offset => INTERVAL ''365 days'',
                    end_offset => INTERVAL ''1 day'',
                    schedule_interval => INTERVAL ''30 days'', 
                    if_not_exists => true)';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Policy for heart_rate_1mo already exists or error: %', SQLERRM;
    END;

    RAISE NOTICE 'Created all heart rate continuous aggregate policies';
END;
$$ LANGUAGE PLPGSQL;

-- Function to refresh a specific aggregation level with intelligent dependency management
CREATE OR REPLACE FUNCTION refresh_heart_rate_aggregation(
    level TEXT,
    start_date TIMESTAMP DEFAULT NULL,
    end_date TIMESTAMP DEFAULT NULL
) RETURNS TEXT AS $$
DECLARE
    start_ts TIMESTAMP;
    end_ts TIMESTAMP;
    last_refresh_time TIMESTAMP;
    refresh_needed BOOLEAN;
    result_message TEXT;
BEGIN
    -- Default date range if not provided
    IF start_date IS NULL THEN
        start_ts := NOW() - INTERVAL '30 days';
    ELSE
        start_ts := start_date;
    END IF;
    
    IF end_date IS NULL THEN
        end_ts := NOW();
    ELSE
        end_ts := end_date;
    END IF;
    
    -- Check if refresh is needed by comparing with last refresh time
    SELECT last_refresh INTO last_refresh_time 
    FROM timescaledb_information.continuous_aggregates 
    WHERE view_name = 'heart_rate_' || level;
    
    -- Skip if already fresh (within 1 hour margin)
    IF last_refresh_time IS NOT NULL AND last_refresh_time >= end_ts - INTERVAL '1 hour' THEN
        RETURN 'Aggregation heart_rate_' || level || ' is already up-to-date (last refresh: ' || last_refresh_time || ')';
    END IF;
    
    result_message := 'To refresh heart_rate_' || level || ' from ' || start_ts || ' to ' || end_ts || ', run these commands in sequence:';
    
    -- Build refresh commands based on level with dependencies
    CASE level
        WHEN '1m' THEN
            result_message := result_message || E'\n1. CALL refresh_continuous_aggregate(''heart_rate_1m'', ''' || start_ts || ''', ''' || end_ts || ''');';
            
        WHEN '1h' THEN
            result_message := result_message || E'\n1. CALL refresh_continuous_aggregate(''heart_rate_1m'', ''' || start_ts || ''', ''' || end_ts || ''');' ||
                            E'\n2. CALL refresh_continuous_aggregate(''heart_rate_1h'', ''' || start_ts || ''', ''' || end_ts || ''');';
            
        WHEN '1d' THEN
            result_message := result_message || E'\n1. CALL refresh_continuous_aggregate(''heart_rate_1m'', ''' || start_ts || ''', ''' || end_ts || ''');' ||
                            E'\n2. CALL refresh_continuous_aggregate(''heart_rate_1h'', ''' || start_ts || ''', ''' || end_ts || ''');' ||
                            E'\n3. CALL refresh_continuous_aggregate(''heart_rate_1d'', ''' || start_ts || ''', ''' || end_ts || ''');';
            
        WHEN '1w' THEN
            result_message := result_message || E'\n1. CALL refresh_continuous_aggregate(''heart_rate_1h'', ''' || start_ts || ''', ''' || end_ts || ''');' ||
                            E'\n2. CALL refresh_continuous_aggregate(''heart_rate_1d'', ''' || start_ts || ''', ''' || end_ts || ''');' ||
                            E'\n3. CALL refresh_continuous_aggregate(''heart_rate_1w'', ''' || start_ts || ''', ''' || end_ts || ''');';
            
        WHEN '1mo' THEN
            result_message := result_message || E'\n1. CALL refresh_continuous_aggregate(''heart_rate_1d'', ''' || start_ts || ''', ''' || end_ts || ''');' ||
                            E'\n2. CALL refresh_continuous_aggregate(''heart_rate_1w'', ''' || start_ts || ''', ''' || end_ts || ''');' ||
                            E'\n3. CALL refresh_continuous_aggregate(''heart_rate_1mo'', ''' || start_ts || ''', ''' || end_ts || ''');';
            
        ELSE
            RETURN 'Invalid aggregation level. Use 1m, 1h, 1d, 1w, or 1mo.';
    END CASE;
    
    RETURN result_message;
END;
$$ LANGUAGE PLPGSQL;

-- Function to select optimal aggregation table based on date range
CREATE OR REPLACE FUNCTION get_optimal_heart_rate_table(
    start_date TIMESTAMP, 
    end_date TIMESTAMP
) RETURNS TEXT AS $$
DECLARE
    interval_days INTEGER;
    table_name TEXT;
BEGIN
    interval_days := EXTRACT(DAY FROM (end_date - start_date));
    
    IF interval_days <= 1 THEN
        table_name := 'heart_rate'; -- Raw data
    ELSIF interval_days <= 7 THEN
        table_name := 'heart_rate_1h'; -- Hourly aggregates
    ELSIF interval_days <= 30 THEN
        table_name := 'heart_rate_1d'; -- Daily aggregates
    ELSIF interval_days <= 90 THEN
        table_name := 'heart_rate_1w'; -- Weekly aggregates
    ELSE
        table_name := 'heart_rate_1mo'; -- Monthly aggregates
    END IF;
    
    RETURN table_name;
END;
$$ LANGUAGE PLPGSQL;

-- Function to get statistics about heart rate aggregations
CREATE OR REPLACE FUNCTION get_heart_rate_aggregation_stats() RETURNS TABLE (
    level TEXT,
    last_refresh TIMESTAMPTZ,
    total_rows BIGINT,
    size_bytes BIGINT,
    compression_ratio NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN relname = 'heart_rate_1m' THEN '1m'
            WHEN relname = 'heart_rate_1h' THEN '1h'
            WHEN relname = 'heart_rate_1d' THEN '1d'
            WHEN relname = 'heart_rate_1w' THEN '1w'
            WHEN relname = 'heart_rate_1mo' THEN '1mo'
        END AS level,
        ca.last_refresh,
        COALESCE(pg_total_relation_size(format('%I.%I', nspname, hypertable_name)), 0) AS size_bytes,
        (SELECT COUNT(*) FROM (SELECT 1 FROM ONLY pg_catalog.pg_class c WHERE relname = relname) t) AS total_rows,
        CASE
            WHEN pg_total_relation_size(format('%I.%I', nspname, hypertable_name)) > 0 AND
                 (SELECT SUM(pg_total_relation_size(format('%I.%I', nspname, c.relname)))
                  FROM pg_class c
                  WHERE c.relkind = 'r' AND c.relname LIKE format('%s_%%', hypertable_name)) > 0
            THEN
                pg_total_relation_size(format('%I.%I', nspname, hypertable_name))::numeric /
                (SELECT SUM(pg_total_relation_size(format('%I.%I', nspname, c.relname)))
                 FROM pg_class c
                 WHERE c.relkind = 'r' AND c.relname LIKE format('%s_%%', hypertable_name))
            ELSE 1
        END AS compression_ratio
    FROM timescaledb_information.continuous_aggregates ca
    JOIN pg_class pc ON pc.relname = ca.materialization_hypertable
    JOIN pg_namespace pn ON pn.oid = pc.relnamespace
    WHERE view_name LIKE 'heart_rate_%'
    ORDER BY 
        CASE 
            WHEN view_name = 'heart_rate_1m' THEN 1
            WHEN view_name = 'heart_rate_1h' THEN 2
            WHEN view_name = 'heart_rate_1d' THEN 3
            WHEN view_name = 'heart_rate_1w' THEN 4
            WHEN view_name = 'heart_rate_1mo' THEN 5
        END;
END;
$$ LANGUAGE PLPGSQL;

-- Execute the creation of aggregations automatically if desired
-- SELECT create_heart_rate_aggregations();