# Deploy WF02 V81 FIXED - Guia Rápido

**Workflow**: WF02 AI Conversation V81 com WF06 Integration (CORRIGIDO)
**Arquivo**: `n8n/workflows/02_ai_agent_conversation_V81_WF06_INTEGRATION_FIXED.json`
**Status**: ✅ Conexões Corrigidas
**Data**: 2026-04-20

---

## ⚡ Quick Deploy

### 1. Preparação (5 min)

```bash
# Verificar arquivo corrigido existe
ls -lh n8n/workflows/02_ai_agent_conversation_V81_WF06_INTEGRATION_FIXED.json

# Arquivo deve existir e ter tamanho similar ao original
# Expected: ~150-200KB
```

### 2. Backup Atual (2 min)

```bash
# No n8n UI (http://localhost:5678)
# 1. Abrir workflow atual WF02
# 2. Menu (⋮) → Download
# 3. Salvar como backup: WF02_BACKUP_BEFORE_V81_20260420.json
```

### 3. Import Workflow (3 min)

```bash
# No n8n UI
# 1. Workflows → Import from file
# 2. Selecionar: 02_ai_agent_conversation_V81_WF06_INTEGRATION_FIXED.json
# 3. Confirmar importação
```

### 4. Validação Visual (5 min)

Verificar que os seguintes nodes **não** mostram "Input: No input connected":

✅ **Path 1 (Next Dates)**:
- `Prepare WF06 Next Dates Data` - Deve ter 1 input conectado
- `Merge WF06 Next Dates with User Data` - Deve ter 2 inputs conectados

✅ **Path 2 (Available Slots)**:
- `Prepare WF06 Available Slots Data` - Deve ter 1 input conectado
- `Merge WF06 Available Slots with User Data` - Deve ter 2 inputs conectados

**Estrutura Visual Esperada**:
```
[HTTP Request] → [Prepare] → [Merge] ← [Get Conversation]
                                ↓
                        [State Machine]
```

### 5. Ativar Workflow (1 min)

```bash
# No n8n UI
# 1. Clicar em "Active" toggle (canto superior direito)
# 2. Verificar que toggle fica verde
```

---

## 🧪 Testes

### Teste 1: Service 1 (Solar) - Next Dates Path

```bash
# Enviar mensagem WhatsApp simulando:
# - Lead novo solicitando energia solar
# - Workflow deve entrar em state 8 (collect_appointment_date)
# - WF06 deve retornar 3 datas com 8 slots cada

# Validação esperada:
# ✅ State Machine recebe `next_dates` com 3 datas
# ✅ Resposta contém "próximas datas disponíveis"
# ✅ PostgreSQL conversations.current_state = 8
```

### Teste 2: Service 3 (Projetos) - Available Slots Path

```bash
# Enviar mensagem WhatsApp simulando:
# - Lead escolhendo data específica
# - Workflow deve entrar em state 9 (collect_appointment_time)
# - WF06 deve retornar 8 slots disponíveis

# Validação esperada:
# ✅ State Machine recebe `available_slots` com 8 horários
# ✅ Resposta contém "horários disponíveis para [data]"
# ✅ PostgreSQL conversations.current_state = 9
```

### Teste 3: Service 2 (Subestação) - Handoff Path

```bash
# Enviar mensagem WhatsApp simulando:
# - Lead solicitando serviço 2 (Subestação)
# - Workflow NÃO deve chamar WF06
# - Deve ir direto para handoff_comercial

# Validação esperada:
# ✅ Não há chamadas HTTP para WF06
# ✅ Resposta contém mensagem de handoff
# ✅ PostgreSQL conversations.current_state = 7
```

---

## 🔍 Troubleshooting

### Problema: "Input No input connected"

**Causa**: Importação não preservou conexões corretamente

**Solução**:
```bash
# 1. Deletar workflow importado
# 2. Verificar arquivo FIXED está correto:
python3 scripts/fix-wf02-v81-connections.py

# 3. Tentar importação novamente
```

### Problema: "State Machine não recebe dados WF06"

**Causa**: Merge node não está recebendo ambos inputs

**Validação**:
```bash
# No n8n UI, executar manualmente:
# 1. Clicar em "HTTP Request - Get Next Dates"
# 2. Execute previous nodes
# 3. Verificar execução passa por Prepare → Merge → State Machine
```

**Solução**: Reconectar nodes manualmente seguindo estrutura em `docs/analysis/WF02_V81_CONNECTION_FIX_ANALYSIS.md`

### Problema: "WF06 retorna erro 500"

**Causa**: WF06 não está ativo ou tem bugs

**Validação**:
```bash
# Testar WF06 diretamente:
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action": "next_dates", "count": 3, "service_type": "energia_solar"}'

# Esperado: JSON com 3 dates_with_availability
```

**Solução**: Verificar `docs/deployment/DEPLOY_WF06_V2_1_COMPLETE_FIX.md`

---

## 📊 Monitoramento

### Logs n8n

```bash
# Monitorar execuções em tempo real
docker logs -f e2bot-n8n-dev | grep -E "V81|Prepare|Merge|WF06"

# Verificar erros
docker logs e2bot-n8n-dev --tail 100 | grep ERROR
```

### PostgreSQL

```bash
# Verificar estados das conversas
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    phone_number,
    lead_name,
    service_type,
    current_state,
    next_stage,
    updated_at
  FROM conversations
  WHERE updated_at > NOW() - INTERVAL '1 hour'
  ORDER BY updated_at DESC
  LIMIT 10;
"

# Verificar collected_data de WF06
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    phone_number,
    collected_data->'next_dates' as next_dates,
    collected_data->'available_slots' as available_slots
  FROM conversations
  WHERE collected_data ? 'next_dates' OR collected_data ? 'available_slots'
  ORDER BY updated_at DESC
  LIMIT 5;
"
```

---

## 🔄 Rollback

Se V81 apresentar problemas:

```bash
# 1. Desativar V81
# n8n UI → WF02 V81 → Active toggle OFF

# 2. Restaurar backup
# n8n UI → Import from file → WF02_BACKUP_BEFORE_V81_20260420.json

# 3. Ativar backup
# n8n UI → WF02 (restaurado) → Active toggle ON

# 4. Verificar execução
# Enviar teste WhatsApp → Confirmar funcionamento normal
```

---

## ✅ Checklist de Deploy

- [ ] Arquivo `V81_FIXED.json` verificado e validado
- [ ] Backup do workflow atual exportado
- [ ] Workflow V81 FIXED importado no n8n
- [ ] Validação visual: Nodes Prepare/Merge têm inputs conectados
- [ ] Workflow ativado (toggle verde)
- [ ] Teste 1: Service 1 (Next Dates path) OK
- [ ] Teste 2: Service 3 (Available Slots path) OK
- [ ] Teste 3: Service 2 (Handoff path) OK
- [ ] Logs n8n sem erros críticos
- [ ] PostgreSQL: states atualizando corretamente
- [ ] WF06 responde com dados corretos
- [ ] Backup disponível para rollback se necessário

---

## 📚 Referências

**Análise Completa**: `docs/analysis/WF02_V81_CONNECTION_FIX_ANALYSIS.md`

**Script de Correção**: `scripts/fix-wf02-v81-connections.py`

**Workflows Relacionados**:
- WF02 V80 COMPLETE: Baseline funcional
- WF06 V2.1: Calendar availability service

**Documentação Adicional**:
- `docs/deployment/DEPLOY_WF02_V80_COMPLETE_STATE_MACHINE.md`
- `docs/deployment/DEPLOY_WF06_V2_1_COMPLETE_FIX.md`
- `docs/analysis/WF02_STATE_MACHINE_WF06_INTEGRATION_PROBLEM.md`

---

**Deploy Guide**: WF02 V81 FIXED
**Created**: 2026-04-20
**Status**: ✅ READY FOR PRODUCTION
