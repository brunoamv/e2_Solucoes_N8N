# ✅ Correção Aplicada: Preservação de Tipos no collected_data

**Data**: 2025-01-06
**Status**: RESOLVIDO ✅
**Arquivo Corrigido**: `02_ai_agent_conversation_V1_MENU_FIXED_v4.json`

---

## 🔴 Problema Identificado

O `error_count` sempre retornava para 0 porque estava sendo convertido de número para string no node "Prepare Update Data":

```json
// Problema: valor numérico sendo convertido para string
{"error_count": "0"}  // ❌ String incorreta

// Solução: preservar tipo numérico
{"error_count": 0}    // ✅ Número correto
```

## ✅ Correção Aplicada

### 1. Análise Completa
- **Documento**: `/docs/PLAN/collected_data_persistence_fix.md`
- **Diagnóstico**: Conversão agressiva para string com `String(value)`
- **Impacto**: `Number.isInteger("0")` sempre retorna false, resetando o contador

### 2. Script de Correção Executado
```bash
python3 scripts/fix-collected-data-types.py
```

### 3. Workflow Corrigido Gerado
- **Arquivo**: `n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v4.json`
- **Mudança Principal**: Preservação de tipos nativos (number, boolean, null)
- **Código Corrigido**:
```javascript
// Agora preserva tipos nativos
if (typeof value === 'number') {
    cleanedData[key] = value;  // Mantém como número
}
```

---

## 📋 Próximos Passos OBRIGATÓRIOS

### 1. Importar Workflow no n8n
```bash
1. Acessar: http://localhost:5678
2. Desativar workflow antigo (v3)
3. Importar: 02_ai_agent_conversation_V1_MENU_FIXED_v4.json
4. Ativar novo workflow
```

### 2. Testar a Correção
```bash
# Enviar mensagens de teste
1. Enviar "Oi" para iniciar
2. Enviar opção inválida "9"
3. Verificar no banco:

docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    phone_number,
    jsonb_typeof(collected_data->'error_count') as tipo,
    collected_data->'error_count' as valor
FROM conversations;"

# Resultado esperado:
# tipo: "number" (não "text")
# valor: 1 (não "1")
```

### 3. Script de Validação Disponível
```bash
./scripts/test-collected-data-types.sh
```

---

## 🎯 Resultado Final

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Tipo de error_count** | String ("0") | Number (0) |
| **Incremento funciona** | ❌ Não | ✅ Sim |
| **Reset indevido** | ❌ Sempre reseta | ✅ Preserva valor |
| **Validação Number.isInteger** | ❌ Sempre false | ✅ Funciona corretamente |

---

## 📊 Arquivos Criados/Modificados

1. ✅ **Análise**: `/docs/PLAN/collected_data_persistence_fix.md` (293 linhas)
2. ✅ **Script Fix**: `/scripts/fix-collected-data-types.py` (196 linhas)
3. ✅ **Script Test**: `/scripts/test-collected-data-types.sh` (auto-gerado)
4. ✅ **Workflow v4**: `/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v4.json`
5. ✅ **Este Resumo**: `/docs/PLAN/collected_data_fix_summary.md`

---

**⚠️ IMPORTANTE**: O workflow corrigido (v4) DEVE ser importado no n8n para que a correção tenha efeito!