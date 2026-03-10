#!/bin/bash
# ============================================================================
# E2 Bot Database Initialization Script
# ============================================================================
# This script creates the e2bot_dev database and applies the complete V43 schema
# It runs automatically on first container startup via docker-entrypoint-initdb.d
# ============================================================================

set -e

echo "=============================================="
echo "E2 Bot Database Initialization"
echo "=============================================="

# Create e2bot_dev database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
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
EOSQL

echo "✅ Database e2bot_dev created"
echo "📋 Applying V43 schema with all tables and columns..."

# Apply schema to e2bot_dev database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "e2bot_dev" -f /docker-entrypoint-initdb.d/01_schema.sql

echo "✅ V43 schema applied"

# Apply appointment functions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "e2bot_dev" -f /docker-entrypoint-initdb.d/02_appointment_functions.sql

echo "✅ Appointment functions created"

# Verify critical V43 columns
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "e2bot_dev" <<-EOSQL
    DO \$\$
    DECLARE
        v_column_count INTEGER;
    BEGIN
        SELECT COUNT(*)
        INTO v_column_count
        FROM information_schema.columns
        WHERE table_name = 'conversations'
        AND column_name IN ('service_id', 'contact_name', 'contact_email', 'city');

        IF v_column_count = 4 THEN
            RAISE NOTICE '✅ All 4 V43 columns verified: service_id, contact_name, contact_email, city';
        ELSE
            RAISE EXCEPTION '❌ Only % V43 columns found (expected 4)', v_column_count;
        END IF;
    END \$\$;
EOSQL

echo "=============================================="
echo "✅ E2 Bot Database Initialization Complete"
echo "=============================================="
