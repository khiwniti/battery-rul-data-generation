-- TimescaleDB Initialization Script
-- Run this script after creating the database on Railway.com

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema for application (optional, using public by default)
-- CREATE SCHEMA IF NOT EXISTS battery_rul;

-- Performance optimizations
ALTER SYSTEM SET shared_preload_libraries = 'timescaledb';
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '10MB';

-- TimescaleDB specific settings
ALTER SYSTEM SET timescaledb.max_background_workers = 8;

-- Reload configuration
SELECT pg_reload_conf();

-- Grant permissions to application user (Railway.com auto-creates user)
-- GRANT ALL PRIVILEGES ON SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;

-- Note: After running Alembic migrations, you need to convert the telemetry table
-- to a hypertable. This is done in the second Alembic migration (002_create_telemetry_hypertable.py)
