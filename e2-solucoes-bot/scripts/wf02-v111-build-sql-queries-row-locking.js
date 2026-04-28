// Build SQL Queries Node - V111 Database Row Locking Fix
// Prepara todas as queries SQL com row locking para prevenir race conditions
//
// FIX: Adiciona FOR UPDATE SKIP LOCKED no query_details
// PROBLEMA: Race condition quando usuário envia mensagens mais rápido que DB commit
// SOLUÇÃO: Row locking previne execuções concorrentes de lerem mesma conversa
//
// Recebe dados do node anterior
const data = $input.first().json;
const phone_with_code = data.phone_with_code || '';
const phone_without_code = data.phone_without_code || '';

// Validação de segurança
if (!phone_with_code || !phone_without_code) {
  throw new Error('Phone numbers not properly formatted');
}

// Escape simples para SQL injection
const escapeSql = (str) => {
  return String(str).replace(/'/g, "''");
};

// Query para contar conversas existentes
const query_count = `
  SELECT COUNT(*) as count
  FROM conversations
  WHERE phone_number IN ('${escapeSql(phone_with_code)}', '${escapeSql(phone_without_code)}')
`.trim();

// Query para buscar detalhes da conversa
// V111 CRITICAL: Adiciona FOR UPDATE SKIP LOCKED para prevenir race conditions
const query_details = `
  SELECT
    *,
    COALESCE(state_machine_state,
      CASE current_state
        WHEN 'novo' THEN 'greeting'
        WHEN 'identificando_servico' THEN 'service_selection'
        WHEN 'coletando_dados' THEN 'collect_name'
        WHEN 'agendando' THEN 'scheduling'
        WHEN 'handoff_comercial' THEN 'handoff_comercial'
        WHEN 'concluido' THEN 'completed'
        ELSE 'greeting'
      END
    ) as state_for_machine
  FROM conversations
  WHERE phone_number IN ('${escapeSql(phone_with_code)}', '${escapeSql(phone_without_code)}')
  ORDER BY updated_at DESC
  LIMIT 1
  FOR UPDATE SKIP LOCKED
`.trim();

// Query para criar/atualizar conversa
const query_upsert = `
  -- Limpar duplicatas antigas
  DELETE FROM conversations
  WHERE phone_number IN ('${escapeSql(phone_with_code)}', '${escapeSql(phone_without_code)}')
  AND id NOT IN (
    SELECT id FROM conversations
    WHERE phone_number IN ('${escapeSql(phone_with_code)}', '${escapeSql(phone_without_code)}')
    ORDER BY updated_at DESC
    LIMIT 1
  );

  -- Inserir ou atualizar conversa
  INSERT INTO conversations (
    phone_number,
    whatsapp_name,
    service_id,
    contact_name,
    contact_email,
    city,
    current_state,
    state_machine_state,
    collected_data,
    error_count,
    created_at,
    updated_at
  ) VALUES (
    '${escapeSql(phone_with_code)}',
    '${escapeSql(data.whatsapp_name || '')}',
    NULL,
    NULL,
    NULL,
    NULL,
    'novo',
    'greeting',
    '{}'::jsonb,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
  )
  ON CONFLICT (phone_number) DO UPDATE SET
    whatsapp_name = COALESCE(EXCLUDED.whatsapp_name, conversations.whatsapp_name),
    last_message_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP,
    state_machine_state = CASE
      WHEN conversations.state_machine_state IN ('completed', 'handoff_comercial')
      THEN 'greeting'
      ELSE conversations.state_machine_state
    END
  RETURNING *
`.trim();

// V111: Log para debug
console.log('=== V111 DATABASE ROW LOCKING ENABLED ===');
console.log('V111: FOR UPDATE SKIP LOCKED added to query_details');
console.log('V111: Phone with code:', phone_with_code);
console.log('V111: Phone without code:', phone_without_code);

// Log campos de mensagem preservados
console.log('V111: Message fields preserved:');
console.log('  data.message:', data.message);
console.log('  data.content:', data.content);
console.log('  data.body:', data.body);
console.log('  data.text:', data.text);

// Retornar cada query como campo string individual
// Preservar TODOS os campos de mensagem e dados originais
const result = {
  ...data,  // Pass through ALL original data

  // SQL Queries
  query_count: query_count,        // String SQL
  query_details: query_details,    // String SQL (V111: com FOR UPDATE SKIP LOCKED)
  query_upsert: query_upsert,      // String SQL

  // Explicitly preserve message fields
  message: data.message || '',
  content: data.content || '',
  body: data.body || '',
  text: data.text || '',

  // Phone fields
  phone_with_code: phone_with_code,
  phone_without_code: phone_without_code,
  phone_number: data.phone_number || phone_with_code,

  // Other fields
  whatsapp_name: data.whatsapp_name || '',

  // V111 version marker
  version: 'V111'
};

// Return as array for n8n compatibility
console.log('V111: Build SQL Queries returning array with row locking enabled');
return [result];
