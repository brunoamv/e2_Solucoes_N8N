# Guia de Configuração - Discord Webhooks

## 📋 Visão Geral

Este guia detalha a configuração dos webhooks do Discord para o sistema de notificações multi-canal do E2 Soluções Bot (Sprint 1.3).

**Objetivo**: Criar 3 webhooks Discord para notificações em tempo real de leads, agendamentos e alertas do sistema.

**Tempo Estimado**: 15-20 minutos

---

## 🎯 Pré-requisitos

1. **Conta Discord**: Acesso a uma conta Discord com permissões de administrador
2. **Servidor Discord**: Servidor existente ou criar um novo para o bot
3. **Permissões**: Direito de criar webhooks no servidor

---

## 📝 Passo 1: Criar Servidor Discord (se necessário)

Se você já possui um servidor Discord para o bot, **pule para o Passo 2**.

### 1.1 Criar Novo Servidor

1. Abra o Discord Desktop ou Web App
2. Clique no botão **"+"** na barra lateral esquerda
3. Selecione **"Criar um servidor"**
4. Escolha **"Criar o Meu Próprio"**
5. Selecione **"Para mim e meus amigos"** ou **"Para um clube ou comunidade"**
6. Configure:
   - **Nome do Servidor**: `E2 Soluções Bot`
   - **Ícone**: Upload do logo da E2 Soluções (opcional)
7. Clique em **"Criar"**

### 1.2 Estrutura de Canais Recomendada

Crie 4 canais de texto:

```
📁 E2 SOLUÇÕES BOT
├─ 📢 #geral (canal padrão)
├─ 💼 #leads (notificações de novos leads)
├─ 📅 #agendamentos (notificações de visitas)
└─ 🚨 #alertas (notificações de sistema/erros)
```

**Como criar canais**:
1. Clique com botão direito no nome do servidor → **"Criar Canal"**
2. Tipo: **Canal de Texto**
3. Nome: `leads`, `agendamentos`, `alertas`
4. Privacidade: **Privado** (somente membros autorizados)

---

## 📝 Passo 2: Criar Webhooks para Cada Canal

Você precisará criar **3 webhooks** (um para cada canal).

### 2.1 Webhook #1: Canal #leads

1. Abra o canal **#leads**
2. Clique no ícone de configurações (⚙️) ao lado do nome do canal
3. Selecione **"Integrações"** no menu lateral
4. Clique em **"Criar Webhook"**
5. Configure o webhook:
   - **Nome**: `E2 Bot - Leads`
   - **Avatar**: Upload de ícone de lead (💼) ou logo E2 (opcional)
   - **Canal**: `#leads` (já selecionado)
6. Clique em **"Copiar URL do Webhook"**
7. **GUARDE ESTA URL** - você precisará dela no `.env`

**Formato da URL**:
```
https://discord.com/api/webhooks/1234567890123456789/AbCdEfGhIjKlMnOpQrStUvWxYz1234567890AbCdEfGhIjKlMnOpQrStUvWxYz
```

### 2.2 Webhook #2: Canal #agendamentos

Repita o processo para o canal **#agendamentos**:

1. Abra o canal **#agendamentos**
2. Clique em ⚙️ → **"Integrações"** → **"Criar Webhook"**
3. Configure:
   - **Nome**: `E2 Bot - Agendamentos`
   - **Avatar**: Ícone de calendário (📅)
4. **Copiar URL do Webhook**
5. **GUARDE ESTA URL**

### 2.3 Webhook #3: Canal #alertas

Repita o processo para o canal **#alertas**:

1. Abra o canal **#alertas**
2. Clique em ⚙️ → **"Integrações"** → **"Criar Webhook"**
3. Configure:
   - **Nome**: `E2 Bot - Alertas`
   - **Avatar**: Ícone de alerta (🚨)
4. **Copiar URL do Webhook**
5. **GUARDE ESTA URL**

---

## 📝 Passo 3: Configurar Variáveis de Ambiente

### 3.1 Editar .env

Copie as **3 URLs de webhook** coletadas e adicione ao arquivo `.env`:

```bash
# Abra o arquivo de configuração
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
nano docker/.env
```

### 3.2 Adicionar Webhooks

Localize a seção **"Discord Notifications"** e substitua os valores:

```bash
# Discord Notifications (Sprint 1.3)
DISCORD_WEBHOOK_LEADS=https://discord.com/api/webhooks/1234567890123456789/LEAD_WEBHOOK_TOKEN_AQUI
DISCORD_WEBHOOK_APPOINTMENTS=https://discord.com/api/webhooks/1234567890123456789/APPOINTMENT_WEBHOOK_TOKEN_AQUI
DISCORD_WEBHOOK_ALERTS=https://discord.com/api/webhooks/1234567890123456789/ALERT_WEBHOOK_TOKEN_AQUI

# Configurações de retry para notificações
NOTIFICATION_RETRY_MAX=3
NOTIFICATION_BATCH_SIZE=10
```

**Dica**: Use `Ctrl+Shift+V` para colar no terminal.

### 3.3 Salvar e Sair

- **Nano**: `Ctrl+O` (salvar) → `Enter` → `Ctrl+X` (sair)
- **Vim**: `:wq`

---

## ✅ Passo 4: Validar Configuração

### 4.1 Testar Webhook do Discord (Manual)

Teste cada webhook enviando uma mensagem de teste via `curl`:

```bash
# Teste webhook de LEADS
curl -X POST "SEU_WEBHOOK_LEADS_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "🧪 Teste de webhook - Canal #leads configurado com sucesso!"
  }'

# Teste webhook de AGENDAMENTOS
curl -X POST "SEU_WEBHOOK_APPOINTMENTS_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "🧪 Teste de webhook - Canal #agendamentos configurado com sucesso!"
  }'

# Teste webhook de ALERTAS
curl -X POST "SEU_WEBHOOK_ALERTS_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "🧪 Teste de webhook - Canal #alertas configurado com sucesso!"
  }'
```

**Resultado Esperado**: Você deve ver 3 mensagens aparecerem nos respectivos canais do Discord.

### 4.2 Verificar .env Completo

Valide que todas as variáveis estão configuradas:

```bash
# Verificar se todos os webhooks estão configurados
grep "DISCORD_WEBHOOK_" docker/.env | wc -l
# Deve retornar: 3
```

---

## 📝 Passo 5: Configurar Evolution API (WhatsApp)

### 5.1 Validar Conexão com Evolution API

O Evolution API deve estar rodando no ambiente de desenvolvimento:

```bash
# Verificar se Evolution API está ativa
curl http://localhost:8080/instance/fetchInstances \
  -H "apikey: SEU_EVOLUTION_API_KEY"
```

**Resultado Esperado**:
```json
[
  {
    "instance": {
      "instanceName": "e2-solucoes-bot",
      "status": "open"
    }
  }
]
```

### 5.2 Verificar Status de Conexão WhatsApp

```bash
# Verificar se QR Code expirou
curl http://localhost:8080/instance/connectionState/e2-solucoes-bot \
  -H "apikey: SEU_EVOLUTION_API_KEY"
```

**Possíveis Status**:
- `"state": "open"` → ✅ Conectado (OK)
- `"state": "close"` → ⚠️ Desconectado (precisa escanear QR Code)
- `"state": "connecting"` → ⏳ Conectando...

### 5.3 Reconectar WhatsApp (se necessário)

Se o status for `"close"`, você precisa escanear o QR Code novamente:

```bash
# Gerar novo QR Code
curl http://localhost:8080/instance/connect/e2-solucoes-bot \
  -H "apikey: SEU_EVOLUTION_API_KEY"
```

**Resultado**: Retornará Base64 do QR Code. Você pode:

1. **Opção 1 - Terminal com qrencode**:
```bash
# Instalar qrencode (se não tiver)
sudo apt install qrencode

# Exibir QR Code no terminal
curl http://localhost:8080/instance/connect/e2-solucoes-bot \
  -H "apikey: SEU_EVOLUTION_API_KEY" \
  | jq -r '.qrcode.base64' \
  | base64 -d \
  | qrencode -t ANSIUTF8
```

2. **Opção 2 - Interface Web**:
Acesse: `http://localhost:8080/manager` (se Evolution API tiver manager ativo)

3. **Opção 3 - Salvar como imagem**:
```bash
curl http://localhost:8080/instance/connect/e2-solucoes-bot \
  -H "apikey: SEU_EVOLUTION_API_KEY" \
  | jq -r '.qrcode.base64' \
  | base64 -d \
  > qrcode.png
```

Depois abra `qrcode.png` e escaneie com WhatsApp no celular.

---

## ✅ Validação Final - Sistema Completo

### 6.1 Iniciar Ambiente de Desenvolvimento

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
./scripts/start-dev.sh
```

### 6.2 Verificar Serviços Ativos

```bash
docker ps
```

**Serviços esperados** (11 containers):
- ✅ n8n (porta 5678)
- ✅ postgres-main (porta 5432)
- ✅ supabase-db (porta 5433)
- ✅ supabase-studio (porta 3000)
- ✅ supabase-kong (porta 8000)
- ✅ supabase-auth (porta 9999)
- ✅ supabase-rest (porta 3001)
- ✅ supabase-realtime (porta 4000)
- ✅ supabase-storage (porta 5000)
- ✅ supabase-meta (porta 8080)
- ✅ evolution-api (porta 8081)

### 6.3 Testar Notificação End-to-End

Execute teste de notificação completa via SQL:

```bash
# Criar lead de teste e agendar visita
psql -h localhost -p 5432 -U postgres -d e2_solucoes_bot -c "
SELECT schedule_appointment_notification(
  (SELECT id FROM leads WHERE phone = '+5562999999999' LIMIT 1),
  'reminder_24h'
);
"
```

**Resultado Esperado**:
1. ✅ Registro criado na tabela `notifications`
2. ✅ Mensagem enviada no Discord (#agendamentos)
3. ✅ Mensagem enviada via WhatsApp
4. ✅ Email enviado (se SMTP configurado)

### 6.4 Verificar Logs do Workflow 12

Acesse n8n: `http://localhost:5678`

1. Abra o **Workflow 12 - Multi-Channel Notifications**
2. Clique em **"Executions"** no menu superior
3. Verifique a última execução:
   - ✅ Status: `success`
   - ✅ Todas as 3 notificações enviadas (Discord, WhatsApp, Email)

---

## 🎨 Personalização de Mensagens Discord

### Formato de Mensagem Enriquecida (Embed)

Os workflows enviam mensagens Discord com formato enriquecido (embeds):

```json
{
  "embeds": [{
    "title": "🎯 Novo Lead Qualificado",
    "description": "Um novo lead foi qualificado pelo bot WhatsApp",
    "color": 5814783,
    "fields": [
      {"name": "👤 Nome", "value": "João Silva", "inline": true},
      {"name": "📞 Telefone", "value": "+55 62 99999-9999", "inline": true},
      {"name": "🔧 Serviço", "value": "Energia Solar", "inline": false}
    ],
    "footer": {
      "text": "E2 Soluções Bot • Sprint 1.3"
    },
    "timestamp": "2025-01-15T10:30:00.000Z"
  }]
}
```

### Cores Disponíveis

Você pode personalizar as cores dos embeds no **Workflow 12** (nó Discord):

| Canal | Cor | Código Decimal | Código Hex |
|-------|-----|----------------|------------|
| #leads | 🟣 Roxo | 5814783 | #58B9FF |
| #agendamentos | 🟢 Verde | 3066993 | #2ECC71 |
| #alertas | 🔴 Vermelho | 15158332 | #E74C3C |

---

## 🐛 Troubleshooting

### Problema 1: Webhook não envia mensagens

**Sintomas**:
- Teste com `curl` retorna erro 404 ou 401

**Solução**:
1. Verifique se o webhook ainda existe no Discord (pode ter sido deletado)
2. Regenere o webhook:
   - Discord → Canal → ⚙️ → Integrações → Deletar webhook antigo → Criar novo
3. Atualize `.env` com a nova URL
4. Reinicie n8n: `docker restart n8n`

### Problema 2: Evolution API desconectada

**Sintomas**:
- Status `"close"` no endpoint `/connectionState`
- Mensagens WhatsApp não são enviadas

**Solução**:
1. Gere novo QR Code (ver Passo 5.3)
2. Escaneie com WhatsApp
3. Aguarde 10-15 segundos para conexão estabilizar
4. Verifique novamente: `curl http://localhost:8080/instance/connectionState/e2-solucoes-bot`

### Problema 3: Variáveis de ambiente não carregadas

**Sintomas**:
- n8n não envia notificações
- Logs mostram erro: `DISCORD_WEBHOOK_LEADS is not defined`

**Solução**:
1. Verifique se `.env` existe: `ls -la docker/.env`
2. Se não existir, copie do template:
   ```bash
   cp docker/.env.dev.example docker/.env
   ```
3. Edite `.env` e adicione as URLs dos webhooks
4. Reinicie TODOS os serviços:
   ```bash
   docker-compose -f docker/docker-compose-dev.yml down
   ./scripts/start-dev.sh
   ```

### Problema 4: Mensagens duplicadas

**Sintomas**:
- Mesma notificação enviada 2-3 vezes
- Workflow 12 executa múltiplas vezes

**Solução**:
1. Verifique se há execuções duplicadas no n8n
2. Desative execuções automáticas:
   - n8n → Workflow 12 → Settings → **Active: OFF**
3. Verifique trigger do workflow (deve ser HTTP Request ou Schedule, não ambos)

---

## 📚 Referências

### Documentação Official

- **Discord Webhooks**: https://discord.com/developers/docs/resources/webhook
- **Evolution API**: https://doc.evolution-api.com/
- **n8n Discord Node**: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.discord/

### Arquivos Relacionados

- **Workflow 12**: `n8n/workflows/12_multi_channel_notifications.json`
- **Workflow 13**: `n8n/workflows/13_discord_notifications.json`
- **Templates WhatsApp**: `templates/whatsapp/`
- **Templates Email**: `templates/emails/`
- **Funções SQL**: `database/appointment_functions.sql`

---

## ✅ Checklist de Configuração

Use este checklist para validar que tudo está configurado:

- [ ] **Servidor Discord criado** com 3 canais (#leads, #agendamentos, #alertas)
- [ ] **3 webhooks criados** e URLs copiadas
- [ ] **Variáveis .env configuradas** (DISCORD_WEBHOOK_*)
- [ ] **Webhooks testados** via curl (mensagens recebidas)
- [ ] **Evolution API conectada** (status `"open"`)
- [ ] **QR Code escaneado** (se necessário)
- [ ] **Ambiente iniciado** (`./scripts/start-dev.sh`)
- [ ] **Teste end-to-end executado** (notificação completa funcionando)
- [ ] **Logs do n8n verificados** (execuções bem-sucedidas)

---

**Última Atualização**: 2025-01-15
**Sprint**: 1.3 - Sistema de Notificações Multi-Canal
**Tempo Total de Configuração**: 20-30 minutos
