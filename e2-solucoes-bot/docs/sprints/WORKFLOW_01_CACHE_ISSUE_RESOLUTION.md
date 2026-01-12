# 🚨 Plano de Resolução - Problema de Cache do n8n no Workflow 01

**Data**: 2025-12-17
**Problema**: n8n mantém configuração antiga do node "Save Inbound Message" mesmo após reimportação
**Causa Raiz**: Cache interno do n8n mescla configurações antigas com novas na reimportação
**Impacto**: Mensagens WhatsApp não são salvas no banco PostgreSQL

---

## 🔍 Análise do Problema

### Erro Persistente

```
NodeOperationError: Column 'success' does not exist in selected table
at checkItemAgainstSchema (...postgres/v2/helpers/utils.ts:540:10)
```

### Comparação de Configurações

**❌ Configuração ERRADA (atualmente no n8n)**:
```json
{
  "parameters": {
    "resource": "database",
    "operation": "insert",
    "table": "messages",
    "dataMode": "autoMapInputData",  // ← PROBLEMA: tenta mapear TODOS os campos
    "options": {}
  }
}
```

**✅ Configuração CORRETA (no arquivo JSON)**:
```json
{
  "parameters": {
    "operation": "insert",
    "table": "messages",
    "columns": "conversation_id, direction, content, message_type, media_url, whatsapp_message_id",
    "additionalFields": {
      "values": "null, 'inbound', '{{ $node[\"Extract Message Data\"].json.content }}', ..."
    }
  }
}
```

### Por Que o Cache Persiste?

1. **Identificação de Nodes**: n8n identifica nodes por `id` interno, não por nome
2. **Mesclagem de Configurações**: Ao reimportar, n8n detecta node similar e MESCLA configs
3. **Persistência de Parâmetros**: Alguns parâmetros (como `dataMode`) são mantidos da versão antiga
4. **Credenciais Vinculadas**: Credencial PostgreSQL mantém vinculação com node antigo

---

## ✅ Solução Definitiva: Método Manual na UI do n8n

### Opção 1: Reconfiguração Manual do Node (RECOMENDADA)

**Por quê?**: Mais rápida, sem risco de perder outros workflows, não requer acesso ao banco SQLite

#### Passo 1: Abrir Workflow no n8n UI

```bash
# 1. Acesse o n8n
http://localhost:5678/workflows

# 2. Abra o workflow "01 - WhatsApp Handler (FIXED v3)"
```

#### Passo 2: Deletar e Recriar Node "Save Inbound Message"

```
1. Clique no node "Save Inbound Message"
2. Pressione DELETE ou clique com botão direito → Delete
3. Clique em "Add Node" → "PostgreSQL" → "V2"
4. Renomeie para "Save Inbound Message"
5. Configure manualmente:
```

**Configuração Manual Exata**:

```yaml
Resource: Database
Operation: Insert
Schema: public
Table: messages
Data Mode: Define Below  # ← ESSENCIAL: NÃO USAR "Auto-Map Input Data"

Columns to Insert:
  - conversation_id
  - direction
  - content
  - message_type
  - media_url
  - whatsapp_message_id

Values:
  conversation_id: (expression) null
  direction: (fixed) inbound
  content: (expression) {{ $node["Extract Message Data"].json.content }}
  message_type: (expression) {{ $node["Extract Message Data"].json.message_type }}
  media_url: (expression) {{ $node["Extract Message Data"].json.media_url }}
  whatsapp_message_id: (expression) {{ $node["Extract Message Data"].json.message_id }}

Credential: PostgreSQL - E2 Bot
```

#### Passo 3: Reconectar Workflow

```
1. Conecte "Is New Message?" (saída TRUE) → "Save Inbound Message"
2. Conecte "Save Inbound Message" → "Is Image?"
3. Salve o workflow (botão "Save" superior direito)
4. Confirme que workflow está ATIVO (toggle verde)
```

#### Passo 4: Testar

```bash
# 1. Envie mensagem WhatsApp (5561981755748):
"TESTE PÓS-RECONFIGURAÇÃO MANUAL"

# 2. Monitore logs:
docker logs -f --tail 50 e2bot-n8n-dev 2>&1 | grep -E "(Save Inbound Message|finished)"

# DEVE mostrar:
# Start executing node "Save Inbound Message"
# Running node "Save Inbound Message" finished successfully  ← SEM "with error"!

# 3. Verificar banco:
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "SELECT id, content, message_type, direction FROM messages ORDER BY created_at DESC LIMIT 1;"

# DEVE retornar:
#  id | content                           | message_type | direction
# ----+-----------------------------------+--------------+-----------
#   1 | TESTE PÓS-RECONFIGURAÇÃO MANUAL   | text         | inbound
```

---

### Opção 2: Deletar Banco SQLite do n8n (ALTERNATIVA)

**Por quê?**: Remove TODOS os caches e workflows, forçando importação limpa

⚠️ **ATENÇÃO**: Esta opção deleta TODOS os workflows do n8n!

```bash
# 1. Parar n8n
docker stop e2bot-n8n-dev

# 2. Deletar banco de dados SQLite do n8n
docker exec e2bot-n8n-dev rm -f /home/node/.n8n/database.sqlite

# OU deletar volume inteiro (mais radical)
docker volume rm e2bot_n8n_dev_data

# 3. Reiniciar n8n (criará banco novo)
docker start e2bot-n8n-dev

# 4. Aguardar inicialização
sleep 30

# 5. Reimportar workflow pelo n8n UI
# http://localhost:5678 → Import from File → 01_main_whatsapp_handler.json

# 6. Configurar credencial PostgreSQL novamente
# 7. ATIVAR workflow
```

---

### Opção 3: Editar Diretamente no Banco SQLite (AVANÇADA)

**Por quê?**: Cirúrgica, preserva outros workflows, mas requer conhecimento SQL

⚠️ **RISCO**: Pode corromper banco do n8n se feito incorretamente

```bash
# 1. Backup do banco n8n
docker exec e2bot-n8n-dev sqlite3 /home/node/.n8n/database.sqlite ".backup /tmp/n8n_backup.db"

# 2. Exportar workflow atual
docker exec e2bot-n8n-dev sqlite3 /home/node/.n8n/database.sqlite \
  "SELECT data FROM workflow_entity WHERE name = '01 - WhatsApp Handler (FIXED v3)';" \
  > /tmp/workflow_export.json

# 3. Editar manualmente o JSON exportado
# Procurar pelo node "Save Inbound Message" e substituir "dataMode": "autoMapInputData"
# pela configuração correta com "columns" e "values"

# 4. Reimportar via UPDATE SQL
# (Complexo demais, NÃO RECOMENDADO)
```

---

## 🎯 Recomendação Final

**USE A OPÇÃO 1: Reconfiguração Manual do Node**

### Vantagens:
- ✅ Mais segura (não deleta outros workflows)
- ✅ Mais rápida (5 minutos)
- ✅ Não requer acesso direto ao banco
- ✅ Interface visual familiar do n8n
- ✅ Garante configuração exata sem cache

### Desvantagens:
- ⚠️ Requer cliques manuais (não automatizável)

---

## 📊 Checklist de Validação

Após aplicar a solução, valide com este checklist:

```
[ ] 1. Node "Save Inbound Message" deletado e recriado
[ ] 2. Configuração manual aplicada com "Data Mode: Define Below"
[ ] 3. Expressões corretas usando $node["Extract Message Data"].json.*
[ ] 4. Workflow salvo e ATIVO (toggle verde)
[ ] 5. Mensagem teste enviada do WhatsApp
[ ] 6. Logs mostram "finished successfully" SEM "with error"
[ ] 7. Banco PostgreSQL contém mensagem inserida
[ ] 8. Workflow executa até "Trigger AI Agent" sem erros
```

---

## 🔧 Troubleshooting Pós-Aplicação

### Problema: Ainda mostra erro "Column 'success' does not exist"

**Solução**: Certifique-se que escolheu "Define Below" e NÃO "Auto-Map Input Data"

```
1. Abra node "Save Inbound Message"
2. Verifique campo "Data Mode"
3. DEVE estar: "Define Below"
4. NÃO DEVE estar: "Auto-Map Input Data"
```

### Problema: Campos vazios no banco

**Solução**: Verificar expressões nos valores

```
1. Abra node "Save Inbound Message"
2. Para cada campo de valor, clique no ícone de expressão
3. Confirme que usa $node["Extract Message Data"].json.[campo]
4. Teste com "Execute Node" para ver preview dos dados
```

### Problema: Workflow não executa

**Solução**: Verificar conexões entre nodes

```
1. Certifique-se que "Is New Message?" (TRUE) → "Save Inbound Message"
2. Certifique-se que "Save Inbound Message" → "Is Image?"
3. Salve workflow novamente
4. Desative e reative o workflow
```

---

## 📝 Lições Aprendidas

1. **n8n UI Cache**: Reimportação de workflows mantém cache interno de configurações
2. **Node Identification**: Nodes são identificados por ID interno, não por nome
3. **Manual > Automático**: Para correções críticas, reconfiguração manual é mais confiável
4. **Validação Essencial**: Sempre verificar configuração real no n8n UI, não apenas no arquivo JSON

---

## 🚀 Próximos Passos Após Correção

Quando a mensagem for salva com sucesso no banco:

1. ✅ Validar workflow completo (até "Trigger AI Agent")
2. ✅ Testar com diferentes tipos de mensagem (texto, imagem)
3. ✅ Validar integração com workflow 02 (AI Agent)
4. ✅ Documentar configuração final funcionando
5. ✅ Criar backup do workflow funcional

---

**Criado em**: 2025-12-17 22:35
**Última Atualização**: 2025-12-17 22:35
**Status**: PRONTO PARA EXECUÇÃO
**Método Recomendado**: Opção 1 - Reconfiguração Manual do Node
