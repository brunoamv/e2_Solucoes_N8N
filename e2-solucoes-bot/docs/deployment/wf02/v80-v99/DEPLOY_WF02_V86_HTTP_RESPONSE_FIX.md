# Deploy WF02 V86 - HTTP Response Fix

**Workflow**: WF02 AI Conversation V86 (Correção HTTP Response Wrapping)
**Arquivo**: `n8n/workflows/02_ai_agent_conversation_V86_HTTP_RESPONSE_FIX.json`
**Status**: ✅ Pronto para Deploy
**Data**: 2026-04-20
**Priority**: CRITICAL

---

## 🎯 O que é o V86?

**V86 = V85 + Correção COMPLETA do HTTP Response Wrapping**

### Problema Resolvido

**Descoberta Crítica**: O n8n HTTP Request node **transforma/wrapeia** a resposta do webhook antes de passar para o próximo node!

- ❌ **V84/V85**: Verificavam apenas 2 paths de acesso (root + json wrapeado)
- ❌ **V84/V85**: Falhavam com "missing dates property" APESAR de WF06 retornar resposta perfeita
- ✅ **V86**: Verifica **6 paths diferentes** de acesso + logs do path usado

### Correções V86

- ✅ Verifica `httpResponse.dates` (root level)
- ✅ Verifica `httpResponse.json.dates` (json wrapeado)
- ✅ Verifica `httpResponse.body.dates` (body property, com parsing string/object)
- ✅ Verifica `httpResponse.data.dates` (data property)
- ✅ Verifica `httpResponse` direto (formato WF06 completo)
- ✅ Logs mostram **QUAL path funcionou** (access path)
- ✅ Se falhar, mostra **estrutura COMPLETA** da resposta para diagnóstico

---

## ⚡ Quick Deploy (3 min)

### 1. Pré-requisitos

```bash
# Verificar WF06 V2.1 está ativo e respondendo
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{
    "action": "next_dates",
    "count": 3,
    "service_type": "energia_solar",
    "duration_minutes": 120
  }'

# Esperado: JSON com "dates" array
# {
#   "success": true,
#   "action": "next_dates",
#   "dates": [...],
#   "total_available": 3
# }

# Se erro 404: Ativar WF06 primeiro
# Ver: docs/deployment/DEPLOY_WF06_V2_1_COMPLETE_FIX.md
```

### 2. Import Workflow V86

```bash
# 1. Acessar n8n UI
http://localhost:5678

# 2. Workflows → Import from file
# 3. Selecionar: 02_ai_agent_conversation_V86_HTTP_RESPONSE_FIX.json
# 4. Confirmar import

# Workflow será importado como INATIVO
```

### 3. Validação Visual (1 min)

✅ **Prepare WF06 Next Dates Data**:
- Abrir node → Code
- Verificar código tem comentário: `// V86 (COMPLETE FIX)`
- Procurar por: `let accessPath = ''`
- Verificar múltiplos `if/else if` para diferentes paths

✅ **Prepare WF06 Available Slots Data**:
- Mesma verificação
- Código similar com múltiplos paths

### 4. Ativar Workflow

```bash
# Toggle "Active" → Verde
# Confirmar ativação
```

### 5. Testar e Monitorar

```bash
# Terminal 1: Logs em tempo real
docker logs -f e2bot-n8n-dev | grep -A 10 "PREPARE WF06 NEXT DATES V86"

# Terminal 2: Teste WhatsApp
# Enviar: "Olá, gostaria de orçamento para energia solar"
# Aguardar: Bot responde com serviços
# Enviar: "1" (Energia Solar)
# Aguardar: Bot pergunta sobre agendamento
# Enviar: "Sim"

# Esperado nos logs (Terminal 1):
# ✅ "=== PREPARE WF06 NEXT DATES V86 (COMPLETE FIX) ==="
# ✅ "Full httpResponse: {...}" (estrutura completa)
# ✅ "✅ Found dates in [PATH]"
# ✅ "Access path used: httpResponse.X.dates" (mostra qual path funcionou!)
# ✅ "SUCCESS: Received 3 dates with availability"

# Esperado no WhatsApp:
# Bot mostra 3 datas disponíveis formatadas
```

---

## 🧪 Testes de Validação

### Teste 1: Next Dates Path (CRÍTICO)

```bash
# Conversa WhatsApp:
# User: "Quero energia solar"
# Bot: [mostra opções de serviços]
# User: "1"
# Bot: [pergunta se quer agendar]
# User: "Sim"

# Esperado:
# ✅ Bot mostra 3 datas disponíveis
# ✅ Formato: "21/04 (segunda-feira) - 8 horários"

# Logs esperados:
docker logs -f e2bot-n8n-dev | grep -A 15 "PREPARE WF06 NEXT DATES V86"

# Deve mostrar:
# ✅ Full httpResponse: {...}
# ✅ Access path used: [httpResponse.X.dates]
# ✅ SUCCESS: Received 3 dates with availability

# PostgreSQL Check:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    phone_number,
    current_state,
    jsonb_pretty(collected_data->'wf06_next_dates') as dates
  FROM conversations
  WHERE phone_number = '+5562999999999'
  ORDER BY updated_at DESC LIMIT 1;
"

# Esperado:
# current_state: 8
# dates: JSON array com 3 objetos
```

### Teste 2: Available Slots Path

```bash
# Continuar conversa:
# User: "21/04"

# Esperado:
# ✅ Bot mostra 8 horários disponíveis
# ✅ Formato: "08:00, 09:00, 10:00, ..., 15:00"

# Logs esperados:
docker logs -f e2bot-n8n-dev | grep -A 15 "PREPARE WF06 AVAILABLE SLOTS V86"

# Deve mostrar:
# ✅ Access path used: [httpResponse.X.slots]
# ✅ SUCCESS: Received 8 available slots

# PostgreSQL Check:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    current_state,
    collected_data->'selected_date' as date,
    jsonb_pretty(collected_data->'wf06_available_slots') as slots
  FROM conversations
  WHERE phone_number = '+5562999999999';
"

# Esperado:
# current_state: 9
# selected_date: "2026-04-21"
# slots: JSON array com 8 strings de horários
```

### Teste 3: Debug Output Analysis

```bash
# Capturar QUAL path funcionou
docker logs e2bot-n8n-dev | grep "Access path used"

# Exemplos de output possível:
# ✅ "Access path used: httpResponse.dates"
# ✅ "Access path used: httpResponse.json.dates"
# ✅ "Access path used: httpResponse.body.dates"
# ✅ "Access path used: httpResponse.data.dates"

# Isso confirma COMO n8n HTTP Request está wrapeando a resposta!
```

---

## 🔍 Troubleshooting

### Problema: V86 ainda lança "missing dates property"

**Causa**: n8n usa path de acesso não previsto nos 6 paths verificados

**Diagnóstico**:
```bash
# Verificar logs COMPLETOS do erro
docker logs e2bot-n8n-dev | grep -A 30 "Response structure:"

# V86 mostrará estrutura COMPLETA da resposta:
# "Response structure: {
#    ... (estrutura completa do objeto)
# }"

# Isso revelará EXATAMENTE como acessar a resposta
```

**Solução**:
```bash
# Se encontrar novo path (exemplo: httpResponse.result.dates):
# 1. Anotar path descoberto
# 2. Criar issue com estrutura encontrada
# 3. Criar V87 adicionando novo path ao código
```

### Problema: Logs não mostram "Access path used"

**Causa**: Prepare node falhou ANTES de encontrar dados

**Diagnóstico**:
```bash
# Ver erro exato
docker logs e2bot-n8n-dev | grep -B 5 -A 20 "PREPARE WF06 NEXT DATES V86"

# Procurar por:
# - "Response structure:" (mostra estrutura completa)
# - "Checked paths:" (mostra quais paths foram verificados)
```

### Problema: "Bad request" ainda persiste

**Causa**: State Machine recebe dados mas em formato errado

**Diagnóstico**:
```bash
# Executar workflow manualmente:
# 1. n8n UI → WF02 V86
# 2. Clicar em "Execute Workflow"
# 3. Inspecionar TODOS nodes:
#    - HTTP Request: Output deve ter status 200
#    - Debug node: Output deve ter dados WF06
#    - Prepare: Output deve ter {wf06_next_dates: [...]}
#    - Merge: Output deve combinar todos dados
#    - State Machine: Input deve ter wf06_next_dates array

# Identificar onde estrutura quebra
```

---

## 📊 Monitoramento

### Logs Críticos

```bash
# Sucesso - Preparação Next Dates
docker logs e2bot-n8n-dev | grep "PREPARE WF06 NEXT DATES V86" -A 5

# Esperado ver:
# === PREPARE WF06 NEXT DATES V86 (COMPLETE FIX) ===
# Full httpResponse: {...}
# ✅ Found dates in [PATH]
# Access path used: httpResponse.X.dates
# SUCCESS: Received 3 dates with availability

# Sucesso - Preparação Slots
docker logs e2bot-n8n-dev | grep "PREPARE WF06 AVAILABLE SLOTS V86" -A 5

# Esperado ver:
# === PREPARE WF06 AVAILABLE SLOTS V86 (COMPLETE FIX) ===
# Access path used: httpResponse.X.slots
# SUCCESS: Received 8 available slots

# Falha - Diagnóstico Completo
docker logs e2bot-n8n-dev | grep "Response structure:" -A 20

# Se aparecer, mostra estrutura COMPLETA para análise
```

### PostgreSQL Monitoring

```bash
# Conversas com WF06 data
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    phone_number,
    current_state,
    CASE
      WHEN collected_data ? 'wf06_next_dates' THEN 'Has Next Dates ✅'
      WHEN collected_data ? 'wf06_available_slots' THEN 'Has Slots ✅'
      ELSE 'No WF06 Data ❌'
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

Se V86 apresentar problemas:

```bash
# 1. Desativar V86
# n8n UI → V86 → Toggle OFF

# 2. Reativar workflow anterior
# Opções:
#   - V74.1_2 (produção atual, sem WF06)
#   - V80 COMPLETE (15 states, sem WF06)

# 3. Capturar logs de diagnóstico
docker logs e2bot-n8n-dev --tail 200 | grep "V86" > /tmp/v86_diagnostic.log

# 4. Analisar estrutura da resposta capturada
grep "Response structure:" /tmp/v86_diagnostic.log -A 30
```

---

## ✅ Checklist de Deploy

- [ ] WF06 V2.1 ativo e respondendo corretamente
- [ ] V86 importado com sucesso
- [ ] Prepare nodes têm código V86 (COMPLETE FIX)
- [ ] Workflow ativado (toggle verde)
- [ ] Logs monitorando em terminal
- [ ] Teste 1: Next Dates → 3 datas recebidas ✅
- [ ] Teste 1: Logs mostram "Access path used" ✅
- [ ] Teste 2: Available Slots → 8 horários recebidos ✅
- [ ] PostgreSQL: wf06_next_dates e wf06_available_slots salvos ✅
- [ ] Sem erros "Bad request" no Send WhatsApp Response ✅
- [ ] Se falhou: "Response structure" logs capturados para análise

---

## 📚 Documentação Relacionada

**Análise do Problema**: `docs/analysis/WF02_V85_V86_HTTP_RESPONSE_WRAPPING_ANALYSIS.md`

**Workflows Base**:
- WF02 V85 DIAGNOSTIC: Versão anterior com Debug nodes
- WF06 V2.1 COMPLETE: Calendar availability service

**Histórico de Correções**:
- V81: Fix conexões desconectadas
- V82: Fix import metadata
- V83: Fix HTTP Request jsonBody
- V84: Fix Prepare extraction (dates property)
- V85: Add Debug nodes
- **V86: Fix HTTP Response wrapping (COMPLETE)** ✅

**Scripts**:
- `scripts/generate-wf02-v86-http-response-fix.py`: Geração V86

---

## 🎯 V85 vs V86

| Feature | V85 DIAGNOSTIC | V86 HTTP RESPONSE FIX |
|---------|----------------|----------------------|
| Debug Nodes | ✅ (mas console.log invisível) | ✅ (herdado) |
| HTTP Request Config | ✅ jsonBody correto | ✅ jsonBody correto |
| Prepare Paths Verificados | 2 (root + json) | 6 (COMPLETE) |
| Root Level Check | ✅ | ✅ |
| JSON Wrapeado Check | ✅ | ✅ |
| Body Property Check | ❌ | ✅ |
| Data Property Check | ❌ | ✅ |
| WF06 Direct Format | ❌ | ✅ |
| Body String Parsing | ❌ | ✅ |
| Access Path Logging | ❌ | ✅ |
| Full Structure on Error | ❌ | ✅ |
| Production Ready | ❌ | ✅ |

**Recomendação**: Deploy V86 imediato (resolve bloqueio HTTP wrapping)

---

**Deploy Guide**: WF02 V86 HTTP RESPONSE FIX
**Created**: 2026-04-20
**Status**: ✅ READY FOR PRODUCTION
**Priority**: CRITICAL - Resolve bloqueio WF06 integration definitivamente
