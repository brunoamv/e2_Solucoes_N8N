#!/bin/bash
# Teste de conexão com o PostgreSQL

echo "=== Testando Conexão com PostgreSQL ==="
echo ""

# Testa conexão direta
echo "1. Testando conexão direta..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "SELECT version();" 2>&1

echo ""
echo "2. Testando tabela messages..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'messages' ORDER BY ordinal_position;" 2>&1

echo ""
echo "3. Contando mensagens existentes..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "SELECT COUNT(*) as total_messages FROM messages;" 2>&1

echo ""
echo "4. Testando INSERT..."
MESSAGE_ID="test_$(date +%s)"
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "INSERT INTO messages (conversation_id, direction, content, message_type, media_url, whatsapp_message_id) VALUES (null, 'inbound', 'Teste', 'text', null, '${MESSAGE_ID}') RETURNING id;" 2>&1

echo ""
echo "5. Verificando INSERT..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "SELECT id, content, whatsapp_message_id FROM messages WHERE whatsapp_message_id = '${MESSAGE_ID}';" 2>&1

echo ""
echo "6. Limpando teste..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "DELETE FROM messages WHERE whatsapp_message_id = '${MESSAGE_ID}';" 2>&1

echo ""
echo "=== Teste Concluído ==="#