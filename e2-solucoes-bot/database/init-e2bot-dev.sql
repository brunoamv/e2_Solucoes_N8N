-- ============================================================================
-- E2 Bot Database Initialization Script
-- ============================================================================
-- This script creates the e2bot_dev database and applies the V43 schema
-- It runs automatically on first container startup via docker-compose
-- ============================================================================

-- Terminate existing connections (if any)
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'e2bot_dev'
  AND pid <> pg_backend_pid();

-- Drop database if exists (clean slate)
DROP DATABASE IF EXISTS e2bot_dev;

-- Create the e2bot_dev database
CREATE DATABASE e2bot_dev
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Connect to the new database for subsequent commands
\c e2bot_dev

-- Log successful creation
DO $$
BEGIN
    RAISE NOTICE '✅ Database e2bot_dev created successfully';
    RAISE NOTICE '📋 Applying V43 schema with all required columns...';
END $$;
