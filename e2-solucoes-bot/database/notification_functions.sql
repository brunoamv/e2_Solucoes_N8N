-- ============================================================================
-- SPRINT 1.3: Sistema de Notificações Multi-Canal
-- Arquivo: notification_functions.sql
-- Descrição: Funções SQL para gerenciamento de notificações
-- Versão: 1.0
-- Data: 2025-12-15
-- ============================================================================

-- ============================================================================
-- FUNÇÃO: create_notification
-- Descrição: Cria uma nova notificação após validar preferências do usuário
-- Retorna: UUID da notificação criada
-- ============================================================================
CREATE OR REPLACE FUNCTION create_notification(
    p_lead_id UUID,
    p_appointment_id UUID DEFAULT NULL,
    p_notification_type VARCHAR DEFAULT 'email',
    p_category VARCHAR DEFAULT 'general',
    p_recipient VARCHAR DEFAULT NULL,
    p_subject VARCHAR DEFAULT NULL,
    p_body TEXT DEFAULT '',
    p_template_used VARCHAR DEFAULT NULL,
    p_priority INTEGER DEFAULT 5,
    p_scheduled_for TIMESTAMP DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'::jsonb
) RETURNS UUID AS $$
DECLARE
    v_notification_id UUID;
    v_final_recipient VARCHAR;
    v_lead_record RECORD;
BEGIN
    -- Validar lead_id existe
    IF NOT EXISTS (SELECT 1 FROM leads WHERE id = p_lead_id) THEN
        RAISE EXCEPTION 'Lead ID % não encontrado', p_lead_id;
    END IF;

    -- Buscar dados do lead (para recipient default)
    SELECT email, phone INTO v_lead_record FROM leads WHERE id = p_lead_id;

    -- Determinar recipient se não fornecido
    v_final_recipient := p_recipient;
    IF v_final_recipient IS NULL THEN
        IF p_notification_type = 'email' THEN
            v_final_recipient := v_lead_record.email;
        ELSIF p_notification_type = 'whatsapp' THEN
            v_final_recipient := v_lead_record.phone;
        ELSE
            RAISE EXCEPTION 'Recipient obrigatório para tipo %', p_notification_type;
        END IF;
    END IF;

    -- Validar recipient não está vazio
    IF v_final_recipient IS NULL OR trim(v_final_recipient) = '' THEN
        RAISE EXCEPTION 'Recipient vazio para tipo % e lead %', p_notification_type, p_lead_id;
    END IF;

    -- Verificar se notificação é permitida pelas preferências do usuário
    IF NOT check_notification_allowed(p_lead_id, p_notification_type, p_category, p_priority) THEN
        RAISE EXCEPTION 'Notificação não permitida pelas preferências do usuário (lead: %, tipo: %, categoria: %)',
            p_lead_id, p_notification_type, p_category;
    END IF;

    -- Validar priority dentro do range
    IF p_priority < 1 OR p_priority > 10 THEN
        RAISE EXCEPTION 'Priority deve estar entre 1 e 10, recebido: %', p_priority;
    END IF;

    -- Criar notificação
    INSERT INTO notifications (
        lead_id,
        appointment_id,
        notification_type,
        category,
        recipient,
        subject,
        body,
        template_used,
        priority,
        scheduled_for,
        metadata,
        status,
        retry_count,
        max_retries
    ) VALUES (
        p_lead_id,
        p_appointment_id,
        p_notification_type,
        p_category,
        v_final_recipient,
        p_subject,
        p_body,
        p_template_used,
        p_priority,
        COALESCE(p_scheduled_for, NOW()),
        p_metadata,
        'pending',
        0,
        3 -- max_retries padrão
    ) RETURNING id INTO v_notification_id;

    RAISE NOTICE 'Notificação criada: % (tipo: %, categoria: %, prioridade: %)',
        v_notification_id, p_notification_type, p_category, p_priority;

    RETURN v_notification_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNÇÃO: check_notification_allowed
-- Descrição: Verifica se notificação é permitida pelas preferências do usuário
-- Retorna: TRUE se permitida, FALSE caso contrário
-- LGPD Compliant: Respeita opt-out do usuário
-- ============================================================================
CREATE OR REPLACE FUNCTION check_notification_allowed(
    p_lead_id UUID,
    p_notification_type VARCHAR,
    p_category VARCHAR,
    p_priority INTEGER DEFAULT 5
) RETURNS BOOLEAN AS $$
DECLARE
    v_prefs RECORD;
    v_current_hour TIME;
    v_current_day INTEGER; -- 0 = domingo, 6 = sábado
BEGIN
    -- Buscar preferências (criar padrão se não existir)
    SELECT * INTO v_prefs FROM notification_preferences WHERE lead_id = p_lead_id;

    IF NOT FOUND THEN
        -- Criar preferências padrão para o lead
        INSERT INTO notification_preferences (lead_id)
        VALUES (p_lead_id)
        RETURNING * INTO v_prefs;

        RAISE NOTICE 'Preferências criadas automaticamente para lead %', p_lead_id;
    END IF;

    -- REGRA 1: Verificar opt-out geral (mais restritivo)
    IF v_prefs.opt_out_all THEN
        -- EXCEÇÃO: Notificações legalmente obrigatórias (confirmação de agendamento)
        IF p_category = 'appointment_confirmation' THEN
            RETURN TRUE; -- Permitir confirmação legal
        END IF;

        RAISE NOTICE 'Notificação bloqueada: opt_out_all ativo para lead %', p_lead_id;
        RETURN FALSE;
    END IF;

    -- REGRA 2: Verificar opt-out por categoria
    IF p_category LIKE '%marketing%' AND v_prefs.opt_out_marketing THEN
        RAISE NOTICE 'Notificação bloqueada: opt_out_marketing ativo (lead: %, categoria: %)',
            p_lead_id, p_category;
        RETURN FALSE;
    END IF;

    IF p_category LIKE '%reminder%' AND v_prefs.opt_out_reminders THEN
        RAISE NOTICE 'Notificação bloqueada: opt_out_reminders ativo (lead: %, categoria: %)',
            p_lead_id, p_category;
        RETURN FALSE;
    END IF;

    -- REGRA 3: Verificar canal específico habilitado
    IF p_notification_type = 'email' AND NOT v_prefs.email_enabled THEN
        RAISE NOTICE 'Notificação bloqueada: email desabilitado para lead %', p_lead_id;
        RETURN FALSE;
    END IF;

    IF p_notification_type = 'whatsapp' AND NOT v_prefs.whatsapp_enabled THEN
        RAISE NOTICE 'Notificação bloqueada: whatsapp desabilitado para lead %', p_lead_id;
        RETURN FALSE;
    END IF;

    -- REGRA 4: Verificar horário preferido (apenas para prioridade normal)
    IF p_priority <= 8 THEN -- Prioridades altas (9-10) ignoram horário
        v_current_hour := CURRENT_TIME AT TIME ZONE v_prefs.timezone;

        IF v_current_hour < v_prefs.preferred_hours_start
           OR v_current_hour > v_prefs.preferred_hours_end THEN
            RAISE NOTICE 'Notificação fora do horário preferido (lead: %, hora: %, range: %-%), mas será agendada',
                p_lead_id, v_current_hour, v_prefs.preferred_hours_start, v_prefs.preferred_hours_end;
            -- NÃO bloquear, apenas informar - workflow agendará para horário adequado
        END IF;
    END IF;

    -- REGRA 5: Verificar dia da semana (não enviar marketing em domingo)
    IF p_category LIKE '%marketing%' THEN
        v_current_day := EXTRACT(DOW FROM CURRENT_DATE); -- 0 = domingo
        IF v_current_day = 0 THEN
            RAISE NOTICE 'Notificação de marketing bloqueada: domingo (lead: %)', p_lead_id;
            RETURN FALSE;
        END IF;
    END IF;

    -- Todas as verificações passaram
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNÇÃO: update_notification_status
-- Descrição: Atualiza status de notificação com timestamps automáticos
-- ============================================================================
CREATE OR REPLACE FUNCTION update_notification_status(
    p_notification_id UUID,
    p_new_status VARCHAR,
    p_error_message TEXT DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    -- Validar status
    IF p_new_status NOT IN ('pending', 'sent', 'delivered', 'failed', 'retrying') THEN
        RAISE EXCEPTION 'Status inválido: %. Válidos: pending, sent, delivered, failed, retrying', p_new_status;
    END IF;

    -- Atualizar com timestamps automáticos
    UPDATE notifications SET
        status = p_new_status,
        updated_at = NOW(),
        sent_at = CASE WHEN p_new_status = 'sent' THEN COALESCE(sent_at, NOW()) ELSE sent_at END,
        delivered_at = CASE WHEN p_new_status = 'delivered' THEN COALESCE(delivered_at, NOW()) ELSE delivered_at END,
        failed_at = CASE WHEN p_new_status = 'failed' THEN NOW() ELSE failed_at END,
        error_message = COALESCE(p_error_message, error_message),
        retry_count = CASE WHEN p_new_status = 'retrying' THEN retry_count + 1 ELSE retry_count END,
        -- Se status = 'retrying', agendar para +5 minutos
        scheduled_for = CASE WHEN p_new_status = 'retrying' THEN NOW() + INTERVAL '5 minutes' ELSE scheduled_for END
    WHERE id = p_notification_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Notificação % não encontrada', p_notification_id;
    END IF;

    RAISE NOTICE 'Status atualizado: % -> % (erro: %)',
        p_notification_id, p_new_status, COALESCE(p_error_message, 'nenhum');
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNÇÃO: get_pending_notifications
-- Descrição: Busca notificações pending prontas para envio (ordenadas por prioridade)
-- Retorna: TABLE com notificações pending
-- ============================================================================
CREATE OR REPLACE FUNCTION get_pending_notifications(
    p_limit INTEGER DEFAULT 10
) RETURNS TABLE (
    notification_id UUID,
    lead_id UUID,
    appointment_id UUID,
    notification_type VARCHAR,
    category VARCHAR,
    recipient VARCHAR,
    subject VARCHAR,
    body TEXT,
    template_used VARCHAR,
    priority INTEGER,
    scheduled_for TIMESTAMP,
    retry_count INTEGER,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.id,
        n.lead_id,
        n.appointment_id,
        n.notification_type,
        n.category,
        n.recipient,
        n.subject,
        n.body,
        n.template_used,
        n.priority,
        n.scheduled_for,
        n.retry_count,
        n.metadata
    FROM notifications n
    WHERE n.status = 'pending'
        AND n.scheduled_for <= NOW() -- apenas notificações agendadas para agora ou passado
        AND n.retry_count < n.max_retries -- apenas notificações que ainda podem ser retentadas
    ORDER BY n.priority DESC, n.scheduled_for ASC -- prioridade alta primeiro, depois por ordem de agendamento
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNÇÃO: get_failed_notifications
-- Descrição: Busca notificações que falharam após todas as tentativas (para auditoria)
-- Retorna: TABLE com notificações failed
-- ============================================================================
CREATE OR REPLACE FUNCTION get_failed_notifications(
    p_hours_ago INTEGER DEFAULT 24,
    p_limit INTEGER DEFAULT 50
) RETURNS TABLE (
    notification_id UUID,
    lead_id UUID,
    notification_type VARCHAR,
    category VARCHAR,
    recipient VARCHAR,
    priority INTEGER,
    failed_at TIMESTAMP,
    retry_count INTEGER,
    max_retries INTEGER,
    error_message TEXT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.id,
        n.lead_id,
        n.notification_type,
        n.category,
        n.recipient,
        n.priority,
        n.failed_at,
        n.retry_count,
        n.max_retries,
        n.error_message,
        n.metadata
    FROM notifications n
    WHERE n.status = 'failed'
        AND n.failed_at >= NOW() - (p_hours_ago || ' hours')::INTERVAL
    ORDER BY n.failed_at DESC, n.priority DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNÇÃO: get_notification_stats
-- Descrição: Retorna estatísticas de notificações por tipo e período
-- Útil para dashboards e monitoramento
-- ============================================================================
CREATE OR REPLACE FUNCTION get_notification_stats(
    p_days_ago INTEGER DEFAULT 7
) RETURNS TABLE (
    notification_type VARCHAR,
    total_count BIGINT,
    sent_count BIGINT,
    failed_count BIGINT,
    pending_count BIGINT,
    delivery_rate NUMERIC,
    avg_processing_seconds NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.notification_type,
        COUNT(*) AS total_count,
        COUNT(*) FILTER (WHERE n.status = 'sent' OR n.status = 'delivered') AS sent_count,
        COUNT(*) FILTER (WHERE n.status = 'failed') AS failed_count,
        COUNT(*) FILTER (WHERE n.status = 'pending' OR n.status = 'retrying') AS pending_count,
        ROUND(
            (COUNT(*) FILTER (WHERE n.status = 'sent' OR n.status = 'delivered')::NUMERIC / NULLIF(COUNT(*), 0)) * 100,
            2
        ) AS delivery_rate,
        ROUND(
            AVG(EXTRACT(EPOCH FROM (n.sent_at - n.created_at)))
            FILTER (WHERE n.sent_at IS NOT NULL),
            2
        ) AS avg_processing_seconds
    FROM notifications n
    WHERE n.created_at >= CURRENT_DATE - (p_days_ago || ' days')::INTERVAL
    GROUP BY n.notification_type
    ORDER BY total_count DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNÇÃO: create_appointment_reminders
-- Descrição: Cria notificações de lembrete para um agendamento (24h e 2h antes)
-- Integração com Sprint 1.2 (Appointments)
-- ============================================================================
CREATE OR REPLACE FUNCTION create_appointment_reminders(
    p_appointment_id UUID,
    p_lead_id UUID,
    p_appointment_datetime TIMESTAMP
) RETURNS JSONB AS $$
DECLARE
    v_reminder_24h_id UUID;
    v_reminder_2h_id UUID;
    v_lead_record RECORD;
    v_result JSONB;
BEGIN
    -- Validar appointment existe
    IF NOT EXISTS (SELECT 1 FROM appointments WHERE id = p_appointment_id) THEN
        RAISE EXCEPTION 'Appointment ID % não encontrado', p_appointment_id;
    END IF;

    -- Buscar dados do lead
    SELECT name, phone, email INTO v_lead_record FROM leads WHERE id = p_lead_id;

    -- Criar lembrete 24h antes (WhatsApp + Email)
    IF p_appointment_datetime > NOW() + INTERVAL '24 hours' THEN
        -- WhatsApp 24h
        BEGIN
            v_reminder_24h_id := create_notification(
                p_lead_id := p_lead_id,
                p_appointment_id := p_appointment_id,
                p_notification_type := 'whatsapp',
                p_category := 'appointment_reminder_24h',
                p_recipient := v_lead_record.phone,
                p_body := format('Olá %s! Lembramos que você tem um agendamento com a E2 Soluções amanhã. Para confirmar, responda SIM.', v_lead_record.name),
                p_template_used := 'reminder_24h',
                p_priority := 7, -- alta prioridade
                p_scheduled_for := p_appointment_datetime - INTERVAL '24 hours',
                p_metadata := jsonb_build_object(
                    'appointment_id', p_appointment_id,
                    'appointment_datetime', p_appointment_datetime,
                    'reminder_type', '24h'
                )
            );
            RAISE NOTICE 'Lembrete 24h (WhatsApp) criado: %', v_reminder_24h_id;
        EXCEPTION
            WHEN OTHERS THEN
                RAISE WARNING 'Erro ao criar lembrete 24h WhatsApp: %', SQLERRM;
                v_reminder_24h_id := NULL;
        END;
    END IF;

    -- Criar lembrete 2h antes (WhatsApp)
    IF p_appointment_datetime > NOW() + INTERVAL '2 hours' THEN
        BEGIN
            v_reminder_2h_id := create_notification(
                p_lead_id := p_lead_id,
                p_appointment_id := p_appointment_id,
                p_notification_type := 'whatsapp',
                p_category := 'appointment_reminder_2h',
                p_recipient := v_lead_record.phone,
                p_body := format('Olá %s! Seu agendamento com a E2 Soluções é daqui a 2 horas. Estamos te esperando!', v_lead_record.name),
                p_template_used := 'reminder_2h',
                p_priority := 9, -- prioridade muito alta
                p_scheduled_for := p_appointment_datetime - INTERVAL '2 hours',
                p_metadata := jsonb_build_object(
                    'appointment_id', p_appointment_id,
                    'appointment_datetime', p_appointment_datetime,
                    'reminder_type', '2h'
                )
            );
            RAISE NOTICE 'Lembrete 2h (WhatsApp) criado: %', v_reminder_2h_id;
        EXCEPTION
            WHEN OTHERS THEN
                RAISE WARNING 'Erro ao criar lembrete 2h WhatsApp: %', SQLERRM;
                v_reminder_2h_id := NULL;
        END;
    END IF;

    -- Retornar IDs criados
    v_result := jsonb_build_object(
        'appointment_id', p_appointment_id,
        'reminder_24h_id', v_reminder_24h_id,
        'reminder_2h_id', v_reminder_2h_id,
        'total_created', (CASE WHEN v_reminder_24h_id IS NOT NULL THEN 1 ELSE 0 END +
                          CASE WHEN v_reminder_2h_id IS NOT NULL THEN 1 ELSE 0 END)
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMENTÁRIOS: Documentação das funções
-- ============================================================================

COMMENT ON FUNCTION create_notification IS
'Cria notificação após validar preferências do usuário (LGPD compliant).
Retorna UUID da notificação criada ou lança exceção se não permitida.
Recipient é opcional para email/whatsapp (usa dados do lead).';

COMMENT ON FUNCTION check_notification_allowed IS
'Verifica se notificação é permitida pelas preferências do usuário.
Regras: opt-out geral, opt-out por categoria, canal habilitado, horário preferido.
EXCEÇÃO: Notificações legalmente obrigatórias sempre permitidas.';

COMMENT ON FUNCTION update_notification_status IS
'Atualiza status com timestamps automáticos e retry logic.
Se status = retrying: incrementa retry_count e agenda para +5 minutos.';

COMMENT ON FUNCTION get_pending_notifications IS
'Busca notificações pending ordenadas por prioridade DESC, scheduled_for ASC.
Usado pelo Workflow 11 (Orchestrator) a cada 1 minuto.';

COMMENT ON FUNCTION get_failed_notifications IS
'Busca notificações failed para auditoria e alertas.
Usado para criar alertas Discord quando notificações falham permanentemente.';

COMMENT ON FUNCTION get_notification_stats IS
'Retorna estatísticas de notificações (delivery rate, tempo médio, etc).
Usado para dashboards e monitoramento de performance.';

COMMENT ON FUNCTION create_appointment_reminders IS
'Cria 2 lembretes automaticamente para agendamento (24h e 2h antes).
Integração com Sprint 1.2. Chamado ao criar/confirmar agendamento.';

-- ============================================================================
-- VALIDAÇÃO: Testar criação das funções
-- ============================================================================

DO $$
DECLARE
    v_function_count INTEGER;
BEGIN
    -- Contar funções criadas
    SELECT count(*) INTO v_function_count
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public'
        AND p.proname IN (
            'create_notification',
            'check_notification_allowed',
            'update_notification_status',
            'get_pending_notifications',
            'get_failed_notifications',
            'get_notification_stats',
            'create_appointment_reminders'
        );

    IF v_function_count = 7 THEN
        RAISE NOTICE 'Todas as 7 funções de notificação foram criadas com sucesso!';
    ELSE
        RAISE WARNING 'Apenas % de 7 funções foram criadas', v_function_count;
    END IF;
END $$;

-- ============================================================================
-- FIM DO ARQUIVO notification_functions.sql
-- ============================================================================
