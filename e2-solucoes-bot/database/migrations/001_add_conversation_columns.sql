-- ====================================
-- V43 MIGRATION - Add Missing Columns
-- ====================================
-- Migration Date: 2025-03-05
-- Purpose: Add columns referenced by n8n workflow V41
-- Columns: service_id, contact_name, contact_email, city
--
-- Context: V41 workflow references these columns but they don't exist
-- in the current schema, causing PostgreSQL errors and stuck executions.
--
-- Strategy: Add columns with NULL defaults (safe migration, no data loss)
-- ====================================

-- Add missing columns to conversations table
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS service_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS contact_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255),
ADD COLUMN IF NOT EXISTS city VARCHAR(100);

-- Add comments for documentation
COMMENT ON COLUMN conversations.service_id IS 'Legacy service identifier (deprecated - use service_type)';
COMMENT ON COLUMN conversations.contact_name IS 'Lead contact name (also stored in collected_data JSONB)';
COMMENT ON COLUMN conversations.contact_email IS 'Lead email address (also stored in collected_data JSONB)';
COMMENT ON COLUMN conversations.city IS 'Lead city location (also stored in collected_data JSONB)';

-- Verify migration success
DO $$
BEGIN
    -- Check if all columns exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'service_id'
    ) THEN
        RAISE EXCEPTION 'Migration failed: service_id column not created';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'contact_name'
    ) THEN
        RAISE EXCEPTION 'Migration failed: contact_name column not created';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'contact_email'
    ) THEN
        RAISE EXCEPTION 'Migration failed: contact_email column not created';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'city'
    ) THEN
        RAISE EXCEPTION 'Migration failed: city column not created';
    END IF;

    RAISE NOTICE 'V43 Migration completed successfully - All 4 columns added';
END $$;
