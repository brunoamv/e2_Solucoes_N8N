-- Appointment Functions for Sprint 1.2
-- Functions to support the appointment scheduling system
-- Run this in Supabase SQL Editor after creating the appointments table

-- Function: get_upcoming_appointments
-- Retrieves appointments that need reminders to be sent
-- Used by n8n workflow 06_appointment_reminders.json
CREATE OR REPLACE FUNCTION get_upcoming_appointments(
    hours_ahead int DEFAULT 24
)
RETURNS TABLE (
    appointment_id uuid,
    lead_id uuid,
    customer_name varchar,
    phone_number varchar,
    email varchar,
    scheduled_date date,
    scheduled_time_start time,
    scheduled_time_end time,
    service_name varchar,
    address text,
    city varchar,
    state varchar,
    google_calendar_event_id varchar,
    hours_until_appointment numeric
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id as appointment_id,
        a.lead_id,
        l.customer_name,
        l.phone_number,
        l.email,
        a.scheduled_date,
        a.scheduled_time_start,
        a.scheduled_time_end,
        l.service_name,
        l.address,
        l.city,
        l.state,
        a.google_calendar_event_id,
        EXTRACT(EPOCH FROM (
            (a.scheduled_date + a.scheduled_time_start) - NOW()
        )) / 3600 as hours_until_appointment
    FROM appointments a
    JOIN leads l ON a.lead_id = l.id
    WHERE
        a.status = 'scheduled'
        AND (a.scheduled_date + a.scheduled_time_start) > NOW()
        AND (a.scheduled_date + a.scheduled_time_start) <= NOW() + (hours_ahead || ' hours')::INTERVAL
    ORDER BY a.scheduled_date, a.scheduled_time_start;
END;
$$;

-- Function: get_appointments_needing_24h_reminder
-- Returns appointments that need 24-hour reminder and haven't received it yet
CREATE OR REPLACE FUNCTION get_appointments_needing_24h_reminder()
RETURNS TABLE (
    appointment_id uuid,
    lead_id uuid,
    customer_name varchar,
    phone_number varchar,
    email varchar,
    scheduled_date date,
    scheduled_time_start time,
    service_name varchar,
    address text,
    city varchar,
    state varchar,
    technician_name varchar
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id as appointment_id,
        a.lead_id,
        l.customer_name,
        l.phone_number,
        l.email,
        a.scheduled_date,
        a.scheduled_time_start,
        l.service_name,
        l.address,
        l.city,
        l.state,
        COALESCE(a.technician_name, 'Equipe E2 Soluções') as technician_name
    FROM appointments a
    JOIN leads l ON a.lead_id = l.id
    WHERE
        a.status = 'scheduled'
        AND a.reminder_24h_sent = false
        AND (a.scheduled_date + a.scheduled_time_start) > NOW()
        AND (a.scheduled_date + a.scheduled_time_start) <= NOW() + INTERVAL '25 hours'
        AND (a.scheduled_date + a.scheduled_time_start) >= NOW() + INTERVAL '23 hours'
    ORDER BY a.scheduled_date, a.scheduled_time_start;
END;
$$;

-- Function: get_appointments_needing_2h_reminder
-- Returns appointments that need 2-hour urgent reminder and haven't received it yet
CREATE OR REPLACE FUNCTION get_appointments_needing_2h_reminder()
RETURNS TABLE (
    appointment_id uuid,
    lead_id uuid,
    customer_name varchar,
    phone_number varchar,
    email varchar,
    scheduled_date date,
    scheduled_time_start time,
    service_name varchar,
    address text,
    city varchar,
    state varchar,
    technician_name varchar,
    technician_phone varchar
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id as appointment_id,
        a.lead_id,
        l.customer_name,
        l.phone_number,
        l.email,
        a.scheduled_date,
        a.scheduled_time_start,
        l.service_name,
        l.address,
        l.city,
        l.state,
        COALESCE(a.technician_name, 'Equipe E2 Soluções') as technician_name,
        COALESCE(a.technician_phone, l.phone_number) as technician_phone
    FROM appointments a
    JOIN leads l ON a.lead_id = l.id
    WHERE
        a.status = 'scheduled'
        AND a.reminder_2h_sent = false
        AND (a.scheduled_date + a.scheduled_time_start) > NOW()
        AND (a.scheduled_date + a.scheduled_time_start) <= NOW() + INTERVAL '2 hours 30 minutes'
        AND (a.scheduled_date + a.scheduled_time_start) >= NOW() + INTERVAL '1 hour 30 minutes'
    ORDER BY a.scheduled_date, a.scheduled_time_start;
END;
$$;

-- Function: mark_reminder_sent
-- Updates reminder flags when reminders are sent successfully
CREATE OR REPLACE FUNCTION mark_reminder_sent(
    p_appointment_id uuid,
    p_reminder_type varchar -- '24h', '2h', 'post_visit'
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_reminder_type = '24h' THEN
        UPDATE appointments
        SET reminder_24h_sent = true,
            reminder_24h_sent_at = NOW(),
            updated_at = NOW()
        WHERE id = p_appointment_id;
    ELSIF p_reminder_type = '2h' THEN
        UPDATE appointments
        SET reminder_2h_sent = true,
            reminder_2h_sent_at = NOW(),
            updated_at = NOW()
        WHERE id = p_appointment_id;
    ELSIF p_reminder_type = 'post_visit' THEN
        UPDATE appointments
        SET post_visit_sent = true,
            post_visit_sent_at = NOW(),
            updated_at = NOW()
        WHERE id = p_appointment_id;
    ELSE
        RETURN false;
    END IF;

    RETURN FOUND;
END;
$$;

-- Function: get_appointment_details
-- Retrieves complete appointment information including lead data
-- Used for generating emails and notifications
CREATE OR REPLACE FUNCTION get_appointment_details(
    p_appointment_id uuid
)
RETURNS TABLE (
    appointment_id uuid,
    lead_id uuid,
    customer_name varchar,
    phone_number varchar,
    email varchar,
    scheduled_date date,
    scheduled_time_start time,
    scheduled_time_end time,
    service_name varchar,
    segment varchar,
    estimated_kwh numeric,
    estimated_kwp numeric,
    estimated_value numeric,
    address text,
    city varchar,
    state varchar,
    google_calendar_event_id varchar,
    technician_name varchar,
    technician_phone varchar,
    status varchar,
    notes text,
    created_at timestamp,
    reminder_24h_sent boolean,
    reminder_2h_sent boolean,
    post_visit_sent boolean
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id as appointment_id,
        a.lead_id,
        l.customer_name,
        l.phone_number,
        l.email,
        a.scheduled_date,
        a.scheduled_time_start,
        a.scheduled_time_end,
        l.service_name,
        l.segment,
        l.estimated_kwh,
        l.estimated_kwp,
        l.estimated_value,
        l.address,
        l.city,
        l.state,
        a.google_calendar_event_id,
        a.technician_name,
        a.technician_phone,
        a.status,
        a.notes,
        a.created_at,
        a.reminder_24h_sent,
        a.reminder_2h_sent,
        a.post_visit_sent
    FROM appointments a
    JOIN leads l ON a.lead_id = l.id
    WHERE a.id = p_appointment_id;
END;
$$;

-- Function: get_available_slots
-- Checks technician availability for scheduling
-- Returns time slots that don't have conflicting appointments
CREATE OR REPLACE FUNCTION get_available_slots(
    p_date date,
    p_technician_name varchar DEFAULT NULL,
    p_slot_duration_minutes int DEFAULT 120
)
RETURNS TABLE (
    slot_start time,
    slot_end time,
    is_available boolean
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_start_hour int := 8; -- Business hours start
    v_end_hour int := 18; -- Business hours end
    v_current_time time;
    v_slot_end time;
    v_conflict_count int;
BEGIN
    -- Generate time slots for the day
    FOR hour IN v_start_hour..(v_end_hour - (p_slot_duration_minutes / 60)) LOOP
        v_current_time := (hour || ':00:00')::time;
        v_slot_end := v_current_time + (p_slot_duration_minutes || ' minutes')::interval;

        -- Check for conflicts with existing appointments
        SELECT COUNT(*) INTO v_conflict_count
        FROM appointments a
        WHERE
            a.scheduled_date = p_date
            AND a.status IN ('scheduled', 'confirmed')
            AND (
                p_technician_name IS NULL
                OR a.technician_name = p_technician_name
            )
            AND (
                -- Check if time ranges overlap
                (a.scheduled_time_start, a.scheduled_time_end) OVERLAPS (v_current_time, v_slot_end)
            );

        slot_start := v_current_time;
        slot_end := v_slot_end;
        is_available := (v_conflict_count = 0);

        RETURN NEXT;
    END LOOP;
END;
$$;

-- Function: update_appointment_status
-- Updates appointment status with validation
CREATE OR REPLACE FUNCTION update_appointment_status(
    p_appointment_id uuid,
    p_new_status varchar,
    p_notes text DEFAULT NULL
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
    -- Validate status transition
    IF p_new_status NOT IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show', 'rescheduled') THEN
        RAISE EXCEPTION 'Invalid appointment status: %', p_new_status;
    END IF;

    UPDATE appointments
    SET
        status = p_new_status,
        notes = COALESCE(p_notes, notes),
        updated_at = NOW(),
        completed_at = CASE
            WHEN p_new_status = 'completed' THEN NOW()
            ELSE completed_at
        END,
        cancelled_at = CASE
            WHEN p_new_status = 'cancelled' THEN NOW()
            ELSE cancelled_at
        END
    WHERE id = p_appointment_id;

    RETURN FOUND;
END;
$$;

-- Function: get_appointments_for_post_visit_followup
-- Returns completed appointments that haven't received post-visit email
CREATE OR REPLACE FUNCTION get_appointments_for_post_visit_followup()
RETURNS TABLE (
    appointment_id uuid,
    lead_id uuid,
    customer_name varchar,
    phone_number varchar,
    email varchar,
    scheduled_date date,
    service_name varchar,
    address text,
    city varchar,
    state varchar,
    technician_name varchar,
    completed_at timestamp
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id as appointment_id,
        a.lead_id,
        l.customer_name,
        l.phone_number,
        l.email,
        a.scheduled_date,
        l.service_name,
        l.address,
        l.city,
        l.state,
        COALESCE(a.technician_name, 'Equipe E2 Soluções') as technician_name,
        a.completed_at
    FROM appointments a
    JOIN leads l ON a.lead_id = l.id
    WHERE
        a.status = 'completed'
        AND a.post_visit_sent = false
        AND a.completed_at IS NOT NULL
        AND a.completed_at >= NOW() - INTERVAL '7 days' -- Only recent completions
    ORDER BY a.completed_at DESC;
END;
$$;

-- Function: get_appointment_statistics
-- Returns statistics about appointments for reporting
CREATE OR REPLACE FUNCTION get_appointment_statistics(
    p_start_date date DEFAULT NULL,
    p_end_date date DEFAULT NULL
)
RETURNS TABLE (
    total_appointments bigint,
    scheduled_appointments bigint,
    completed_appointments bigint,
    cancelled_appointments bigint,
    no_show_appointments bigint,
    completion_rate numeric,
    avg_appointments_per_day numeric
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_start_date date := COALESCE(p_start_date, CURRENT_DATE - INTERVAL '30 days');
    v_end_date date := COALESCE(p_end_date, CURRENT_DATE);
    v_days_count numeric;
BEGIN
    v_days_count := v_end_date - v_start_date + 1;

    RETURN QUERY
    SELECT
        COUNT(*) as total_appointments,
        COUNT(*) FILTER (WHERE status = 'scheduled') as scheduled_appointments,
        COUNT(*) FILTER (WHERE status = 'completed') as completed_appointments,
        COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_appointments,
        COUNT(*) FILTER (WHERE status = 'no_show') as no_show_appointments,
        CASE
            WHEN COUNT(*) > 0 THEN
                ROUND(
                    (COUNT(*) FILTER (WHERE status = 'completed')::numeric / COUNT(*)::numeric) * 100,
                    2
                )
            ELSE 0
        END as completion_rate,
        ROUND(COUNT(*)::numeric / v_days_count, 2) as avg_appointments_per_day
    FROM appointments
    WHERE
        scheduled_date BETWEEN v_start_date AND v_end_date;
END;
$$;

-- Create trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_appointment_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER appointments_updated_at
BEFORE UPDATE ON appointments
FOR EACH ROW
EXECUTE FUNCTION update_appointment_timestamp();

-- Grant necessary permissions (adjust role name as needed)
-- GRANT EXECUTE ON FUNCTION get_upcoming_appointments TO anon, authenticated, service_role;
-- GRANT EXECUTE ON FUNCTION get_appointments_needing_24h_reminder TO service_role;
-- GRANT EXECUTE ON FUNCTION get_appointments_needing_2h_reminder TO service_role;
-- GRANT EXECUTE ON FUNCTION mark_reminder_sent TO service_role;
-- GRANT EXECUTE ON FUNCTION get_appointment_details TO anon, authenticated, service_role;
-- GRANT EXECUTE ON FUNCTION get_available_slots TO anon, authenticated, service_role;
-- GRANT EXECUTE ON FUNCTION update_appointment_status TO service_role;
-- GRANT EXECUTE ON FUNCTION get_appointments_for_post_visit_followup TO service_role;
-- GRANT EXECUTE ON FUNCTION get_appointment_statistics TO authenticated, service_role;

COMMENT ON FUNCTION get_upcoming_appointments IS 'Returns appointments within specified hours for reminder processing';
COMMENT ON FUNCTION get_appointments_needing_24h_reminder IS 'Returns appointments that need 24-hour advance reminder email';
COMMENT ON FUNCTION get_appointments_needing_2h_reminder IS 'Returns appointments that need 2-hour urgent reminder email';
COMMENT ON FUNCTION mark_reminder_sent IS 'Marks reminder as sent (24h, 2h, or post_visit)';
COMMENT ON FUNCTION get_appointment_details IS 'Returns complete appointment details with lead information for emails';
COMMENT ON FUNCTION get_available_slots IS 'Checks technician availability and returns available time slots';
COMMENT ON FUNCTION update_appointment_status IS 'Updates appointment status with validation and timestamp management';
COMMENT ON FUNCTION get_appointments_for_post_visit_followup IS 'Returns completed appointments needing post-visit follow-up email';
COMMENT ON FUNCTION get_appointment_statistics IS 'Returns appointment statistics for reporting and analytics';
