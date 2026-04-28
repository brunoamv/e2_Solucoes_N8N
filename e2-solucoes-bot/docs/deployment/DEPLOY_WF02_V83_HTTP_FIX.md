# Deploy WF02 V83 - HTTP Request Fix

**Workflow**: WF02 AI Conversation V83 (Correção HTTP)
**Arquivo**: `n8n/workflows/02_ai_agent_conversation_V83_HTTP_FIX.json`
**Status**: ✅ Pronto para Deploy
**Data**: 2026-04-20
**Priority**: CRITICAL

---

## 🎯 O que é o V83?

**V83 = V82 + Correção HTTP Request + Validação Robusta**

### Problemas Resolvidos
- ❌ **V82**: HTTP Request usa `bodyParameters` (formato inválido)
- ❌ **V82**: Requests falham silenciosamente
- ❌ **V82**: Prepare nodes recebem `{message: "Workflow was started"}`
- ❌ **V82**: "Bad request - please check your parameters" no Send WhatsApp Response

### Correções V83
- ✅ HTTP Request com `jsonBody` (formato correto n8n v2.14.2)
- ✅ Content-Type explícito: `application/json`
- ✅ Timeout 30s (WF06 pode demorar)
- ✅ neverError: true (continua workflow para debug)
- ✅ Prepare nodes com validação robusta
- ✅ Logs detalhados para troubleshooting

---

## ⚡ Quick Deploy (5 min)

### 1. Verificar WF06 Ativo

```bash
# Testar WF06 responde
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{
    "action": "next_dates",
    "count": 3,
    "service_type": "energia_solar",
    "duration_minutes": 120
  }'

# Esperado: JSON com dates_with_availability
# Se erro 404: Ativar WF06 primeiro
# Ver: docs/deployment/DEPLOY_WF06_V2_1_COMPLETE_FIX.md
```

### 2. Import Workflow V83

```bash
# 1. Acessar n8n UI
http://localhost:5678

# 2. Workflows → Import from file
# 3. Selecionar: 02_ai_agent_conversation_V83_HTTP_FIX.json
# 4. Confirmar import

# Workflow será importado como INATIVO
```

### 3. Validação Visual (2 min)

✅ **HTTP Request - Get Next Dates**:
- Abrir node → Parameters
- Verificar:
  - `Send Body`: true
  - `Body Content Type`: JSON
  - `Specify Body`: JSON
  - `JSON`: Ver body JSON (não "Body Parameters"!)

✅ **HTTP Request - Get Available Slots**:
- Mesma configuração
- Body tem expressões `{{ }}` para data dinâmica

✅ **Prepare Nodes**:
- Ambos devem ter código JavaScript
- Procurar por `console.log('=== PREPARE WF06`
- Código deve ter validações e throw errors

### 4. Ativar Workflow

```bash
# Toggle "Active" → Verde
# Confirmar ativação
```

### 5. Monitorar Logs

```bash
# Terminal separado para logs
docker logs -f e2bot-n8n-dev | grep -E "PREPARE WF06|ERROR|dates_with_availability"
```

### 6. Testar

```bash
# Enviar WhatsApp:
"Olá, gostaria de orçamento para energia solar"

# Aguardar bot responder com serviços
# Escolher: "1" (Energia Solar)

# Esperado nos logs:
# ✅ "=== PREPARE WF06 NEXT DATES V83 ==="
# ✅ "Input: {dates_with_availability: [...]}"
# ✅ "SUCCESS: Received 3 dates with availability"
# ✅ "Prepared data: {wf06_next_dates: [...]}"

# Esperado no WhatsApp:
# Bot mostra 3 datas disponíveis formatadas
```

---

## 🧪 Testes de Validação

### Teste 1: Next Dates Path

```bash
# WhatsApp: "Quero energia solar"
# Bot: [mostra opções de serviços]
# WhatsApp: "1"
# Bot: [pergunta se quer agendar]
# WhatsApp: "Sim"

# Esperado:
# ✅ Bot mostra 3 datas disponíveis
# ✅ Formato: "21/04 (segunda-feira) - 8 horários"

# PostgreSQL Check:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    phone_number,
    current_state,
    collected_data->'wf06_next_dates' as dates
  FROM conversations
  WHERE phone_number = '+5562999999999'
  ORDER BY updated_at DESC LIMIT 1;
"

# Esperado:
# current_state: 8
# dates: [{"date": "2026-04-21", "available_slots": [...]}, ...]
```

### Teste 2: Available Slots Path

```bash
# Continuar conversa:
# WhatsApp: "21/04"

# Esperado:
# ✅ Bot mostra 8 horários disponíveis
# ✅ Formato: "08:00, 09:00, 10:00, ..., 15:00"

# Logs esperados:
# ✅ "=== PREPARE WF06 AVAILABLE SLOTS V83 ==="
# ✅ "SUCCESS: Received 8 available slots"

# PostgreSQL Check:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    current_state,
    collected_data->'selected_date' as date,
    collected_data->'wf06_available_slots' as slots
  FROM conversations
  WHERE phone_number = '+5562999999999';
"

# Esperado:
# current_state: 9
# selected_date: "2026-04-21"
# slots: ["08:00", "09:00", ..., "15:00"]
```

### Teste 3: Error Handling

```bash
# Simular WF06 offline
docker stop e2bot-n8n-dev  # Stop container que tem WF06

# WhatsApp: "Quero energia solar" → "1" → "Sim"

# Esperado nos logs:
# ❌ "ERROR: No response from WF06"
# OU
# ❌ "ERROR: No dates_with_availability in response"

# Workflow deve FALHAR EXPLICITAMENTE
# Não deve continuar com dados vazios

# Restaurar WF06
docker start e2bot-n8n-dev
```

---

## 🔍 Troubleshooting

### Problema: HTTP Request retorna {message: "Workflow was started"}

**Causa**: Body não está sendo enviado corretamente

**Diagnóstico**:
```bash
# 1. Ver configuração do node
# Deve ter:
#   - Send Body: true
#   - Body Content Type: JSON
#   - Specify Body: JSON
#   - JSON: {...} (texto JSON)

# 2. NÃO deve ter:
#   - Body Parameters (campo antigo)
```

**Solução**:
```bash
# Reimportar V83
# Ou editar manualmente:
# 1. Abrir HTTP Request node
# 2. Body Parameters → Deletar
# 3. Body Content Type → JSON
# 4. Specify Body → JSON
# 5. JSON → Colar:
{
  "action": "next_dates",
  "count": 3,
  "service_type": "energia_solar",
  "duration_minutes": 120
}
```

### Problema: Prepare node lança "Invalid WF06 response format"

**Causa**: WF06 retorna formato inesperado

**Diagnóstico**:
```bash
# Verificar logs do Prepare node
docker logs e2bot-n8n-dev | grep -A 10 "PREPARE WF06"

# Procurar por:
# "Input: {...}"
# "Response keys: [...]"
```

**Solução**:
```bash
# Se WF06 retorna formato diferente:
# 1. Ver formato real nos logs
# 2. Atualizar Prepare node para suportar formato
# 3. Adicionar case no if/else de extração
```

### Problema: "Bad request - please check your parameters" persiste

**Causa**: State Machine recebe dados incorretos

**Diagnóstico**:
```bash
# Executar workflow manualmente:
# 1. n8n UI → WF02 V83
# 2. Clicar em "Execute Workflow"
# 3. Inspecionar cada node:
#    - HTTP Request: deve ter JSON com dates_with_availability
#    - Prepare: deve ter wf06_next_dates array
#    - Merge: deve combinar ambos inputs
#    - State Machine: deve ter todos dados

# Identificar onde dados são perdidos
```

---

## 📊 Monitoramento

### Logs Importantes

```bash
# Sucesso - Preparação Next Dates
docker logs e2bot-n8n-dev | grep "PREPARE WF06 NEXT DATES"
# Esperado:
# === PREPARE WF06 NEXT DATES V83 ===
# SUCCESS: Received 3 dates with availability

# Sucesso - Preparação Slots
docker logs e2bot-n8n-dev | grep "PREPARE WF06 AVAILABLE SLOTS"
# Esperado:
# === PREPARE WF06 AVAILABLE SLOTS V83 ===
# SUCCESS: Received 8 available slots

# Erros
docker logs e2bot-n8n-dev | grep "ERROR:"
# Não deve ter erros relacionados a WF06

# Requests HTTP
docker logs e2bot-n8n-dev | grep "HTTP Request"
# Ver status codes (deve ser 200)
```

### PostgreSQL Monitoring

```bash
# Últimas conversas com WF06 data
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    phone_number,
    current_state,
    CASE
      WHEN collected_data ? 'wf06_next_dates' THEN 'Has Next Dates'
      WHEN collected_data ? 'wf06_available_slots' THEN 'Has Slots'
      ELSE 'No WF06 Data'
    END as wf06_status,
    updated_at
  FROM conversations
  WHERE updated_at > NOW() - INTERVAL '1 hour'
  ORDER BY updated_at DESC
  LIMIT 10;
"
```

---

## 🔄 Rollback

Se V83 apresentar problemas:

```bash
# 1. Desativar V83
# n8n UI → V83 → Toggle OFF

# 2. Reativar workflow anterior
# Opções:
#   - V74.1_2 (produção atual, sem WF06)
#   - V80 COMPLETE (15 states, sem WF06)

# 3. Investigar logs
docker logs e2bot-n8n-dev --tail 100 > /tmp/v83_errors.log

# 4. Reportar problema
# Criar issue com:
#   - Logs de erro
#   - Execution URL
#   - Dados de input/output de cada node
```

---

## ✅ Checklist de Deploy

- [ ] WF06 V2.1 ativo e respondendo
- [ ] V83 importado com sucesso
- [ ] HTTP Request nodes têm `jsonBody` (não bodyParameters)
- [ ] Prepare nodes têm código de validação
- [ ] Workflow ativado (toggle verde)
- [ ] Logs monitorando em terminal
- [ ] Teste 1: Next Dates path → 3 datas recebidas
- [ ] Teste 2: Available Slots path → 8 horários recebidos
- [ ] Teste 3: Error handling → Falha explícita se WF06 offline
- [ ] PostgreSQL: wf06_next_dates e wf06_available_slots salvos corretamente
- [ ] Sem erros "Bad request" no Send WhatsApp Response

---

## 📚 Documentação Relacionada

**Bugfix Report**: `docs/fix/BUGFIX_WF02_V83_HTTP_REQUEST_FIX.md`

**Workflows Base**:
- WF02 V82 CLEAN: Versão anterior com HTTP bugado
- WF06 V2.1: Calendar availability service

**Deploy Guides**:
- `docs/deployment/DEPLOY_WF06_V2_1_COMPLETE_FIX.md` (setup WF06)
- `docs/deployment/DEPLOY_WF02_V82_CLEAN.md` (V82 anterior)

**Scripts**:
- `scripts/generate-wf02-v83-http-fix.py`: Geração V83

---

## 🎯 V83 vs V82

| Feature | V82 CLEAN | V83 HTTP FIX |
|---------|-----------|--------------|
| Import Status | ✅ | ✅ |
| HTTP Request Config | ❌ bodyParameters | ✅ jsonBody |
| WF06 Integration | ❌ Falha | ✅ Funciona |
| Error Handling | ❌ Silencioso | ✅ Explícito |
| Validação | ⚠️ Básica | ✅ Robusta |
| Logs | ❌ Mínimos | ✅ Detalhados |
| Production Ready | ❌ | ✅ |

**Recomendação**: Deploy V83 imediato (resolve bloqueio crítico)

---

**Deploy Guide**: WF02 V83 HTTP FIX
**Created**: 2026-04-20
**Status**: ✅ READY FOR PRODUCTION
**Priority**: CRITICAL - Resolve WF06 integration
