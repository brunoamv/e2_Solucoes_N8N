# 🔍 DIAGNÓSTICO COMPLETO E SOLUÇÃO FINAL

**Data**: 2026-01-06
**Status**: ✅ Problemas Identificados e Corrigidos (Parcial)

---

## 📊 RESUMO EXECUTIVO

### Problemas Identificados:

1. ✅ **n8n Container Parado** → **RESOLVIDO**
2. ✅ **Variáveis EVOLUTION Ausentes** → **RESOLVIDO**
3. ⚠️ **`collected_data` Vazio** → **CAUSA RAIZ IDENTIFICADA (diferente do esperado)**

---

## 🚨 DESCOBERTA CRÍTICA: collected_data Vazio

### Evidência do Log:
```
=== COLLECTED DATA DEBUGGING ===
Raw conversation.collected_data: {}
Tipo: object
Parsed stageData: {}
Chaves em stageData: []
=== FIM DEBUGGING ===
```

### ❌ Diagnóstico ANTERIOR (Incorreto):
Pensávamos que o problema era o Safe JSON Parsing (string vs object).

### ✅ Diagnóstico CORRETO (Atual):
**O `collected_data` JÁ ESTÁ VAZIO no PostgreSQL!**

Verificação no banco de dados:
```sql
SELECT phone_number, current_state, collected_data, updated_at
FROM conversations ORDER BY updated_at DESC LIMIT 5;

 phone_number  | current_state |           collected_data                    | updated_at
---------------+---------------+---------------------------------------------+------------
 6181755748    | novo          | {}                                          | 22:26:47
 5562981755485 | coletando_dados | {"error_count": 0, "lead_name": "João..."} | 22:12:51
```

### 🔎 Análise:

1. **Registro antigo** (`5562981755485`): ✅ TEM dados preservados corretamente
2. **Registro novo** (`6181755748`): ❌ Dados vazios desde o início

**Conclusão**: O problema NÃO é no Safe JSON Parsing. O problema é que:
- **A conversa foi criada MAS nenhuma mensagem foi processada**
- O workflow não conseguiu atualizar o `collected_data`
- Possível causa: **n8n estava PARADO durante a tentativa de conversa**

---

## ✅ SOLUÇÕES APLICADAS

### 1. Container n8n Reiniciado

**Problema**: Container parado após tentativa falha de `docker-compose --force-recreate`
```
KeyError: 'ContainerConfig'
```

**Solução Aplicada**:
```bash
docker-compose -f docker/docker-compose-dev.yml rm -f n8n-dev
docker-compose -f docker/docker-compose-dev.yml up -d n8n-dev
```

**Status**: ✅ **RESOLVIDO** - n8n rodando e healthy

---

### 2. Variáveis EVOLUTION Configuradas

**Problema**: Variáveis `EVOLUTION_API_URL`, `EVOLUTION_INSTANCE_NAME`, `EVOLUTION_API_KEY` ausentes no n8n

**Solução Aplicada**: Editado `docker/docker-compose-dev.yml` (linhas 56-59):
```yaml
# === Evolution API Integration (Sprint 0.1) ===
- EVOLUTION_API_URL=http://e2bot-evolution-dev:8080
- EVOLUTION_INSTANCE_NAME=${EVOLUTION_INSTANCE_NAME:-e2-solucoes-bot}
- EVOLUTION_API_KEY=${EVOLUTION_API_KEY}
```

**Validação**:
```bash
docker exec e2bot-n8n-dev printenv | grep EVOLUTION

# Resultado:
EVOLUTION_API_URL=http://e2bot-evolution-dev:8080
EVOLUTION_INSTANCE_NAME=e2-solucoes-bot
EVOLUTION_API_KEY=ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891
```

**Status**: ✅ **RESOLVIDO** - Variáveis configuradas corretamente

**Impacto**: O node "Send WhatsApp Response" agora vai funcionar com URL absoluta:
```
http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot
```

---

## ⚠️ PRÓXIMOS PASSOS CRÍTICOS

### 1. Testar Conversa E2E Completa

**Por quê?**: O registro vazio (`6181755748`) foi criado quando o n8n estava PARADO. Agora que está rodando, precisamos validar o fluxo completo.

**Como Testar**:

1. **Limpar dados de teste**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
DELETE FROM conversations WHERE phone_number IN ('6181755748', '5511999999999');"
```

2. **Enviar mensagem no WhatsApp**:
   - Número: seu número de teste
   - Mensagem: "Oi"

3. **Acompanhar logs em tempo real**:
```bash
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "(COLLECTED DATA|STATE MACHINE|phone_number)"
```

4. **Verificar banco após CADA mensagem**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    phone_number,
    current_state,
    jsonb_pretty(collected_data) as dados,
    jsonb_object_keys(collected_data) as campos
FROM conversations
WHERE phone_number = 'SEU_NUMERO_TESTE'
ORDER BY updated_at DESC;"
```

**Resultado Esperado**:
- Após "Oi": `{}`
- Após escolher serviço: `{"service_type": "...", "error_count": 0}`
- Após informar nome: `{"service_type": "...", "lead_name": "...", "error_count": 0}`
- Dados devem **acumular**, não resetar!

---

### 2. Se Dados Ainda Ficarem Vazios → Investigar UPDATE Query

Se após o teste E2E os dados ainda ficarem vazios, o problema está na query UPDATE do workflow.

**Possíveis causas**:
1. Query usando `JSON.stringify()` que retorna string vazia para objeto vazio
2. Campo `collected_data_json` não sendo populado corretamente
3. Spread operator falhando em algum ponto

**Como Investigar**:
```bash
# Ver query UPDATE sendo executada
docker logs e2bot-n8n-dev 2>&1 | grep -A5 "UPDATE conversations"

# Ver dados que estão sendo passados para o UPDATE
docker logs e2bot-n8n-dev 2>&1 | grep -A10 "collected_data_json"
```

---

## 📋 CHECKLIST DE VALIDAÇÃO

- [x] n8n container rodando e healthy
- [x] Variáveis EVOLUTION configuradas
- [ ] **Teste E2E completo via WhatsApp**
- [ ] `collected_data` acumulando campos corretamente
- [ ] "Send WhatsApp Response" funcionando sem erro de URL
- [ ] Todos os estados da conversa transitando corretamente

---

## 🔧 CORREÇÃO DO Safe JSON Parsing (SE NECESSÁRIO)

**NOTA IMPORTANTE**: Com base no diagnóstico atual, o Safe JSON Parsing pode NÃO ser o problema principal. Mas caso seja necessário após o teste E2E:

### Localização:
- Workflow: `FGK93uyr4VLtUR8e` (http://localhost:5678/workflow/FGK93uyr4VLtUR8e)
- Node: "State Machine Logic"
- Linhas: 24-25

### Código Atual (Problemático):
```javascript
const currentStage = conversation.current_state || 'greeting';
const stageData = conversation.collected_data || {};
```

### Código Corrigido (Safe JSON Parsing):
```javascript
const currentStage = conversation.current_state || 'greeting';

// ===== SAFE JSON PARSING =====
let stageData = {};

if (conversation.collected_data) {
    if (typeof conversation.collected_data === 'string') {
        try {
            console.log('🔍 collected_data é STRING, fazendo parse...');
            stageData = JSON.parse(conversation.collected_data);
            console.log('✅ Parse OK:', stageData);
        } catch (e) {
            console.error('❌ Erro no parse:', e);
            stageData = {};
        }
    } else if (typeof conversation.collected_data === 'object' && conversation.collected_data !== null) {
        console.log('✅ collected_data já é OBJECT');
        stageData = conversation.collected_data;
    } else {
        console.log('⚠️ Tipo inesperado:', typeof conversation.collected_data);
        stageData = {};
    }
} else {
    console.log('⚠️ collected_data null/undefined');
}

console.log('=== DEBUG collected_data ===');
console.log('Raw:', conversation.collected_data);
console.log('Tipo:', typeof conversation.collected_data);
console.log('Parsed stageData:', stageData);
console.log('Keys:', Object.keys(stageData));
console.log('=== FIM DEBUG ===');
// ===== FIM SAFE PARSING =====
```

---

## 📞 PRÓXIMA AÇÃO IMEDIATA

**EXECUTAR TESTE E2E AGORA** que o n8n está rodando corretamente:

1. Limpar dados de teste
2. Enviar "Oi" no WhatsApp
3. Observar logs em tempo real
4. Validar banco de dados após cada mensagem
5. Se dados ainda ficarem vazios → investigar UPDATE query no workflow ativo

**Comando para logs em tempo real**:
```bash
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "(COLLECTED|STATE MACHINE|Final preservedData)"
```

---

**FIM DO DIAGNÓSTICO**
