# WF02 V97 - Quick Deploy Card

> **5-Minute Deployment Guide** | 2026-04-27 | Status: ✅ Production Ready

---

## 🎯 What This Fixes

**Problem**: conversation_id se perde entre State Machine e Build Update Queries (V90-V96)

**Root Cause**: State Machine executa DUAS vezes → segunda execução perde context `conversation_id`

**Solution**: V97 preserva `conversation_id` explicitamente em ambos os nodes

---

## 📋 Pre-Flight Checklist

- [ ] n8n rodando: http://localhost:5678
- [ ] PostgreSQL acessível
- [ ] Evolution API ativa
- [ ] Workflow atual identificado (V74.1_2 ou V90-V96)

---

## 🚀 Deploy (5 minutos)

### 1. Import V97
```bash
# Arquivo:
/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V97_CONVERSATION_ID_COMPLETE_FIX.json

# n8n UI:
Workflows → Import from File → Selecionar arquivo → Import
```

### 2. Desativar Workflow Atual
```bash
# n8n UI:
Abrir workflow ativo atual → Toggle "Active" OFF (cinza)
```

### 3. Ativar V97
```bash
# n8n UI:
Abrir "02 - AI Agent Conversation V97" → Toggle "Active" ON (verde)
```

### 4. Testar
```bash
# Enviar mensagem WhatsApp:
"1"

# Monitorar logs:
docker logs -f e2bot-n8n-dev | grep -E 'V97:|conversation_id'
```

---

## ✅ Validation (2 minutos)

### Logs Esperados
```
✅ GOOD:
V97: conversation_id: 123e4567-e89b-12d3-a456-426614174000
V97: RESOLVED conversation_id: 123e4567-e89b-12d3-a456-426614174000
V97: Output conversation_id: 123e4567-e89b-12d3-a456-426614174000

❌ BAD (não deve aparecer):
V97 CRITICAL WARNING: conversation_id is NULL!
```

### Database Check
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT id, phone_number, current_state FROM conversations ORDER BY updated_at DESC LIMIT 3;"
```

**Esperado**:
- Coluna `id`: UUID presente (não NULL)
- Coluna `current_state`: Estado correto
- Coluna `updated_at`: Timestamp recente

---

## 🔄 Rollback (se necessário)

```bash
# 1. Desativar V97
#    n8n UI → V97 → Toggle "Active" OFF

# 2. Reativar anterior
#    n8n UI → V74.1_2 → Toggle "Active" ON

# 3. Monitorar
docker logs -f e2bot-n8n-dev | grep ERROR
```

---

## 📊 O Que Mudou

### State Machine
```javascript
// ANTES (V94)
const output = {
  response_text: responseText,
  // ... outros campos
};

// DEPOIS (V97)
const output = {
  response_text: responseText,
  conversation_id: input.conversation_id || input.id || input.currentData?.conversation_id || null,  // ✅ NOVO
  // ... outros campos
};
```

### Build Update Queries
```javascript
// ANTES (V94)
const conversation_id = inputData.conversation_id || null;  // ❌ Perde

// DEPOIS (V97)
const conversation_id =
  inputData.conversation_id ||              // ✅ Nível 1
  inputData.id ||                           // ✅ Nível 2
  inputData.currentData?.conversation_id || // ✅ Nível 3
  inputData.currentData?.id ||              // ✅ Nível 4
  null;

if (!conversation_id) {
  console.error('V97 CRITICAL WARNING: conversation_id is NULL!');  // ✅ Validação
}
```

---

## 📝 Testing Scenarios

### ✅ Test 1: Basic Flow
```
User: "1" (serviço)
Expected: conversation_id preservado, state transitions corretos
```

### ✅ Test 2: WF06 Integration (Services 1 ou 3)
```
User: Completar States 1-7 → "1" (agendar)
Expected:
  - State 9 → trigger_wf06_next_dates
  - conversation_id preservado durante WF06
  - State 10 → show_available_dates (NÃO service_selection)
```

### ✅ Test 3: Complete Flow
```
User: greeting → schedule_confirmation (15 states)
Expected: conversation_id preservado em TODOS os estados
```

---

## 🎯 Success Criteria

- [ ] V97 logs mostram conversation_id em todas execuções
- [ ] Sem warnings "conversation_id is NULL"
- [ ] Database UPDATEs bem-sucedidos
- [ ] State transitions corretos
- [ ] WF06 integration funcional (services 1 & 3)
- [ ] Sem loops ou resets de conversa

---

## 📚 Full Documentation

- **Deployment Guide**: `docs/deployment/DEPLOY_WF02_V97_CONVERSATION_ID_COMPLETE_FIX.md`
- **Executive Summary**: `docs/WF02_V97_EXECUTIVE_SUMMARY.md`
- **Generator Script**: `scripts/generate-wf02-v97-conversation-id-complete-fix.py`

---

## 🆘 Support

### Common Issues

**Issue**: "conversation_id is NULL" nos logs
**Fix**: Verificar State Machine output structure e input data do Build Update Queries

**Issue**: Database UPDATE falha
**Fix**: Verificar conversation_id não NULL e phone_number presente

**Issue**: State transitions incorretos
**Fix**: Verificar next_stage logic e current_stage no database

---

**Version**: V97
**Risk Level**: 🟢 Low
**Deploy Time**: 5 minutes
**Rollback Time**: < 2 minutes
**Status**: ✅ Ready

---

**Quick Commands**:
```bash
# Import: n8n UI → Import from file
# Activate: Toggle "Active" ON
# Monitor: docker logs -f e2bot-n8n-dev | grep 'V97:'
# Validate: docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "SELECT id, phone_number, current_state FROM conversations ORDER BY updated_at DESC LIMIT 3;"
```

**Date**: 2026-04-27
**Author**: Claude Code
