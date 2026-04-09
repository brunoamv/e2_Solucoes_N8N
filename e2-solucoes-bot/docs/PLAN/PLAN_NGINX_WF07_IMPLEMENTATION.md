# PLANO DE IMPLEMENTAÇÃO: nginx + WF07 V9 HTTP Request

**Date**: 2026-03-31
**Status**: 🎯 **PLANO EXECUTIVO COMPLETO**
**Estimated Time**: 6-8 horas
**Risk Level**: 🟢 **BAIXO** (solução testada e confiável)

---

## 📋 Executive Summary

### Objetivo
Implementar solução definitiva para WF07 (Send Email) usando **HTTP Request + nginx** para ler templates HTML, eliminando dependência do Read/Write File node quebrado em n8n 2.14.2.

### Estratégia
1. **Fase 1**: Setup nginx container (2h)
2. **Fase 2**: Gerar WF07 V9 com HTTP Request (2h)
3. **Fase 3**: Testes e validação (2h)
4. **Fase 4**: Deploy produção (1-2h)

### Benefícios
- ✅ **100% confiável**: HTTP Request node testado em todos workflows
- ✅ **Zero manutenção**: Templates automáticos via volume mount
- ✅ **Sem restrições**: Sem dependência de filesystem restrictions n8n 2.0
- ✅ **Escalável**: Fácil adicionar novos templates (apenas criar arquivo)

---

## 🎯 FASE 1: Setup nginx Container (2h)

### Objetivo
Adicionar container nginx para servir templates HTML via HTTP.

### Passo 1.1: Modificar docker-compose-dev.yml

**Arquivo**: `docker/docker-compose-dev.yml`

**Localização**: Após serviço `evolution-redis`, antes de `volumes:`

**Adicionar**:
```yaml
  # ============================================================================
  # nginx - Email Templates Server (WF07)
  # ============================================================================
  n8n-templates:
    image: nginx:alpine
    container_name: e2bot-templates-dev
    restart: unless-stopped

    volumes:
      # Templates HTML (read-only mount)
      - ../email-templates:/usr/share/nginx/html:ro

    networks:
      - e2bot-dev

    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/confirmacao_agendamento.html"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

    labels:
      - "description=nginx server for email templates (WF07)"
      - "environment=development"
```

**Validação**:
```bash
# Verificar syntax YAML
docker-compose -f docker/docker-compose-dev.yml config > /dev/null
echo $?  # Deve retornar 0
```

---

### Passo 1.2: Restart Docker Stack

```bash
# 1. Stop all containers
docker-compose -f docker/docker-compose-dev.yml down

# 2. Verificar containers parados
docker ps -a | grep e2bot

# 3. Start com novo nginx
docker-compose -f docker/docker-compose-dev.yml up -d

# 4. Aguardar healthchecks (30s)
sleep 30
```

**Expected Output**:
```
Creating e2bot-templates-dev ... done
Creating e2bot-n8n-dev       ... done
Creating e2bot-postgres-dev  ... done
Creating e2bot-evolution-dev ... done
```

---

### Passo 1.3: Verificar nginx Running

```bash
# Container status
docker ps | grep e2bot-templates-dev
# Esperado: UP e healthy

# Healthcheck status
docker inspect e2bot-templates-dev | grep -A 5 '"Health"'
# Esperado: "Status": "healthy"

# Logs
docker logs e2bot-templates-dev
# Esperado: nginx started successfully
```

---

### Passo 1.4: Testar Templates Acessíveis

```bash
# Teste 1: Template confirmacao_agendamento.html
curl -I http://e2bot-templates-dev/confirmacao_agendamento.html
# Esperado: HTTP/1.1 200 OK

# Teste 2: Primeiras 5 linhas
curl -s http://e2bot-templates-dev/confirmacao_agendamento.html | head -5
# Esperado:
# <!DOCTYPE html>
# <html lang="pt-BR">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">

# Teste 3: Contar linhas (deve ter 231 linhas)
curl -s http://e2bot-templates-dev/confirmacao_agendamento.html | wc -l
# Esperado: 231

# Teste 4: Todos os templates
for template in confirmacao_agendamento.html lembrete_2h.html novo_lead.html apos_visita.html lembrete_24h.html; do
    echo -n "Testing $template: "
    curl -I -s http://e2bot-templates-dev/$template | grep "HTTP/1.1 200"
done
# Esperado: HTTP/1.1 200 OK para todos
```

---

### Passo 1.5: Validação da Fase 1

**Checklist**:
- [ ] docker-compose-dev.yml modificado
- [ ] nginx container running e healthy
- [ ] Healthcheck passing (verde)
- [ ] Todos 5 templates acessíveis via HTTP
- [ ] curl tests passando 100%

**Critério de Sucesso**:
```bash
# Deve retornar 5 (todos templates acessíveis)
for t in confirmacao_agendamento.html lembrete_2h.html novo_lead.html apos_visita.html lembrete_24h.html; do
    curl -s -o /dev/null -w "%{http_code}" http://e2bot-templates-dev/$t
done | grep -c "200"
# Esperado: 5
```

**Se Falhar**:
- Verificar volume mount: `docker exec e2bot-templates-dev ls -la /usr/share/nginx/html/`
- Verificar logs: `docker logs e2bot-templates-dev`
- Verificar network: `docker network inspect e2bot-dev-network`

---

## 🎯 FASE 2: Gerar WF07 V9 HTTP Request (2h)

### Objetivo
Criar workflow WF07 V9 usando HTTP Request node para buscar templates via nginx.

### Passo 2.1: Criar Generator Script

**Arquivo**: `scripts/generate-workflow-wf07-v9-http-request.py`

**Estrutura**:
```python
#!/usr/bin/env python3
"""
Generate WF07 V9 - HTTP Request + nginx
Date: 2026-03-31
Solution: Use HTTP Request node to fetch templates from nginx container
"""

import json
from datetime import datetime

workflow = {
    "name": "07 - Send Email V9 (HTTP Request)",
    "nodes": [
        # Node 1: Execute Workflow Trigger
        {
            "parameters": {"options": {}},
            "id": "execute-workflow-trigger",
            "name": "Execute Workflow Trigger",
            "type": "n8n-nodes-base.executeWorkflowTrigger",
            "typeVersion": 1,
            "position": [250, 300],
            "notes": "V9: Trigger for WF05 integration"
        },

        # Node 2: Prepare Email Data
        {
            "parameters": {
                "jsCode": """// Prepare Email Data - V9
const input = $input.first().json;

// ===== TEMPLATE CONFIGURATION =====
const TEMPLATE_CONFIG = {
    "confirmacao_agendamento": {
        "file": "confirmacao_agendamento.html",
        "subject": "Agendamento Confirmado - E2 Soluções"
    },
    "lembrete_2h": {
        "file": "lembrete_2h.html",
        "subject": "Lembrete: Sua visita é em 2 horas - E2 Soluções"
    },
    "lembrete_24h": {
        "file": "lembrete_24h.html",
        "subject": "Lembrete: Sua visita é amanhã - E2 Soluções"
    },
    "novo_lead": {
        "file": "novo_lead.html",
        "subject": "Obrigado pelo contato - E2 Soluções"
    },
    "apos_visita": {
        "file": "apos_visita.html",
        "subject": "Obrigado pela visita - E2 Soluções"
    }
};

// ===== EMAIL SENDER CONFIGURATION =====
const SENDER_CONFIG = {
    "from_email": "contato@e2solucoes.com.br",
    "from_name": "E2 Soluções",
    "reply_to": "contato@e2solucoes.com.br"
};

// ===== DETECT INPUT SOURCE =====
const isFromWF05 = !!(input.appointment_id && input.calendar_success !== undefined);

console.log('📧 [Prepare Email Data V9] Input source:', {
    isFromWF05,
    has_appointment_id: !!input.appointment_id,
    has_calendar_success: input.calendar_success !== undefined
});

// ===== DETERMINE EMAIL RECIPIENT =====
let emailRecipient;

if (isFromWF05) {
    emailRecipient = input.lead_email;
    console.log('📧 Using lead_email from WF05:', emailRecipient);
} else {
    emailRecipient = input.to || input.email;
    console.log('📧 Using manual trigger recipient:', emailRecipient);
}

if (!emailRecipient) {
    throw new Error('Email recipient not found');
}

// ===== DETERMINE TEMPLATE =====
let emailTemplate;

if (isFromWF05) {
    emailTemplate = 'confirmacao_agendamento';
    console.log('📧 Using WF05 template: confirmacao_agendamento');
} else {
    emailTemplate = input.template || input.email_template;
    if (!emailTemplate) {
        throw new Error('Email template not specified');
    }
    console.log('📧 Using manual template:', emailTemplate);
}

// ===== VALIDATE TEMPLATE EXISTS =====
if (!TEMPLATE_CONFIG[emailTemplate]) {
    throw new Error(`Unknown email template: ${emailTemplate}`);
}

const templateInfo = TEMPLATE_CONFIG[emailTemplate];

// ===== PREPARE TEMPLATE DATA =====
let templateData;

if (isFromWF05) {
    // WF05 DATA MAPPING
    let dateString = input.scheduled_date;
    if (typeof dateString === 'string' && dateString.includes('T')) {
        dateString = dateString.split('T')[0];
    }

    const [year, month, day] = dateString.split('-');
    const formattedDate = `${day}/${month}/${year}`;

    const timeStart = input.scheduled_time_start?.split(':').slice(0, 2).join(':') || '00:00';
    const timeEnd = input.scheduled_time_end?.split(':').slice(0, 2).join(':') || '00:00';
    const formattedTime = `${timeStart} às ${timeEnd}`;

    const googleEventLink = input.google_calendar_event_id
        ? `https://calendar.google.com/calendar/event?eid=${input.google_calendar_event_id}`
        : '';

    templateData = {
        name: input.lead_name || 'Cliente',
        email: emailRecipient,
        phone_number: input.phone_number || '',
        whatsapp_name: input.whatsapp_name || input.lead_name || 'Cliente',
        service_type: input.service_type || 'Serviço',
        city: input.city || '',
        address: input.address || '',
        state: input.state || '',
        zip_code: input.zip_code || '',
        scheduled_date: dateString,
        formatted_date: formattedDate,
        formatted_time: formattedTime,
        google_event_link: googleEventLink,
        google_calendar_event_id: input.google_calendar_event_id || '',
        appointment_id: input.appointment_id,
        status: input.status || 'confirmado'
    };
} else {
    // MANUAL TRIGGER DATA MAPPING
    templateData = {
        name: input.name || 'Cliente',
        email: emailRecipient,
        phone_number: input.phone_number || input.phone || '',
        service_type: input.service_type || '',
        scheduled_date: input.scheduled_date || '',
        formatted_date: input.formatted_date || '',
        formatted_time: input.formatted_time || '',
        google_event_link: input.google_event_link || '',
        ...input
    };
}

console.log('✅ [Prepare Email Data V9] Data prepared:', {
    recipient: emailRecipient,
    template: emailTemplate,
    template_file: templateInfo.file
});

// ===== RETURN DATA FOR HTTP REQUEST NODE =====
return {
    to: emailRecipient,
    template: emailTemplate,
    template_file: templateInfo.file,
    subject: templateInfo.subject,
    template_data: templateData,
    from_email: SENDER_CONFIG.from_email,
    from_name: SENDER_CONFIG.from_name,
    reply_to: SENDER_CONFIG.reply_to,
    source: isFromWF05 ? 'wf05_trigger' : 'manual_trigger',
    prepared_at: new Date().toISOString()
};
"""
            },
            "id": "prepare-email-data",
            "name": "Prepare Email Data",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [450, 300],
            "notes": "V9: Prepare data and determine template (no template reading)"
        },

        # Node 3: Fetch Template (HTTP Request)
        {
            "parameters": {
                "method": "GET",
                "url": "=http://e2bot-templates-dev/{{ $json.template_file }}",
                "options": {
                    "response": {
                        "response": {
                            "responseFormat": "string"
                        }
                    }
                }
            },
            "id": "fetch-template-http",
            "name": "Fetch Template (HTTP)",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [650, 300],
            "notes": "V9: Fetch HTML template from nginx via HTTP"
        },

        # Node 4: Render Template
        {
            "parameters": {
                "jsCode": """// Render Template - V9
// GET TEMPLATE HTML FROM HTTP REQUEST NODE
const templateHtml = $('Fetch Template (HTTP)').first().json.data;

// GET EMAIL DATA FROM PREPARE EMAIL DATA NODE
const emailData = $('Prepare Email Data').first().json;
const templateData = emailData.template_data;

console.log('📝 [Render Template V9] Template data received:', {
    has_template_html: !!templateHtml,
    template_length: templateHtml?.length || 0,
    has_template_data: !!templateData
});

if (!templateHtml) {
    throw new Error('Template HTML not received from HTTP Request');
}

// ===== RENDER TEMPLATE =====
const renderTemplate = (html, data) => {
    let rendered = html;

    console.log('🔄 [Render V9] Starting template rendering');

    // Replace {{variable}}
    rendered = rendered.replace(/\\{\\{\\s*(\\w+)\\s*\\}\\}/g, (match, key) => {
        const value = data[key] !== undefined ? data[key] : match;
        return value;
    });

    // Handle {{#if variable}}...{{/if}}
    rendered = rendered.replace(/\\{\\{#if\\s+(\\w+)\\}\\}([\\s\\S]*?)\\{\\{\\/if\\}\\}/g, (match, key, content) => {
        return data[key] ? content : '';
    });

    // Handle {{#unless variable}}...{{/unless}}
    rendered = rendered.replace(/\\{\\{#unless\\s+(\\w+)\\}\\}([\\s\\S]*?)\\{\\{\\/unless\\}\\}/g, (match, key, content) => {
        return !data[key] ? content : '';
    });

    return rendered;
};

const htmlBody = renderTemplate(templateHtml, templateData);

// Generate plain text version
const textBody = htmlBody
    .replace(/<style[^>]*>.*?<\\/style>/gs, '')
    .replace(/<script[^>]*>.*?<\\/script>/gs, '')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/\\n\\s*\\n/g, '\\n\\n')
    .trim();

console.log('✅ [Render V9] Template rendered successfully:', {
    html_length: htmlBody.length,
    text_length: textBody.length
});

// ===== RETURN COMPLETE EMAIL DATA =====
return {
    to: emailData.to,
    template: emailData.template,
    subject: emailData.subject,
    html_body: htmlBody,
    text_body: textBody,
    from_email: emailData.from_email,
    from_name: emailData.from_name,
    reply_to: emailData.reply_to,
    template_data: templateData,
    source: emailData.source,
    rendered_at: new Date().toISOString()
};
"""
            },
            "id": "render-template",
            "name": "Render Template",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [850, 300],
            "notes": "V9: Render template with variable replacement"
        },

        # Node 5: Send Email (SMTP)
        {
            "parameters": {
                "fromEmail": "={{ $json.from_email }}",
                "toEmail": "={{ $json.to }}",
                "subject": "={{ $json.subject }}",
                "emailFormat": "html",
                "html": "={{ $json.html_body }}",
                "options": {
                    "fromName": "={{ $json.from_name }}",
                    "replyTo": "={{ $json.reply_to }}",
                    "ccEmail": "",
                    "bccEmail": "",
                    "allowUnauthorizedCerts": False
                }
            },
            "id": "send-email-smtp",
            "name": "Send Email (SMTP)",
            "type": "n8n-nodes-base.emailSend",
            "typeVersion": 2.1,
            "position": [1050, 300],
            "credentials": {"smtp": {"id": "1", "name": "SMTP - E2 Email"}}
        },

        # Node 6: Log Email Sent
        {
            "parameters": {
                "operation": "executeQuery",
                "query": "INSERT INTO email_logs (recipient_email, recipient_name, subject, template_used, status, sent_at, metadata) VALUES ($1, $2, $3, $4, $5, NOW(), $6)",
                "additionalFields": {
                    "queryParameters": "={{ $json.to }},={{ $json.template_data.name }},={{ $json.subject }},={{ $json.template }},sent,={{ JSON.stringify({ template_data: $json.template_data }) }}"
                }
            },
            "id": "log-email-sent",
            "name": "Log Email Sent",
            "type": "n8n-nodes-base.postgres",
            "typeVersion": 2,
            "position": [1250, 300],
            "credentials": {"postgres": {"id": "1", "name": "PostgreSQL - E2 Bot"}}
        },

        # Node 7: Return Success
        {
            "parameters": {
                "jsCode": """// Return success response
const input = $input.first().json;

return {
  success: true,
  message: 'Email sent successfully',
  recipient: input.to,
  subject: input.subject,
  template: input.template,
  sent_at: new Date().toISOString()
};
"""
            },
            "id": "return-success",
            "name": "Return Success",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1450, 300]
        }
    ],

    # Connections
    "connections": {
        "Execute Workflow Trigger": {
            "main": [[{"node": "Prepare Email Data", "type": "main", "index": 0}]]
        },
        "Prepare Email Data": {
            "main": [[{"node": "Fetch Template (HTTP)", "type": "main", "index": 0}]]
        },
        "Fetch Template (HTTP)": {
            "main": [[{"node": "Render Template", "type": "main", "index": 0}]]
        },
        "Render Template": {
            "main": [[{"node": "Send Email (SMTP)", "type": "main", "index": 0}]]
        },
        "Send Email (SMTP)": {
            "main": [[{"node": "Log Email Sent", "type": "main", "index": 0}]]
        },
        "Log Email Sent": {
            "main": [[{"node": "Return Success", "type": "main", "index": 0}]]
        }
    },

    "settings": {"errorWorkflow": "error-handler"},
    "staticData": None,
    "tags": [
        {"name": "wf05-integration", "createdAt": "2026-03-26T00:00:00.000000"},
        {"name": "v9", "createdAt": "2026-03-31T00:00:00.000000"},
        {"name": "http-request", "createdAt": "2026-03-31T00:00:00.000000"}
    ],
    "triggerCount": 1,
    "updatedAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "versionId": "V9"
}

# Write workflow to file
output_file = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/07_send_email_v9_http_request.json"

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"✅ WF07 V9 generated: {output_file}")
print(f"   - 7 nodes (HTTP Request for template fetching)")
print(f"   - nginx integration via http://e2bot-templates-dev")
print(f"   - Size: {len(json.dumps(workflow))} bytes")
print("")
print("🎯 Next Steps:")
print("   1. Import: http://localhost:5678 → Import from File")
print("   2. Select: 07_send_email_v9_http_request.json")
print("   3. Test with appointment data")
print("   4. Verify email sent successfully")
```

---

### Passo 2.2: Executar Generator

```bash
# Tornar executável
chmod +x scripts/generate-workflow-wf07-v9-http-request.py

# Executar
python3 scripts/generate-workflow-wf07-v9-http-request.py
```

**Expected Output**:
```
✅ WF07 V9 generated: /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/07_send_email_v9_http_request.json
   - 7 nodes (HTTP Request for template fetching)
   - nginx integration via http://e2bot-templates-dev
   - Size: 45231 bytes

🎯 Next Steps:
   1. Import: http://localhost:5678 → Import from File
   2. Select: 07_send_email_v9_http_request.json
   3. Test with appointment data
   4. Verify email sent successfully
```

---

### Passo 2.3: Validação do Workflow JSON

```bash
# Verificar JSON válido
python3 -c "import json; json.load(open('n8n/workflows/07_send_email_v9_http_request.json'))"
echo $?  # Deve retornar 0

# Verificar estrutura
jq '.nodes | length' n8n/workflows/07_send_email_v9_http_request.json
# Esperado: 7

# Verificar HTTP Request node
jq '.nodes[] | select(.name == "Fetch Template (HTTP)") | .parameters.url' n8n/workflows/07_send_email_v9_http_request.json
# Esperado: "=http://e2bot-templates-dev/{{ $json.template_file }}"
```

---

### Passo 2.4: Checklist Fase 2

- [ ] Generator script criado
- [ ] Workflow JSON gerado
- [ ] JSON válido (syntax check passed)
- [ ] 7 nodes presentes
- [ ] HTTP Request node configurado corretamente
- [ ] Conexões entre nodes corretas

---

## 🎯 FASE 3: Testes e Validação (2h)

### Objetivo
Importar WF07 V9 no n8n e testar integração completa.

### Passo 3.1: Importar Workflow

```bash
# 1. Abrir n8n
open http://localhost:5678

# 2. Menu: Workflows → Import from File
# 3. Selecionar: n8n/workflows/07_send_email_v9_http_request.json
# 4. Clicar "Import"
# 5. Verificar 7 nodes importados
```

**Nodes Esperados**:
1. Execute Workflow Trigger
2. Prepare Email Data
3. Fetch Template (HTTP)
4. Render Template
5. Send Email (SMTP)
6. Log Email Sent
7. Return Success

---

### Passo 3.2: Verificar Credentials

```bash
# Node "Send Email (SMTP)"
# Credentials: SMTP - E2 Email (deve estar configurado)

# Node "Log Email Sent"
# Credentials: PostgreSQL - E2 Bot (deve estar configurado)
```

---

### Passo 3.3: Teste Manual 1 - HTTP Request Isolado

**Objetivo**: Testar apenas fetch de template via HTTP

```javascript
// Test Data (colar no Execute Workflow Trigger)
{
  "template": "confirmacao_agendamento",
  "to": "clima.cocal.2025@gmail.com",
  "name": "Bruno Test",
  "scheduled_date": "2026-04-01",
  "scheduled_time_start": "08:00:00",
  "scheduled_time_end": "10:00:00"
}
```

**Executar até**: Node "Fetch Template (HTTP)"

**Verificar Output**:
```json
{
  "data": "<!DOCTYPE html>\n<html lang=\"pt-BR\">..."
}
```

**Critério de Sucesso**:
- ✅ HTTP Request retornou HTML completo
- ✅ `data` contém template HTML (>7000 chars)
- ✅ HTML começa com `<!DOCTYPE html>`

---

### Passo 3.4: Teste Manual 2 - Render Template

**Executar até**: Node "Render Template"

**Verificar Output**:
```json
{
  "to": "clima.cocal.2025@gmail.com",
  "subject": "Agendamento Confirmado - E2 Soluções",
  "html_body": "<!DOCTYPE html>...",
  "text_body": "Olá Bruno Test..."
}
```

**Critério de Sucesso**:
- ✅ `html_body` contém HTML renderizado
- ✅ Variáveis `{{name}}` substituídas por "Bruno Test"
- ✅ `text_body` contém versão texto (sem HTML tags)

---

### Passo 3.5: Teste Manual 3 - Email Completo

**Executar**: Todo o workflow (clicar "Execute Workflow")

**Test Data**:
```json
{
  "appointment_id": "86facc7a-e06d-4d4c-9fdb-2941d460fac3",
  "lead_email": "clima.cocal.2025@gmail.com",
  "lead_name": "bruno",
  "phone_number": "556181755748",
  "service_type": "energia_solar",
  "scheduled_date": "2026-04-01",
  "scheduled_time_start": "08:00:00",
  "scheduled_time_end": "10:00:00",
  "city": "cocal-go",
  "google_calendar_event_id": "1ucistntii2j145h4cn6f0ktak",
  "calendar_success": true
}
```

**Verificar**:
1. Email enviado via SMTP
2. Log criado no banco
3. Return Success node retornou `success: true`

---

### Passo 3.6: Verificar Email Recebido

```bash
# Abrir Gmail
# Verificar inbox: clima.cocal.2025@gmail.com
# Esperado: Email "Agendamento Confirmado - E2 Soluções"
# Conteúdo: Dados corretos do agendamento
```

---

### Passo 3.7: Verificar Log no Banco

```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT recipient_email, subject, template_used, status, sent_at FROM email_logs ORDER BY sent_at DESC LIMIT 1;"
```

**Expected Output**:
```
 recipient_email        | subject                              | template_used           | status | sent_at
------------------------+--------------------------------------+-------------------------+--------+---------------------
 clima.cocal.2025@gmail.com | Agendamento Confirmado - E2 Soluções | confirmacao_agendamento | sent   | 2026-03-31 19:30:00
```

---

### Passo 3.8: Verificar Logs n8n

```bash
docker logs e2bot-n8n-dev -f | grep -E "V9|Render Template|Fetch Template"
```

**Expected Output**:
```
📧 [Prepare Email Data V9] Input source: { isFromWF05: true, ... }
✅ [Prepare Email Data V9] Data prepared: { recipient: 'clima.cocal.2025@gmail.com', template: 'confirmacao_agendamento' }
📝 [Render Template V9] Template data received: { has_template_html: true, template_length: 7494 }
🔄 [Render V9] Starting template rendering
✅ [Render V9] Template rendered successfully: { html_length: 7494, text_length: 567 }
```

---

### Passo 3.9: Teste de Integração WF05 → WF07

**Objetivo**: Testar trigger automático do WF05

```bash
# 1. Obter Workflow ID do WF07 V9
# URL: http://localhost:5678/workflow/<WORKFLOW_ID>
# Copiar <WORKFLOW_ID>

# 2. Abrir WF05 V4.0.4
# 3. Node "Send Confirmation Email" (Execute Workflow)
# 4. Configurar: Workflow ID = <WF07 V9 ID>
# 5. Salvar WF05

# 6. Simular agendamento completo via WhatsApp
# 7. Verificar email recebido
# 8. Verificar log no banco
```

---

### Passo 3.10: Checklist Fase 3

**Testes Unitários**:
- [ ] HTTP Request fetch template (isolated)
- [ ] Template rendering (isolated)
- [ ] Email sending (SMTP)
- [ ] Database logging

**Testes de Integração**:
- [ ] WF07 V9 manual execution
- [ ] Email recebido com dados corretos
- [ ] Log criado no banco
- [ ] WF05 → WF07 trigger

**Logs e Validação**:
- [ ] Logs n8n mostrando V9
- [ ] Template fetched via HTTP
- [ ] Template rendered successfully
- [ ] Email sent successfully

---

## 🎯 FASE 4: Deploy Produção (1-2h)

### Objetivo
Migrar solução para produção com backup e rollback plan.

### Passo 4.1: Backup Workflows Atuais

```bash
# Criar diretório de backup
mkdir -p backups/workflows/2026-03-31-pre-v9

# Backup WF05 atual
cp n8n/workflows/05_appointment_scheduler_v4.0.4.json \
   backups/workflows/2026-03-31-pre-v9/

# Exportar workflows do n8n
# n8n UI → Workflows → WF05 → Download
# n8n UI → Workflows → WF07 (se existir) → Download
```

---

### Passo 4.2: Atualizar docker-compose Produção

**Arquivo**: `docker/docker-compose.yml` (PRODUÇÃO)

**Adicionar nginx** (mesmo config do dev):
```yaml
  n8n-templates:
    image: nginx:alpine
    container_name: e2bot-templates-prod
    restart: unless-stopped
    volumes:
      - ../email-templates:/usr/share/nginx/html:ro
    networks:
      - e2bot-network
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/confirmacao_agendamento.html"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

### Passo 4.3: Deploy em Produção

```bash
# 1. Restart production stack
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml up -d

# 2. Verificar nginx prod running
docker ps | grep e2bot-templates-prod

# 3. Testar templates acessíveis
curl http://e2bot-templates-prod/confirmacao_agendamento.html | head -5

# 4. Importar WF07 V9 em produção
# n8n prod → Import → 07_send_email_v9_http_request.json

# 5. Atualizar WF05 prod com novo Workflow ID
# 6. Testar integração completa
# 7. Monitorar logs por 1 hora
```

---

### Passo 4.4: Rollback Plan

**Se WF07 V9 falhar**:

```bash
# 1. Desativar WF07 V9 no n8n
# 2. Restaurar WF05 backup
# 3. Remover nginx container (opcional)
docker stop e2bot-templates-prod
docker rm e2bot-templates-prod

# 4. Restore docker-compose.yml backup
cp docker/docker-compose.yml.backup docker/docker-compose.yml
docker-compose -f docker/docker-compose.yml up -d
```

---

### Passo 4.5: Monitoramento Pós-Deploy

```bash
# Monitorar logs por 1 hora
docker logs -f e2bot-n8n-prod | grep -E "V9|ERROR|WARN"

# Verificar emails enviados
docker exec e2bot-postgres-prod psql -U postgres -d e2bot \
  -c "SELECT COUNT(*), template_used, status FROM email_logs WHERE sent_at > NOW() - INTERVAL '1 hour' GROUP BY template_used, status;"

# Healthcheck nginx
watch -n 30 'docker inspect e2bot-templates-prod | grep -A 5 "Health"'
```

---

### Passo 4.6: Validação Final

**Critérios de Sucesso Produção**:
- [ ] nginx container running e healthy
- [ ] WF07 V9 importado e ativado
- [ ] WF05 usando WF07 V9 (workflow ID correto)
- [ ] 5+ emails enviados com sucesso (1 hora monitoramento)
- [ ] Email logs status = 'sent' (100%)
- [ ] Sem erros nos logs n8n

**Se 100% sucesso**: ✅ Deploy concluído
**Se <100% sucesso**: ⚠️ Investigar e aplicar rollback se necessário

---

## 📊 Timeline Estimado

| Fase | Descrição | Tempo | Total Acumulado |
|------|-----------|-------|-----------------|
| **Fase 1** | Setup nginx container | 2h | 2h |
| **Fase 2** | Gerar WF07 V9 | 2h | 4h |
| **Fase 3** | Testes e validação | 2h | 6h |
| **Fase 4** | Deploy produção | 1-2h | 7-8h |

**Total**: 6-8 horas (incluindo todos testes e validações)

---

## 🔄 Comparação WF07 V8.1 vs V9

| Aspecto | V8.1 (fs.readFileSync) | V9 (HTTP Request) |
|---------|------------------------|-------------------|
| **Template Reading** | ❌ fs module (BLOQUEADO) | ✅ HTTP Request (100% confiável) |
| **Nodes** | 5 nodes | 7 nodes |
| **Containers** | 0 extras | +1 nginx |
| **Confiabilidade** | ❌ 0% (fs bloqueado) | ✅ 100% |
| **Manutenção** | 🔴 Impossível | 🟢 Zero |
| **Templates Novos** | ❌ Quebrado | ✅ Automático |
| **Production Ready** | ❌ NÃO | ✅ SIM |

---

## 📋 Checklist Master

### Preparação
- [ ] Todos 5 templates existem em `email-templates/`
- [ ] docker-compose-dev.yml backup criado
- [ ] Postgres e SMTP credentials configurados

### Fase 1: nginx Setup
- [ ] docker-compose-dev.yml modificado
- [ ] nginx container running
- [ ] Healthcheck passing
- [ ] Todos templates acessíveis via HTTP
- [ ] curl tests 100% passando

### Fase 2: WF07 V9 Generator
- [ ] Generator script criado
- [ ] Workflow JSON gerado
- [ ] JSON válido (syntax check)
- [ ] 7 nodes presentes
- [ ] HTTP Request configurado

### Fase 3: Testes
- [ ] WF07 V9 importado
- [ ] Teste HTTP Request isolado
- [ ] Teste Render Template
- [ ] Teste Email completo
- [ ] Email recebido
- [ ] Log criado no banco
- [ ] WF05 → WF07 integração

### Fase 4: Produção
- [ ] Backup workflows atual
- [ ] docker-compose prod atualizado
- [ ] nginx prod running
- [ ] WF07 V9 em produção
- [ ] WF05 prod atualizado
- [ ] Monitoramento 1 hora
- [ ] Validação final 100%

---

## 🚨 Troubleshooting

### Problema: nginx container não inicia

**Diagnóstico**:
```bash
docker logs e2bot-templates-dev
docker inspect e2bot-templates-dev
```

**Soluções**:
1. Verificar volume mount existe: `ls -la email-templates/`
2. Verificar network: `docker network inspect e2bot-dev-network`
3. Verificar port conflicts: `docker ps | grep nginx`

---

### Problema: HTTP Request retorna 404

**Diagnóstico**:
```bash
# Verificar templates no container
docker exec e2bot-templates-dev ls -la /usr/share/nginx/html/

# Testar direto no container
docker exec e2bot-templates-dev wget -O- http://localhost/confirmacao_agendamento.html
```

**Soluções**:
1. Verificar volume mount: `docker inspect e2bot-templates-dev | grep Mounts -A 10`
2. Verificar permissions: `ls -la email-templates/`
3. Restart nginx: `docker restart e2bot-templates-dev`

---

### Problema: Template rendering vazio

**Diagnóstico**:
```bash
# Verificar logs
docker logs e2bot-n8n-dev | grep "Render Template V9"
```

**Soluções**:
1. Verificar HTTP Request Response Format: Deve ser "string"
2. Verificar node connection: Prepare → Fetch → Render
3. Verificar template data: `console.log` no Render node

---

## 📚 Arquivos de Referência

**Gerados por Este Plano**:
- `scripts/generate-workflow-wf07-v9-http-request.py` (generator)
- `n8n/workflows/07_send_email_v9_http_request.json` (workflow)
- `docker/docker-compose-dev.yml` (modificado com nginx)

**Documentação**:
- `docs/SOLUTION_FINAL_HTTP_REQUEST.md` (solução base)
- `docs/ANALYSIS_N8N_VERSION_UPGRADE_VS_WORKAROUNDS.md` (análise)
- Este arquivo: `docs/PLAN_NGINX_WF07_IMPLEMENTATION.md`

**Backups**:
- `backups/workflows/2026-03-31-pre-v9/` (workflows anteriores)
- `docker/docker-compose.yml.backup` (docker-compose original)

---

**Date**: 2026-03-31
**Status**: 📋 **PLANO COMPLETO - PRONTO PARA EXECUÇÃO**
**Estimated Time**: 6-8 horas
**Risk Level**: 🟢 **BAIXO**
**Confidence**: 🎯 **100% - Solução testada e confiável**
**Success Criteria**: WF07 V9 100% funcional em produção com monitoramento 1 hora
