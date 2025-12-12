# 🔄 Importar Workflow n8n - Sprint 1.1

## Objetivo
Importar workflow RAG (03_rag_knowledge_query.json) no n8n development para criar endpoint de consulta ao conhecimento.

## ✅ Pré-requisitos
- ✅ n8n rodando: `docker ps | grep n8n-dev` → Status: healthy
- ✅ Workflow file: `n8n/workflows/03_rag_knowledge_query.json`
- ✅ Credenciais disponíveis:
  - OpenAI API Key (em docker/.env)
  - Supabase PostgreSQL (em docker/.env)

## 📋 Passos de Importação

### Passo 1: Acessar n8n UI
```bash
# Abrir no navegador
http://localhost:5678
```

**Primeira vez**:
- Criar conta local (email/senha qualquer - modo dev sem auth)
- Ou usar diretamente se já configurado

### Passo 2: Importar Workflow JSON

**Via UI (Recomendado)**:
1. Menu superior: **Workflows** → **Import from File**
2. Selecionar arquivo: `n8n/workflows/03_rag_knowledge_query.json`
3. Clicar **Import**

**Via Clipboard (Alternativa)**:
1. Copiar conteúdo do arquivo JSON
2. Menu: **Workflows** → **Import from URL or Clipboard**
3. Colar JSON e confirmar

### Passo 3: Configurar Credenciais

O workflow requer 2 credenciais:

#### 3.1 OpenAI API (Embeddings)
**Nó**: "Generate Embedding (OpenAI)"

1. Clicar no nó **Generate Embedding (OpenAI)**
2. Clicar em **Select Credential** → **Create New**
3. Preencher:
   - **Name**: `OpenAI API (Embeddings)`
   - **API Key**: Copiar de `docker/.env` → `OPENAI_API_KEY`
     ```bash
     grep '^OPENAI_API_KEY=' docker/.env
     ```
4. **Save** credential

**⚠️ Importante**: Aguardar novo token da equipe comercial se quota atual esgotada.

#### 3.2 Supabase PostgreSQL
**Nó**: "Query Supabase (match_documents)"

1. Clicar no nó **Query Supabase (match_documents)**
2. Clicar em **Select Credential** → **Create New**
3. Preencher com dados de `docker/.env`:

**Formato Supabase URL**: `https://PROJECT_REF.supabase.co`
```bash
# Extrair PROJECT_REF da SUPABASE_URL
grep '^SUPABASE_URL=' docker/.env
# Exemplo: https://zvbfidflkjvexfjgnhin.supabase.co
# PROJECT_REF = zvbfidflkjvexfjgnhin
```

**Configuração PostgreSQL**:
```yaml
Host: aws-0-us-east-1.pooler.supabase.com
Port: 6543
Database: postgres
User: postgres.PROJECT_REF  # Substituir PROJECT_REF
Password: <SUPABASE_SERVICE_KEY>
SSL: Require
```

**Obter Password**:
```bash
grep '^SUPABASE_SERVICE_KEY=' docker/.env
# Copiar valor completo eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

4. **Save** credential

### Passo 4: Ativar Workflow

1. Verificar status: Switch superior direito → **OFF**
2. Clicar para ativar → **ON** (verde)
3. Verificar webhook ativo:
   ```
   Webhook URL: http://localhost:5678/webhook/rag-query
   Method: POST
   ```

### Passo 5: Testar Estrutura (Sem Dados)

**Teste básico de validação**:
```bash
curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{"query_text": "como funciona energia solar"}' | jq .
```

**Resultado esperado SEM ingest**:
```json
{
  "success": false,
  "results": [],
  "context": "",
  "metadata": {
    "query": "como funciona energia solar",
    "total_results": 0,
    "category_filter": null,
    "match_threshold": 0.75
  },
  "message": "Nenhum conhecimento relevante encontrado"
}
```

**✅ Sucesso**: Workflow respondeu corretamente (estrutura validada)
**❌ Falha**: Verificar credenciais ou logs n8n

**Resultado esperado COM ingest** (após novo token):
```json
{
  "success": true,
  "results": [
    {
      "rank": 1,
      "content": "...",
      "source": {"file": "energia_solar.md", "category": "servicos"},
      "similarity": "0.892",
      "relevance": "high"
    }
  ],
  "context": "[Fonte 1 - energia_solar.md (89.2% similar)]\n...",
  "metadata": {
    "total_results": 3,
    "average_similarity": "0.856"
  }
}
```

## 🔍 Validação de Componentes

### Workflow Nodes (7 componentes)

| Nó | Tipo | Função | Status |
|----|------|--------|--------|
| Webhook RAG Query | webhook | Recebe POST /webhook/rag-query | ✅ Estrutural |
| Validate Input | if | Valida query_text presente | ✅ Estrutural |
| Error Missing Query | respondToWebhook | Retorna 400 se query vazio | ✅ Estrutural |
| Generate Embedding (OpenAI) | openAi | Gera embedding 1536d | ⏸️ Aguarda token |
| Query Supabase | postgres | Executa match_documents() | ✅ Funcional* |
| Format Results for AI | code | Formata resposta JSON | ✅ Estrutural |
| Respond Success | respondToWebhook | Retorna 200 com resultados | ✅ Estrutural |

*Funcional mas retornará 0 resultados até ingest completar

### Parâmetros Opcionais da Query

```json
{
  "query_text": "texto da pergunta",  // OBRIGATÓRIO
  "match_threshold": 0.75,             // Default: 0.75 (75% similaridade)
  "match_count": 5,                    // Default: 5 (máximo de resultados)
  "category": "servicos"               // Opcional (filtro por categoria)
}
```

## 🐛 Troubleshooting

### Workflow não aparece após import
**Causa**: Cache do browser
**Fix**: F5 para recarregar página n8n

### Credencial OpenAI falha
**Causa**: Quota exceeded
**Fix**: Aguardar novo token da equipe comercial, substituir em credentials

### Credencial PostgreSQL falha
**Causa**: Formato incorreto de host/user
**Fix**:
```
❌ Errado: Host: zvbfidflkjvexfjgnhin.supabase.co
✅ Correto: Host: aws-0-us-east-1.pooler.supabase.com

❌ Errado: User: postgres
✅ Correto: User: postgres.zvbfidflkjvexfjgnhin
```

### Webhook retorna 404
**Causa**: Workflow não ativado
**Fix**: Toggle workflow para ON (verde)

### Query retorna "Nenhum conhecimento relevante"
**Causa Normal**: Banco vazio (ingest pendente)
**Fix**: Executar ingest quando novo token OpenAI disponível

## 📊 Logs e Debugging

**Ver execuções do workflow**:
1. n8n UI → **Executions** (menu esquerdo)
2. Clicar em execução para ver detalhes
3. Verificar cada nó (verde = sucesso, vermelho = erro)

**Ver logs Docker**:
```bash
docker-compose -f docker/docker-compose-dev.yml logs -f n8n-dev
```

**Verificar webhook ativo**:
```bash
# Lista webhooks ativos
curl -s http://localhost:5678/webhook-test/rag-query
# Esperado: 404 (webhook só responde a POST)
```

## ✅ Critérios de Sucesso

- [ ] Workflow importado e visível no n8n UI
- [ ] 2 credenciais configuradas (OpenAI, PostgreSQL)
- [ ] Workflow ativado (toggle ON verde)
- [ ] Webhook responde a POST (mesmo sem dados)
- [ ] Estrutura JSON validada (success: false esperado sem ingest)

## 🎯 Próximos Passos

**Após importação bem-sucedida**:
1. **Com novo token OpenAI**: Executar ingest (`scripts/ingest-simple.sh`)
2. **Validação completa**: Testar queries com dados reais
3. **Integração**: Conectar com cliente WhatsApp (Evolution API)

**Status atual**: ⏸️ Workflow estrutural pronto, aguardando dados (ingest)
**Tempo estimado**: 10-15 minutos (importação + configuração credenciais)
