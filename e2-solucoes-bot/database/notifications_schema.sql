-- ============================================================================
-- SPRINT 1.3: Sistema de Notificações Multi-Canal
-- Arquivo: notifications_schema.sql
-- Descrição: Schema completo para sistema de notificações (email, whatsapp, discord)
-- Versão: 1.0
-- Data: 2025-12-15
-- ============================================================================

-- ============================================================================
-- TABELA: notifications
-- Descrição: Armazena todas as notificações do sistema (email, whatsapp, discord)
--            com rastreamento completo de status e retry logic
-- ============================================================================
CREATE TABLE IF NOT EXISTS notifications (
    -- Identificação
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    appointment_id UUID REFERENCES appointments(id) ON DELETE SET NULL,

    -- Tipo e categoria
    notification_type VARCHAR(50) NOT NULL CHECK (notification_type IN ('email', 'whatsapp', 'discord')),
    category VARCHAR(50) NOT NULL, -- appointment_reminder, qualification_complete, handoff_alert, etc

    -- Destinatário e conteúdo
    recipient VARCHAR(255) NOT NULL, -- email, phone (55XXXXXXXXXXX), ou webhook_url
    subject VARCHAR(255), -- apenas para email
    body TEXT NOT NULL,
    template_used VARCHAR(100), -- referência ao template HTML/TXT usado

    -- Status e controle
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'retrying')),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10), -- 1 (baixa) a 10 (alta)

    -- Scheduling e timestamps
    scheduled_for TIMESTAMP NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    failed_at TIMESTAMP,

    -- Retry logic
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,

    -- Metadados adicionais (JSON)
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- ÍNDICES: notifications
-- ============================================================================

-- Índice para buscar notificações pending (workflow orchestrator)
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);

-- Índice para buscar notificações agendadas (scheduled_for)
CREATE INDEX IF NOT EXISTS idx_notifications_scheduled
ON notifications(scheduled_for)
WHERE status = 'pending';

-- Índice para buscar notificações por lead
CREATE INDEX IF NOT EXISTS idx_notifications_lead ON notifications(lead_id);

-- Índice para buscar notificações por tipo (email, whatsapp, discord)
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);

-- Índice para buscar notificações por categoria
CREATE INDEX IF NOT EXISTS idx_notifications_category ON notifications(category);

-- Índice para buscar notificações falhadas que precisam retry
CREATE INDEX IF NOT EXISTS idx_notifications_retry
ON notifications(retry_count, max_retries, status)
WHERE status IN ('failed', 'retrying');

-- Índice composto para ordenação por prioridade e scheduling
CREATE INDEX IF NOT EXISTS idx_notifications_priority_scheduled
ON notifications(priority DESC, scheduled_for ASC)
WHERE status = 'pending';

-- ============================================================================
-- TABELA: notification_preferences
-- Descrição: Preferências de notificação por lead (opt-in/opt-out, horários, canais)
--            LGPD compliant - respeita escolhas do usuário
-- ============================================================================
CREATE TABLE IF NOT EXISTS notification_preferences (
    -- Identificação
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE UNIQUE, -- 1 preferência por lead

    -- Preferências de canal
    email_enabled BOOLEAN DEFAULT true,
    whatsapp_enabled BOOLEAN DEFAULT true,

    -- Horários preferidos (timezone aware)
    preferred_hours_start TIME DEFAULT '08:00',
    preferred_hours_end TIME DEFAULT '20:00',
    timezone VARCHAR(50) DEFAULT 'America/Sao_Paulo',

    -- Opt-out flags (LGPD)
    opt_out_all BOOLEAN DEFAULT false, -- opt-out completo (não recebe nada)
    opt_out_marketing BOOLEAN DEFAULT false, -- apenas marketing
    opt_out_reminders BOOLEAN DEFAULT false, -- apenas lembretes

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- ÍNDICES: notification_preferences
-- ============================================================================

-- Índice único para buscar preferências por lead (primary access pattern)
CREATE UNIQUE INDEX IF NOT EXISTS idx_notification_preferences_lead
ON notification_preferences(lead_id);

-- Índice para buscar leads com opt-out ativo
CREATE INDEX IF NOT EXISTS idx_notification_preferences_optout
ON notification_preferences(opt_out_all)
WHERE opt_out_all = true;

-- ============================================================================
-- CONSTRAINT: Evitar notificações duplicadas
-- ============================================================================

-- Não permitir notificações pendentes duplicadas para mesmo lead + categoria + horário
-- (permite re-tentativas de failed, mas não criação duplicada)
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_pending_notification
ON notifications(lead_id, notification_type, category, scheduled_for)
WHERE status = 'pending';

-- ============================================================================
-- TRIGGER: Atualizar updated_at automaticamente
-- ============================================================================

-- Função genérica para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para notifications
DROP TRIGGER IF EXISTS trigger_notifications_updated_at ON notifications;
CREATE TRIGGER trigger_notifications_updated_at
    BEFORE UPDATE ON notifications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para notification_preferences
DROP TRIGGER IF EXISTS trigger_notification_preferences_updated_at ON notification_preferences;
CREATE TRIGGER trigger_notification_preferences_updated_at
    BEFORE UPDATE ON notification_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMENTÁRIOS: Documentação das tabelas
-- ============================================================================

COMMENT ON TABLE notifications IS
'Tabela central do sistema de notificações multi-canal (Sprint 1.3).
Armazena todas as notificações (email, whatsapp, discord) com rastreamento
completo de status, retry logic e priorização.';

COMMENT ON COLUMN notifications.notification_type IS
'Tipo de canal: email (SMTP), whatsapp (Evolution API), discord (webhook)';

COMMENT ON COLUMN notifications.category IS
'Categoria da notificação: appointment_reminder, qualification_complete,
handoff_alert, system_alert, etc. Define template e comportamento.';

COMMENT ON COLUMN notifications.recipient IS
'Destinatário no formato apropriado para o canal:
- email: joao.silva@example.com
- whatsapp: 5561999999999 (formato E.164 sem +)
- discord: URL completa do webhook';

COMMENT ON COLUMN notifications.status IS
'Status atual da notificação:
- pending: aguardando processamento
- sent: enviada com sucesso
- delivered: confirmação de entrega (quando disponível)
- failed: falha após todas as tentativas
- retrying: em processo de retry';

COMMENT ON COLUMN notifications.priority IS
'Prioridade de 1 (baixa) a 10 (alta). Notificações urgentes (handoff) usam 10.
Processamento ordenado por prioridade DESC, scheduled_for ASC.';

COMMENT ON COLUMN notifications.retry_count IS
'Contador de tentativas de reenvio. Máximo definido em max_retries (padrão 3).
Incremented automaticamente pela função update_notification_status().';

COMMENT ON COLUMN notifications.metadata IS
'Dados adicionais em formato JSON. Exemplos:
- appointment_id, appointment_datetime para lembretes
- service_type, rdstation_deal_url para alertas comerciais
- error_details para debugging de falhas';

COMMENT ON TABLE notification_preferences IS
'Preferências de notificação por lead (LGPD compliant).
Controla opt-in/opt-out por canal e categoria, horários preferidos e timezone.
Criada automaticamente no primeiro check_notification_allowed().';

COMMENT ON COLUMN notification_preferences.opt_out_all IS
'Opt-out completo (LGPD). Se true, NENHUMA notificação é enviada,
exceto as legalmente obrigatórias (confirmação de agendamento).';

COMMENT ON COLUMN notification_preferences.preferred_hours_start IS
'Horário preferido de início para receber notificações (timezone aware).
Notificações de alta prioridade (>8) ignoram esta restrição.';

-- ============================================================================
-- VALIDAÇÃO: Verificar criação das tabelas
-- ============================================================================

DO $$
BEGIN
    -- Verificar se tabelas foram criadas
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'notifications'
    ) THEN
        RAISE NOTICE 'Tabela notifications criada com sucesso';
    ELSE
        RAISE EXCEPTION 'Erro ao criar tabela notifications';
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'notification_preferences'
    ) THEN
        RAISE NOTICE 'Tabela notification_preferences criada com sucesso';
    ELSE
        RAISE EXCEPTION 'Erro ao criar tabela notification_preferences';
    END IF;

    -- Verificar índices criados
    RAISE NOTICE 'Schema de notificações criado com sucesso!';
    RAISE NOTICE 'Tabelas: notifications (% indices), notification_preferences (% indices)',
        (SELECT count(*) FROM pg_indexes WHERE tablename = 'notifications'),
        (SELECT count(*) FROM pg_indexes WHERE tablename = 'notification_preferences');
END $$;

-- ============================================================================
-- FIM DO ARQUIVO notifications_schema.sql
-- ============================================================================
