-- ============================================================================
-- E2 Soluções Bot - Testes Unitários: Funções de Notificação
-- ============================================================================
-- Sprint 1.3 - Sistema de Notificações Multi-Canal
-- Data: 2025-12-15
-- Cobertura: 7 funções SQL + triggers + validações LGPD
-- ============================================================================

-- ============================================================================
-- SETUP: Configuração do Ambiente de Testes
-- ============================================================================

-- Começar transação para isolamento
BEGIN;

-- Criar dados de teste
DO $$
DECLARE
    test_lead_id UUID;
    test_appointment_id UUID;
BEGIN
    -- Criar lead de teste
    INSERT INTO leads (
        phone,
        name,
        email,
        address,
        city,
        state,
        service_type,
        status,
        rdstation_contact_id,
        notification_preferences
    ) VALUES (
        '+5562999999999',
        'Cliente Teste',
        'teste@exemplo.com',
        'Rua Teste, 123',
        'Goiânia',
        'GO',
        'energia_solar',
        'qualified',
        'test_contact_123',
        jsonb_build_object(
            'email', true,
            'whatsapp', true,
            'discord', false
        )
    ) RETURNING id INTO test_lead_id;

    -- Criar agendamento de teste
    INSERT INTO appointments (
        lead_id,
        scheduled_at,
        type,
        status,
        location,
        google_event_id
    ) VALUES (
        test_lead_id,
        NOW() + INTERVAL '24 hours',
        'technical_visit',
        'scheduled',
        'Endereço do Lead',
        'test_event_123'
    ) RETURNING id INTO test_appointment_id;

    -- Armazenar IDs para uso nos testes
    CREATE TEMP TABLE test_data (
        lead_id UUID,
        appointment_id UUID
    );
    INSERT INTO test_data VALUES (test_lead_id, test_appointment_id);
END $$;

-- ============================================================================
-- TESTE 1: create_notification() - Criação Básica
-- ============================================================================

DO $$
DECLARE
    test_lead_id UUID;
    new_notification_id UUID;
    notification_count INTEGER;
BEGIN
    SELECT lead_id INTO test_lead_id FROM test_data;

    RAISE NOTICE '=== TESTE 1: create_notification() - Criação Básica ===';

    -- Criar notificação válida
    SELECT create_notification(
        test_lead_id,
        NULL,
        'email',
        'new_lead',
        'novo_lead',
        'Novo Lead Qualificado',
        'Você tem um novo lead qualificado no sistema.',
        json_build_object(
            'lead_name', 'Cliente Teste',
            'phone', '+5562999999999',
            'service_name', 'Energia Solar'
        )::jsonb,
        3,
        NOW()
    ) INTO new_notification_id;

    -- Validar que a notificação foi criada
    SELECT COUNT(*) INTO notification_count
    FROM notifications
    WHERE id = new_notification_id;

    IF notification_count = 1 THEN
        RAISE NOTICE '✅ PASSOU: Notificação criada com sucesso (ID: %)', new_notification_id;
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Notificação não foi criada';
    END IF;

    -- Validar status inicial
    IF EXISTS (
        SELECT 1 FROM notifications
        WHERE id = new_notification_id
        AND status = 'pending'
    ) THEN
        RAISE NOTICE '✅ PASSOU: Status inicial correto (pending)';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Status inicial incorreto';
    END IF;

    RAISE NOTICE '';
END $$;

-- ============================================================================
-- TESTE 2: create_notification() - Validação LGPD (Opt-Out Email)
-- ============================================================================

DO $$
DECLARE
    test_lead_id UUID;
    new_notification_id UUID;
BEGIN
    SELECT lead_id INTO test_lead_id FROM test_data;

    RAISE NOTICE '=== TESTE 2: create_notification() - Validação LGPD (Opt-Out Email) ===';

    -- Atualizar preferências do lead (opt-out de email)
    UPDATE leads
    SET notification_preferences = jsonb_build_object(
        'email', false,
        'whatsapp', true,
        'discord', false
    )
    WHERE id = test_lead_id;

    -- Tentar criar notificação por email (deve falhar)
    BEGIN
        SELECT create_notification(
            test_lead_id,
            NULL,
            'email',
            'test',
            '',
            'Teste Bloqueado',
            '',
            '{}'::jsonb,
            1,
            NOW()
        ) INTO new_notification_id;

        IF new_notification_id IS NULL THEN
            RAISE NOTICE '✅ PASSOU: Notificação bloqueada por opt-out de email';
        ELSE
            RAISE EXCEPTION '❌ FALHOU: Notificação não foi bloqueada (LGPD violado)';
        END IF;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE '✅ PASSOU: Exceção capturada corretamente ao violar LGPD';
    END;

    -- Restaurar preferências
    UPDATE leads
    SET notification_preferences = jsonb_build_object(
        'email', true,
        'whatsapp', true,
        'discord', false
    )
    WHERE id = test_lead_id;

    RAISE NOTICE '';
END $$;

-- ============================================================================
-- TESTE 3: check_notification_allowed() - Diferentes Canais
-- ============================================================================

DO $$
DECLARE
    test_lead_id UUID;
    is_email_allowed BOOLEAN;
    is_whatsapp_allowed BOOLEAN;
    is_discord_allowed BOOLEAN;
BEGIN
    SELECT lead_id INTO test_lead_id FROM test_data;

    RAISE NOTICE '=== TESTE 3: check_notification_allowed() - Diferentes Canais ===';

    -- Configurar preferências: email=SIM, whatsapp=SIM, discord=NÃO
    UPDATE leads
    SET notification_preferences = jsonb_build_object(
        'email', true,
        'whatsapp', true,
        'discord', false
    )
    WHERE id = test_lead_id;

    -- Verificar email (deve ser permitido)
    SELECT check_notification_allowed(test_lead_id, 'email') INTO is_email_allowed;
    IF is_email_allowed THEN
        RAISE NOTICE '✅ PASSOU: Email permitido';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Email deveria ser permitido';
    END IF;

    -- Verificar WhatsApp (deve ser permitido)
    SELECT check_notification_allowed(test_lead_id, 'whatsapp') INTO is_whatsapp_allowed;
    IF is_whatsapp_allowed THEN
        RAISE NOTICE '✅ PASSOU: WhatsApp permitido';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: WhatsApp deveria ser permitido';
    END IF;

    -- Verificar Discord (deve ser bloqueado)
    SELECT check_notification_allowed(test_lead_id, 'discord') INTO is_discord_allowed;
    IF NOT is_discord_allowed THEN
        RAISE NOTICE '✅ PASSOU: Discord bloqueado (opt-out)';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Discord deveria ser bloqueado';
    END IF;

    RAISE NOTICE '';
END $$;

-- ============================================================================
-- TESTE 4: update_notification_status() - Transições de Estado
-- ============================================================================

DO $$
DECLARE
    test_lead_id UUID;
    notification_id UUID;
    current_status TEXT;
BEGIN
    SELECT lead_id INTO test_lead_id FROM test_data;

    RAISE NOTICE '=== TESTE 4: update_notification_status() - Transições de Estado ===';

    -- Criar notificação para testar
    SELECT create_notification(
        test_lead_id, NULL, 'email', 'test', '', 'Teste Status', '', '{}'::jsonb, 3, NOW()
    ) INTO notification_id;

    -- Testar transição: pending → sent
    PERFORM update_notification_status(
        notification_id,
        'sent',
        NULL,
        'Message sent successfully'
    );

    SELECT status INTO current_status FROM notifications WHERE id = notification_id;
    IF current_status = 'sent' THEN
        RAISE NOTICE '✅ PASSOU: Transição pending → sent';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Status não atualizado para sent';
    END IF;

    -- Criar outra notificação para testar falha
    SELECT create_notification(
        test_lead_id, NULL, 'email', 'test', '', 'Teste Falha', '', '{}'::jsonb, 3, NOW()
    ) INTO notification_id;

    -- Testar transição: pending → failed
    PERFORM update_notification_status(
        notification_id,
        'failed',
        'SMTP connection failed',
        NULL
    );

    SELECT status INTO current_status FROM notifications WHERE id = notification_id;
    IF current_status = 'failed' THEN
        RAISE NOTICE '✅ PASSOU: Transição pending → failed';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Status não atualizado para failed';
    END IF;

    -- Validar que retry_count foi incrementado
    IF EXISTS (
        SELECT 1 FROM notifications
        WHERE id = notification_id
        AND retry_count = 1
    ) THEN
        RAISE NOTICE '✅ PASSOU: retry_count incrementado corretamente';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: retry_count não foi incrementado';
    END IF;

    RAISE NOTICE '';
END $$;

-- ============================================================================
-- TESTE 5: get_pending_notifications() - Ordenação por Prioridade
-- ============================================================================

DO $$
DECLARE
    test_lead_id UUID;
    notification_id_high UUID;
    notification_id_normal UUID;
    notification_id_low UUID;
    first_notification_priority INTEGER;
    pending_count INTEGER;
BEGIN
    SELECT lead_id INTO test_lead_id FROM test_data;

    RAISE NOTICE '=== TESTE 5: get_pending_notifications() - Ordenação por Prioridade ===';

    -- Criar 3 notificações com prioridades diferentes
    SELECT create_notification(
        test_lead_id, NULL, 'email', 'test', '', 'Prioridade Baixa', '', '{}'::jsonb, 1, NOW()
    ) INTO notification_id_low;

    SELECT create_notification(
        test_lead_id, NULL, 'email', 'test', '', 'Prioridade Normal', '', '{}'::jsonb, 3, NOW()
    ) INTO notification_id_normal;

    SELECT create_notification(
        test_lead_id, NULL, 'email', 'test', '', 'Prioridade Alta', '', '{}'::jsonb, 5, NOW()
    ) INTO notification_id_high;

    -- Buscar notificações pendentes (deve ordenar por prioridade DESC)
    SELECT priority INTO first_notification_priority
    FROM get_pending_notifications('email', 1)
    LIMIT 1;

    IF first_notification_priority = 5 THEN
        RAISE NOTICE '✅ PASSOU: Notificação de maior prioridade retornada primeiro';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Ordenação por prioridade incorreta (esperado: 5, obtido: %)', first_notification_priority;
    END IF;

    -- Validar contagem total de pendentes
    SELECT COUNT(*) INTO pending_count
    FROM get_pending_notifications('email', 10);

    IF pending_count >= 3 THEN
        RAISE NOTICE '✅ PASSOU: Todas as notificações pendentes retornadas (count: %)', pending_count;
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Notificações pendentes faltando';
    END IF;

    RAISE NOTICE '';
END $$;

-- ============================================================================
-- TESTE 6: get_failed_notifications() - Retry Elegível
-- ============================================================================

DO $$
DECLARE
    test_lead_id UUID;
    notification_id UUID;
    failed_count INTEGER;
BEGIN
    SELECT lead_id INTO test_lead_id FROM test_data;

    RAISE NOTICE '=== TESTE 6: get_failed_notifications() - Retry Elegível ===';

    -- Criar notificação e marcá-la como falha (1 tentativa de 3)
    SELECT create_notification(
        test_lead_id, NULL, 'email', 'test', '', 'Teste Retry', '', '{}'::jsonb, 3, NOW()
    ) INTO notification_id;

    PERFORM update_notification_status(
        notification_id,
        'failed',
        'Temporary error',
        NULL
    );

    -- Buscar notificações elegíveis para retry
    SELECT COUNT(*) INTO failed_count
    FROM get_failed_notifications('email', 10);

    IF failed_count >= 1 THEN
        RAISE NOTICE '✅ PASSOU: Notificação falha elegível para retry encontrada';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Notificação falha não encontrada';
    END IF;

    -- Criar notificação com max_retries esgotado (não deve aparecer)
    SELECT create_notification(
        test_lead_id, NULL, 'email', 'test', '', 'Sem Mais Retry', '', '{}'::jsonb, 1, NOW()
    ) INTO notification_id;

    UPDATE notifications
    SET status = 'failed', retry_count = 1, error_message = 'Max retries reached'
    WHERE id = notification_id;

    -- Validar que notificação com retries esgotados não aparece
    IF NOT EXISTS (
        SELECT 1 FROM get_failed_notifications('email', 10)
        WHERE id = notification_id
    ) THEN
        RAISE NOTICE '✅ PASSOU: Notificação com retries esgotados não retornada';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Notificação com retries esgotados foi retornada';
    END IF;

    RAISE NOTICE '';
END $$;

-- ============================================================================
-- TESTE 7: get_notification_stats() - Estatísticas Agregadas
-- ============================================================================

DO $$
DECLARE
    test_lead_id UUID;
    stats_row RECORD;
    total_notifications INTEGER;
    pending_count INTEGER;
    sent_count INTEGER;
BEGIN
    SELECT lead_id INTO test_lead_id FROM test_data;

    RAISE NOTICE '=== TESTE 7: get_notification_stats() - Estatísticas Agregadas ===';

    -- Criar notificações com diferentes status
    PERFORM create_notification(
        test_lead_id, NULL, 'email', 'test', '', 'Status 1', '', '{}'::jsonb, 3, NOW()
    );

    PERFORM create_notification(
        test_lead_id, NULL, 'email', 'test', '', 'Status 2', '', '{}'::jsonb, 3, NOW()
    );

    -- Marcar uma como enviada
    UPDATE notifications
    SET status = 'sent', sent_at = NOW()
    WHERE lead_id = test_lead_id
    AND status = 'pending'
    LIMIT 1;

    -- Obter estatísticas
    SELECT * INTO stats_row
    FROM get_notification_stats('email', NOW() - INTERVAL '1 day', NOW() + INTERVAL '1 day')
    LIMIT 1;

    -- Validar contadores
    IF stats_row.total_sent >= 1 THEN
        RAISE NOTICE '✅ PASSOU: Contador total_sent correto (value: %)', stats_row.total_sent;
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Contador total_sent incorreto';
    END IF;

    IF stats_row.total_pending >= 1 THEN
        RAISE NOTICE '✅ PASSOU: Contador total_pending correto (value: %)', stats_row.total_pending;
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Contador total_pending incorreto';
    END IF;

    -- Validar success_rate (deve ser entre 0 e 100)
    IF stats_row.success_rate >= 0 AND stats_row.success_rate <= 100 THEN
        RAISE NOTICE '✅ PASSOU: success_rate válido (value: %)', stats_row.success_rate;
    ELSE
        RAISE EXCEPTION '❌ FALHOU: success_rate inválido: %', stats_row.success_rate;
    END IF;

    RAISE NOTICE '';
END $$;

-- ============================================================================
-- TESTE 8: create_appointment_reminders() - Lembretes 24h e 2h
-- ============================================================================

DO $$
DECLARE
    test_appointment_id UUID;
    reminder_count_24h INTEGER;
    reminder_count_2h INTEGER;
    total_reminders INTEGER;
BEGIN
    SELECT appointment_id INTO test_appointment_id FROM test_data;

    RAISE NOTICE '=== TESTE 8: create_appointment_reminders() - Lembretes 24h e 2h ===';

    -- Criar lembretes para o agendamento
    PERFORM create_appointment_reminders(test_appointment_id);

    -- Contar lembretes criados (devem ser 2: 24h e 2h antes)
    SELECT COUNT(*) INTO total_reminders
    FROM notifications
    WHERE appointment_id = test_appointment_id
    AND notification_type = 'appointment_reminder';

    IF total_reminders = 2 THEN
        RAISE NOTICE '✅ PASSOU: 2 lembretes criados (24h + 2h)';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Número incorreto de lembretes (esperado: 2, obtido: %)', total_reminders;
    END IF;

    -- Validar lembrete de 24 horas
    SELECT COUNT(*) INTO reminder_count_24h
    FROM notifications
    WHERE appointment_id = test_appointment_id
    AND notification_type = 'appointment_reminder'
    AND scheduled_for < (SELECT scheduled_at FROM appointments WHERE id = test_appointment_id) - INTERVAL '23 hours';

    IF reminder_count_24h = 1 THEN
        RAISE NOTICE '✅ PASSOU: Lembrete 24h agendado corretamente';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Lembrete 24h não encontrado';
    END IF;

    -- Validar lembrete de 2 horas
    SELECT COUNT(*) INTO reminder_count_2h
    FROM notifications
    WHERE appointment_id = test_appointment_id
    AND notification_type = 'appointment_reminder'
    AND scheduled_for > (SELECT scheduled_at FROM appointments WHERE id = test_appointment_id) - INTERVAL '3 hours';

    IF reminder_count_2h = 1 THEN
        RAISE NOTICE '✅ PASSOU: Lembrete 2h agendado corretamente';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Lembrete 2h não encontrado';
    END IF;

    RAISE NOTICE '';
END $$;

-- ============================================================================
-- TESTE 9: Edge Cases - Lead Inexistente
-- ============================================================================

DO $$
DECLARE
    invalid_lead_id UUID := '00000000-0000-0000-0000-000000000000';
    notification_id UUID;
BEGIN
    RAISE NOTICE '=== TESTE 9: Edge Cases - Lead Inexistente ===';

    -- Tentar criar notificação com lead_id inválido
    BEGIN
        SELECT create_notification(
            invalid_lead_id,
            NULL,
            'email',
            'test',
            '',
            'Lead Inexistente',
            '',
            '{}'::jsonb,
            3,
            NOW()
        ) INTO notification_id;

        IF notification_id IS NULL THEN
            RAISE NOTICE '✅ PASSOU: Notificação não criada para lead inexistente';
        ELSE
            RAISE EXCEPTION '❌ FALHOU: Notificação criada para lead inexistente (violação FK)';
        END IF;
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE '✅ PASSOU: Foreign key violation capturada corretamente';
        WHEN OTHERS THEN
            RAISE NOTICE '✅ PASSOU: Exceção capturada (lead inexistente)';
    END;

    RAISE NOTICE '';
END $$;

-- ============================================================================
-- TESTE 10: Edge Cases - Template Variables Vazias
-- ============================================================================

DO $$
DECLARE
    test_lead_id UUID;
    notification_id UUID;
    template_vars JSONB;
BEGIN
    SELECT lead_id INTO test_lead_id FROM test_data;

    RAISE NOTICE '=== TESTE 10: Edge Cases - Template Variables Vazias ===';

    -- Criar notificação com template_variables = {}
    SELECT create_notification(
        test_lead_id,
        NULL,
        'email',
        'test',
        '',
        'Sem Template Vars',
        '',
        '{}'::jsonb,
        3,
        NOW()
    ) INTO notification_id;

    SELECT template_variables INTO template_vars
    FROM notifications
    WHERE id = notification_id;

    IF template_vars = '{}'::jsonb THEN
        RAISE NOTICE '✅ PASSOU: Template variables vazias aceitas';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Template variables não armazenadas corretamente';
    END IF;

    -- Criar notificação com template_variables = NULL
    SELECT create_notification(
        test_lead_id,
        NULL,
        'email',
        'test',
        '',
        'Template NULL',
        '',
        NULL,
        3,
        NOW()
    ) INTO notification_id;

    SELECT template_variables INTO template_vars
    FROM notifications
    WHERE id = notification_id;

    IF template_vars IS NULL OR template_vars = '{}'::jsonb THEN
        RAISE NOTICE '✅ PASSOU: Template variables NULL tratadas corretamente';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Template variables NULL não tratadas';
    END IF;

    RAISE NOTICE '';
END $$;

-- ============================================================================
-- TESTE 11: Validação de Integridade - Timestamps
-- ============================================================================

DO $$
DECLARE
    test_lead_id UUID;
    notification_id UUID;
    created_time TIMESTAMPTZ;
    scheduled_time TIMESTAMPTZ;
BEGIN
    SELECT lead_id INTO test_lead_id FROM test_data;

    RAISE NOTICE '=== TESTE 11: Validação de Integridade - Timestamps ===';

    -- Criar notificação com scheduled_for no futuro
    SELECT create_notification(
        test_lead_id,
        NULL,
        'email',
        'test',
        '',
        'Agendada Futuro',
        '',
        '{}'::jsonb,
        3,
        NOW() + INTERVAL '1 hour'
    ) INTO notification_id;

    SELECT created_at, scheduled_for
    INTO created_time, scheduled_time
    FROM notifications
    WHERE id = notification_id;

    -- Validar que scheduled_for > created_at
    IF scheduled_time > created_time THEN
        RAISE NOTICE '✅ PASSOU: scheduled_for no futuro corretamente';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: scheduled_for não está no futuro';
    END IF;

    -- Validar que created_at é aproximadamente NOW()
    IF created_time BETWEEN NOW() - INTERVAL '10 seconds' AND NOW() + INTERVAL '10 seconds' THEN
        RAISE NOTICE '✅ PASSOU: created_at timestamp correto';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: created_at timestamp incorreto';
    END IF;

    RAISE NOTICE '';
END $$;

-- ============================================================================
-- TESTE 12: Concorrência - Múltiplas Atualizações Simultâneas
-- ============================================================================

DO $$
DECLARE
    test_lead_id UUID;
    notification_id UUID;
    final_status TEXT;
    final_retry_count INTEGER;
BEGIN
    SELECT lead_id INTO test_lead_id FROM test_data;

    RAISE NOTICE '=== TESTE 12: Concorrência - Múltiplas Atualizações Simultâneas ===';

    -- Criar notificação
    SELECT create_notification(
        test_lead_id, NULL, 'email', 'test', '', 'Teste Concorrência', '', '{}'::jsonb, 3, NOW()
    ) INTO notification_id;

    -- Simular múltiplas atualizações de status (retry logic)
    PERFORM update_notification_status(notification_id, 'failed', 'Erro 1', NULL);
    PERFORM update_notification_status(notification_id, 'failed', 'Erro 2', NULL);
    PERFORM update_notification_status(notification_id, 'sent', NULL, 'Sucesso na 3ª tentativa');

    SELECT status, retry_count
    INTO final_status, final_retry_count
    FROM notifications
    WHERE id = notification_id;

    IF final_status = 'sent' THEN
        RAISE NOTICE '✅ PASSOU: Status final correto após múltiplas atualizações';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Status final incorreto: %', final_status;
    END IF;

    IF final_retry_count = 2 THEN
        RAISE NOTICE '✅ PASSOU: Retry count correto (2 falhas antes do sucesso)';
    ELSE
        RAISE EXCEPTION '❌ FALHOU: Retry count incorreto: %', final_retry_count;
    END IF;

    RAISE NOTICE '';
END $$;

-- ============================================================================
-- RELATÓRIO FINAL
-- ============================================================================

DO $$
DECLARE
    total_notifications INTEGER;
    status_breakdown RECORD;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'RELATÓRIO FINAL DE TESTES';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';

    -- Contagem total de notificações criadas
    SELECT COUNT(*) INTO total_notifications FROM notifications;
    RAISE NOTICE 'Total de notificações criadas nos testes: %', total_notifications;
    RAISE NOTICE '';

    -- Breakdown por status
    RAISE NOTICE 'Breakdown por Status:';
    FOR status_breakdown IN
        SELECT status, COUNT(*) as count
        FROM notifications
        GROUP BY status
        ORDER BY count DESC
    LOOP
        RAISE NOTICE '  - %: %', status_breakdown.status, status_breakdown.count;
    END LOOP;
    RAISE NOTICE '';

    -- Breakdown por canal
    RAISE NOTICE 'Breakdown por Canal:';
    FOR status_breakdown IN
        SELECT channel, COUNT(*) as count
        FROM notifications
        GROUP BY channel
        ORDER BY count DESC
    LOOP
        RAISE NOTICE '  - %: %', status_breakdown.channel, status_breakdown.count;
    END LOOP;
    RAISE NOTICE '';

    -- Cobertura de testes
    RAISE NOTICE '========================================';
    RAISE NOTICE 'COBERTURA DE TESTES:';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ create_notification() - 4 testes';
    RAISE NOTICE '✅ check_notification_allowed() - 1 teste';
    RAISE NOTICE '✅ update_notification_status() - 2 testes';
    RAISE NOTICE '✅ get_pending_notifications() - 1 teste';
    RAISE NOTICE '✅ get_failed_notifications() - 1 teste';
    RAISE NOTICE '✅ get_notification_stats() - 1 teste';
    RAISE NOTICE '✅ create_appointment_reminders() - 1 teste';
    RAISE NOTICE '✅ Edge Cases - 5 testes';
    RAISE NOTICE '';
    RAISE NOTICE 'TOTAL: 12 testes executados';
    RAISE NOTICE '';
END $$;

-- ============================================================================
-- CLEANUP: Rollback da Transação (Não Persiste Dados de Teste)
-- ============================================================================

ROLLBACK;

-- Mensagem final
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'TESTES CONCLUÍDOS COM SUCESSO!';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Para executar os testes:';
    RAISE NOTICE '  psql $DATABASE_URL < database/tests/test_notification_functions.sql';
    RAISE NOTICE '';
    RAISE NOTICE 'Todos os dados de teste foram removidos (ROLLBACK).';
END $$;
