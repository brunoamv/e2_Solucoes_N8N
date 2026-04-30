# V46 - Fix Leads Table Duplication

**Data**: 2026-03-06
**Status**: Plano pronto para execução
**Approach**: Remover referências incorretas a `state_machine_state` da tabela `leads`

---

## 🚨 PROBLEMA IDENTIFICADO

### Erro Atual
```
column "state_machine_state" of relation "leads" does not exist
Failed query: UPDATE leads SET [...] state_machine_state = 'service_selection' [...]
```

### Root Cause Analysis
**Workflow V41 tenta escrever `state_machine_state` em DUAS tabelas**:
```
conversations → state_machine_state ✅ (adicionado em V45)
leads → state_machine_state ❌ (não existe, não deveria existir)
```

### Análise Arquitetural

**`conversations` table** (linha 10-42 schema.sql):
- **Propósito**: Armazena conversas ATIVAS do WhatsApp
- **Estado**: Tracking do estado atual da conversa
- **Ciclo de vida**: Ativa enquanto conversa está em andamento
- **Deve ter**: `state_machine_state`, `error_count` ✅

**`leads` table** (linha 75-127 schema.sql):
- **Propósito**: Leads QUALIFICADOS prontos para atendimento comercial
- **Estado**: Status do lead (novo, em_atendimento, agendado, concluido)
- **Ciclo de vida**: Persistente após conversa completa
- **NÃO deve ter**: `state_machine_state` (é propriedade da conversa ativa)

### Impact
- ❌ Workflow V41 falha ao tentar UPDATE/INSERT em leads
- ❌ Confusão arquitetural: estado de conversa ativa vs. lead qualificado
- ❌ Duplicação desnecessária de dados

---

## ✅ SOLUÇÃO V46

### Estratégia
**Remover todas as referências a `state_machine_state` da tabela `leads` no workflow V41**

### Arquitetura Correta

```
CONVERSATION LIFECYCLE:
┌─────────────────────────────────────┐
│ conversations table                 │
│ - state_machine_state ✅           │
│ - error_count ✅                    │
│ - collected_data (JSONB)            │
│ - Ativa durante conversa            │
└─────────────────────────────────────┘
            │
            │ (conversa completa)
            ↓
┌─────────────────────────────────────┐
│ leads table                         │
│ - status (novo/em_atendimento)      │
│ - service_details (JSONB)           │
│ - Lead qualificado e persistente    │
│ - SEM state_machine_state ❌        │
└─────────────────────────────────────┘
```

---

## 🎯 PLANO DE EXECUÇÃO

### Fase 1: Criar Script de Correção

**Arquivo**: `scripts/fix-workflow-v46-leads-duplication.py`

O script deve:
1. Ler workflow V41: `n8n/workflows/02_ai_agent_conversation_V41_QUERY_BATCHING_FIX.json`
2. Localizar node "Build Update Queries"
3. Remover `state_machine_state` da query `query_upsert_lead`
4. Salvar como: `02_ai_agent_conversation_V46_LEADS_FIX.json`

### Fase 2: Modificações Necessárias

**No node "Build Update Queries" do workflow V41**:

#### Query `query_upsert_lead` - UPDATE section (REMOVER):
```sql
-- ANTES (ERRADO):
UPDATE leads
SET
  name = COALESCE(NULLIF('...', ''), name),
  email = COALESCE(NULLIF('...', ''), email),
  city = COALESCE(NULLIF('...', ''), city),
  service_type = COALESCE(NULLIF('...', ''), service_type),
  state_machine_state = '${next_stage}',  -- ← REMOVER ESTA LINHA
  service_details = '${collected_data_json}'::jsonb,
  updated_at = NOW()

-- DEPOIS (CORRETO):
UPDATE leads
SET
  name = COALESCE(NULLIF('...', ''), name),
  email = COALESCE(NULLIF('...', ''), email),
  city = COALESCE(NULLIF('...', ''), city),
  service_type = COALESCE(NULLIF('...', ''), service_type),
  -- state_machine_state REMOVIDO ✅
  service_details = '${collected_data_json}'::jsonb,
  updated_at = NOW()
```

#### Query `query_upsert_lead` - INSERT section (REMOVER):
```sql
-- ANTES (ERRADO):
INSERT INTO leads (
  phone_number,
  name,
  email,
  city,
  service_type,
  state_machine_state,  -- ← REMOVER ESTA LINHA
  service_details,
  created_at,
  updated_at
)
SELECT
  '${phone_with_code}',
  '...',
  '...',
  '...',
  '...',
  '${next_stage}',  -- ← REMOVER ESTA LINHA
  '${collected_data_json}'::jsonb,
  NOW(),
  NOW()

-- DEPOIS (CORRETO):
INSERT INTO leads (
  phone_number,
  name,
  email,
  city,
  service_type,
  -- state_machine_state REMOVIDO ✅
  service_details,
  created_at,
  updated_at
)
SELECT
  '${phone_with_code}',
  '...',
  '...',
  '...',
  '...',
  -- next_stage REMOVIDO ✅
  '${collected_data_json}'::jsonb,
  NOW(),
  NOW()
```

### Fase 3: Verificar Correção

**Comandos de Verificação**:
```bash
# 1. Verificar que workflow V46 foi criado
ls -lh n8n/workflows/02_ai_agent_conversation_V46_LEADS_FIX.json

# 2. Verificar que não há referências a state_machine_state em leads
grep -n "state_machine_state" n8n/workflows/02_ai_agent_conversation_V46_LEADS_FIX.json | grep -i lead
# Esperado: SEM resultados

# 3. Verificar que state_machine_state ainda existe em conversations
grep -n "state_machine_state" n8n/workflows/02_ai_agent_conversation_V46_LEADS_FIX.json | grep -i conversation
# Esperado: DEVE ter resultados (uso correto)
```

### Fase 4: Importar e Testar

**Importar workflow corrigido**:
1. Acessar n8n: http://localhost:5678
2. Importar: `02_ai_agent_conversation_V46_LEADS_FIX.json`
3. Desativar workflow V41
4. Ativar workflow V46

**Teste Manual**:
```
1. Enviar mensagem WhatsApp: "oi"
2. Responder ao menu: "1"
3. Completar dados (nome, telefone, email, cidade)
4. Verificar que NÃO há erro de coluna em leads
5. Verificar que lead é criado corretamente
```

**Verificação Database**:
```bash
# Verificar que lead foi criado SEM state_machine_state
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    phone_number,
    name,
    service_type,
    status
  FROM leads
  ORDER BY created_at DESC
  LIMIT 1;
"

# Verificar que conversation TEM state_machine_state
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    phone_number,
    current_state,
    state_machine_state,
    created_at
  FROM conversations
  ORDER BY created_at DESC
  LIMIT 1;
"
```

---

## 📊 CRITÉRIOS DE SUCESSO

### ✅ Correção Completa Quando:
1. **Workflow V46 Criado**: Arquivo JSON existe e é válido
2. **Sem Referências Incorretas**: `state_machine_state` removido de queries de leads
3. **Referências Corretas Mantidas**: `state_machine_state` permanece em queries de conversations
4. **Execução Sem Erros**: Workflow V46 executa sem erro de coluna
5. **Lead Criado**: Registro em leads sem `state_machine_state`
6. **Conversation Atualizada**: Registro em conversations COM `state_machine_state`

### ✅ Arquitetura Correta Quando:
1. **Separation of Concerns**: Estado de máquina só em conversations
2. **Lead Simplificado**: Lead contém apenas dados de negócio
3. **Sem Duplicação**: Nenhum dado duplicado entre tabelas
4. **Clear Responsibilities**: Cada tabela tem propósito bem definido

---

## 🔧 SCRIPT DE EXECUÇÃO AUTOMATIZADO

**Arquivo**: `scripts/fix-workflow-v46-leads-duplication.py`

```python
#!/usr/bin/env python3
"""
V46 Fix Script - Remove state_machine_state from leads table queries
Purpose: Fix architectural duplication between conversations and leads tables
"""

import json
import re
from pathlib import Path

def fix_workflow_v46():
    """Remove state_machine_state references from leads queries in V41"""

    # Paths
    base_dir = Path(__file__).parent.parent
    workflow_v41 = base_dir / "n8n/workflows/02_ai_agent_conversation_V41_QUERY_BATCHING_FIX.json"
    workflow_v46 = base_dir / "n8n/workflows/02_ai_agent_conversation_V46_LEADS_FIX.json"

    print("=== V46 FIX: Remove state_machine_state from leads queries ===")
    print(f"Reading: {workflow_v41}")

    # Read workflow V41
    with open(workflow_v41, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Find "Build Update Queries" node
    build_update_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Build Update Queries':
            build_update_node = node
            break

    if not build_update_node:
        print("❌ ERROR: 'Build Update Queries' node not found")
        return False

    print("✅ Found 'Build Update Queries' node")

    # Get JavaScript code
    js_code = build_update_node['parameters']['jsCode']

    # Pattern 1: Remove state_machine_state from UPDATE SET clause
    print("\n1. Removing state_machine_state from UPDATE SET clause...")
    pattern_update = r"(\s+)(state_machine_state\s*=\s*'\${next_stage}',\s*\n)"
    js_code_fixed = re.sub(pattern_update, r"\1-- V46: state_machine_state removed (belongs to conversations only)\n", js_code)

    # Pattern 2: Remove state_machine_state from INSERT column list
    print("2. Removing state_machine_state from INSERT columns...")
    pattern_insert_col = r"(\s+)(state_machine_state,\s*\n)"
    js_code_fixed = re.sub(pattern_insert_col, r"\1-- V46: state_machine_state removed\n", js_code_fixed)

    # Pattern 3: Remove next_stage value from INSERT VALUES
    print("3. Removing next_stage value from INSERT VALUES...")
    pattern_insert_val = r"(\s+)('\${next_stage}',\s*\n)"
    js_code_fixed = re.sub(pattern_insert_val, r"\1-- V46: next_stage value removed\n", js_code_fixed)

    # Update node with fixed code
    build_update_node['parameters']['jsCode'] = js_code_fixed

    # Update workflow metadata
    workflow['name'] = "02 - AI Agent Conversation V46 (Leads Duplication Fix)"
    workflow['versionId'] = "v46-leads-fix"

    # Save as V46
    print(f"\nSaving fixed workflow: {workflow_v46}")
    with open(workflow_v46, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n✅ V46 Fix Complete!")
    print("\nNext steps:")
    print("1. Import workflow V46 in n8n interface")
    print("2. Deactivate workflow V41")
    print("3. Activate workflow V46")
    print("4. Test with WhatsApp message")

    return True

if __name__ == '__main__':
    success = fix_workflow_v46()
    exit(0 if success else 1)
```

---

## 📝 RESUMO EXECUTIVO

### Problema
Workflow V41 tenta escrever `state_machine_state` em DUAS tabelas: `conversations` (correto) e `leads` (incorreto).

### Causa
Confusão arquitetural sobre qual tabela deve armazenar estado da máquina de conversação.

### Solução
Remover todas as referências a `state_machine_state` da tabela `leads` no workflow V41.

### Impacto
- **Baixo**: Apenas remoção de referências incorretas
- **Rápido**: 1 minuto para executar script
- **Seguro**: Não afeta dados existentes
- **Reversível**: Pode reverter para V41 se necessário

### Benefício
- ✅ Workflow V46 funcionará sem erros de coluna
- ✅ Arquitetura correta: estado de máquina só em conversations
- ✅ Leads simplificados: apenas dados de negócio
- ✅ Sem duplicação desnecessária de dados

---

## 🚨 PRECAUÇÕES

### Antes de Executar
- ✅ Workflow V41 existe
- ✅ Backup não necessário (apenas mudança em workflow JSON)

### Durante Execução
- ⚠️ **NÃO** modificar tabelas do banco
- ⚠️ **NÃO** remover state_machine_state de conversations
- ⚠️ Script apenas modifica arquivo JSON do workflow

### Após Execução
- ✅ Importar workflow V46 em n8n
- ✅ Desativar V41
- ✅ Ativar V46
- ✅ Testar fluxo completo

---

**Autor**: Claude Code Analysis
**Data**: 2026-03-06
**Versão**: V46 Plan
**Status**: Ready for Execution
**Estimated Time**: 1-2 minutes
**Risk Level**: LOW (workflow change only)
**Rollback**: Easy (revert to V41)

---

**EXECUTE QUANDO PRONTO**
**Instrução**:
1. Executar script: `python3 scripts/fix-workflow-v46-leads-duplication.py`
2. Importar V46 em n8n
3. Ativar V46, desativar V41
4. Testar com WhatsApp
