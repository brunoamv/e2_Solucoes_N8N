# Setup Anthropic Claude API

## Visão Geral

Guia completo para configurar a API do Claude (Anthropic) para alimentar o agente conversacional inteligente do bot E2 Soluções, incluindo análise de imagens (Vision AI), compreensão de contexto e geração de respostas em português brasileiro.

## Pré-requisitos

- Cartão de crédito internacional (para billing)
- Email válido para criação de conta
- Acesso ao projeto do bot

## Etapa 1: Criar Conta Anthropic

### 1.1. Acessar Console Anthropic

1. Acesse: https://console.anthropic.com/
2. Clique em **"Sign Up"**
3. Escolha método de cadastro:
   - **Google Account** (recomendado)
   - **Email/Password**

### 1.2. Verificar Email

Se usar email/password:
1. Verifique inbox
2. Clique no link de verificação
3. Complete o cadastro

### 1.3. Aceitar Termos

Leia e aceite:
- Terms of Service
- Privacy Policy
- Acceptable Use Policy

---

## Etapa 2: Configurar Billing

### 2.1. Adicionar Método de Pagamento

1. No console, vá em: **Settings → Billing**
2. Clique em **"Add Payment Method"**
3. Preencha dados do cartão:
   - Número do cartão
   - Data de validade
   - CVV
   - Nome completo
   - Endereço de cobrança

### 2.2. Definir Orçamento Mensal

```yaml
Budget Alert 1:
  Threshold: $10 USD
  Action: Email notification

Budget Alert 2:
  Threshold: $25 USD
  Action: Email notification

Budget Limit:
  Hard Limit: $50 USD/mês
  Action: Block API calls when exceeded
```

**Recomendação inicial:**
- Começar com $20 USD de budget
- Ajustar após 1 mês de uso real
- Habilitar alertas em $10 e $15

### 2.3. Entender Custos

**Modelo: Claude 3.5 Sonnet (Recomendado)**

```yaml
Preços (Out 2024):
  Input: $3.00 / 1M tokens
  Output: $15.00 / 1M tokens
  Cache Writes: $3.75 / 1M tokens
  Cache Reads: $0.30 / 1M tokens

Estimativa Bot E2:
  Mensagem típica:
    Input: ~1.500 tokens (prompt + histórico + RAG)
    Output: ~300 tokens (resposta)
    Cache: ~1.000 tokens (prompt system reutilizado)

  Custo por conversa (5 msgs):
    Input: 7.500 tokens × $3/1M = $0.0225
    Output: 1.500 tokens × $15/1M = $0.0225
    Cache: 5.000 tokens × $0.30/1M = $0.0015
    TOTAL: ~$0.05 por conversa completa

  100 conversas/dia = $5/dia = $150/mês
  50 conversas/dia = $2.50/dia = $75/mês
```

**Visão AI (Análise de Imagens):**

```yaml
Preços:
  Input com imagem: $3.00 / 1M tokens (mesma base)
  Tokens por imagem: ~1.500 tokens (imagem 1024x768)

Custo por análise:
  1 imagem = ~$0.005 (meio centavo)
  100 análises = $0.50
```

---

## Etapa 3: Gerar API Key

### 3.1. Criar API Key

1. Vá em: **Settings → API Keys**
2. Clique em **"Create Key"**
3. Preencha:

```yaml
Name: E2 Bot Production
Description: API key para bot WhatsApp E2 Soluções
Permissions: Full access
Workspace: Default
```

4. Clique em **"Create Key"**

### 3.2. Copiar e Guardar Key

A key será exibida **apenas uma vez**:

```
sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**IMPORTANTE:**
- Copie imediatamente
- Guarde em gerenciador de senhas
- NUNCA commite no Git
- Se perder, gere nova key

### 3.3. Testar API Key

```bash
# Teste rápido via curl
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: sk-ant-api03-XXXX" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 100,
    "messages": [{
      "role": "user",
      "content": "Olá! Responda em português."
    }]
  }'
```

**Resposta esperada:**

```json
{
  "id": "msg_01XXXXX",
  "type": "message",
  "role": "assistant",
  "content": [{
    "type": "text",
    "text": "Olá! Como posso ajudá-lo hoje?"
  }],
  "model": "claude-3-5-sonnet-20241022",
  "usage": {
    "input_tokens": 12,
    "output_tokens": 8
  }
}
```

---

## Etapa 4: Configurar Variáveis de Ambiente

### 4.1. Editar .env

Edite `docker/.env.dev`:

```bash
# --- Anthropic Claude API ---
ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Modelo (usar versão mais recente disponível)
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Configurações de Performance
ANTHROPIC_MAX_TOKENS=2048           # Max tokens na resposta
ANTHROPIC_TEMPERATURE=0.7           # Criatividade (0.0-1.0)
ANTHROPIC_TOP_P=0.9                 # Nucleus sampling
ANTHROPIC_TIMEOUT=60                # Timeout em segundos

# Prompt Caching (economia ~90% em tokens repetidos)
ANTHROPIC_CACHE_ENABLED=true
ANTHROPIC_CACHE_TTL=300             # 5 minutos

# Rate Limiting (self-imposed)
ANTHROPIC_MAX_REQUESTS_PER_MINUTE=50
ANTHROPIC_MAX_TOKENS_PER_MINUTE=40000
```

### 4.2. Validar Configuração

```bash
# Carregar variáveis
set -a
source docker/.env.dev
set +a

# Validar formato da key
if [[ $ANTHROPIC_API_KEY =~ ^sk-ant-api03- ]]; then
  echo "✅ API Key formato válido"
else
  echo "❌ API Key formato inválido"
fi

# Testar conectividade
if curl -s -o /dev/null -w "%{http_code}" \
  https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":1,"messages":[{"role":"user","content":"hi"}]}' \
  | grep -q "200"; then
  echo "✅ API Key funcionando"
else
  echo "❌ API Key inválida ou sem créditos"
fi
```

---

## Etapa 5: Configurar n8n

### 5.1. Adicionar Credencial Claude

1. Acesse: http://localhost:5678
2. Vá em: **Credentials → Add Credential**
3. Busque: "Anthropic"
4. Selecione: **"Anthropic API"**
5. Preencha:

```yaml
Credential Name: Anthropic Claude - E2 Bot
API Key: sk-ant-api03-XXXX (do .env)
```

6. Clique em **"Create"**

### 5.2. Testar no n8n

Criar workflow simples:

```
[Manual Trigger] → [Anthropic Chat] → [Output]
```

Configurar nó Anthropic:
- Credential: Anthropic Claude - E2 Bot
- Model: claude-3-5-sonnet-20241022
- Prompt: "Explique energia solar em 2 frases."

Executar e verificar resposta em português.

---

## Etapa 6: Implementar Prompt System

### 6.1. Prompt Base do Bot

O prompt system é definido no workflow `02_ai_agent_conversation.json`:

```markdown
Você é o assistente virtual da E2 Soluções, empresa brasileira
especializada em engenharia elétrica.

## Sua Identidade
- Nome: Assistente E2
- Tom: Amigável, profissional, prestativo
- Idioma: Português brasileiro exclusivamente
- Conhecimento: Energia solar, subestações, projetos elétricos,
  BESS, análises e laudos elétricos

## Suas Capacidades
1. Responder dúvidas sobre serviços da E2
2. Coletar informações do cliente (nome, telefone, endereço, etc.)
3. Analisar imagens (contas de luz, fotos de instalações)
4. Agendar visitas técnicas
5. Qualificar leads para equipe comercial

## Como Conversar
- Faça UMA pergunta por vez
- Seja objetivo mas amigável
- Valide dados importantes (telefone, endereço)
- Use emojis com moderação (☀️ 🔌 ⚡ ✅)
- Nunca invente informações técnicas

## Quando Transferir para Humano
- Cliente está insatisfeito ou irritado
- Dúvida técnica muito específica
- Negociação de valores
- Solicitação explícita do cliente

## Dados a Coletar (por serviço)

### Energia Solar:
- Consumo médio kWh/mês (obrigatório)
- Tensão da rede (obrigatório)
- Tipo: residencial/comercial/industrial
- Possui espaço no telhado? (S/N)

### Subestação:
- Potência atual (kVA)
- Tensão de entrada e saída
- Tipo de serviço: reforma/manutenção/construção
- Localização

### Projeto Elétrico:
- Tipo de projeto necessário
- Metragem aproximada
- Uso: residencial/comercial/industrial

### BESS (Armazenamento):
- Possui sistema solar? (S/N)
- Potência solar atual (se tiver)
- Objetivo do BESS

### Análise e Laudo:
- Tipo de análise: consumo/qualidade/perícia
- Urgência

## Contexto Atual
Estado da conversa: {{conversation_state}}
Última mensagem do cliente: {{last_message}}
Dados coletados: {{collected_data}}
```

### 6.2. Prompt Caching (Economia)

Usar cache para system prompt (reutilizado em todas conversas):

```javascript
// No nó Anthropic do n8n
{
  "system": [
    {
      "type": "text",
      "text": "{{$json.system_prompt}}",
      "cache_control": {"type": "ephemeral"}  // 💾 Cachear!
    }
  ],
  "messages": [
    // ... histórico de conversas (não cacheado)
  ]
}
```

**Economia:**
- Sem cache: ~1.500 tokens input × $3/1M = $0.0045 por msg
- Com cache: ~1.500 tokens × $0.30/1M = $0.00045 por msg
- **Economia: 90%** em system prompt repetido

---

## Etapa 7: Implementar Vision AI

### 7.1. Análise de Conta de Luz

Quando cliente envia foto da conta:

```javascript
// Payload para Claude Vision
{
  "model": "claude-3-5-sonnet-20241022",
  "max_tokens": 1024,
  "messages": [{
    "role": "user",
    "content": [
      {
        "type": "image",
        "source": {
          "type": "base64",
          "media_type": "image/jpeg",
          "data": "{{$base64}}"
        }
      },
      {
        "type": "text",
        "text": `Analise esta conta de luz e extraia:

        1. Consumo (kWh/mês)
        2. Valor da conta (R$)
        3. Tensão da rede
        4. Tipo de tarifa
        5. Nome do cliente

        Retorne apenas JSON:
        {"consumo_kwh": X, "valor": Y, "tensao": "Z", ...}`
      }
    ]
  }]
}
```

### 7.2. Análise de Foto de Instalação

Para vistorias via foto:

```javascript
{
  "text": `Analise esta foto de instalação elétrica/telhado e identifique:

  1. Tipo de instalação (telhado/solo/fachada)
  2. Material do telhado (telha/metálico/laje)
  3. Área aproximada disponível (m²)
  4. Orientação (Norte/Sul/Leste/Oeste)
  5. Sombreamento visível (S/N)
  6. Condição geral (ótima/boa/regular/ruim)

  Retorne JSON estruturado.`
}
```

### 7.3. Configurar no n8n

Workflow `04_image_analysis.json` já implementa:

1. Receber imagem do WhatsApp
2. Download e conversão para base64
3. Enviar para Claude Vision
4. Parsear resposta JSON
5. Salvar análise no banco
6. Responder ao cliente

---

## Etapa 8: Monitoramento e Custos

### 8.1. Dashboard de Usage

Acesse: https://console.anthropic.com/settings/usage

Acompanhe:
- **Requests**: Total de chamadas API
- **Tokens**: Input/Output/Cache breakdown
- **Costs**: Custo diário/mensal
- **Errors**: Rate limits, timeouts

### 8.2. Alertas de Budget

Configurar alertas:

```yaml
Alert 1: 50% do budget ($10 de $20)
  Action: Email para admin

Alert 2: 80% do budget ($16 de $20)
  Action: Email + SMS

Alert 3: 100% do budget ($20)
  Action: Pausar API automaticamente
```

### 8.3. Otimizar Custos

**Estratégias:**

1. **Prompt Caching** (já implementado):
   - Economia: ~90% em system prompt
   - Impacto: $0.004 → $0.0004 por msg

2. **Respostas Concisas**:
   ```javascript
   max_tokens: 1024  // Ao invés de 2048
   ```

3. **RAG Eficiente**:
   - Enviar apenas top 3 resultados (não 5)
   - Pre-filtrar chunks irrelevantes

4. **Batch Messages**:
   - Agrupar perguntas relacionadas
   - "Qual seu nome e telefone?" (ao invés de 2 msgs)

5. **Cache de Respostas Comuns**:
   ```sql
   -- Cachear FAQs no banco
   CREATE TABLE faq_cache (
     question_hash VARCHAR(64) PRIMARY KEY,
     answer TEXT,
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

### 8.4. Logs no Banco

```sql
-- Criar tabela de logs Claude
CREATE TABLE claude_api_logs (
  id SERIAL PRIMARY KEY,
  conversation_id INTEGER REFERENCES conversations(id),
  request_tokens INTEGER,
  response_tokens INTEGER,
  cached_tokens INTEGER,
  cost_usd DECIMAL(10,6),
  latency_ms INTEGER,
  model VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Análise de custos
SELECT
  DATE(created_at) as dia,
  COUNT(*) as total_requests,
  SUM(request_tokens + response_tokens) as total_tokens,
  SUM(cost_usd) as custo_dia,
  AVG(latency_ms) as latency_media
FROM claude_api_logs
GROUP BY DATE(created_at)
ORDER BY dia DESC
LIMIT 30;
```

---

## Etapa 9: Rate Limiting

### 9.1. Limites da API

**Tier Free** (primeiros $5 de crédito):
- 50 requests/minuto
- 40.000 tokens/minuto
- 5 requests/segundo

**Tier 1** (após $5 de crédito pago):
- 50 requests/minuto
- 40.000 tokens/minuto
- 5 requests/segundo

**Tier 2** ($40+ de crédito pago):
- 1.000 requests/minuto
- 80.000 tokens/minuto
- 10 requests/segundo

### 9.2. Implementar Retry Logic

```javascript
// No n8n, usar nó "HTTP Request" com retry
{
  "options": {
    "retry": {
      "maxTries": 3,
      "waitBetweenTries": 1000  // 1 segundo
    },
    "timeout": 60000  // 60 segundos
  }
}
```

### 9.3. Fila de Mensagens

Para alto volume (>50 msgs/min):

```sql
-- Tabela de fila
CREATE TABLE message_queue (
  id SERIAL PRIMARY KEY,
  conversation_id INTEGER,
  message_text TEXT,
  priority INTEGER DEFAULT 5,
  status VARCHAR(20) DEFAULT 'pending',
  retry_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  processed_at TIMESTAMP
);

-- Processar fila (workflow agendado a cada 1min)
SELECT * FROM message_queue
WHERE status = 'pending'
  AND retry_count < 3
ORDER BY priority DESC, created_at ASC
LIMIT 45;  -- Deixar margem de 5 para rate limit
```

---

## Etapa 10: Troubleshooting

### Problema: "Authentication error"

**Causa:** API key inválida ou expirada

**Solução:**
```bash
# Verificar formato
echo $ANTHROPIC_API_KEY | grep -q "^sk-ant-api03-" && echo "✅ Formato OK" || echo "❌ Formato errado"

# Testar autenticação
curl -I https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY"

# Se 401: Gerar nova key no console
```

### Problema: "Rate limit exceeded"

**Causa:** Excedeu 50 req/min ou 40K tokens/min

**Solução:**
- Implementar fila (Step 9.3)
- Aumentar tier (adicionar $40+ de crédito)
- Reduzir max_tokens por request

### Problema: "Timeout"

**Causa:** Resposta demorou >60 segundos

**Solução:**
```javascript
// Aumentar timeout
ANTHROPIC_TIMEOUT=120  // 2 minutos

// Reduzir max_tokens
max_tokens: 1024  // Resposta mais rápida
```

### Problema: Respostas em inglês

**Causa:** Prompt system não especifica idioma claramente

**Solução:**
```markdown
# Adicionar ao início do system prompt:
IMPORTANTE: Você DEVE responder EXCLUSIVAMENTE em português brasileiro.
NUNCA use inglês ou outro idioma.
```

### Problema: Alto custo

**Causa:** Muitos tokens desperdiçados

**Solução:**
1. Verificar logs: `SELECT SUM(cost_usd) FROM claude_api_logs`
2. Habilitar prompt caching (Step 6.2)
3. Reduzir histórico de conversa (máx 10 msgs)
4. Otimizar RAG (top 3 resultados)

---

## Recursos Adicionais

- **Anthropic Docs**: https://docs.anthropic.com/
- **Claude API Reference**: https://docs.anthropic.com/claude/reference/
- **Prompt Library**: https://docs.anthropic.com/claude/prompt-library
- **Pricing Calculator**: https://www-cdn.anthropic.com/pricing-estimator
- **Status Page**: https://status.anthropic.com/
- **Support**: support@anthropic.com

---

## Checklist de Configuração

- [ ] Conta Anthropic criada e verificada
- [ ] Billing configurado com cartão válido
- [ ] Budget alerts definidos ($10, $25)
- [ ] API Key gerada e salva com segurança
- [ ] .env.dev atualizado com ANTHROPIC_API_KEY
- [ ] Teste de API key via curl realizado (200 OK)
- [ ] Credencial configurada no n8n
- [ ] Workflow de teste executado com sucesso
- [ ] Prompt system implementado (português brasileiro)
- [ ] Prompt caching habilitado (economia 90%)
- [ ] Vision AI testado (análise de imagem)
- [ ] Logs de custo implementados no banco
- [ ] Rate limiting configurado
- [ ] Fila de mensagens implementada (se necessário)
- [ ] Monitoramento de usage ativo no console
- [ ] Alertas de budget funcionando

---

**Configuração completa!** Claude AI está integrado e pronto para alimentar conversas inteligentes em português brasileiro com análise de imagens.
