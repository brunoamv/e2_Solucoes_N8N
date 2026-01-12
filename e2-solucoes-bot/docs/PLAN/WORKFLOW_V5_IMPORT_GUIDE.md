# 🚨 GUIA CRÍTICO: Importação do Workflow v5 Corrigido

**Data**: 2026-01-06
**Status**: AÇÃO IMEDIATA NECESSÁRIA
**Problema**: `collected_data` sempre retornando vazio ou apenas `{"error_count":0}`

---

## 🔴 PROBLEMA IDENTIFICADO

### Diagnóstico Completo
1. **Workflow errado está ativo** no n8n (ID: `KvY01p1QW9B66Ai2`)
2. **Workflow v5 corrigido** foi criado mas **NÃO foi importado**
3. **Erros no banco**: `undefined` states violando constraints
4. **Perda de dados**: Apenas `error_count` sendo salvo, todos outros campos perdidos

### Evidências do Problema
```sql
-- Resultado atual (ERRADO):
collected_data = {"error_count": 0}  -- Apenas isso!

-- Resultado esperado (CORRETO):
collected_data = {
  "error_count": 0,
  "lead_name": "João Silva",
  "phone": "62981755485",
  "email": "joao@email.com",
  "city": "Goiânia",
  "service_type": "energia_solar"
}
```

---

## ✅ SOLUÇÃO: IMPORTAR WORKFLOW v5

### Passo 1: Execute o Script de Importação
```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
./scripts/import-v5-workflow.sh
```

### Passo 2: Siga as Instruções no n8n
1. **Acesse n8n**: http://localhost:5678
2. **Desative workflows antigos**:
   - Encontre: "02 - AI Agent Conversation_V28" → Toggle OFF
   - Encontre: "02 - AI Agent Conversation_V1_MENU" → Toggle OFF
3. **Importe o v5**:
   - Click "Import from File"
   - Selecione: `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v5.json`
4. **Ative o novo workflow**:
   - Nome: "02 - AI Agent Conversation_V1_MENU_FIXED_v5"
   - Toggle ON (verde)

### Passo 3: Valide a Correção
```bash
# Execute o validador
./scripts/validate-v5-fix.sh

# Deve mostrar:
# ✅ error_count type is 'number' - CORRECT
# ✅ lead_name exists with value: João Silva
# ✅ phone exists with value: 62981755485
```

---

## 🔧 O QUE FOI CORRIGIDO NO v5

### 1. Preservação de Tipos (Prepare Update Data)
```javascript
// ANTES (v3) - ERRADO:
cleanedData[key] = String(value);  // Convertia tudo para string!

// DEPOIS (v5) - CORRETO:
if (typeof value === 'number') {
    cleanedData[key] = value;  // Mantém como número
} else if (typeof value === 'boolean') {
    cleanedData[key] = value;  // Mantém como boolean
}
```

### 2. Preservação de Dados (State Machine)
```javascript
// ANTES (v3) - ERRADO:
updateData.error_count = errorCount;  // Sobrescrevia tudo!

// DEPOIS (v5) - CORRETO:
updateData = {
    ...stageData,      // Mantém dados existentes
    ...updateData,     // Adiciona novos
    error_count: errorCount
};
```

### 3. Query Segura (Update Conversation)
```sql
-- DEPOIS (v5) - COM PROTEÇÃO:
collected_data = COALESCE(
    NULLIF('{{ $json.collected_data_json }}', '')::jsonb,
    '{}'::jsonb
)
```

---

## 📊 TESTE RÁPIDO APÓS IMPORTAÇÃO

### 1. Envie uma mensagem teste no WhatsApp
```
Oi
```

### 2. Verifique no banco de dados
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    phone_number,
    current_state,
    jsonb_pretty(collected_data) as data,
    jsonb_typeof(collected_data->'error_count') as type_check
FROM conversations
ORDER BY updated_at DESC
LIMIT 1;"
```

### 3. Resultado Esperado
```
type_check | data
-----------+---------------------------
number     | {
           |   "error_count": 0,
           |   "last_state": "greeting"
           | }
```

---

## ⚠️ TROUBLESHOOTING

### Se ainda não funcionar:

1. **Verifique workflows ativos**:
   - Apenas UM workflow "02_ai_agent" deve estar ativo
   - Desative TODOS os outros similares

2. **Limpe dados de teste**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
DELETE FROM conversations WHERE phone_number='5562981755485';"
```

3. **Reinicie n8n**:
```bash
docker restart e2bot-n8n-dev
```

4. **Verifique logs**:
```bash
docker logs e2bot-n8n-dev --tail 50
```

---

## 🎯 CHECKLIST FINAL

- [ ] Script `import-v5-workflow.sh` executado
- [ ] Workflow v5 importado no n8n
- [ ] Workflows antigos desativados
- [ ] Workflow v5 ativado (toggle verde)
- [ ] Teste enviado via WhatsApp
- [ ] Validação executada com sucesso
- [ ] `error_count` aparece como tipo `number` (não `text`)
- [ ] Todos os campos são preservados entre conversas

---

## 📞 SUPORTE

Se precisar de ajuda:
1. Verifique os logs: `docker logs e2bot-n8n-dev`
2. Consulte: `/docs/PLAN/collected_data_persistence_fix.md`
3. Script de correção: `/scripts/fix-complete-data-loss.py`

**AÇÃO IMEDIATA**: Execute `./scripts/import-v5-workflow.sh` AGORA!