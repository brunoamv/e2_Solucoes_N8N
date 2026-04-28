# Deploy WF02 V82 CLEAN - Workflow Limpo e Validado

**Workflow**: WF02 AI Conversation V82 (Versão Limpa)
**Arquivo**: `n8n/workflows/02_ai_agent_conversation_V82_CLEAN.json`
**Status**: ✅ Validado e Pronto para Import
**Data**: 2026-04-20

---

## 🎯 O que é o V82?

**V82 = V81 FIXED + Limpeza + Novo ID + Validações**

### Origem
- **Base**: WF02 V81 com conexões WF06 corrigidas
- **Problema**: n8n rejeitava import do V81 FIXED com erro "Required"
- **Solução**: Gerar workflow limpo com novo ID e metadata validada

### Melhorias sobre V81
- ✅ Novo ID único (evita conflitos com workflows existentes)
- ✅ Metadata limpa (versionId regenerado, pinData removido)
- ✅ Validação completa de todos nodes e conexões
- ✅ Normalização de campos obrigatórios
- ✅ Importar inativo por padrão (segurança)
- ✅ Tags organizacionais: V82, WF06-Integration, Clean

---

## ⚡ Quick Deploy (5 min)

### 1. Preparação

```bash
# Verificar arquivo V82 existe
ls -lh n8n/workflows/02_ai_agent_conversation_V82_CLEAN.json

# Expected: ~150-200KB, 42 nodes, 33 conexões
```

### 2. Backup (Opcional)

```bash
# Se houver workflow ativo, fazer backup primeiro
# n8n UI → Export current workflow
```

### 3. Import no n8n

```bash
# 1. Acessar: http://localhost:5678
# 2. Workflows → Import from file
# 3. Selecionar: 02_ai_agent_conversation_V82_CLEAN.json
# 4. Confirmar importação

# Workflow será importado como INATIVO (active: false)
```

### 4. Validação Visual (3 min)

✅ **Verificar que NÃO há warnings**:
- "Input: No input connected" em qualquer node
- Nodes com ícone vermelho de erro
- Conexões quebradas (linhas tracejadas)

✅ **Verificar Paths WF06**:

**Path 1 (Next Dates)**:
```
HTTP Request - Get Next Dates
  ↓
Prepare WF06 Next Dates Data (1 input)
  ↓
Merge WF06 Next Dates with User Data (2 inputs)
  ↓
State Machine Logic
```

**Path 2 (Available Slots)**:
```
HTTP Request - Get Available Slots
  ↓
Prepare WF06 Available Slots Data (1 input)
  ↓
Merge WF06 Available Slots with User Data (2 inputs)
  ↓
State Machine Logic
```

### 5. Ativar Workflow

```bash
# Após validação visual OK:
# 1. Clicar no toggle "Active" (canto superior direito)
# 2. Confirmar ativação
# 3. Verificar toggle fica verde
```

---

## 🧪 Testes de Validação

### Teste 1: Service 1 (Solar) - Next Dates

```bash
# Enviar mensagem WhatsApp:
# "Olá, gostaria de orçamento para energia solar"

# Esperado:
# ✅ Bot responde com opções de serviços
# ✅ Escolher Service 1 (Solar)
# ✅ Bot entra em state 8 (collect_appointment_date)
# ✅ HTTP Request chama WF06 next_dates
# ✅ Prepare processa resposta
# ✅ Merge combina com user data
# ✅ State Machine recebe 3 datas disponíveis
# ✅ Bot mostra: "Temos as seguintes datas disponíveis..."
```

**PostgreSQL Check**:
```sql
SELECT
  phone_number,
  service_type,
  current_state,
  collected_data->'next_dates' as dates
FROM conversations
WHERE phone_number = '+5562999999999'
ORDER BY updated_at DESC LIMIT 1;

-- Esperado:
-- current_state = 8
-- dates = [{"date": "2026-04-21", "slots": [...8 slots]}, ...]
```

### Teste 2: Service 3 (Projetos) - Available Slots

```bash
# Continuar conversa anterior:
# "Escolho a data 21/04"

# Esperado:
# ✅ Bot valida data escolhida
# ✅ Bot entra em state 9 (collect_appointment_time)
# ✅ HTTP Request chama WF06 available_slots
# ✅ Prepare processa resposta
# ✅ Merge combina com user data
# ✅ State Machine recebe 8 horários disponíveis
# ✅ Bot mostra: "Para 21/04, temos os horários..."
```

**PostgreSQL Check**:
```sql
SELECT
  current_state,
  collected_data->'available_slots' as slots,
  collected_data->'selected_date' as selected_date
FROM conversations
WHERE phone_number = '+5562999999999';

-- Esperado:
-- current_state = 9
-- selected_date = "2026-04-21"
-- slots = ["08:00", "09:00", ..., "15:00"]
```

### Teste 3: Service 2 (Subestação) - Handoff

```bash
# Nova conversa com Service 2:
# "Preciso de subestação"

# Esperado:
# ✅ Bot NÃO chama WF06
# ✅ Bot vai direto para handoff_comercial
# ✅ Mensagem: "Vou transferir para um especialista..."
# ✅ current_state = 7 (handoff)
```

---

## 🔍 Troubleshooting

### Problema: Erro "Problem importing workflow - Required"

**Possíveis Causas**:
1. Arquivo JSON corrompido
2. Campos obrigatórios faltando
3. Conexões referenciando nodes inexistentes

**Solução**:
```bash
# 1. Validar JSON
python3 -m json.tool n8n/workflows/02_ai_agent_conversation_V82_CLEAN.json > /dev/null
echo $?
# Esperado: 0 (sem erros)

# 2. Recriar V82 se necessário
python3 scripts/generate-wf02-v82-clean.py

# 3. Tentar import novamente
```

### Problema: Nodes com "Input: No input connected"

**Causa**: Conexões não foram salvas corretamente

**Solução**:
```bash
# Verificar arquivo tem as conexões:
grep -A 5 "Prepare WF06 Next Dates Data" \
  n8n/workflows/02_ai_agent_conversation_V82_CLEAN.json \
  | grep -c "connections"

# Esperado: > 0
```

Se conexões estão no arquivo mas não aparecem no n8n:
1. Deletar workflow importado
2. Reiniciar n8n: `docker restart e2bot-n8n-dev`
3. Importar novamente

### Problema: WF06 retorna erro 404/500

**Causa**: WF06 não está ativo ou tem bugs

**Validação**:
```bash
# Testar WF06 diretamente
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{
    "action": "next_dates",
    "count": 3,
    "service_type": "energia_solar",
    "duration_minutes": 120
  }'

# Esperado: JSON com dates_with_availability
```

**Solução**: Ver `docs/deployment/DEPLOY_WF06_V2_1_COMPLETE_FIX.md`

---

## 📊 Monitoramento

### Logs n8n

```bash
# Tempo real
docker logs -f e2bot-n8n-dev | grep -E "V82|Prepare|Merge|WF06"

# Últimas 50 linhas
docker logs e2bot-n8n-dev --tail 50

# Erros apenas
docker logs e2bot-n8n-dev --tail 100 | grep ERROR
```

### PostgreSQL

```bash
# Estados recentes
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    phone_number,
    service_type,
    current_state,
    next_stage,
    updated_at
  FROM conversations
  WHERE updated_at > NOW() - INTERVAL '1 hour'
  ORDER BY updated_at DESC;
"

# Dados WF06 coletados
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    phone_number,
    jsonb_pretty(collected_data) as data
  FROM conversations
  WHERE collected_data ? 'next_dates'
     OR collected_data ? 'available_slots'
  ORDER BY updated_at DESC LIMIT 3;
"
```

---

## 🔄 Rollback

Se V82 apresentar problemas:

```bash
# 1. Desativar V82
# n8n UI → WF02 V82 → Toggle OFF

# 2. Reativar workflow anterior (V74 ou V80)
# n8n UI → WF02 anterior → Toggle ON

# 3. Verificar funcionamento
# Enviar teste WhatsApp
```

---

## ✅ Checklist de Deploy

- [ ] Arquivo V82 CLEAN verificado (42 nodes, 33 conexões)
- [ ] Backup do workflow atual (se houver)
- [ ] V82 importado no n8n com sucesso
- [ ] Validação visual: Sem warnings ou erros
- [ ] Nodes WF06 (Prepare/Merge) têm inputs conectados corretamente
- [ ] Workflow ativado (toggle verde)
- [ ] Teste 1: Service 1 → Next Dates path → OK
- [ ] Teste 2: Service 3 → Available Slots path → OK
- [ ] Teste 3: Service 2 → Handoff path → OK
- [ ] Logs sem erros críticos
- [ ] PostgreSQL: states e collected_data corretos
- [ ] WF06 responde com dados válidos

---

## 📚 Documentação Relacionada

**Análise do Problema**:
- `docs/analysis/WF02_V81_CONNECTION_FIX_ANALYSIS.md` - Análise V81 original
- Script: `scripts/fix-wf02-v81-connections.py` - Correção de conexões
- Script: `scripts/generate-wf02-v82-clean.py` - Geração V82

**Workflows Base**:
- WF02 V74.1_2: Baseline produção funcionando
- WF02 V80 COMPLETE: State machine completa (15 states)
- WF06 V2.1: Calendar availability microservice

**Deploy Guides**:
- `docs/deployment/DEPLOY_WF02_V80_COMPLETE_STATE_MACHINE.md`
- `docs/deployment/DEPLOY_WF06_V2_1_COMPLETE_FIX.md`

**Analysis**:
- `docs/analysis/WF02_STATE_MACHINE_WF06_INTEGRATION_PROBLEM.md`

---

## 🎯 V82 vs V81 vs V80

| Feature | V80 COMPLETE | V81 ORIGINAL | V82 CLEAN |
|---------|--------------|--------------|-----------|
| States | 15 | 10 | 10 |
| WF06 Integration | ❌ | ✅ | ✅ |
| Conexões | 29 | 29 (broken) | 33 |
| Import Status | ✅ OK | ❌ Fail | ✅ OK |
| Validation | ✅ | ❌ | ✅ |
| Clean Metadata | ✅ | ❌ | ✅ |

**Recomendação**:
- **Para produção**: V82 CLEAN (WF06 integration + validado)
- **Fallback**: V80 COMPLETE (completo mas sem WF06)

---

**Deploy Guide**: WF02 V82 CLEAN
**Created**: 2026-04-20
**Status**: ✅ READY FOR PRODUCTION
**Priority**: HIGH - Resolve import issues V81
