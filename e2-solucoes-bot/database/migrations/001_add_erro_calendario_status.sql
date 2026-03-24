-- ============================================================================
-- Migration: Add 'erro_calendario' status to appointments
-- ============================================================================
-- Date: 2026-03-13
-- Version: 001
-- Description: Allow appointments to have 'erro_calendario' status when
--              Google Calendar event creation fails in Workflow V2.0
-- ============================================================================

BEGIN;

-- Remove old constraint
ALTER TABLE appointments DROP CONSTRAINT IF EXISTS valid_status;

-- Add new constraint with 'erro_calendario'
ALTER TABLE appointments ADD CONSTRAINT valid_status
CHECK (status IN (
    'agendado',
    'confirmado',
    'em_andamento',
    'realizado',
    'cancelado',
    'reagendado',
    'no_show',
    'erro_calendario'  -- NEW STATUS for Google Calendar failures
));

-- Create index for error tracking and monitoring
CREATE INDEX IF NOT EXISTS idx_appointments_error_status
ON appointments(status)
WHERE status = 'erro_calendario';

COMMIT;

-- ============================================================================
-- Verification Query
-- ============================================================================
-- Run this to verify the migration succeeded:
--
-- SELECT conname, pg_get_constraintdef(oid)
-- FROM pg_constraint
-- WHERE conrelid = 'appointments'::regclass
--   AND conname = 'valid_status';
-- ============================================================================
