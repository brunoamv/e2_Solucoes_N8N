#!/bin/bash

# Script de teste para validar a extração correta do phone_number
# Data: $(date)

echo "🧪 Teste de extração de phone_number"
echo "====================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para testar extração
test_phone_extraction() {
    local remote_jid="$1"
    local expected="$2"

    # Simula a extração usando node
    result=$(node -e "
    function extractPhoneNumber(remoteJid) {
        if (!remoteJid) return '';

        // Remove @s.whatsapp.net ou @g.us (grupos)
        let cleaned = remoteJid.replace(/@[sg]\.(?:whatsapp\.net|us)$/, '');

        // Se o número tem o formato brasileiro completo (55 + DDD + número)
        if (cleaned.startsWith('55') && cleaned.length >= 12) {
            // Remove o código do país (55) e mantém DDD + número
            cleaned = cleaned.substring(2);
        }

        // Validação adicional
        if (!/^\d{10,11}$/.test(cleaned)) {
            console.log('WARNING: Format unexpected for', cleaned);
        }

        return cleaned;
    }

    console.log(extractPhoneNumber('$remote_jid'));
    ")

    if [ "$result" = "$expected" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $remote_jid → $result"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: $remote_jid → $result (expected: $expected)"
        return 1
    fi
}

echo "📋 Testando diferentes formatos de remoteJid:"
echo ""

# Casos de teste
test_phone_extraction "556198175548@s.whatsapp.net" "6198175548"
test_phone_extraction "5561981755748@s.whatsapp.net" "61981755748"
test_phone_extraction "556298175548@s.whatsapp.net" "6298175548"
test_phone_extraction "5511987654321@s.whatsapp.net" "11987654321"
test_phone_extraction "5521987654321@s.whatsapp.net" "21987654321"
test_phone_extraction "276754908315794@s.whatsapp.net" "276754908315794"  # ID do WhatsApp
test_phone_extraction "556198175548@g.us" "6198175548"  # Grupo
test_phone_extraction "" ""  # Vazio

echo ""
echo "📊 Testando no banco de dados:"
echo ""

# Testa se os telefones no banco estão no formato correto
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    phone_number,
    CASE
        WHEN phone_number IS NULL THEN '❌ NULL'
        WHEN phone_number = '' THEN '❌ EMPTY'
        WHEN phone_number = 'undefined' THEN '❌ UNDEFINED'
        WHEN LENGTH(phone_number) NOT BETWEEN 10 AND 11 THEN '⚠️ FORMATO INVÁLIDO'
        WHEN phone_number ~ '^[0-9]{10,11}$' THEN '✅ OK'
        ELSE '⚠️ FORMATO SUSPEITO'
    END as status,
    whatsapp_name,
    current_state
FROM conversations
ORDER BY created_at DESC
LIMIT 10;
"

echo ""
echo "📈 Resumo de validação do banco:"
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -t -c "
SELECT
    COUNT(*) FILTER (WHERE phone_number IS NULL) as nulls,
    COUNT(*) FILTER (WHERE phone_number = '') as empty,
    COUNT(*) FILTER (WHERE phone_number = 'undefined') as undefined,
    COUNT(*) FILTER (WHERE LENGTH(phone_number) NOT BETWEEN 10 AND 11) as invalid_format,
    COUNT(*) FILTER (WHERE phone_number ~ '^[0-9]{10,11}$') as valid_format,
    COUNT(*) as total
FROM conversations;
" | while read nulls empty undefined invalid valid total; do
    echo "  📱 Telefones no banco:"
    echo "    - NULL: $nulls"
    echo "    - Vazios: $empty"
    echo "    - Undefined: $undefined"
    echo "    - Formato inválido: $invalid"
    echo "    - ✅ Formato válido: $valid"
    echo "    - Total: $total"
done

echo ""
echo "🔍 Verificando últimas mensagens processadas:"
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    m.id,
    c.phone_number,
    m.direction,
    LEFT(m.content, 30) as content_preview,
    m.created_at
FROM messages m
LEFT JOIN conversations c ON m.conversation_id = c.id
ORDER BY m.created_at DESC
LIMIT 5;
"

echo ""
echo "✨ Teste concluído!"
echo ""
echo "📝 Recomendações:"
echo "  - Se houver telefones com formato inválido, reimporte os workflows corrigidos"
echo "  - Workflows corrigidos:"
echo "    • 01 - WhatsApp Handler (ULTIMATE)_FIXED_PHONE_CORRECT.json"
echo "    • 02_ai_agent_conversation_V1_MENU_COMPLETE_REFACTOR.json"