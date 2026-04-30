# WF02 V78.2 - Quick Reference

> **Deploy Rápido**: 5 minutos | **Rollback**: < 1 minuto | **Status**: ✅ PRONTO

---

## 🚀 Deploy em 3 Passos

### 1. Import (2 min)
```
n8n UI → Workflows → Import from File
→ Selecionar: n8n/workflows/02_ai_agent_conversation_V78_2_FINAL.json
→ Aguardar: "Workflow imported successfully"
```

### 2. Validate (2 min)
```
Abrir: "Route Based on Stage"
Verificar: 2 conditions visíveis
Verificar: 3 outputs no canvas (0, 1, 2)
```

### 3. Activate (1 min)
```
Workflows → 02_ai_agent_conversation_V78_2_FINAL → Activate
Workflows → V74_1_2 → Deactivate (se ativo)
```

---

## ✅ Validação Rápida

### Checklist Visual

**Switch Node "Route Based on Stage":**
- [ ] Mostra **2 conditions** no painel
- [ ] Mostra **3 saídas** no canvas (linhas para 3 nodes diferentes)
- [ ] Output 0 → "HTTP Request - Get Next Dates"
- [ ] Output 1 → "HTTP Request - Get Available Slots"
- [ ] Output 2 → 5 nodes paralelos

**State Machine Logic:**
- [ ] Code presente (18,293 caracteres)
- [ ] Buscar `trigger_wf06` no código → encontra ✅

**HTTP Requests:**
- [ ] URL: `http://e2bot-n8n-dev:5678/webhook/calendar-availability`
- [ ] Body parameters configurados

---

## 🧪 Teste Rápido (5 min)

### Test 1: Service 1 (WF06)
```bash
curl -X POST http://localhost:8080/message/sendText/e2-solucoes-bot \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" \
  -H "Content-Type: application/json" \
  -d '{"number":"556299999999","text":"1"}'
```

**✅ Sucesso**: Recebe mensagem com 3 opções de data

### Test 2: Service 2 (Handoff)
```bash
curl -X POST http://localhost:8080/message/sendText/e2-solucoes-bot \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" \
  -H "Content-Type: application/json" \
  -d '{"number":"556299999998","text":"2"}'
```

**✅ Sucesso**: Recebe mensagem de handoff (sem WF06)

---

## 🔄 Rollback Instantâneo

**Se algo der errado:**
```
n8n UI
→ Workflows → 02_ai_agent_conversation_V78_2_FINAL → Deactivate
→ Workflows → V74_1_2 → Activate
```

**Tempo**: < 1 minuto | **Impacto**: Zero (V74 estável)

---

## 🐛 Troubleshooting Rápido

### Erro: "Could not find property option" ao importar
**Causa**: Arquivo errado ou cache n8n
**Solução**:
```bash
# Verificar arquivo
ls -lh n8n/workflows/02_ai_agent_conversation_V78_2_FINAL.json

# Limpar cache
docker restart e2bot-n8n-dev

# Reimportar
```

### Switch mostra 4+ outputs (deveria ser 3)
**Causa**: Estrutura do Switch incorreta
**Solução**:
```bash
# Regerar workflow
python3 scripts/generate-workflow-wf02-v78_2-final.py

# Reimportar JSON gerado
```

### WF06 não responde
**Causa**: WF06 inativo
**Solução**:
```bash
# Verificar WF06
curl http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"next_dates","count":3}' | jq

# Se erro, ativar WF06 no n8n UI
```

---

## 📊 Comandos Úteis

```bash
# Ver logs n8n
docker logs -f e2bot-n8n-dev

# Ver últimas conversas
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, current_state FROM conversations ORDER BY updated_at DESC LIMIT 5;"

# Testar WF06
curl http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"next_dates","count":3}' | jq

# Regenerar workflow
python3 scripts/generate-workflow-wf02-v78_2-final.py
```

---

## 🎯 O Que Mudou?

### V74 → V78.2

**Adicionado**:
- ✅ Switch Node "Route Based on Stage" (routing WF06)
- ✅ HTTP Request - Get Next Dates (WF06 call)
- ✅ HTTP Request - Get Available Slots (WF06 call)
- ✅ State Machine V78 (14 states, WF06 logic)

**Preservado**:
- ✅ Todos os 34 nodes V74 (sem duplicatas)
- ✅ Parallel connections (5 nodes simultâneos)
- ✅ Handoff flow (services 2/4/5)

**Comportamento**:
- **Services 1/3**: Apresentam datas via WF06 ✨ NOVO
- **Services 2/4/5**: Handoff direto (igual V74)

---

## 📚 Docs Completas

- **Plano Estratégico**: `docs/PLAN/PLAN_WF02_V78_2_STRATEGIC_FIX.md`
- **Guia Implementação**: `docs/implementation/WF02_V78_2_IMPLEMENTATION_GUIDE.md`
- **Análise Completa**: `docs/WF02_V78_2_FINAL_ANALYSIS.md`

---

**Data**: 2026-04-13 | **Versão**: V78.2 FINAL | **Status**: ✅ PRONTO
