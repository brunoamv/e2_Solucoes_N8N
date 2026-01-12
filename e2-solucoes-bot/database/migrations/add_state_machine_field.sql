-- ====================================
-- MIGRAÇÃO: Adicionar campo state_machine_state
-- Data: 2025-01-08
-- Objetivo: Permitir armazenamento do estado exato do State Machine
-- ====================================

-- 1. Adicionar novo campo state_machine_state na tabela leads
ALTER TABLE leads
ADD COLUMN IF NOT EXISTS state_machine_state VARCHAR(50);

-- 2. Criar constraint para valores válidos do State Machine
ALTER TABLE leads
ADD CONSTRAINT valid_state_machine_state CHECK (
    state_machine_state IN (
        'greeting',
        'service_selection',
        'collect_name',
        'collect_phone',
        'collect_email',
        'collect_city',
        'confirmation',
        'scheduling',
        'handoff_comercial',
        'completed'
    ) OR state_machine_state IS NULL
);

-- 3. Adicionar índice para performance
CREATE INDEX IF NOT EXISTS idx_leads_state_machine ON leads(state_machine_state);

-- 4. Comentário para documentação
COMMENT ON COLUMN leads.state_machine_state IS 'Estado atual do State Machine do bot - mantém sincronização com workflow n8n';

-- 5. Atualizar registros existentes (opcional)
-- Se quiser mapear status existentes para o novo campo
UPDATE leads
SET state_machine_state = CASE
    WHEN status = 'novo' THEN 'greeting'
    WHEN status = 'em_atendimento' THEN 'service_selection'
    WHEN status = 'agendado' THEN 'scheduling'
    WHEN status = 'handoff' THEN 'handoff_comercial'
    WHEN status = 'concluido' THEN 'completed'
    ELSE NULL
END
WHERE state_machine_state IS NULL;

-- 6. Adicionar campo similar na tabela conversations para consistência
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS state_machine_state VARCHAR(50);

-- 7. Constraint para conversations
ALTER TABLE conversations
DROP CONSTRAINT IF EXISTS valid_state_machine_state_conv;

ALTER TABLE conversations
ADD CONSTRAINT valid_state_machine_state_conv CHECK (
    state_machine_state IN (
        'greeting',
        'service_selection',
        'collect_name',
        'collect_phone',
        'collect_email',
        'collect_city',
        'confirmation',
        'scheduling',
        'handoff_comercial',
        'completed'
    ) OR state_machine_state IS NULL
);

-- 8. Índice para conversations
CREATE INDEX IF NOT EXISTS idx_conversations_state_machine ON conversations(state_machine_state);

-- 9. Comentário para conversations
COMMENT ON COLUMN conversations.state_machine_state IS 'Estado atual do State Machine do bot - sincronizado com workflow n8n';

-- 10. Função para mapear state_machine_state para status
CREATE OR REPLACE FUNCTION map_state_to_status(p_state VARCHAR)
RETURNS VARCHAR AS $$
BEGIN
    RETURN CASE p_state
        WHEN 'greeting' THEN 'novo'
        WHEN 'service_selection' THEN 'em_atendimento'
        WHEN 'collect_name' THEN 'em_atendimento'
        WHEN 'collect_phone' THEN 'em_atendimento'
        WHEN 'collect_email' THEN 'em_atendimento'
        WHEN 'collect_city' THEN 'em_atendimento'
        WHEN 'confirmation' THEN 'em_atendimento'
        WHEN 'scheduling' THEN 'agendado'
        WHEN 'handoff_comercial' THEN 'handoff'
        WHEN 'completed' THEN 'concluido'
        ELSE 'novo'
    END;
END;
$$ LANGUAGE plpgsql;

-- 11. Trigger para auto-atualizar status baseado no state_machine_state
CREATE OR REPLACE FUNCTION update_status_from_state()
RETURNS TRIGGER AS $$
BEGIN
    -- Atualiza status automaticamente quando state_machine_state muda
    IF NEW.state_machine_state IS NOT NULL AND NEW.state_machine_state != COALESCE(OLD.state_machine_state, '') THEN
        NEW.status = map_state_to_status(NEW.state_machine_state);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 12. Criar trigger na tabela leads
DROP TRIGGER IF EXISTS trigger_update_status_from_state ON leads;
CREATE TRIGGER trigger_update_status_from_state
    BEFORE INSERT OR UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_status_from_state();

-- 13. Criar trigger similar para conversations
DROP TRIGGER IF EXISTS trigger_update_status_from_state_conv ON conversations;
CREATE TRIGGER trigger_update_status_from_state_conv
    BEFORE INSERT OR UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_status_from_state();

-- ====================================
-- FIM DA MIGRAÇÃO
-- ====================================

-- Para executar:
-- psql -U postgres -d e2_bot -f add_state_machine_field.sql

-- Para reverter (se necessário):
-- ALTER TABLE leads DROP COLUMN state_machine_state;
-- ALTER TABLE conversations DROP COLUMN state_machine_state;
-- DROP FUNCTION IF EXISTS map_state_to_status(VARCHAR);
-- DROP FUNCTION IF EXISTS update_status_from_state();