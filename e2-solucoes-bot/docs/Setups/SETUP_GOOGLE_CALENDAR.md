# Setup Google Calendar Integration

## Visão Geral

Guia completo para configurar a integração do bot E2 Soluções com Google Calendar para agendamento automatizado de visitas técnicas, envio de lembretes e sincronização de eventos.

## Pré-requisitos

- Conta Google (Gmail ou Google Workspace)
- Acesso ao Google Cloud Console
- Permissões de administrador no calendário
- Projeto do bot configurado

## Etapa 1: Criar Projeto no Google Cloud

### 1.1. Acessar Google Cloud Console

1. Acesse: https://console.cloud.google.com/
2. Faça login com sua conta Google
3. Clique em **"Selecionar Projeto"** no topo
4. Clique em **"Novo Projeto"**

### 1.2. Configurar Projeto

```yaml
Nome do Projeto: E2 Soluções Bot
ID do Projeto: e2-solucoes-bot-XXXX (gerado automaticamente)
Organização: Sem organização (ou sua empresa)
Local: Sem organização
```

Clique em **"Criar"** e aguarde 1-2 minutos.

### 1.3. Selecionar Projeto

No topo da página, certifique-se que o projeto **"E2 Soluções Bot"** está selecionado.

---

## Etapa 2: Habilitar Google Calendar API

### 2.1. Acessar Biblioteca de APIs

1. No menu lateral, vá em: **APIs e Serviços → Biblioteca**
2. Na busca, digite: "Google Calendar API"
3. Clique em **"Google Calendar API"**
4. Clique em **"Ativar"**
5. Aguarde confirmação (30 segundos)

### 2.2. Verificar API Ativada

Vá em: **APIs e Serviços → Painel**

Deve aparecer "Google Calendar API" na lista de APIs ativadas.

---

## Etapa 3: Criar Conta de Serviço

### 3.1. Acessar Contas de Serviço

1. Vá em: **APIs e Serviços → Credenciais**
2. Clique em **"Criar Credenciais"**
3. Selecione **"Conta de Serviço"**

### 3.2. Configurar Conta de Serviço

**Etapa 1: Detalhes da conta de serviço**

```yaml
Nome da conta de serviço: E2 Bot Calendar Service
ID da conta: e2-bot-calendar (gerado automaticamente)
Descrição: Conta de serviço para agendamento de visitas técnicas
```

Clique em **"Criar e continuar"**

**Etapa 2: Conceder acesso ao projeto (opcional)**

```yaml
Papel: Nenhum necessário (pular esta etapa)
```

Clique em **"Continuar"**

**Etapa 3: Conceder acesso aos usuários (opcional)**

```yaml
(Deixar em branco)
```

Clique em **"Concluir"**

### 3.3. Gerar Chave JSON

1. Na lista de Contas de Serviço, clique na conta criada
2. Vá na aba **"Chaves"**
3. Clique em **"Adicionar Chave" → "Criar nova chave"**
4. Selecione tipo: **JSON**
5. Clique em **"Criar"**

Um arquivo `e2-solucoes-bot-XXXXX.json` será baixado automaticamente.

**IMPORTANTE:**
- Guarde este arquivo com segurança!
- Nunca commite no Git!
- É a única vez que você verá esta chave!

### 3.4. Anotar Email da Conta de Serviço

No arquivo JSON baixado, localize o campo `client_email`:

```json
{
  "type": "service_account",
  "project_id": "e2-solucoes-bot-xxxxx",
  "private_key_id": "xxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "e2-bot-calendar@e2-solucoes-bot-xxxxx.iam.gserviceaccount.com",
  "client_id": "xxxxx",
  ...
}
```

**Anote o `client_email`** - você usará na próxima etapa.

---

## Etapa 4: Criar e Compartilhar Calendário

### 4.1. Criar Calendário Dedicado

1. Acesse: https://calendar.google.com/
2. No lado esquerdo, próximo a "Outros calendários", clique no **"+"**
3. Selecione **"Criar novo calendário"**

```yaml
Nome: Visitas Técnicas E2 Soluções
Descrição: Agendamento automatizado de visitas técnicas pelo bot
Fuso horário: (GMT-03:00) Brasília
```

Clique em **"Criar calendário"**

### 4.2. Compartilhar Calendário com Conta de Serviço

1. Na lista de calendários, localize "Visitas Técnicas E2 Soluções"
2. Clique nos **3 pontos** → **"Configurações e compartilhamento"**
3. Role até **"Compartilhar com pessoas específicas"**
4. Clique em **"Adicionar pessoas"**

```yaml
Email: e2-bot-calendar@e2-solucoes-bot-xxxxx.iam.gserviceaccount.com
Permissões: Fazer alterações em eventos
```

Clique em **"Enviar"**

**IMPORTANTE:** Use o email da conta de serviço (step 3.4), não seu email pessoal!

### 4.3. Obter ID do Calendário

1. Ainda em "Configurações e compartilhamento"
2. Role até **"Integrar calendário"**
3. Localize **"ID do calendário"**
4. Copie o ID (formato: `xxxxx@group.calendar.google.com`)

**Anote o `CALENDAR_ID`** - você usará no .env.

---

## Etapa 5: Configurar Variáveis de Ambiente

### 5.1. Copiar Arquivo de Chave

Copie o arquivo JSON baixado para o projeto:

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Criar diretório de credenciais (se não existir)
mkdir -p docker/credentials

# Copiar arquivo JSON (ajuste o caminho)
cp ~/Downloads/e2-solucoes-bot-xxxxx.json docker/credentials/google-service-account.json

# Proteger arquivo
chmod 600 docker/credentials/google-service-account.json
```

### 5.2. Editar .env

Edite `docker/.env.dev` e adicione:

```bash
# --- Google Calendar ---
GOOGLE_SERVICE_ACCOUNT_EMAIL=e2-bot-calendar@e2-solucoes-bot-xxxxx.iam.gserviceaccount.com
GOOGLE_CALENDAR_ID=xxxxx@group.calendar.google.com
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=/app/credentials/google-service-account.json

# Configurações de Agendamento
CALENDAR_TIMEZONE=America/Sao_Paulo
CALENDAR_DEFAULT_DURATION=90  # minutos (1h30)
CALENDAR_BUFFER_TIME=30       # minutos entre agendamentos

# Horário de Funcionamento (24h format)
CALENDAR_WORK_START=08:00
CALENDAR_WORK_END=18:00
CALENDAR_WORK_DAYS=1,2,3,4,5  # Segunda a Sexta (0=Dom, 6=Sáb)

# Lembretes
CALENDAR_REMINDER_24H=true
CALENDAR_REMINDER_2H=true
```

### 5.3. Atualizar docker-compose

Edite `docker/docker-compose-dev.yml` e adicione o volume:

```yaml
services:
  n8n:
    volumes:
      - ./credentials:/app/credentials:ro  # Adicionar esta linha
      # ... outros volumes
```

---

## Etapa 6: Testar Integração

### 6.1. Teste Manual via n8n

1. Acesse: http://localhost:5678
2. Vá em: **Credentials → Add Credential**
3. Busque: "Google Calendar"
4. Selecione: **"Service Account"**
5. Preencha:
   - Service Account Email: (do .env)
   - Private Key: (conteúdo do JSON)
6. Clique em **"Connect"**

Se conectar com sucesso, a credencial está configurada!

### 6.2. Teste via Script

Crie um script de teste:

```bash
#!/bin/bash
# scripts/test-calendar.sh

set -a
source docker/.env.dev
set +a

echo "🧪 Testando Google Calendar Integration..."

# Teste 1: Verificar arquivo de credenciais
echo "1. Verificando credenciais..."
if [ -f "docker/credentials/google-service-account.json" ]; then
  echo "✅ Arquivo de credenciais encontrado"
else
  echo "❌ Arquivo de credenciais não encontrado"
  exit 1
fi

# Teste 2: Verificar variáveis
echo "2. Verificando variáveis de ambiente..."
[ -n "$GOOGLE_SERVICE_ACCOUNT_EMAIL" ] && echo "✅ GOOGLE_SERVICE_ACCOUNT_EMAIL configurado" || echo "❌ Faltando"
[ -n "$GOOGLE_CALENDAR_ID" ] && echo "✅ GOOGLE_CALENDAR_ID configurado" || echo "❌ Faltando"

# Teste 3: Validar JSON
echo "3. Validando JSON..."
if jq empty docker/credentials/google-service-account.json 2>/dev/null; then
  echo "✅ JSON válido"
else
  echo "❌ JSON inválido"
  exit 1
fi

echo "✅ Testes básicos passaram!"
echo "🔹 Próximo: Testar criação de evento via n8n"
```

Execute:

```bash
chmod +x scripts/test-calendar.sh
./scripts/test-calendar.sh
```

### 6.3. Teste de Criação de Evento

Via n8n ou workflow dedicado:

1. Importar workflow `05_appointment_scheduler.json`
2. Executar teste manual com dados:

```json
{
  "lead_id": 1,
  "lead_name": "João Teste",
  "lead_phone": "62999999999",
  "visit_date": "2024-01-15",
  "visit_time": "14:00",
  "service_type": "Energia Solar",
  "address": "Rua Teste, 123, Goiânia-GO"
}
```

3. Verificar se evento aparece no Google Calendar
4. Verificar se recebeu confirmação no WhatsApp

---

## Etapa 7: Configurar Disponibilidade

### 7.1. Horários Bloqueados

Para bloquear horários específicos (almoço, reuniões, etc):

```sql
-- Função SQL já criada: check_calendar_availability()
-- Ela consulta automaticamente o Google Calendar para conflitos

-- Adicionar bloqueio manual (se necessário)
INSERT INTO calendar_blocks (
  block_date,
  start_time,
  end_time,
  reason,
  created_by
) VALUES (
  '2024-01-15',
  '12:00',
  '13:30',
  'Almoço',
  'admin'
);
```

### 7.2. Feriados

```sql
-- Criar tabela de feriados (se não existir)
CREATE TABLE IF NOT EXISTS holidays (
  id SERIAL PRIMARY KEY,
  holiday_date DATE NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50) DEFAULT 'national', -- national, state, local
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Adicionar feriados de 2024
INSERT INTO holidays (holiday_date, name, type) VALUES
('2024-01-01', 'Ano Novo', 'national'),
('2024-02-12', 'Carnaval', 'national'),
('2024-02-13', 'Carnaval', 'national'),
('2024-03-29', 'Sexta-feira Santa', 'national'),
('2024-04-21', 'Tiradentes', 'national'),
('2024-05-01', 'Dia do Trabalho', 'national'),
('2024-05-30', 'Corpus Christi', 'national'),
('2024-09-07', 'Independência', 'national'),
('2024-10-12', 'Nossa Senhora Aparecida', 'national'),
('2024-11-02', 'Finados', 'national'),
('2024-11-15', 'Proclamação da República', 'national'),
('2024-12-25', 'Natal', 'national');
```

---

## Etapa 8: Configurar Lembretes

### 8.1. Lembretes no Google Calendar

O bot já cria eventos com lembretes automáticos:

```javascript
// Configuração no workflow n8n (05_appointment_scheduler)
{
  "event": {
    "summary": "Visita Técnica - {{lead_name}}",
    "description": "Serviço: {{service_type}}\nEndereço: {{address}}",
    "start": {
      "dateTime": "{{visit_datetime}}",
      "timeZone": "America/Sao_Paulo"
    },
    "reminders": {
      "useDefault": false,
      "overrides": [
        {"method": "email", "minutes": 1440},  // 24h antes
        {"method": "popup", "minutes": 120}    // 2h antes
      ]
    }
  }
}
```

### 8.2. Lembretes via WhatsApp

Os lembretes via WhatsApp são enviados pelo workflow `06_appointment_reminders.json`:

**Cronograma:**
- **24h antes**: Confirmação detalhada (data, hora, endereço)
- **2h antes**: Lembrete final ("Técnico a caminho")

**Configuração do Cron:**

```yaml
# No workflow 06_appointment_reminders.json
Cron Expression: */30 * * * *  # Executar a cada 30 minutos

Query SQL:
SELECT * FROM appointments
WHERE status = 'confirmed'
  AND reminder_24h_sent = false
  AND visit_datetime <= NOW() + INTERVAL '24 hours'
  AND visit_datetime > NOW()
```

---

## Etapa 9: Fluxo Completo de Agendamento

```
┌─────────────────────────────────────────────────────┐
│   1. Lead Solicita Agendamento no WhatsApp         │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│   2. Bot Consulta Disponibilidade                   │
│      check_calendar_availability(date, time)        │
│      → Verifica conflitos no Google Calendar        │
│      → Verifica feriados                            │
│      → Verifica horário comercial                   │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│   3. Criar Evento no Google Calendar                │
│      POST /calendars/{id}/events                    │
│      → Evento com duração 90min                     │
│      → Lembretes configurados                       │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│   4. Salvar no Banco                                │
│      INSERT INTO appointments (...)                 │
│      → google_event_id (para updates futuros)       │
│      → status = 'confirmed'                         │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│   5. Enviar Confirmação WhatsApp                    │
│      "✅ Agendado para DD/MM às HH:MM"              │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│   6. Lembretes Automáticos                          │
│      24h antes: Confirmação detalhada               │
│      2h antes: "Técnico a caminho"                  │
└─────────────────────────────────────────────────────┘
```

---

## Etapa 10: Troubleshooting

### Problema: "Permission denied" ao criar evento

**Causa:** Calendário não foi compartilhado com conta de serviço

**Solução:**
1. Vá em Google Calendar
2. Configurações do calendário "Visitas Técnicas E2"
3. Compartilhar com: `e2-bot-calendar@...iam.gserviceaccount.com`
4. Permissão: "Fazer alterações em eventos"

### Problema: "Calendar not found"

**Causa:** CALENDAR_ID incorreto

**Solução:**
```bash
# Verificar ID do calendário
grep GOOGLE_CALENDAR_ID docker/.env.dev

# Formato esperado: xxxxx@group.calendar.google.com
# NÃO usar: seu-email@gmail.com
```

### Problema: Eventos criados no calendário errado

**Causa:** Usando calendário primário ao invés do dedicado

**Solução:**
Sempre usar o `GOOGLE_CALENDAR_ID` do calendário criado no Step 4, não o calendário pessoal.

### Problema: "Invalid credentials"

**Causa:** JSON malformado ou chave incorreta

**Solução:**
```bash
# Validar JSON
jq empty docker/credentials/google-service-account.json

# Verificar permissões
ls -lh docker/credentials/google-service-account.json
# Deve ser: -rw------- (600)

# Re-baixar chave se necessário (Google Cloud Console)
```

### Problema: Fuso horário errado

**Causa:** Timezone não configurado

**Solução:**
```bash
# Verificar .env
grep CALENDAR_TIMEZONE docker/.env.dev

# Deve ser: America/Sao_Paulo
# Lista completa: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
```

---

## Etapa 11: Monitoramento

### 11.1. Verificar Agendamentos

```sql
-- Ver agendamentos futuros
SELECT
  a.id,
  l.name as lead_name,
  l.phone,
  a.visit_datetime,
  a.status,
  a.reminder_24h_sent,
  a.reminder_2h_sent,
  a.google_event_id
FROM appointments a
JOIN leads l ON a.lead_id = l.id
WHERE a.visit_datetime >= NOW()
ORDER BY a.visit_datetime;
```

### 11.2. Verificar Lembretes Pendentes

```sql
-- Lembretes 24h que precisam ser enviados
SELECT * FROM appointments
WHERE status = 'confirmed'
  AND reminder_24h_sent = false
  AND visit_datetime BETWEEN NOW() AND NOW() + INTERVAL '24 hours';

-- Lembretes 2h que precisam ser enviados
SELECT * FROM appointments
WHERE status = 'confirmed'
  AND reminder_2h_sent = false
  AND visit_datetime BETWEEN NOW() AND NOW() + INTERVAL '2 hours';
```

### 11.3. Dashboard de Ocupação

```sql
-- Agendamentos por dia (próximas 2 semanas)
SELECT
  DATE(visit_datetime) as dia,
  COUNT(*) as total_visitas,
  STRING_AGG(
    TO_CHAR(visit_datetime, 'HH24:MI') || ' - ' || l.name,
    ', '
  ) as visitas
FROM appointments a
JOIN leads l ON a.lead_id = l.id
WHERE visit_datetime BETWEEN NOW() AND NOW() + INTERVAL '14 days'
  AND status = 'confirmed'
GROUP BY DATE(visit_datetime)
ORDER BY dia;
```

---

## Recursos Adicionais

- **Google Calendar API Docs**: https://developers.google.com/calendar/api
- **Service Account Auth**: https://developers.google.com/identity/protocols/oauth2/service-account
- **Calendar Quickstart**: https://developers.google.com/calendar/api/quickstart/nodejs
- **Limites de API**: 1.000.000 requests/dia (mais que suficiente)
- **Quota Monitoring**: https://console.cloud.google.com/apis/api/calendar-json.googleapis.com/quotas

---

## Checklist de Configuração

- [ ] Projeto criado no Google Cloud Console
- [ ] Google Calendar API habilitada
- [ ] Conta de serviço criada
- [ ] Chave JSON baixada e salva em `docker/credentials/`
- [ ] Email da conta de serviço anotado
- [ ] Calendário "Visitas Técnicas E2" criado
- [ ] Calendário compartilhado com conta de serviço
- [ ] CALENDAR_ID obtido e anotado
- [ ] `.env.dev` atualizado com todas as variáveis
- [ ] `docker-compose-dev.yml` atualizado com volume
- [ ] Arquivo JSON validado (`jq empty`)
- [ ] Permissões do arquivo configuradas (chmod 600)
- [ ] Teste de conexão no n8n realizado
- [ ] Teste de criação de evento realizado
- [ ] Workflows de agendamento importados
- [ ] Lembretes automáticos testados
- [ ] Feriados cadastrados no banco
- [ ] Monitoramento configurado

---

**Configuração completa!** O bot agora pode agendar visitas técnicas automaticamente no Google Calendar com lembretes integrados.
