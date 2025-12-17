# Templates WhatsApp - E2 Soluções Bot

> **Objetivo**: Templates de mensagens WhatsApp para notificações automáticas do sistema

---

## 📋 Visão Geral

Este diretório contém os templates de mensagens WhatsApp utilizados pelo sistema de notificações automatizado da E2 Soluções. Todas as mensagens são enviadas via **Evolution API** através do **Workflow 12 (WhatsApp Notification Sender)**.

---

## 📂 Templates Disponíveis

### 1. `reminder_24h.txt` - Lembrete 24 Horas Antes

**Quando Enviado**: 24 horas antes da visita técnica agendada

**Trigger**: Workflow 06 (Appointment Reminders) executa cron job diário

**Variáveis Necessárias**:
- `{{lead_name}}` - Nome do lead/cliente
- `{{appointment_date}}` - Data da visita (formato: DD/MM/YYYY)
- `{{appointment_time}}` - Horário da visita (formato: HH:MM)
- `{{appointment_location}}` - Endereço completo da visita
- `{{service_name}}` - Nome do serviço (Energia Solar, Subestação, etc.)

**Exemplo de Uso**:
```
🔔 Lembrete de Visita Técnica - E2 Soluções

Olá, João Silva! 👋

Lembramos que sua visita técnica está agendada para amanhã:

📅 Data: 16/12/2025
🕐 Horário: 14:00
📍 Local: Rua das Flores, 123 - Setor Central, Goiânia/GO
🔧 Serviço: Energia Solar Residencial
```

**Função SQL Relacionada**: `create_appointment_reminders()` em `database/appointment_functions.sql:320`

---

### 2. `reminder_2h.txt` - Lembrete 2 Horas Antes

**Quando Enviado**: 2 horas antes da visita técnica agendada

**Trigger**: Workflow 06 (Appointment Reminders) executa cron job a cada 30 minutos

**Variáveis Necessárias**:
- `{{lead_name}}` - Nome do lead/cliente
- `{{appointment_time}}` - Horário da visita (formato: HH:MM)
- `{{appointment_location}}` - Endereço completo da visita
- `{{service_name}}` - Nome do serviço

**Exemplo de Uso**:
```
⏰ Lembrete Urgente - Visita Hoje!

João Silva, sua visita técnica da E2 Soluções é HOJE em breve! ⚡

🕐 Horário: 14:00
📍 Local: Rua das Flores, 123 - Setor Central, Goiânia/GO
🔧 Serviço: Energia Solar Residencial
```

**Função SQL Relacionada**: `create_appointment_reminders()` em `database/appointment_functions.sql:340`

---

### 3. `qualification_complete.txt` - Confirmação de Qualificação

**Quando Enviado**: Quando lead completa qualificação e avança para estágio "scheduling"

**Trigger**: Workflow 02 (AI Agent Conversation) detecta transição de estágio

**Variáveis Necessárias**:
- `{{lead_name}}` - Nome do lead/cliente
- `{{service_name}}` - Nome do serviço solicitado
- `{{phone}}` - Telefone do lead
- `{{email}}` - Email do lead (opcional)

**Exemplo de Uso**:
```
✅ Obrigado por Entrar em Contato!

Olá, João Silva! 👋

Recebemos suas informações sobre Energia Solar Residencial e estamos processando sua solicitação! 🚀

📋 Resumo do Seu Interesse:
🔧 Serviço: Energia Solar Residencial
📞 Contato: (62) 99999-9999
📧 Email: joao.silva@email.com
```

**Workflow Relacionado**: `n8n/workflows/02_ai_agent_conversation.json` (nó "Create Email Notification")

---

## 🔧 Como Usar os Templates

### 1. Integração com Workflow 12

Os templates são carregados dinamicamente pelo **Workflow 12 (WhatsApp Notification Sender)** através da seguinte lógica:

```javascript
// Nó "Format WhatsApp Message" (workflow 12)
const template = $json.category; // 'reminder_24h', 'reminder_2h', 'qualification_complete'
const templatePath = `/templates/whatsapp/${template}.txt`;
const templateContent = $files(templatePath).readAsString();

// Substituir variáveis
let message = templateContent;
const metadata = $json.metadata;

Object.keys(metadata).forEach(key => {
  message = message.replace(new RegExp(`{{${key}}}`, 'g'), metadata[key]);
});
```

### 2. Sintaxe de Variáveis

**Simples**:
```
{{variable_name}}
```

**Condicional** (Handlebars-like):
```
{{#if email}}
Texto se email existir
{{/if}}
```

**IMPORTANTE**: As variáveis devem estar presentes no campo `metadata` JSONB da tabela `notifications`.

### 3. Criação de Notificação WhatsApp

Para criar uma notificação que usa estes templates:

```sql
-- Exemplo: Lembrete 24h
SELECT create_notification(
  123,                          -- lead_id
  456,                          -- appointment_id
  'whatsapp',                   -- notification_type
  'reminder_24h',               -- category (nome do template)
  '5562999999999',              -- recipient (phone com DDI)
  'Lembrete de Visita',         -- subject
  '',                           -- body (será substituído pelo template)
  json_build_object(
    'lead_name', 'João Silva',
    'appointment_date', '16/12/2025',
    'appointment_time', '14:00',
    'appointment_location', 'Rua das Flores, 123',
    'service_name', 'Energia Solar'
  )::jsonb,                     -- metadata com variáveis do template
  5,                            -- priority
  NOW() + INTERVAL '24 hours'  -- scheduled_for
);
```

---

## 📝 Boas Práticas

### 1. Formatação WhatsApp

**Textos em Negrito**:
```
*Texto em Negrito*
```

**Textos em Itálico**:
```
_Texto em Itálico_
```

**Textos Tachados**:
```
~Texto Tachado~
```

**Textos Monoespaçados**:
```
```Código ou Monospace```
```

**Emojis**:
- Use emojis para melhorar legibilidade e engajamento
- Evite excesso (máximo 5-7 por mensagem)
- Prefira emojis universais (✅ ❌ 📅 🕐 📍 ⚡)

### 2. Tamanho das Mensagens

- **Máximo**: 4096 caracteres (limite Evolution API)
- **Recomendado**: 300-500 caracteres para melhor engajamento
- **Crítico**: Mensagens muito longas podem ser truncadas

### 3. Números de Telefone

Formato obrigatório: `55DDDNNNNNNNNN` (DDI + DDD + Número)

**Exemplo Correto**:
- `5562999999999` (Goiânia)
- `5511987654321` (São Paulo)

**Exemplo Errado**:
- `(62) 99999-9999` ❌
- `62999999999` ❌
- `+55 62 99999-9999` ❌

### 4. Variáveis Obrigatórias vs Opcionais

**Obrigatórias**: Sempre devem estar no metadata
```
{{lead_name}}
{{service_name}}
{{phone}}
```

**Opcionais**: Usar com condicional `{{#if}}`
```
{{#if email}}📧 Email: {{email}}{{/if}}
{{#if notes}}💡 Observação: {{notes}}{{/if}}
```

---

## 🔄 Fluxo de Notificação WhatsApp

```
1. Evento Trigger
   ↓
2. create_notification() em PostgreSQL
   ↓
3. Workflow 11 (Notification Orchestrator)
   - Cron: a cada 1 minuto
   - Query: get_pending_notifications(10)
   - Switch: notification_type = 'whatsapp'
   ↓
4. Workflow 12 (WhatsApp Notification Sender)
   - Webhook recebe dados da notificação
   - Valida número de telefone (regex ^55\d{10,11}$)
   - Carrega template baseado em 'category'
   - Substitui variáveis do metadata
   - POST para Evolution API
   ↓
5. Evolution API
   - Envia mensagem via WhatsApp
   - Retorna status (sent/failed)
   ↓
6. update_notification_status()
   - Atualiza status no banco
   - Incrementa retry_count se falha
   - Define sent_at se sucesso
```

---

## 🧪 Como Testar Templates

### Teste Manual via SQL

```sql
-- 1. Criar notificação de teste
SELECT create_notification(
  (SELECT id FROM leads LIMIT 1),  -- Usar lead real
  NULL,
  'whatsapp',
  'reminder_24h',                  -- Template a testar
  '5562999999999',                 -- SEU NÚMERO para teste
  'Teste de Template',
  '',
  json_build_object(
    'lead_name', 'Teste Usuario',
    'appointment_date', '16/12/2025',
    'appointment_time', '14:00',
    'appointment_location', 'Endereço de Teste',
    'service_name', 'Energia Solar'
  )::jsonb,
  5,
  NOW()
);

-- 2. Verificar criação
SELECT * FROM notifications WHERE category = 'reminder_24h' ORDER BY created_at DESC LIMIT 1;

-- 3. Aguardar execução do Workflow 11 (máximo 1 minuto)
-- 4. Verificar status
SELECT status, sent_at, error_message FROM notifications WHERE id = [ID_DA_NOTIFICACAO];

-- 5. Conferir mensagem recebida no WhatsApp
```

### Teste via n8n Interface

1. Abrir n8n: http://localhost:5678
2. Executar **Workflow 12** manualmente:
   - Click em "Execute Workflow"
   - Fornecer JSON de teste no webhook:
   ```json
   {
     "notification_id": 123,
     "recipient": "5562999999999",
     "category": "reminder_24h",
     "metadata": {
       "lead_name": "Teste Usuario",
       "appointment_date": "16/12/2025",
       "appointment_time": "14:00",
       "appointment_location": "Endereço de Teste",
       "service_name": "Energia Solar"
     }
   }
   ```
3. Verificar resultado na interface n8n
4. Conferir mensagem recebida no WhatsApp

---

## 🚨 Troubleshooting

### Mensagem não recebida

**Verificar**:
1. Status da notificação no banco:
   ```sql
   SELECT status, error_message, retry_count FROM notifications WHERE id = [ID];
   ```

2. Evolution API está conectada:
   ```bash
   curl $EVOLUTION_API_URL/instance/fetchInstances -H "apikey: $EVOLUTION_API_KEY"
   ```

3. Número está correto (formato `55DDDNNNNNNNNN`)

4. Workflow 11 está ativo (polling a cada 1 minuto)

5. Logs do Evolution API:
   ```bash
   docker logs evolution-api
   ```

### Template não encontrado

**Erro**: "Template file not found"

**Solução**:
- Verificar nome do arquivo corresponde ao `category` da notificação
- Path esperado: `/templates/whatsapp/{category}.txt`
- Verificar permissões de leitura do arquivo

### Variáveis não substituídas

**Sintoma**: Mensagem enviada com `{{variable_name}}` literalmente

**Solução**:
- Verificar variável está presente no `metadata` JSONB
- Verificar nome da variável está correto (case-sensitive)
- Verificar sintaxe: `{{variable}}` não `${variable}` ou `{variable}`

### Limite de caracteres excedido

**Erro**: "Message exceeds 4096 characters"

**Solução**:
- Reduzir tamanho do template
- Remover informações não essenciais
- Dividir em 2 mensagens separadas (criar 2 notificações)

---

## 📚 Referências

- **Evolution API Docs**: https://doc.evolution-api.com
- **WhatsApp Formatting**: https://faq.whatsapp.com/539178204879377
- **Workflow 11 (Orchestrator)**: `n8n/workflows/11_notification_orchestrator.json`
- **Workflow 12 (WhatsApp Sender)**: `n8n/workflows/12_whatsapp_notification_sender.json`
- **Database Functions**: `database/notification_functions.sql`
- **Schema**: `database/notifications_schema.sql`

---

**Última Atualização**: 2025-12-15
**Sprint**: 1.3 - Sistema de Notificações Multi-Canal
**Maintainer**: E2 Soluções Dev Team
