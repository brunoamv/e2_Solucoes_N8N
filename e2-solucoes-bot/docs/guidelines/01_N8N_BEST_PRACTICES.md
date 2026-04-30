# 01 - n8n Best Practices e Limitações

> **Guia completo** de limitações do n8n 2.x e suas soluções
> **Stack**: n8n 2.14.2 + Docker + PostgreSQL
> **Atualizado**: 2026-04-29

---

## 📋 Índice

1. [Limitações Críticas do n8n 2.x](#limitações-críticas-do-n8n-2x)
2. [Workarounds Comprovados](#workarounds-comprovados)
3. [Padrões de Nodes](#padrões-de-nodes)
4. [Estrutura de Dados](#estrutura-de-dados)
5. [Boas Práticas de Desenvolvimento](#boas-práticas-de-desenvolvimento)
6. [Debugging e Troubleshooting](#debugging-e-troubleshooting)

---

## 🚫 Limitações Críticas do n8n 2.x

### Breaking Changes n8n 1.x → 2.x

Com a atualização para n8n 2.0+, várias funcionalidades que funcionavam em versões anteriores foram **bloqueadas por segurança**. É crucial entender essas limitações para evitar horas de debugging.

### 1. Acesso ao Filesystem Bloqueado

#### ❌ O QUE NÃO FUNCIONA MAIS

```javascript
// ❌ ERRO - n8n 2.x bloqueia acesso ao filesystem
const fs = require('fs');
const path = require('path');

// Tentativa de ler template HTML
const templatePath = path.join(__dirname, 'templates', 'confirmation.html');
const template = fs.readFileSync(templatePath, 'utf8');

// ERRO: Error: Access to 'fs' module is not allowed
```

#### Nodes Afetados
- **Read/Write Binary File**: Só acessa `~/.n8n/files/` (não `/app/templates/` ou outros caminhos)
- **Function/Code nodes**: Bloqueiam `require('fs')`
- **Execute Command nodes**: Limitados (sem acesso direto ao filesystem do container)

#### 🔍 Por Que Foi Bloqueado
- **Segurança**: Previne scripts maliciosos de acessar filesystem do servidor
- **Isolamento**: Workflows não devem depender de arquivos locais externos
- **Cloud-Ready**: Arquitetura preparada para execução em ambientes serverless

### ✅ SOLUÇÃO: HTTP Request + nginx Container

**Estratégia**: Servir arquivos estáticos via HTTP usando nginx como proxy reverso

#### docker-compose Configuration

```yaml
# docker-compose-dev.yml
services:
  e2bot-templates-dev:
    image: nginx:alpine
    container_name: e2bot-templates-dev
    restart: unless-stopped
    volumes:
      - ../email-templates:/usr/share/nginx/html:ro  # Read-only
    ports:
      - "8081:80"
    networks:
      - e2bot-network
    depends_on:
      - e2bot-n8n-dev
```

#### Email Templates Directory Structure

```
email-templates/
├── confirmation.html          # Template de confirmação de agendamento
├── reminder.html              # Template de lembrete
├── styles/
│   └── email.css              # Estilos compartilhados
└── images/
    └── logo.png               # Imagens inline
```

#### n8n HTTP Request Node

```javascript
// WF07 - Send Email (V13)
// Node: HTTP Request - Get Email Template

{
  method: 'GET',
  url: 'http://e2bot-templates-dev/{{ $json.template_file }}',
  // Example: http://e2bot-templates-dev/confirmation.html

  // Response Format: binary (HTML content)
  responseFormat: 'file',

  // Error Handling
  continueOnFail: true,
  retryOnFail: true,
  maxTries: 3
}
```

#### Code Node - Template Processing

```javascript
// After HTTP Request gets template

const items = $input.all();

return items.map(item => {
  // Get HTML template from HTTP Request
  const template = item.binary.data.toString('utf8');

  // Replace variables
  const processedTemplate = template
    .replace('{{LEAD_NAME}}', item.json.lead_name)
    .replace('{{SERVICE_TYPE}}', item.json.service_type)
    .replace('{{SCHEDULED_DATE}}', item.json.scheduled_date)
    .replace('{{SCHEDULED_TIME}}', item.json.scheduled_time);

  return {
    json: {
      ...item.json,
      html_content: processedTemplate
    }
  };
});
```

#### ✅ Vantagens desta Abordagem

1. **Funciona em n8n 2.x**: Sem bloqueios de segurança
2. **Versionado**: Templates no git junto com código
3. **Hot Reload**: Alterações em templates sem restart (nginx recarrega automaticamente)
4. **Testável**: Acesso via browser (`http://localhost:8081/confirmation.html`)
5. **Escalável**: Fácil adicionar CDN ou cache

### 2. Variáveis de Ambiente ($env) Bloqueadas

#### ❌ O QUE NÃO FUNCIONA MAIS

```javascript
// ❌ ERRO - n8n 2.x bloqueia acesso a $env em Code nodes
const apiKey = $env.OPENAI_API_KEY;
const dbPassword = $env.POSTGRES_PASSWORD;

// ERRO: $env is not defined

// ❌ ERRO - Também bloqueado em Set nodes
// Ao tentar: {{ $env.VARIABLE_NAME }}
// ERRO: Cannot read properties of undefined (reading 'VARIABLE_NAME')
```

#### Nodes Afetados
- **Code/Function nodes**: `$env` não está disponível
- **Set nodes**: Expressões `{{ $env.X }}` retornam `undefined`
- **HTTP Request nodes**: Headers com `$env` não funcionam

#### 🔍 Por Que Foi Bloqueado
- **Segurança**: Previne workflows de expor variáveis de ambiente sensíveis
- **Isolamento**: Workflows não devem ter acesso irrestrito ao ambiente do servidor
- **Multi-Tenancy**: Em cloud, variáveis de um tenant não devem vazar para outro

### ✅ SOLUÇÃO 1: Hardcoded Values (Desenvolvimento)

```javascript
// Code Node - Business Hours Configuration

// ✅ Hardcoded configuration (works in n8n 2.x)
const businessHours = {
  start: "08:00",
  end: "18:00",
  timezone: "America/Sao_Paulo",
  daysOfWeek: [1, 2, 3, 4, 5], // Monday-Friday
  holidays: [] // Empty for now, manage in PostgreSQL later
};

const slotDuration = 60; // minutes
const breakTime = 0; // minutes between slots

return [{
  json: {
    business_hours: businessHours,
    slot_duration: slotDuration,
    break_time: breakTime
  }
}];
```

**Quando Usar**:
- Valores que raramente mudam
- Configurações de desenvolvimento
- Valores não-sensíveis

**Limitações**:
- Requer alteração de código para mudar configuração
- Dificulta ambientes diferentes (dev/staging/prod)

### ✅ SOLUÇÃO 2: PostgreSQL Configuration Table (Produção Recomendado)

```sql
-- Schema de configuração
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Inserir configuração de business hours
INSERT INTO system_config (config_key, config_value, description)
VALUES (
    'business_hours',
    '{
        "start": "08:00",
        "end": "18:00",
        "timezone": "America/Sao_Paulo",
        "daysOfWeek": [1, 2, 3, 4, 5],
        "holidays": []
    }'::jsonb,
    'Business hours configuration for appointment scheduling'
);

-- Inserir API keys (criptografadas)
INSERT INTO system_config (config_key, config_value, description)
VALUES (
    'api_keys',
    '{
        "anthropic": "sk-ant-...",
        "evolution_api": "key123"
    }'::jsonb,
    'External API authentication keys'
);
```

```javascript
// Code Node - Load Configuration from PostgreSQL

// After PostgreSQL node executes query:
// SELECT config_value FROM system_config WHERE config_key = 'business_hours'

const config = $input.first().json.config_value;

return [{
  json: {
    business_hours: config,
    // Now can be used by rest of workflow
  }
};
```

**Vantagens**:
- ✅ Alterável via interface (sem code deploy)
- ✅ Auditável (tracked changes com timestamps)
- ✅ Versionável (histórico em PostgreSQL)
- ✅ Ambiente-específico (diferentes configs por ambiente)

### ✅ SOLUÇÃO 3: n8n Credentials (Para API Keys)

Para **API keys e credenciais sensíveis**, use o sistema nativo de credentials do n8n:

```javascript
// HTTP Request node - Anthropic API
// Credentials: "Anthropic API Key" (criada em n8n Settings → Credentials)

{
  method: 'POST',
  url: 'https://api.anthropic.com/v1/messages',
  authentication: 'predefinedCredentialType',
  nodeCredentialType: 'anthropicApi',

  // n8n automaticamente injeta API key do credential no header:
  // x-api-key: {{credential value}}
}
```

**Credenciais Configuradas no Projeto**:
1. **Anthropic API** - Claude 3.5 Sonnet access
2. **PostgreSQL** - Database connection (host, user, password, database)
3. **Evolution API** - WhatsApp API authentication
4. **Gmail SMTP** - Email sending (smtp.gmail.com:465 SSL/TLS)
5. **Google OAuth2** - Calendar API access

**Vantagens**:
- ✅ Seguro (criptografado no banco do n8n)
- ✅ Centralizado (gerenciar em um lugar)
- ✅ Reutilizável (mesmo credential em múltiplos workflows)
- ✅ Multi-ambiente (diferentes credentials dev/prod)

### 3. PostgreSQL queryReplacement com Expressões `={{ }}`

#### ❌ O QUE NÃO FUNCIONA

```javascript
// ❌ ERRO - queryReplacement NÃO RESOLVE expressões n8n

// PostgreSQL node configuration
{
  operation: 'executeQuery',
  query: `
    INSERT INTO email_queue (conversation_id, template_name, recipient_email)
    VALUES (:conversation_id, :template_name, :recipient_email)
  `,
  queryReplacement: `={
    "conversation_id": "{{ $json.conversation_id }}",
    "template_name": "{{ $json.template_name }}",
    "recipient_email": "{{ $json.recipient_email }}"
  }`
}

// RESULTADO: INSERT INTO email_queue VALUES ([undefined], [undefined], [undefined])
// n8n passa literalmente a string "{{ $json.conversation_id }}" sem resolver
```

#### Nodes Afetados
- **PostgreSQL node**: queryReplacement não processa `={{ }}`
- **MySQL node**: Mesmo problema
- **Outros SQL nodes**: Comportamento similar

#### 🔍 Por Que Não Funciona
- queryReplacement espera JSON literal, não expressões n8n
- n8n não processa `={{ }}` dentro de JSON strings
- Parsing happens antes de expression evaluation

### ✅ SOLUÇÃO: INSERT...SELECT Pattern

**Estratégia**: Usar subquery com SELECT que acessa dados de nodes anteriores

```sql
-- ✅ WF07 V13 - INSERT...SELECT Pattern (FUNCIONA)

INSERT INTO email_queue (
    conversation_id,
    template_name,
    recipient_email,
    recipient_name,
    service_type
)
SELECT
    c.id as conversation_id,
    'confirmation' as template_name,
    (c.collected_data->>'email') as recipient_email,
    (c.collected_data->>'name') as recipient_name,
    c.service_type
FROM conversations c
WHERE c.phone_number = '{{ $json.phone_number }}'
LIMIT 1;
```

#### Por Que INSERT...SELECT Funciona

1. **Expressões apenas em WHERE**: `{{ $json.phone_number }}` está na cláusula WHERE, que n8n processa corretamente
2. **Valores diretos no SELECT**: `'confirmation'` é valor literal, sem expressão
3. **Acesso JSONB**: `collected_data->>'email'` é PostgreSQL nativo, não expressão n8n
4. **Subquery única**: Uma query SELECT resolve múltiplos valores

#### Comparação: VALUES vs INSERT...SELECT

```sql
-- ❌ ANTIGA ABORDAGEM (V12 e anteriores) - NÃO FUNCIONA
INSERT INTO email_queue (conversation_id, template_name)
VALUES ('{{ $json.conversation_id }}', 'confirmation');
-- Resultado: VALUES (undefined, 'confirmation')

-- ✅ NOVA ABORDAGEM (V13+) - FUNCIONA
INSERT INTO email_queue (conversation_id, template_name)
SELECT id, 'confirmation'
FROM conversations
WHERE phone_number = '{{ $json.phone_number }}';
-- Resultado: VALUES (uuid-real, 'confirmation')
```

### ✅ SOLUÇÃO ALTERNATIVA: Code Node Before PostgreSQL

Se INSERT...SELECT não for possível (lógica complexa), use Code node:

```javascript
// Code Node - Prepare INSERT Data

const items = $input.all();

return items.map(item => {
  return {
    json: {
      query: `
        INSERT INTO email_queue (conversation_id, template_name, recipient_email)
        VALUES (
          '${item.json.conversation_id}',
          '${item.json.template_name}',
          '${item.json.recipient_email}'
        )
        RETURNING *;
      `
    }
  };
});
```

**Desvantagens**:
- ⚠️ SQL injection risk (precisa sanitizar inputs)
- ⚠️ Mais verboso que INSERT...SELECT
- ⚠️ Menos performático (múltiplas queries)

**Quando Usar**:
- Lógica condicional complexa
- Transformações de dados antes de INSERT
- Múltiplos INSERTs com diferentes valores

### 4. Outros Bloqueios e Limitações

#### require() de Módulos Nativos

```javascript
// ❌ BLOQUEADO
const crypto = require('crypto');
const util = require('util');

// ✅ PERMITIDO (módulos integrados ao n8n)
// - Nenhum require externo funciona
// - Use funções nativas JavaScript ou PostgreSQL
```

#### process.env

```javascript
// ❌ BLOQUEADO
const currentPath = process.cwd();
const nodeVersion = process.version;

// ✅ ALTERNATIVA
// Use n8n workflow variables ou PostgreSQL
```

#### child_process

```javascript
// ❌ BLOQUEADO
const { exec } = require('child_process');
exec('ls -la');

// ✅ ALTERNATIVA
// Use Execute Command node (com limitações)
// Ou HTTP Request para APIs externas
```

---

## 🛠️ Workarounds Comprovados

### Resumo de Soluções Implementadas

| Limitação | Solução Implementada | Workflow | Versão |
|-----------|----------------------|----------|--------|
| **Filesystem access** | nginx + HTTP Request | WF07 | V9+ |
| **$env variables** | Hardcoded values | WF05 | V7 |
| **queryReplacement** | INSERT...SELECT | WF07 | V13 |
| **Template processing** | nginx + Code node | WF07 | V9+ |
| **Configuration management** | PostgreSQL config table | WF06 | V8+ (planned) |

### Evolution Path: Filesystem Workaround (WF07)

```
V2-V5:  fs.readFileSync() → ❌ BLOQUEADO
V6-V8:  Read Binary File → ❌ Só acessa ~/.n8n/files/
V9:     HTTP Request + nginx container → ✅ FUNCIONA
V10-V12: queryReplacement VALUES → ❌ [undefined]
V13:    INSERT...SELECT pattern → ✅ FUNCIONA
```

### Evolution Path: $env Workaround (WF05)

```
V3-V5:  $env.BUSINESS_HOURS → ❌ BLOQUEADO
V6:     Hardcoded no Code node → ✅ FUNCIONA (temporário)
V7:     Hardcoded final → ✅ PRODUÇÃO
V8:     PostgreSQL config table → ⏳ PLANEJADO
```

---

## 📦 Padrões de Nodes

### Function/Code Node Best Practices

#### Estrutura Padrão de Retorno

```javascript
// ✅ Estrutura correta - compatível com n8n

const items = $input.all();  // Pega TODOS os items do node anterior

return items.map((item, index) => {
  // Processa cada item

  return {
    json: {
      // Seus dados aqui
      id: item.json.id,
      processed: true,
      index: index
    },
    // Opcional: binary data
    binary: item.binary || {}
  };
});
```

#### ❌ Erros Comuns

```javascript
// ❌ ERRO 1: Retornar objeto diretamente
return { id: 1, name: "Test" };
// CORRETO: return [{ json: { id: 1, name: "Test" } }];

// ❌ ERRO 2: Não usar map para múltiplos items
const items = $input.all();
return items[0];  // Perde outros items!
// CORRETO: return items.map(item => ({ json: {...} }));

// ❌ ERRO 3: Modificar item.json diretamente
item.json.newField = "value";  // Pode causar side effects
// CORRETO: return { json: { ...item.json, newField: "value" } };
```

#### Acesso a Dados de Nodes Anteriores

```javascript
// Método 1: Input do node anterior (default)
const previousData = $input.first().json;

// Método 2: Todos os items do node anterior
const allItems = $input.all();

// Método 3: Node específico por nome
const specificNodeData = $node["Node Name"].json;

// Exemplo: WF02 State Machine
const currentStage = $node["Get User Context"].json.state_machine_state;
const userMessage = $input.first().json.message_text;
```

#### Logging e Debugging

```javascript
// ✅ Console.log funciona (aparece em logs do Docker)
console.log('=== DEBUG START ===');
console.log('Current item:', JSON.stringify($input.first().json, null, 2));
console.log('=== DEBUG END ===');

// Ver logs:
// docker logs -f e2bot-n8n-dev | grep "DEBUG"
```

### HTTP Request Node Best Practices

#### Configuração para Workflows Internos

```javascript
// WF02 → WF06 HTTP Request
{
  method: 'POST',
  url: 'http://localhost:5678/webhook/wf06-next-dates',

  // Body como JSON
  bodyParametersJson: `={
    "conversation_id": "{{ $json.conversation_id }}",
    "user_timezone": "America/Sao_Paulo"
  }`,

  // Headers
  headers: {
    'Content-Type': 'application/json'
  },

  // Options
  options: {
    timeout: 30000,  // 30 segundos
    retryOnFail: true,
    maxTries: 3
  }
}
```

#### Error Handling

```javascript
// Continue On Fail: true
{
  continueOnFail: true,  // Workflow continua mesmo se request falhar
  // Item retornado terá { error: {...} }
}

// Code node após HTTP Request para tratar erro
const item = $input.first().json;

if (item.error) {
  console.error('HTTP Request failed:', item.error);
  return [{
    json: {
      success: false,
      error_message: item.error.message || 'HTTP Request failed'
    }
  }];
}

// Sucesso
return [{
  json: {
    success: true,
    data: item
  }
}];
```

### PostgreSQL Node Best Practices

#### Query com RETURNING

```sql
-- ✅ SEMPRE use RETURNING para obter dados inseridos/atualizados

INSERT INTO conversations (phone_number, lead_name, current_state)
VALUES ('5562999999999', 'Bruno Rosa', 'novo')
RETURNING *;

-- Resultado disponível em $json imediatamente
```

#### Row Locking (V111 Critical Fix)

```sql
-- ✅ Use FOR UPDATE SKIP LOCKED para prevenir race conditions

SELECT *
FROM conversations
WHERE phone_number = '{{ $json.phone_number }}'
ORDER BY updated_at DESC
LIMIT 1
FOR UPDATE SKIP LOCKED;
```

**Por Que Isso é Crítico**:
- Previne múltiplas execuções processarem mesma conversa simultaneamente
- `FOR UPDATE`: Trava linha até transaction commit
- `SKIP LOCKED`: Se linha já travada, retorna vazio (não espera)
- Resultado: Apenas UMA execução processa conversa por vez

#### JSONB Operations

```sql
-- Ler valor de JSONB
SELECT
    collected_data->>'name' as lead_name,
    collected_data->>'email' as email
FROM conversations
WHERE phone_number = '{{ $json.phone_number }}';

-- Atualizar JSONB (merge)
UPDATE conversations
SET collected_data = collected_data || '{"phone": "62999999999"}'::jsonb
WHERE phone_number = '{{ $json.phone_number }}';

-- Atualizar JSONB (replace)
UPDATE conversations
SET collected_data = '{"name": "Bruno Rosa", "phone": "62999999999"}'::jsonb
WHERE phone_number = '{{ $json.phone_number }}';
```

### IF Node Best Practices

#### Condições Simples

```javascript
// Verificar se valor existe
{{ $json.next_stage !== undefined }}

// Comparação de string
{{ $json.next_stage === "trigger_wf06_next_dates" }}

// Verificar múltiplos valores
{{ ["estado1", "estado2"].includes($json.current_stage) }}
```

#### Condições com WF06 (V105 Critical Fix)

```yaml
# ❌ ORDEM ERRADA (V104 e anteriores)
Build Update Queries → Check If WF06 → Update Conversation State

# ✅ ORDEM CORRETA (V105+)
Build Update Queries → Update Conversation State → Check If WF06

# Por quê?
# Update State deve executar ANTES de Check If WF06 routing
# Garante que database está atualizado antes de decidir rota
```

### Merge Node Best Practices

#### Merge WF06 Response

```javascript
// Merge node: Combina dados de WF02 + resposta WF06

// Input 1: Estado atual da conversa ($node["State Machine Logic"])
// Input 2: Resposta do WF06 ($node["HTTP Request - Get Next Dates"])

// Mode: Merge By Index (combina items na mesma posição)

// Output:
{
  "conversation_id": "uuid",           // De Input 1
  "current_stage": "show_dates",       // De Input 1
  "next_dates": ["2026-05-01", ...],  // De Input 2 (WF06)
  "formatted_options": "1 (01/05)..." // De Input 2 (WF06)
}
```

#### V113 WF06 Persistence Pattern

```javascript
// Build Update Queries1 (persiste date_suggestions)
// Executa APÓS receber resposta do WF06 next dates

UPDATE conversations
SET
    collected_data = collected_data || jsonb_build_object(
        'wf06_next_dates', '{{ $node["HTTP Request - Get Next Dates"].json.next_dates }}'::jsonb,
        'date_suggestions', '{{ $node["HTTP Request - Get Next Dates"].json.next_dates }}'::text[]
    )
WHERE phone_number = '{{ $json.phone_number }}';
```

---

## 📊 Estrutura de Dados

### Formato de Items n8n

```javascript
// Cada "item" em n8n tem essa estrutura:
{
  json: {
    // Seus dados aqui
    id: 1,
    name: "Test"
  },
  binary: {
    // Dados binários (imagens, arquivos, etc.)
    data: Buffer,
    mimeType: "image/png",
    fileName: "image.png"
  },
  pairedItem: {
    // Tracking de item original (para debugging)
    item: 0,
    input: 1
  }
}
```

### Empty Item Handling (V2.2 Empty Calendar Fix)

```javascript
// ❌ ERRO: n8n com continueOnFail retorna [{ json: {} }], não []
const events = $input.all();
if (events.length === 0) {  // NUNCA é 0!
  console.log("No events");
}

// ✅ CORRETO: Verificar por propriedade significativa
const events = $input.all();
const validEvents = events.filter(item => item.json.id || item.json.start);

if (validEvents.length === 0) {
  console.log("No events (calendar empty)");
  // Processar calendário vazio
}
```

### State Machine Return Structure (V106.1 Fix)

```javascript
// ✅ ESTRUTURA CORRETA - Compatível com n8n workflow

return [{
  json: {
    // OBRIGATÓRIO: response_text (não "response")
    response_text: "Mensagem para o usuário",

    // OBRIGATÓRIO: next_stage (não "nextStage")
    next_stage: "collect_phone",

    // OBRIGATÓRIO: collected_data (não "updateData")
    collected_data: {
      name: "Bruno Rosa",
      phone: "62999999999"
    },

    // OPCIONAL: flags de trigger WF06
    trigger_wf06_next_dates: false,
    trigger_wf06_available_slots: false,

    // OPCIONAL: current_stage para compatibilidade V104
    current_stage: "collect_name"  // Mesmo valor que next_stage atual
  }
}];
```

**Por Que Essa Estrutura é Crítica**:
- `response_text`: Send WhatsApp Response node espera esse nome exato
- `next_stage`: Build Update Queries usa para atualizar state_machine_state
- `collected_data`: PostgreSQL JSONB merge espera esse formato
- `current_stage`: V104+ usa para resolver estado atual (fallback chain)

---

## ✅ Boas Práticas de Desenvolvimento

### 1. Sempre Validar Schema Antes de UPDATE

```javascript
// ❌ ERRO: Tentar atualizar coluna que não existe
UPDATE conversations
SET contact_phone = '{{ $json.phone }}'  -- Coluna não existe!
WHERE phone_number = '{{ $json.phone_number }}';

// ✅ CORRETO: Verificar schema primeiro
// docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
//   -c "\d conversations"

// Só atualizar colunas que EXISTEM no schema
UPDATE conversations
SET collected_data = collected_data || '{"phone": "{{ $json.phone }}"}'::jsonb
WHERE phone_number = '{{ $json.phone_number }}';
```

### 2. Testar Race Conditions

```javascript
// Simular usuário enviando mensagens rápidas

// Teste 1: Mensagens sequenciais rápidas (< 1 segundo intervalo)
// Mensagem 1: "oi"
// Aguardar: 500ms
// Mensagem 2: "1" (agendar)
// Aguardar: 500ms
// Mensagem 3: "Bruno Rosa"

// Sem V111 row locking: Mensagem 2 processa estado obsoleto ❌
// Com V111 row locking: Apenas uma execução por vez ✅
```

### 3. Logging Estruturado

```javascript
// ✅ PADRÃO: Prefixo com versão do workflow

console.log('=== V114 STATE MACHINE START ===');
console.log('V114: conversation_id:', conversationId);
console.log('V114: current_stage:', currentStage);
console.log('V114: user_message:', userMessage);
console.log('=== V114 STATE MACHINE END ===');

// Ver logs:
// docker logs -f e2bot-n8n-dev 2>&1 | grep "V114"
```

### 4. Fallback Chains (V91 State Initialization)

```javascript
// ✅ 4-Level Fallback Chain para resolver estado atual

// Level 1: input.current_stage (de Build Update Queries)
let currentStage = $input.first().json.current_stage;

// Level 2: input.state_machine_state (de PostgreSQL)
if (!currentStage) {
  currentStage = $input.first().json.state_machine_state;
}

// Level 3: input.wf06_current_stage (de WF06 response após Merge)
if (!currentStage) {
  currentStage = $input.first().json.wf06_current_stage;
}

// Level 4: Default to 'greeting'
if (!currentStage) {
  console.log('V91: WARNING - No stage found in inputs, defaulting to greeting');
  currentStage = 'greeting';
}

console.log('V91: RESOLVED currentStage:', currentStage);
```

### 5. Proactive UX > Reactive Validation

```javascript
// ❌ ABORDAGEM REATIVA (V1-V75)
// User: "12345" (telefone inválido)
// Bot: "❌ Telefone inválido! Digite novamente."

// ✅ ABORDAGEM PROATIVA (V76+)
// Bot PRIMEIRO: "Digite seu telefone (ex: 62999999999)"
// User: "12345"
// Bot: "✓ Telefone recebido. Qual seu email?"
// Aceita QUALQUER input, guia ao invés de validar

// Resultado: 100% eliminação de erros de validação
```

### 6. Sempre Retornar response_text Válido

```javascript
// ❌ ERRO: Estado sem response_text
case 'trigger_wf06_next_dates':
  return {
    json: {
      next_stage: 'awaiting_wf06_next_dates',
      trigger_wf06_next_dates: true
      // Falta response_text! ❌
    }
  };

// ✅ CORRETO: TODOS os estados retornam response_text
case 'trigger_wf06_next_dates':
  return [{
    json: {
      response_text: '⏳ Consultando datas disponíveis...',  // ✅
      next_stage: 'awaiting_wf06_next_dates',
      trigger_wf06_next_dates: true
    }
  }];
```

---

## 🐛 Debugging e Troubleshooting

### Logs do Docker

```bash
# Logs em tempo real
docker logs -f e2bot-n8n-dev

# Filtrar por versão específica
docker logs -f e2bot-n8n-dev 2>&1 | grep "V114"

# Filtrar erros
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "ERROR|ERRO"

# Últimas 100 linhas
docker logs --tail 100 e2bot-n8n-dev

# Logs com timestamp
docker logs -f -t e2bot-n8n-dev
```

### Verificar Estado do Banco de Dados

```bash
# Consultar conversa específica
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, state_machine_state, current_state,
             collected_data->>'name' as name
      FROM conversations
      WHERE phone_number = '556281755748';"

# Ver últimas 5 conversas
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, state_machine_state, updated_at
      FROM conversations
      ORDER BY updated_at DESC
      LIMIT 5;"

# Verificar se row locking está ativo (durante execução)
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT pid, state, query
      FROM pg_stat_activity
      WHERE datname = 'e2bot_dev'
        AND query LIKE '%FOR UPDATE%';"
```

### Testar Workflows Isoladamente

```bash
# Testar WF06 diretamente (sem passar por WF02)
curl -X POST http://localhost:5678/webhook/wf06-next-dates \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test-uuid",
    "user_timezone": "America/Sao_Paulo"
  }'

# Expected: JSON com next_dates array

# Testar WF05
curl -X POST http://localhost:5678/webhook/wf05-schedule \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test-uuid",
    "scheduled_date": "2026-05-01",
    "scheduled_time_start": "08:00",
    "scheduled_time_end": "09:00"
  }'

# Expected: Confirmação de agendamento criado
```

### Debugging State Machine Issues

```bash
# 1. Verificar logs do State Machine
docker logs -f e2bot-n8n-dev 2>&1 | grep "STATE MACHINE"

# 2. Verificar estado no banco vs. logs
# Banco:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT state_machine_state FROM conversations WHERE phone_number = '556281755748';"

# Logs (deve corresponder):
# V114: current_stage: [valor do banco]

# 3. Verificar se WF06 foi acionado
docker logs -f e2bot-n8n-dev 2>&1 | grep "trigger_wf06"

# Expected:
# V114: trigger_wf06_next_dates: true  (se deve acionar)
# HTTP Request - Get Next Dates  (se executou)
```

### Common Issues and Solutions

| Issue | Causa Provável | Solução |
|-------|----------------|---------|
| `[undefined]` in database | queryReplacement com `={{ }}` | Use INSERT...SELECT pattern |
| `$env is not defined` | Acesso a variável de ambiente | Use hardcoded ou PostgreSQL config |
| `Access to 'fs' module is not allowed` | require('fs') em Code node | Use HTTP Request + nginx |
| State Machine returns `greeting` when should be other | Estado não resolvido corretamente | Implementar 4-level fallback (V91) |
| Infinite loop showing same dates | Update State AFTER routing check | Reorder: Update BEFORE Check If WF06 (V105) |
| `response_text` is undefined | Estado não retorna response_text | Garantir TODOS estados retornam response_text válido |

---

## 📚 Referências

### Documentação Externa
- **n8n Docs**: https://docs.n8n.io/
- **n8n Breaking Changes 2.0**: https://docs.n8n.io/2-0-breaking-changes/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **Docker Documentation**: https://docs.docker.com/

### Documentação do Projeto
- **Análise n8n Upgrade**: `docs/analysis/system/ANALYSIS_N8N_VERSION_UPGRADE_VS_WORKAROUNDS.md`
- **WF07 V13 Bugfix**: `docs/fix/wf07/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md`
- **WF05 V7 Deployment**: `docs/deployment/wf05/DEPLOY_WF05_V7_HARDCODED_FINAL.md`
- **Setup Email**: `docs/Setups/SETUP_EMAIL.md`
- **Quick Start**: `docs/Setups/QUICKSTART.md`

### Próximos Documentos
- **[02_STATE_MACHINE_PATTERNS.md](02_STATE_MACHINE_PATTERNS.md)** - Padrão de State Machine do WF02
- **[03_DATABASE_PATTERNS.md](03_DATABASE_PATTERNS.md)** - Padrões PostgreSQL e race conditions

---

**Mantido por**: Bruno Rosa & Claude Code
**Data de Atualização**: 2026-04-29
**Status**: ✅ COMPLETO - n8n 2.14.2 Best Practices
**Documento Anterior**: [00_VISAO_GERAL.md](00_VISAO_GERAL.md)
**Próximo Documento**: [02_STATE_MACHINE_PATTERNS.md](02_STATE_MACHINE_PATTERNS.md)
