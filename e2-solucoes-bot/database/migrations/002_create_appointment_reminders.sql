-- Migration: Create appointment_reminders table
-- Date: 2026-03-24
-- Purpose: Store automated reminders for appointments (email, SMS, WhatsApp)

-- Create appointment_reminders table
CREATE TABLE IF NOT EXISTS appointment_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    reminder_type VARCHAR(20) NOT NULL CHECK (reminder_type IN ('email', 'sms', 'whatsapp', 'push')),
    reminder_time TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    sent_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Prevent duplicate reminders for same appointment/type/time
    CONSTRAINT unique_appointment_reminder UNIQUE (appointment_id, reminder_type, reminder_time)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_appointment_reminders_appointment_id
    ON appointment_reminders(appointment_id);

CREATE INDEX IF NOT EXISTS idx_appointment_reminders_status
    ON appointment_reminders(status);

CREATE INDEX IF NOT EXISTS idx_appointment_reminders_reminder_time
    ON appointment_reminders(reminder_time)
    WHERE status = 'pending';

-- Create trigger to update updated_at
CREATE OR REPLACE FUNCTION update_appointment_reminders_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_appointment_reminders_updated_at
    BEFORE UPDATE ON appointment_reminders
    FOR EACH ROW
    EXECUTE FUNCTION update_appointment_reminders_updated_at();

-- Add comments
COMMENT ON TABLE appointment_reminders IS 'Automated reminders for appointments (email, SMS, WhatsApp)';
COMMENT ON COLUMN appointment_reminders.id IS 'Primary key (UUID)';
COMMENT ON COLUMN appointment_reminders.appointment_id IS 'Foreign key to appointments table';
COMMENT ON COLUMN appointment_reminders.reminder_type IS 'Type: email, sms, whatsapp, push';
COMMENT ON COLUMN appointment_reminders.reminder_time IS 'When to send the reminder';
COMMENT ON COLUMN appointment_reminders.status IS 'Status: pending, sent, failed, cancelled';
COMMENT ON COLUMN appointment_reminders.sent_at IS 'When the reminder was actually sent';
COMMENT ON COLUMN appointment_reminders.error_message IS 'Error message if failed';
COMMENT ON COLUMN appointment_reminders.retry_count IS 'Number of retry attempts';

-- Sample query to create reminders (for reference)
-- INSERT INTO appointment_reminders (appointment_id, reminder_type, reminder_time, status)
-- SELECT
--     a.id,
--     'email' as reminder_type,
--     a.scheduled_date + (a.scheduled_time_start - interval '24 hours') as reminder_time,
--     'pending' as status
-- FROM appointments a
-- WHERE a.google_calendar_event_id IS NOT NULL
-- ON CONFLICT (appointment_id, reminder_type, reminder_time) DO NOTHING;
