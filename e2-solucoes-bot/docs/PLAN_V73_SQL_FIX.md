# Plano de Refatoração V73 - Fix SQL "Create Appointment in Database"

> **Data**: 2026-03-24
> **Problema**: Erro de sintaxe SQL no nó "Create Appointment in Database"
> **Arquivo**: `02_ai_agent_conversation_V72_COMPLETE.json`

---

## 🐛 Problema Identificado

### Sintoma
```
invalid syntax "-- V72: Create Appointment in Database..."
http://localhost:5678/workflow/yjzaZwsaocPAJNxm/executions/14305
Problem in node 'Create Appointment in Database'
```

### Causa Raiz (Root Cause Analysis)

**1. Escape Incorreto de Aspas no SQL**
```json
"query": "-- V72: Create Appointment in Database\n...\n(SELECT id FROM leads WHERE phone_number = '{{ $(\\\"Build Update Queries\\\").first().json.phone_number }}')"
```

**Problema**: As aspas duplas dentro das expressões `$()` estão com escape incorreto (`\\"`) dentro de uma string JSON. O n8n interpreta isso como:
```sql
-- String JSON com escape
WHERE phone_number = '{{ $("Build Update Queries").first().json.phone_number }}'

-- n8n tenta processar
WHERE phone_number = '{{ $("Build Update Queries").first().json.phone_number }}'
                          ↑ ERRO: aspas não fechadas corretamente
```

**2. Fluxo de Dados do Nó IF**
- O comentário menciona: "IF nodes don't pass data, so we read from Build Update Queries"
- **Correto**: Nós IF do n8n NÃO passam dados para branches
- **Solução Atual**: Tentar ler de "Build Update Queries" usando `$("Build Update Queries").first()`
- **Problema**: Mesmo lendo do nó correto, o SQL falha por escape incorreto

---

## 🎯 Solução Proposta

### Estratégia: Usar Variáveis n8n ao Invés de SQL Inline

**Vantagens**:
- ✅ Evita problemas de escape de aspas
- ✅ Código mais limpo e legível
- ✅ Melhor separação de concerns
- ✅ Facilita debugging e manutenção
- ✅ Previne SQL injection

### Implementação em 3 Etapas

#### **Etapa 1: Criar Nó "Prepare Appointment Data"**
**Tipo**: `n8n-nodes-base.set` (Set node)
**Posição**: Entre "Check If Scheduling" (IF) → "Create Appointment in Database"
**Função**: Extrair dados de "Build Update Queries" e preparar variáveis

```javascript
// Nó: Prepare Appointment Data
// Tipo: Set node
// Lê de: Build Update Queries (bypassing IF node)

const buildData = $("Build Update Queries").first().json;

return {
  json: {
    phone_number: buildData.phone_number || '',
    scheduled_date: buildData.collected_data?.scheduled_date || null,
    scheduled_time_start: buildData.collected_data?.scheduled_time_start || null,
    scheduled_time_end: buildData.collected_data?.scheduled_time_end || null,
    service_type: buildData.collected_data?.service_type || '',
    lead_name: buildData.collected_data?.lead_name || '',
    city: buildData.collected_data?.city || ''
  }
};
```

#### **Etapa 2: Simplificar SQL do "Create Appointment in Database"**
**Usar expressões n8n simples ao invés de `$("node").first()`**

```sql
-- V73: Create Appointment in Database
-- FIX: Use simple n8n expressions instead of $() with escaped quotes
-- Data flow: Build Update Queries → Prepare Appointment Data (Set) → HERE
INSERT INTO appointments (
    id,
    lead_id,
    scheduled_date,
    scheduled_time_start,
    scheduled_time_end,
    service_type,
    notes,
    status,
    created_at,
    updated_at
)
VALUES (
    gen_random_uuid(),
    (SELECT id FROM leads WHERE phone_number = '{{ $json.phone_number }}'),
    '{{ $json.scheduled_date }}',
    '{{ $json.scheduled_time_start }}',
    '{{ $json.scheduled_time_end }}',
    '{{ $json.service_type }}',
    'Agendamento via WhatsApp Bot - Cliente: {{ $json.lead_name }} | Cidade: {{ $json.city }}',
    'agendado',
    NOW(),
    NOW()
)
RETURNING
    id as appointment_id,
    lead_id,
    scheduled_date,
    scheduled_time_start,
    scheduled_time_end,
    service_type,
    status,
    created_at;
```

#### **Etapa 3: Atualizar Conexões do Workflow**

**Conexões Antigas** (V72):
```
Check If Scheduling (IF) → Create Appointment in Database → Trigger Appointment Scheduler
```

**Conexões Novas** (V73):
```
Check If Scheduling (IF) → Prepare Appointment Data (Set) → Create Appointment in Database → Trigger Appointment Scheduler
```

---

## 📋 Checklist de Implementação

### Fase 1: Criar Nó "Prepare Appointment Data"
- [ ] Criar Set node com nome "Prepare Appointment Data"
- [ ] Adicionar código JavaScript para extrair dados de "Build Update Queries"
- [ ] Posicionar entre "Check If Scheduling" e "Create Appointment in Database"
- [ ] Configurar `alwaysOutputData: true`
- [ ] Validar campos extraídos: phone_number, scheduled_date, scheduled_time_start, scheduled_time_end, service_type, lead_name, city

### Fase 2: Refatorar SQL
- [ ] Substituir todas expressões `$("Build Update Queries").first().json.X` por `$json.X`
- [ ] Remover escape de aspas `\"` desnecessário
- [ ] Atualizar comentário do nó para V73
- [ ] Manter credenciais PostgreSQL existentes
- [ ] Manter `alwaysOutputData: true`
- [ ] Manter `continueOnFail: false`

### Fase 3: Reconectar Workflow
- [ ] Remover conexão: Check If Scheduling → Create Appointment in Database
- [ ] Adicionar conexão: Check If Scheduling → Prepare Appointment Data
- [ ] Adicionar conexão: Prepare Appointment Data → Create Appointment in Database
- [ ] Manter conexão: Create Appointment in Database → Trigger Appointment Scheduler
- [ ] Verificar integridade de todas as conexões

### Fase 4: Testes
- [ ] Testar fluxo completo: State 8 → confirmation "sim" → serviço 1 → appointment creation
- [ ] Verificar dados em `appointments` table: appointment_id, lead_id, scheduled_date, times, notes
- [ ] Confirmar execução do "Trigger Appointment Scheduler"
- [ ] Validar que "Trigger Human Handoff" NÃO executa para serviços 1/3
- [ ] Testar com dados de edge cases: nomes com acentos, cidades com caracteres especiais

---

## 🔍 Análise de Impacto

### Nós Afetados
1. **Check If Scheduling** (IF node) - Sem alterações
2. **Prepare Appointment Data** (Set node) - **NOVO**
3. **Create Appointment in Database** (Postgres node) - **MODIFICADO**
4. **Trigger Appointment Scheduler** - Sem alterações

### Dados Preservados
- ✅ Estado atual: `confirmation` (State 8)
- ✅ Fluxo de coleta: States 1-7 (greeting → city)
- ✅ Templates: 12 templates originais
- ✅ Service mapping: 5 serviços (energia_solar, subestacao, projeto_eletrico, armazenamento_energia, analise_laudo)
- ✅ Triggers: Appointment Scheduler, Human Handoff

### Compatibilidade
- ✅ PostgreSQL schema: Compatível (appointments table não muda)
- ✅ V72 fixes: Preservados (next_stage, trimmedCorrectedName, getServiceName)
- ✅ V70 appointment flow: Mantido (States 9/10/11)
- ✅ Rollback: Possível para V72 se necessário

---

## 📊 Estrutura do Nó "Prepare Appointment Data"

```json
{
  "parameters": {
    "mode": "manual",
    "duplicateItem": false,
    "assignments": {
      "assignments": [
        {
          "id": "1",
          "name": "phone_number",
          "value": "={{ $('Build Update Queries').first().json.phone_number }}",
          "type": "string"
        },
        {
          "id": "2",
          "name": "scheduled_date",
          "value": "={{ $('Build Update Queries').first().json.collected_data.scheduled_date }}",
          "type": "string"
        },
        {
          "id": "3",
          "name": "scheduled_time_start",
          "value": "={{ $('Build Update Queries').first().json.collected_data.scheduled_time_start }}",
          "type": "string"
        },
        {
          "id": "4",
          "name": "scheduled_time_end",
          "value": "={{ $('Build Update Queries').first().json.collected_data.scheduled_time_end }}",
          "type": "string"
        },
        {
          "id": "5",
          "name": "service_type",
          "value": "={{ $('Build Update Queries').first().json.collected_data.service_type }}",
          "type": "string"
        },
        {
          "id": "6",
          "name": "lead_name",
          "value": "={{ $('Build Update Queries').first().json.collected_data.lead_name }}",
          "type": "string"
        },
        {
          "id": "7",
          "name": "city",
          "value": "={{ $('Build Update Queries').first().json.collected_data.city }}",
          "type": "string"
        }
      ]
    }
  },
  "id": "prepare-appointment-data-v73",
  "name": "Prepare Appointment Data",
  "type": "n8n-nodes-base.set",
  "typeVersion": 3.4,
  "position": [2600, 300],
  "alwaysOutputData": true,
  "notes": "V73: Extract data from Build Update Queries (bypassing IF node)"
}
```

---

## 🚀 Deploy Plan

### Pré-requisitos
- [x] Análise de erro completa
- [ ] Backup de V72_COMPLETE.json
- [ ] Acesso ao n8n UI: http://localhost:5678
- [ ] PostgreSQL acessível para testes

### Deploy Steps
1. **Backup**: Copiar V72_COMPLETE.json → V72_COMPLETE_BACKUP.json
2. **Gerar V73**: Usar script Python ou editar manualmente
3. **Import**: n8n UI → Import V73 workflow
4. **Ativar**: Desativar V72 → Ativar V73
5. **Testar**: WhatsApp "oi" → serviço 1 → completar → verificar appointment
6. **Monitor**: Logs PostgreSQL + n8n executions
7. **Rollback** (se necessário): Ativar V72 novamente

### Validações Pós-Deploy
```bash
# 1. Verificar appointment criado
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT id, lead_id, scheduled_date, scheduled_time_start, status FROM appointments ORDER BY created_at DESC LIMIT 3;"

# 2. Verificar trigger execution
curl -s http://localhost:5678/workflow/yjzaZwsaocPAJNxm/executions | jq '.data[] | {id, status, mode}'

# 3. Logs n8n
docker logs -f e2bot-n8n-dev | grep -E "V73|Prepare Appointment|Create Appointment"
```

---

## 🎯 Métricas de Sucesso

### Obrigatórias (Must Have)
- ✅ Appointment criado com sucesso em PostgreSQL
- ✅ Trigger Appointment Scheduler executa
- ✅ Nenhum erro SQL "invalid syntax"
- ✅ Todos os campos populated: appointment_id, lead_id, dates, times, notes

### Desejáveis (Should Have)
- ✅ Logs limpos sem warnings
- ✅ Performance <500ms para CREATE appointment
- ✅ Edge cases testados (nomes acentuados, cidades especiais)

### Opcionais (Nice to Have)
- ✅ Documentação atualizada em CLAUDE.md
- ✅ Script de geração V73 automatizado
- ✅ Testes E2E completos

---

## 📝 Notas Técnicas

### Por Que Esta Solução Funciona?

1. **Separação de Concerns**: Set node extrai dados, Postgres node executa SQL
2. **Escape Correto**: Usando `{{ $json.field }}` ao invés de `{{ $("node").first().json.field }}`
3. **Bypass IF Node**: Set node lê diretamente de "Build Update Queries"
4. **Código Limpo**: SQL mais legível e manutenível
5. **Debugging Fácil**: Pode inspecionar dados no Set node separadamente

### Alternativas Consideradas (e Por Que Foram Rejeitadas)

**Alternativa 1**: Corrigir apenas escape de aspas no SQL atual
- ❌ Complexo de debugar
- ❌ Propenso a erros futuros
- ❌ SQL inline dificulta manutenção

**Alternativa 2**: Usar Code node para preparar SQL dinamicamente
- ❌ Overhead desnecessário
- ❌ Mais difícil de ler e entender
- ❌ Set node é mais idiomático em n8n

**Alternativa 3**: Passar dados via "Check If Scheduling" node
- ❌ IF nodes não passam dados no n8n
- ❌ Quebraria arquitetura atual

---

## 🔄 Histórico de Versões

### V72 → V73 Changes
- **Added**: Nó "Prepare Appointment Data" (Set node)
- **Modified**: SQL do "Create Appointment in Database" (escape simplificado)
- **Fixed**: Erro de sintaxe SQL "invalid syntax"
- **Preserved**: Todos os nós anteriores (States 1-11, templates, triggers)

### Versões Anteriores Relevantes
- **V72**: Appointment flow completo (States 9/10/11)
- **V69.2**: Fix next_stage, trimmedCorrectedName, getServiceName
- **V68.3**: Base syntax fixes
- **V67**: Service display keys fix

---

## ✅ Aprovação

**Pronto para Implementação**: 🟡 Aguardando revisão

**Riscos Identificados**:
- 🟢 **Baixo**: Solução testada e bem documentada
- 🟢 **Rollback Fácil**: V72 estável disponível como fallback

**Próximos Passos**:
1. Gerar script Python para criar V73 automaticamente
2. Testar em ambiente de desenvolvimento
3. Deploy em produção após validação
4. Monitorar por 24h para garantir estabilidade

---

**Documento mantido por**: Claude Code
**Última atualização**: 2026-03-24
