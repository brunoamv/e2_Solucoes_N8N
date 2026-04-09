# Setup Google Calendar Integration - OAuth2

> **Versão**: 3.0 (DEFINITIVA) | **Atualização**: 2026-04-08
> **Método**: OAuth2 (substituiu Service Account)
> **Objetivo**: Configurar integração Google Calendar para WF05 e WF06

---

## 📋 Visão Geral

Guia completo para configurar integração Google Calendar com n8n usando **OAuth2**.

**Diferença OAuth2 vs Service Account**:
- ✅ **OAuth2** (V3 - atual): Autenticação via conta Google pessoal/workspace, acesso direto ao calendário
- ❌ **Service Account** (V1 - deprecado): Requer compartilhamento de calendário, mais complexo

**Este guia usa OAuth2** - método mais simples e recomendado.

---

## 🎯 Workflows que Usam

- **WF05** (Appointment Scheduler): Cria eventos no calendário
- **WF06** (Calendar Availability): Consulta disponibilidade de datas/horários

---

## 🚨 Pré-requisitos

**Antes de começar**:
- ✅ Conta Google (Gmail ou Google Workspace)
- ✅ Acesso ao Google Cloud Console
- ✅ n8n rodando em `http://localhost:5678`
- ✅ Containers Docker ativos (PostgreSQL + n8n)

**Verificar n8n rodando**:
```bash
curl -I http://localhost:5678
# Deve retornar: HTTP 200 ou redirecionamento
```

---

## 📖 Etapas de Configuração

```
┌─────────────────────────────────────────────────┐
│ Etapa 1: Criar Projeto no Google Cloud         │
│ Etapa 2: Habilitar Google Calendar API         │
│ Etapa 3: Criar OAuth2 Client Credentials       │
│ Etapa 4: Configurar Credencial no n8n          │
│ Etapa 5: Autenticar e Obter Access Token       │
│ Etapa 6: Configurar Variáveis de Ambiente      │
│ Etapa 7: Testar Integração                     │
└─────────────────────────────────────────────────┘
```

**Tempo estimado**: 15-20 minutos

---

## Etapa 1: Criar Projeto no Google Cloud

### 1.1. Acessar Google Cloud Console

1. Acesse: https://console.cloud.google.com/
2. Faça login com sua conta Google
3. Clique em **"Select a project"** (topo da página)
4. Clique em **"NEW PROJECT"**

### 1.2. Configurar Projeto

```yaml
Project name: E2 Bot n8n Integration
Project ID: e2-bot-n8n-XXXX (gerado automaticamente)
Organization: No organization (ou sua empresa)
Location: No organization
```

Clique em **"CREATE"** e aguarde 1-2 minutos.

### 1.3. Selecionar Projeto

No topo da página, verifique se o projeto **"E2 Bot n8n Integration"** está selecionado.

---

## Etapa 2: Habilitar Google Calendar API

### 2.1. Acessar Biblioteca de APIs

1. No menu lateral (☰), vá em: **APIs & Services → Library**
2. Na busca, digite: **"Google Calendar API"**
3. Clique em **"Google Calendar API"**
4. Clique em **"ENABLE"**
5. Aguarde confirmação (30 segundos)

### 2.2. Verificar API Ativada

Vá em: **APIs & Services → Dashboard**

Deve aparecer **"Google Calendar API"** na lista de APIs ativadas.

✅ **API habilitada com sucesso!**

---

## Etapa 3: Criar OAuth2 Client Credentials

### 3.1. Configurar OAuth Consent Screen (Primeira vez)

Se for a primeira vez usando OAuth no projeto:

1. **APIs & Services → OAuth consent screen**
2. **User Type**: External (ou Internal se Google Workspace)
3. Clique em **"CREATE"**

**App information**:
```yaml
App name: E2 Bot n8n Integration
User support email: seu-email@gmail.com
Developer contact: seu-email@gmail.com
```

4. Clique em **"SAVE AND CONTINUE"**
5. **Scopes**: Deixar vazio por enquanto → **"SAVE AND CONTINUE"**
6. **Test users**: Adicionar seu email → **"SAVE AND CONTINUE"**
7. **Summary**: Revisar → **"BACK TO DASHBOARD"**

### 3.2. Criar OAuth2 Client ID

1. **APIs & Services → Credentials**
2. Clique em **"+ CREATE CREDENTIALS"**
3. Selecione **"OAuth client ID"**

**Configuração**:
```yaml
Application type: Web application
Name: E2 Bot n8n Integration

Authorized JavaScript origins:
  - http://localhost:5678

Authorized redirect URIs:
  - http://localhost:5678/rest/oauth2-credential/callback
```

4. Clique em **"CREATE"**

### 3.3. Copiar Credenciais

Uma modal aparecerá com:
- **Client ID**: `xxxxxxxxxxxxx.apps.googleusercontent.com`
- **Client Secret**: `GOCSPX-xxxxxxxxxxxxxxxxxxxxx`

**🚨 IMPORTANTE**: Copie e guarde essas credenciais com segurança!

Você pode baixar o JSON ou copiar manualmente.

**Anotar**:
```
Client ID: xxxxxxxxxxxxx.apps.googleusercontent.com
Client Secret: GOCSPX-xxxxxxxxxxxxxxxxxxxxx
```

---

## Etapa 4: Configurar Credencial no n8n

### 4.1. Criar Credencial OAuth2

1. Acesse n8n: http://localhost:5678
2. Menu lateral → **Credentials**
3. Clique em **"Add credential"**
4. Buscar: **"Google Calendar OAuth2 API"**
5. Selecionar **"Google Calendar OAuth2 API"**

### 4.2. Preencher Credenciais

```yaml
Credential name: Google Calendar API - E2 Bot

Authentication:
  - Client ID: <Client ID copiado da Etapa 3.3>
  - Client Secret: <Client Secret copiado da Etapa 3.3>

Scopes (deixar o padrão):
  - https://www.googleapis.com/auth/calendar
  - https://www.googleapis.com/auth/calendar.events
```

**NÃO SALVAR AINDA** - Prossiga para Etapa 5 (autenticação OAuth).

---

## Etapa 5: Autenticar e Obter Access Token

### 5.1. Iniciar OAuth Flow

1. Na tela de credencial (ainda aberta), clique em **"Connect my account"** ou **"Sign in with Google"**

2. **Pop-up do Google abrirá**:
   - Se o pop-up não abrir, desabilite bloqueador de pop-ups para `localhost:5678`

3. **Selecionar Conta Google**:
   - Escolha a conta que tem acesso ao calendário que você quer usar

4. **Tela de Permissões** ("E2 Bot n8n Integration wants to access your Google Account"):
   - ✅ Marque **"Select all"** ou marque individualmente:
     - View and edit events on all your calendars
     - View events on all your calendars
   - Clique em **"Continue"**

5. **Redirecionamento**:
   - Você será redirecionado de volta para n8n
   - n8n receberá automaticamente **Access Token** e **Refresh Token**

### 5.2. Confirmar Autenticação

A credencial n8n deve mostrar:
- ✅ **"OAuth2 authentication successful"**
- ✅ Status verde com token ativo

### 5.3. Salvar Credencial

Agora sim, clique em **"Save"** (botão inferior direito).

✅ **Credencial Google Calendar OAuth2 configurada com sucesso!**

---

## Etapa 6: Configurar Variáveis de Ambiente

### 6.1. Obter Calendar ID

**Método 1 - Via Google Calendar UI** (mais simples):

1. Acesse: https://calendar.google.com
2. No lado esquerdo, localize seu calendário
3. Clique nos **três pontos (⋮)** ao lado do nome do calendário
4. Selecione **"Settings and sharing"**
5. Role até seção **"Integrate calendar"**
6. Copie o **"Calendar ID"**

**Formatos possíveis**:
- Calendário primário: `seu-email@gmail.com`
- Calendário secundário: `xxxxxxxxxxxxx@group.calendar.google.com`

**Método 2 - Via n8n Test** (se preferir):

1. n8n → Criar novo workflow temporário
2. Adicionar node **"Google Calendar"**
3. Operation: **"Get All Calendars"**
4. Credential: Selecionar **"Google Calendar API - E2 Bot"**
5. Execute node
6. Na saída, copie o `id` do calendário desejado

**Anotar Calendar ID**:
```
GOOGLE_CALENDAR_ID=xxxxxxxxxxxxx@group.calendar.google.com
```

### 6.2. Obter Credential ID (n8n interno)

1. n8n → **Credentials**
2. Clique na credencial **"Google Calendar API - E2 Bot"**
3. Na URL, observe o ID no final:
   ```
   http://localhost:5678/credentials/VXA1r8sd0TMIdPvS
                                      ^^^^^^^^^^^^^^^^
                                      Este é o Credential ID
   ```

**Anotar Credential ID**:
```
GOOGLE_CALENDAR_CREDENTIAL_ID=VXA1r8sd0TMIdPvS
```

### 6.3. Atualizar docker/.env

Edite o arquivo `docker/.env` e adicione:

```bash
# ============================================================================
# Google Calendar Configuration
# ============================================================================
GOOGLE_CALENDAR_ID=xxxxxxxxxxxxx@group.calendar.google.com
GOOGLE_CALENDAR_CREDENTIAL_ID=VXA1r8sd0TMIdPvS
GOOGLE_TECHNICIAN_EMAIL=tecnico@e2solucoes.com.br
CALENDAR_TIMEZONE=America/Sao_Paulo

# Horário de Funcionamento (Opcional - usado por WF05 V7+)
CALENDAR_WORK_START=08:00
CALENDAR_WORK_END=18:00
CALENDAR_WORK_DAYS=1,2,3,4,5  # Segunda a Sexta (0=Dom, 6=Sáb)

# Configurações de Agendamento (Opcional)
CALENDAR_DEFAULT_DURATION=90  # minutos (1h30)
CALENDAR_BUFFER_TIME=30       # minutos entre agendamentos
```

### 6.4. Reiniciar n8n para Carregar Variáveis

```bash
docker-compose -f docker/docker-compose-dev.yml restart e2bot-n8n-dev
```

Aguarde 30 segundos para n8n reiniciar.

**Verificar variáveis carregadas**:
```bash
docker exec e2bot-n8n-dev env | grep GOOGLE_CALENDAR_ID
# Deve mostrar: GOOGLE_CALENDAR_ID=xxxxxxxxxxxxx@group.calendar.google.com
```

---

## Etapa 7: Testar Integração

### 7.1. Teste Básico - WF06 (Calendar Availability)

**Pré-requisito**: WF06 importado e ativo

```bash
curl -X POST "http://localhost:5678/webhook/calendar-availability" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "next_dates",
    "count": 3
  }' | jq
```

**✅ Resultado esperado**:
```json
{
  "dates": [
    {
      "date": "2026-04-09",
      "dayOfWeek": "Quarta-feira",
      "available": true
    },
    {
      "date": "2026-04-10",
      "dayOfWeek": "Quinta-feira",
      "available": true
    },
    {
      "date": "2026-04-11",
      "dayOfWeek": "Sexta-feira",
      "available": true
    }
  ]
}
```

### 7.2. Teste Avançado - WF05 (Criar Evento)

**Pré-requisito**: WF05 importado, PostgreSQL configurado

1. **Criar lead de teste no banco**:
   ```sql
   INSERT INTO conversations (phone_number, lead_name, service_type, current_state)
   VALUES ('5561999999999', 'Teste Manual', 'energia_solar', 'confirmation');
   ```

2. **Executar WF05 manualmente**:
   - n8n → Workflow **"05_appointment_scheduler"**
   - Execute Workflow

3. **Verificar**:
   - ✅ Google Calendar → Evento criado com título "Visita Técnica - Teste Manual"
   - ✅ Database → Tabela `appointments` com novo registro
   - ✅ Campo `google_calendar_event_id` preenchido

### 7.3. Teste de Consulta de Horários Disponíveis

```bash
curl -X POST "http://localhost:5678/webhook/calendar-availability" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "available_slots",
    "date": "2026-04-15"
  }' | jq
```

**✅ Resultado esperado**:
```json
{
  "date": "2026-04-15",
  "slots": [
    { "time": "08:00", "available": true },
    { "time": "09:30", "available": true },
    { "time": "11:00", "available": false },
    { "time": "14:00", "available": true },
    { "time": "15:30", "available": true }
  ]
}
```

---

## 🐛 Troubleshooting

### Erro: "invalid_grant" ou "Token has been expired or revoked"

**Causa**: Refresh Token expirou ou foi revogado

**Solução**:
1. n8n → Credentials → **"Google Calendar API - E2 Bot"**
2. **Delete** a credencial
3. Criar nova credencial (refazer Etapas 4-5)
4. Re-vincular credencial nos workflows WF05 e WF06

---

### Erro: "Access blocked: E2 Bot n8n Integration has not completed the Google verification process"

**Causa**: App não verificado pelo Google (normal em desenvolvimento)

**Solução**:
1. Na tela de permissões, clique em **"Advanced"**
2. Clique em **"Go to E2 Bot n8n Integration (unsafe)"**
3. Autorizar permissões
4. ✅ Isso é seguro para desenvolvimento local

**Para produção**: Submeter app para verificação Google (processo de 4-6 semanas)

---

### Erro: "Redirect URI mismatch"

**Causa**: URI configurado no Google Cloud não corresponde ao n8n

**Solução**:
1. Google Cloud Console → APIs & Services → Credentials
2. Editar OAuth2 Client ID
3. **Authorized redirect URIs** → Adicionar:
   ```
   http://localhost:5678/rest/oauth2-credential/callback
   ```
4. Salvar e aguardar 5 minutos para propagação

---

### Erro: "Calendar not found" ou "404"

**Causa**: `GOOGLE_CALENDAR_ID` incorreto ou calendário não acessível

**Solução**:
1. Verificar Calendar ID:
   ```bash
   grep GOOGLE_CALENDAR_ID docker/.env
   ```

2. Testar acesso ao calendário:
   - n8n → Novo workflow temporário
   - Google Calendar node → Operation: "Get All Calendars"
   - Execute → Verificar se o calendar ID está na lista

3. Se calendário não aparece:
   - Verificar se a conta autenticada no OAuth é a mesma que tem o calendário
   - Re-fazer OAuth flow com conta correta

---

### Erro: "Insufficient permissions"

**Causa**: Scopes OAuth2 incorretos

**Solução**:
1. n8n → Credentials → Google Calendar OAuth2 API
2. Verificar **Scopes**:
   ```
   https://www.googleapis.com/auth/calendar
   https://www.googleapis.com/auth/calendar.events
   ```
3. Se faltando, adicionar e refazer OAuth flow

---

### Erro: "$env.GOOGLE_CALENDAR_ID is undefined" no workflow

**Causa**: Variável de ambiente não carregada no container n8n

**Solução**:
1. Verificar `docker/.env` contém a variável:
   ```bash
   cat docker/.env | grep GOOGLE_CALENDAR_ID
   ```

2. Reiniciar container:
   ```bash
   docker-compose -f docker/docker-compose-dev.yml restart e2bot-n8n-dev
   ```

3. Verificar variável dentro do container:
   ```bash
   docker exec e2bot-n8n-dev env | grep GOOGLE_CALENDAR_ID
   ```

---

## ✅ Checklist de Validação

Antes de usar em produção:

- [ ] Projeto criado no Google Cloud Console
- [ ] Google Calendar API habilitada
- [ ] OAuth2 Client ID criado com redirect URI correto
- [ ] Credencial criada no n8n com OAuth2 autenticado
- [ ] Calendar ID obtido e configurado em `docker/.env`
- [ ] Credential ID obtido e configurado em `docker/.env`
- [ ] Container n8n reiniciado para carregar variáveis
- [ ] WF06 responde com datas disponíveis (teste curl)
- [ ] WF05 cria evento no Google Calendar com sucesso
- [ ] Eventos aparecem no Google Calendar UI

**Tudo OK?** 🎉 **Integração Google Calendar configurada com sucesso!**

---

## 📚 Referências

- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [OAuth2 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
- [n8n Google Calendar Node](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-generic/)
- [Calendar API Quickstart](https://developers.google.com/calendar/api/quickstart/nodejs)

---

## 🔄 Histórico de Versões

- **V3.0** (2026-04-08): Versão definitiva consolidada com OAuth2
- **V2.0** (2026-04-06): Migração para OAuth2 (deprecou Service Account)
- **V1.0** (2024-12-15): Versão inicial com Service Account

---

**Última Atualização**: 2026-04-08
**Mantido por**: E2 Soluções Dev Team
**Próximo**: `QUICKSTART.md` seção 2.2 ou `SETUP_CREDENTIALS.md` seção 2
