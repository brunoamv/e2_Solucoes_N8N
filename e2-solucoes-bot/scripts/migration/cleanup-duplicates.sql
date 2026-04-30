-- Script para limpar mensagens duplicadas no banco de dados
-- Data: 2025-01-12

-- 1. Identificar mensagens duplicadas
SELECT
    whatsapp_message_id,
    COUNT(*) as duplicate_count,
    MIN(id) as keep_id,
    ARRAY_AGG(id ORDER BY created_at DESC) as all_ids,
    ARRAY_AGG(created_at ORDER BY created_at DESC) as created_times
FROM messages
WHERE whatsapp_message_id IS NOT NULL
GROUP BY whatsapp_message_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- 2. Criar backup das mensagens que serão removidas
CREATE TABLE IF NOT EXISTS messages_backup_20250112 AS
SELECT m.*
FROM messages m
WHERE m.whatsapp_message_id IN (
    SELECT whatsapp_message_id
    FROM messages
    WHERE whatsapp_message_id IS NOT NULL
    GROUP BY whatsapp_message_id
    HAVING COUNT(*) > 1
);

-- 3. Contar quantas mensagens serão afetadas
SELECT
    COUNT(DISTINCT whatsapp_message_id) as unique_messages_with_duplicates,
    SUM(duplicate_count) - COUNT(*) as total_duplicates_to_remove
FROM (
    SELECT whatsapp_message_id, COUNT(*) as duplicate_count
    FROM messages
    WHERE whatsapp_message_id IS NOT NULL
    GROUP BY whatsapp_message_id
    HAVING COUNT(*) > 1
) dup;

-- 4. Remover duplicatas mantendo apenas a mensagem mais antiga
DELETE FROM messages
WHERE id IN (
    SELECT id
    FROM (
        SELECT
            id,
            whatsapp_message_id,
            ROW_NUMBER() OVER (PARTITION BY whatsapp_message_id ORDER BY created_at ASC) as rn
        FROM messages
        WHERE whatsapp_message_id IS NOT NULL
    ) t
    WHERE rn > 1
);

-- 5. Verificar se a limpeza foi bem-sucedida
SELECT
    'After cleanup' as status,
    COUNT(*) as total_messages,
    COUNT(DISTINCT whatsapp_message_id) as unique_message_ids
FROM messages
WHERE whatsapp_message_id IS NOT NULL;