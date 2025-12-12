# Setup de Credenciais - Sprint 1.1 Validation

**Objetivo**: Configurar todas as credenciais necessárias para validar o Sprint 1.1

**Tempo Estimado**: 30-45 minutos

---

## 📋 Credenciais Necessárias para Sprint 1.1

Para validar o sistema RAG, você precisa de **3 credenciais obrigatórias**:

1. ✅ **OpenAI API Key** - Para gerar embeddings
2. ✅ **Supabase URL** - PostgreSQL com pgvector
3. ✅ **Supabase Service Key** - Acesso admin ao banco

As demais credenciais serão necessárias nos próximos sprints.

---

## 🔑 Passo a Passo: Obter Credenciais

### 1. OpenAI API Key (OBRIGATÓRIO)

**Tempo**: 5 minutos

**Passos**:
1. Acesse: https://platform.openai.com/signup
2. Faça login ou crie uma conta
3. Acesse: https://platform.openai.com/api-keys
4. Clique em "Create new secret key"
5. Dê um nome: "E2 Bot RAG Embeddings"
6. Copie a key (começa com `sk-proj-...`)

**Formato**:
```
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Custo Estimado**:
- Ingest inicial: ~$0.10 (1.380 linhas → 50K tokens)
- Query: ~$0.00001 por pergunta
- Mensal (1000 queries): ~$0.01

**IMPORTANTE**:
- Guarde a key em local seguro (só aparece uma vez!)
- Configure billing: https://platform.openai.com/account/billing
- Adicione crédito mínimo: $5

---

### 2. Supabase Project (OBRIGATÓRIO)

**Tempo**: 10-15 minutos

**Opção A: Supabase Cloud (Recomendado para validação)**

1. **Criar Conta**:
   - Acesse: https://supabase.com/dashboard
   - Faça login com GitHub ou email

2. **Criar Projeto**:
   - Clique em "New Project"
   - Nome: "e2-solucoes-bot"
   - Database Password: Gere uma senha forte (salve!)
   - Region: South America (São Paulo) ou mais próximo
   - Plano: Free tier (suficiente para validação)
   - Clique em "Create new project"
   - **Aguarde 2-3 minutos** enquanto provisiona

3. **Obter Credenciais**:
   - No painel do projeto, vá em: Settings → API
   - Copie:
     - **Project URL**: `https://XXXXXXXX.supabase.co`
     - **anon public**: (para frontend futuro)
     - **service_role**: (ESTE é o importante! Usa para backend)

4. **Habilitar pgvector**:
   - Vá em: Database → Extensions
   - Procure "vector"
   - Clique em "Enable" ao lado de `vector`
   - Aguarde confirmação

**Formato**:
```
SUPABASE_URL=https://XXXXXXXXXXXXXXXX.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.XXXXXX...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.XXXXXX...
```

**Opção B: Supabase Local (Para desenvolvimento avançado)**

```bash
# Instalar Supabase CLI
npm install -g supabase

# Inicializar projeto
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
supabase init

# Iniciar Supabase local (Docker)
supabase start

# Copiar credenciais exibidas no terminal
# API URL: http://localhost:54321
# Service Role Key: eyJhbGciOi...
```

---

### 3. n8n Workflow Engine (Incluído no Docker)

**Tempo**: 5 minutos (se usando Docker local)

**Opção A: n8n via Docker Compose (Recomendado)**

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Verificar se docker-compose.yml existe
ls docker-compose.yml

# Se existir, iniciar stack
docker-compose up -d

# Aguardar inicialização (30-60 segundos)
docker-compose ps

# Acessar n8n
open http://localhost:5678
```

**Credenciais**:
```
N8N_HOST=localhost:5678
```

**Opção B: n8n Cloud**

1. Acesse: https://n8n.io/cloud
2. Crie conta gratuita
3. Anote URL: `https://XXXXX.app.n8n.cloud`

```
N8N_HOST=XXXXX.app.n8n.cloud
```

---

## 💾 Configurar Arquivo .env

**Passos**:

1. **Copiar Template**:
```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
cp .env.example .env
```

2. **Editar .env**:
```bash
# Abrir com editor favorito
nano .env
# OU
vim .env
# OU
code .env
```

3. **Preencher Credenciais Mínimas**:
```bash
# Substituir XXXXX pelos valores reais

# OpenAI (obter em platform.openai.com)
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Supabase (obter em supabase.com/dashboard)
SUPABASE_URL=https://XXXXXXXXXXXXXXXX.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.XXXXXX...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.XXXXXX...

# n8n (se local, usar localhost)
N8N_HOST=localhost:5678
```

4. **Salvar e Sair**:
   - nano: `Ctrl+O` → `Enter` → `Ctrl+X`
   - vim: `ESC` → `:wq` → `Enter`
   - code: `Ctrl+S` → Fechar

5. **Verificar Arquivo**:
```bash
# Listar arquivo (NÃO exibir conteúdo completo por segurança)
ls -lh .env

# Verificar se tem conteúdo
wc -l .env
# Deve retornar: ~20-30 linhas
```

---

## ✅ Validar Configuração

### Teste 1: Verificar .env Existe e Tem Conteúdo

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Verificar arquivo existe
[ -f .env ] && echo "✅ .env existe" || echo "❌ .env não encontrado"

# Verificar tem conteúdo (sem exibir credenciais)
grep -q "OPENAI_API_KEY=sk-" .env && echo "✅ OpenAI configurado" || echo "❌ OpenAI faltando"
grep -q "SUPABASE_URL=https://" .env && echo "✅ Supabase URL configurado" || echo "❌ Supabase URL faltando"
grep -q "SUPABASE_SERVICE_KEY=eyJ" .env && echo "✅ Supabase Key configurado" || echo "❌ Supabase Key faltando"
```

**Resultado Esperado**:
```
✅ .env existe
✅ OpenAI configurado
✅ Supabase URL configurado
✅ Supabase Key configurado
```

### Teste 2: Carregar Variáveis de Ambiente

```bash
# Carregar .env no shell
set -a
source .env
set +a

# Testar se variáveis foram carregadas (sem exibir valores completos)
echo "OpenAI: ${OPENAI_API_KEY:0:10}..."
echo "Supabase: ${SUPABASE_URL}"
echo "n8n: ${N8N_HOST}"
```

**Resultado Esperado**:
```
OpenAI: sk-proj-XX...
Supabase: https://XXXXXXXX.supabase.co
n8n: localhost:5678
```

### Teste 3: Validar OpenAI API Key

```bash
# Testar conectividade com OpenAI API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -s | jq -r '.data[0].id' 2>/dev/null || echo "❌ OpenAI API Key inválida"
```

**Resultado Esperado**:
```
gpt-4
# OU
text-embedding-3-small
# OU qualquer modelo válido
```

Se retornar erro:
- ❌ Verifique se API key está correta
- ❌ Verifique se billing está configurado
- ❌ Verifique se tem créditos disponíveis

### Teste 4: Validar Supabase Connection

```bash
# Testar conectividade com Supabase
curl "${SUPABASE_URL}/rest/v1/" \
  -H "apikey: ${SUPABASE_SERVICE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" \
  -s | jq '.' 2>/dev/null && echo "✅ Supabase conectado" || echo "❌ Supabase falhou"
```

**Resultado Esperado**:
```json
{
  "swagger": "2.0",
  "info": {
    "title": "PostgREST API",
    ...
  }
}
✅ Supabase conectado
```

### Teste 5: Validar n8n Está Rodando

```bash
# Testar se n8n está acessível
curl -s -o /dev/null -w "%{http_code}" http://${N8N_HOST}/ || echo "❌ n8n não está rodando"
```

**Resultado Esperado**:
```
200
# OU
302 (redirect para /workflow)
```

Se retornar erro:
```bash
# Iniciar n8n via Docker
docker-compose up -d

# Aguardar 30 segundos
sleep 30

# Testar novamente
curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/
```

---

## 🚨 Troubleshooting

### Problema: "OpenAI API key invalid"

**Soluções**:
1. Verificar key está completa (começa com `sk-proj-` ou `sk-`)
2. Verificar não tem espaços extras: `echo "$OPENAI_API_KEY" | wc -c` (deve ser ~51-56 chars)
3. Gerar nova key em: https://platform.openai.com/api-keys
4. Configurar billing: https://platform.openai.com/account/billing
5. Adicionar crédito mínimo ($5)

### Problema: "Supabase connection failed"

**Soluções**:
1. Verificar URL está correta (https://XXXXX.supabase.co)
2. Verificar está usando **service_role** key (não anon key)
3. Verificar projeto Supabase está ativo (não pausado)
4. Verificar extensão vector foi habilitada:
   - Supabase Dashboard → Database → Extensions → vector (Enable)

### Problema: "n8n not accessible"

**Soluções**:
1. Verificar Docker está rodando: `docker ps`
2. Iniciar stack: `docker-compose up -d`
3. Ver logs: `docker-compose logs n8n`
4. Verificar porta 5678 não está ocupada: `lsof -i :5678`
5. Se ocupada, mudar porta em docker-compose.yml

### Problema: ".env not loading"

**Soluções**:
1. Verificar arquivo existe: `ls -la .env`
2. Verificar permissões: `chmod 600 .env`
3. Carregar manualmente: `set -a; source .env; set +a`
4. Verificar sem BOM: `file .env` (deve ser ASCII text)

---

## 📝 Checklist Final

Antes de prosseguir para próxima etapa, confirme:

- [ ] ✅ .env.example copiado para .env
- [ ] ✅ OPENAI_API_KEY preenchida e validada
- [ ] ✅ SUPABASE_URL preenchida e validada
- [ ] ✅ SUPABASE_SERVICE_KEY preenchida e validada
- [ ] ✅ N8N_HOST configurado corretamente
- [ ] ✅ Variáveis carregam sem erro: `source .env`
- [ ] ✅ OpenAI API responde: `curl test`
- [ ] ✅ Supabase conecta: `curl test`
- [ ] ✅ n8n acessível: `http://localhost:5678`

**Status**: Se todos os checkboxes estão marcados, você está pronto para a **Etapa 2: Deploy Funções SQL**

---

## 🔐 Segurança

**IMPORTANTE**:

1. ✅ .env está no .gitignore (NUNCA commitar!)
2. ✅ Usar service_role key APENAS em backend
3. ✅ Não compartilhar keys publicamente
4. ✅ Rotacionar keys se expostas
5. ✅ Usar variáveis de ambiente em produção (não .env)

**Revogar Keys**:
- OpenAI: https://platform.openai.com/api-keys → Delete
- Supabase: Settings → API → Reset service_role key

---

**Próximo Documento**: `DEPLOY_SQL.md` - Deploy de funções SQL no Supabase

**Tempo Total Etapa 1**: 30-45 minutos
**Próxima Etapa**: 10-15 minutos
