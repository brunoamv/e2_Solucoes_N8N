-- ============================================================================
-- MIGRAÇÃO 003: Sistema de Notificações Multi-Canal (Sprint 1.3)
-- Data: 2025-12-15
-- Descrição: Adiciona tabelas e funções para sistema de notificações
-- ============================================================================

\echo '========================================='
\echo 'INICIANDO MIGRAÇÃO 003: NOTIFICAÇÕES'
\echo '========================================='

-- Executar schema
\i /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/database/notifications_schema.sql

-- Executar funções
\i /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/database/notification_functions.sql

-- Criar preferências padrão para leads existentes
\echo 'Criando preferências padrão para leads existentes...'

INSERT INTO notification_preferences (lead_id, email_enabled, whatsapp_enabled)
SELECT id, true, true
FROM leads
WHERE id NOT IN (SELECT lead_id FROM notification_preferences)
ON CONFLICT (lead_id) DO NOTHING;

\echo 'Migração 003 concluída com sucesso!'
\echo '========================================='
