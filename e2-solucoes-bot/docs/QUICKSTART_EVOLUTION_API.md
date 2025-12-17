# 🚀 Guia Rápido: Setup Evolution API (MÉTODO FUNCIONAL)

**Situação**: Você precisa iniciar a Evolution API para WhatsApp no Docker e gerar QR Code para conectar.

**Tempo estimado**: 10-15 minutos

> **⚠️ PRÉ-REQUISITO IMPORTANTE**
>
> Este guia assume que você **JÁ COMPLETOU** o setup inicial do ambiente:
> - ✅ n8n rodando em `http://localhost:5678`
> - ✅ PostgreSQL e Supabase configurados
> - ✅ Credenciais no `docker/.env`
>
> **Se você ainda NÃO tem o n8n rodando**, siga primeiro:
> 📘 **[QUICKSTART.md](QUICKSTART.md)** - Setup completo do ambiente (n8n + PostgreSQL + Supabase)
>
> **Depois volte aqui** para configurar apenas o WhatsApp (Evolution API).

> **⚠️ DESCOBERTA CRÍTICA (2025-12-17)**
>
> Evolution API v2.2.3 possui bug (Issue #1474) que afeta:
> 1. ✅ Inicialização do Baileys
> 2. ✅ **Geração de QR Code** (descoberta nova!)
>
> **SOLUÇÃO VALIDADA**: Copiar `.env` para dentro do container + reiniciar
>
> **Referência**: `docs/EVOLUTION_API_ISSUE_1474_WORKAROUND.md`

---

## 📝 Passo a Passo Completo (TESTADO E FUNCIONAL)

### Passo 0: Verificar Pré-Requisitos

**Verificar se n8n está rodando**:
```bash
docker ps | grep n8n
curl -I http://localhost:5678
```

**Resultado esperado**:
- Container `n8n-dev` com status "Up"
- HTTP 200 OK ou página do n8n carregando

**❌ Se n8n NÃO está rodando**:
```bash
# Volte para o QUICKSTART principal
cat docs/QUICKSTART.md

# Ou inicie todo o ambiente de desenvolvimento
cd docker
docker-compose -f docker-compose-dev.yml up -d
```

---

### Passo 1: Iniciar APENAS Containers Evolution API

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/docker
docker-compose -f docker-compose-dev.yml up -d evolution-postgres evolution-redis evolution-api
```

**Por que docker-compose?**
- ✅ Gerencia lifecycle completo (depends_on, healthchecks)
- ✅ Networking automático entre containers
- ✅ Restart policies e easy monitoring

**Aguardar inicialização**:
```bash
sleep 20
```

---

### Passo 2: Aplicar Workaround da Issue #1474

**🚨 CRÍTICO**: Evolution API v2.2.3 requer arquivo `.env` **físico** dentro do container para gerar QR Code!

```bash
# Copiar .env para dentro do container
docker cp /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/docker/.env e2bot-evolution-dev:/evolution/.env

# Reiniciar para carregar
docker restart e2bot-evolution-dev

# Aguardar reinicialização
sleep 20
```

**Verificar se .env foi copiado**:
```bash
docker exec e2bot-evolution-dev ls -la /evolution/.env
# Deve mostrar: -rw-r--r-- ... /evolution/.env
```

---

### Passo 3: Verificar Status da API

```bash
# Verificar se container está UP (não Restarting)
docker ps --filter "name=e2bot-evolution-dev" --format "{{.Names}}\t{{.Status}}"

# Testar conectividade
curl -I http://localhost:8080/manager/instances
# Deve retornar HTTP/1.1 200 OK ou 401 Unauthorized (ambos OK)
```

---

### Passo 4: Usar Evolution Helper Script

O helper script facilita todas as operações e auto-carrega EVOLUTION_API_KEY:

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
source ./scripts/evolution-helper.sh
evolution_status
```

**Verificar status da instância**:
```bash
evolution_status
```

**Possíveis resultados:**

#### ✅ Se `"state": "open"`:
```json
{"instance": {"instanceName": "e2-solucoes-bot", "state": "open"}}
```
**→ WhatsApp já conectado! Pule para Passo 7 (Testar Envio)**

#### ⏳ Se `"state": "connecting"`:
```json
{"instance": {"instanceName": "e2-solucoes-bot", "state": "connecting"}}
```
**→ Instância aguardando QR Code. Vá para Passo 5**

#### ❌ Se erro 404 ou `"state": "close"`:
```json
{"status":404,"error":"Not Found"}
```
**→ Precisa criar instância. Vá para Passo 5**

---

### Passo 5: Criar/Conectar Instância e Gerar QR Code

**Opção A: Recriar do zero (recomendado se já existe)**
```bash
evolution_recreate
```

Este comando faz:
1. ✅ Deleta instância antiga (se existir)
2. ✅ Aguarda 3 segundos
3. ✅ Cria nova instância
4. ✅ Aguarda Evolution gerar QR Code (5s)
5. ✅ Busca QR Code com retry automático (10 tentativas)
6. ✅ Salva como `qrcode.png`
7. ✅ Abre automaticamente a imagem

**Opção B: Apenas conectar (se já existe em "connecting")**
```bash
evolution_connect
```

---

### Passo 6: Escanear QR Code no WhatsApp

1. **O QR Code foi salvo** em: `qrcode.png` (raiz do projeto)

2. **Escanear com WhatsApp**:
   - Abra WhatsApp no celular
   - Menu (⋮) → **Aparelhos conectados**
   - **Conectar um aparelho**
   - Escaneie o QR Code

3. **⏰ QR Code expira em 60 segundos**
   - Se expirou, rode `evolution_connect` novamente

4. **Verificar conexão**:
```bash
evolution_status
# Deve mostrar: "state": "open"
```

---

### Passo 7: Testar Envio de Mensagem

Envie uma mensagem de teste:

```bash
# Substituir pelo SEU número (DDI + DDD + número)
source ./scripts/evolution-helper.sh
evolution_send "5561981755748" "🤖 Teste do Bot E2 Soluções!\n\nSe você recebeu esta mensagem, o WhatsApp está funcionando! ✅"
```

**Você deve receber a mensagem no WhatsApp em 2-3 segundos.**

---

### Passo 8: Configurar Credenciais no n8n

1. **Acesse o n8n**: http://localhost:5678

2. **Vá em Credentials** (menu lateral)

3. **Clique em "Add Credential"**

4. **Busque por**: "HTTP Header Auth"

5. **Configure**:
   - **Credential Name**: `Evolution API`
   - **Header Name**: `apikey`
   - **Header Value**: `ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891`
     *(Copie do `docker/.env` → `EVOLUTION_API_KEY`)*

6. **Clique em "Save"**

---

### Passo 9: Configurar Credencial PostgreSQL no n8n

**🚨 CRÍTICO**: Os workflows precisam de acesso ao banco de dados!

1. **Acesse o n8n**: http://localhost:5678

2. **Vá em Credentials** (menu lateral)

3. **Clique em "Add Credential"**

4. **Busque por**: "Postgres"

5. **Configure**:
   - **Credential Name**: `PostgreSQL - E2 Bot`
   - **Host**: `localhost`
   - **Database**: `e2_bot`
   - **User**: `postgres`
   - **Password**: `CHANGE_ME_TO_STRONG_PASSWORD`
     *(Copie do `docker/.env` → `POSTGRES_PASSWORD`)*
   - **Port**: `5432`
   - **SSL Mode**: `disable` (para desenvolvimento)

6. **Clique em "Save"**

7. **Teste a conexão**: Clique no botão "Test" para verificar

**✅ Resultado esperado**: "Connection successful"

**❌ Se falhar**: Verifique se o container PostgreSQL está rodando:
```bash
docker ps | grep postgres
# Deve mostrar: e2bot-postgres-dev
```

---

### Passo 10: Atualizar Workflows com Credenciais

Agora vamos configurar TODOS os workflows importados:

#### 10.1 - Workflow "01 - WhatsApp Handler"

1. **Abra o workflow** "01_main_whatsapp_handler"

2. **Encontre os nodes PostgreSQL** (ícone de elefante 🐘):
   - "Check Duplicate"
   - "Save Inbound Message"

3. **Para cada node PostgreSQL**:
   - Clique no node
   - Em "Credential to connect with"
   - Selecione: **PostgreSQL - E2 Bot**
   - Salve o node

4. **Salve o workflow**

#### 10.2 - Workflow "02 - AI Agent Conversation V1 (Menu-Based)"

1. **Abra o workflow** "02_ai_agent_conversation_V1_MENU"

2. **Encontre os nodes PostgreSQL** (ícone 🐘):
   - "Get Conversation State"
   - "Create New Conversation"
   - "Update Conversation State"
   - "Save Inbound Message"
   - "Save Outbound Message"
   - "Upsert Lead Data"

3. **Para cada node PostgreSQL**:
   - Clique no node
   - Em "Credential to connect with"
   - Selecione: **PostgreSQL - E2 Bot**
   - Salve o node

4. **Encontre os nodes HTTP Request** (ícone 🌐):
   - "Send WhatsApp Response"

5. **Para cada node HTTP Request**:
   - Clique no node
   - Em "Credential for HTTP Request Header Auth"
   - Selecione: **Evolution API**
   - Salve o node

6. **Salve o workflow**

#### 10.3 - Ativar os Workflows

**IMPORTANTE**: Os workflows precisam estar ATIVOS para receberem webhooks!

1. **Workflow "01 - WhatsApp Handler"**:
   - Abra o workflow
   - No canto superior direito, ative o toggle "Active"
   - ✅ Deve ficar verde

2. **Workflow "02 - AI Agent Conversation V1"**:
   - Abra o workflow
   - Ative o toggle "Active"
   - ✅ Deve ficar verde

---

### Passo 11: Configurar Webhook na Evolution API

Agora precisamos conectar a Evolution API ao n8n:

```bash
# Obter URL do webhook do n8n
echo "Webhook URL: http://localhost:5678/webhook/whatsapp-evolution"

# Configurar webhook na Evolution API
source ./scripts/evolution-helper.sh

curl -X POST "http://localhost:8080/webhook/set/e2-solucoes-bot" \
  -H "apikey: $EVOLUTION_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://n8n-dev:5678/webhook/whatsapp-evolution",
    "webhook_by_events": false,
    "webhook_base64": false,
    "events": [
      "MESSAGES_UPSERT",
      "MESSAGES_UPDATE",
      "MESSAGES_DELETE",
      "SEND_MESSAGE",
      "CONNECTION_UPDATE"
    ]
  }'
```

**✅ Resultado esperado**:
```json
{
  "webhook": {
    "url": "http://n8n-dev:5678/webhook/whatsapp-evolution",
    "enabled": true
  }
}
```

**💡 Nota**: Usamos `n8n-dev:5678` (nome do container) ao invés de `localhost:5678` porque a Evolution API precisa se comunicar com n8n pela rede Docker interna.

---

## ✅ Teste Completo End-to-End

Do seu celular, envie mensagem para o número conectado:
```
Oi
```

**Você deve receber**:
```
Olá! Bem-vindo à E2 Soluções! 👋

Escolha um serviço:
1️⃣ Energia Solar
2️⃣ Subestação
3️⃣ Projetos Elétricos
4️⃣ Armazenamento de Energia
5️⃣ Análise e Laudos
```

**Se recebeu**: ✅ **SUCESSO! Bot funcionando!**

---

## 🔧 Comandos Úteis (Evolution Helper)

Após carregar o helper (`source ./scripts/evolution-helper.sh`):

```bash
# Ver todos comandos disponíveis
evolution_help

# Verificar status
evolution_status

# Criar/recriar instância completa
evolution_recreate

# Apenas conectar/gerar QR
evolution_connect

# Apenas gerar QR (com retry)
evolution_qrcode

# Deletar instância
evolution_delete

# Criar nova instância
evolution_create

# Enviar mensagem
evolution_send "5561981755748" "Mensagem de teste"
```

---

## ❌ Troubleshooting

### Problema: QR Code retorna 404

**Sintoma**:
```
❌ Não foi possível obter QR Code após 10 tentativas.
```

**Causa**: Workaround da Issue #1474 não foi aplicado (`.env` não está no container)

**Solução**:
```bash
# 1. Copiar .env para container
docker cp docker/.env e2bot-evolution-dev:/evolution/.env

# 2. Reiniciar
docker restart e2bot-evolution-dev && sleep 20

# 3. Tentar novamente
source ./scripts/evolution-helper.sh
evolution_connect
```

---

### Problema: Container em "Restarting"

```bash
# Ver logs
docker logs e2bot-evolution-dev --tail 50
```

**Causas comuns:**

1. **"Database provider invalid"** → Limpeza nuclear:
```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
./scripts/nuclear-cleanup-evolution.sh

# Depois recomeçar do Passo 1
```

2. **Porta 8080 em uso**:
```bash
sudo lsof -i :8080
sudo kill -9 <PID>
```

---

### Problema: 401 Unauthorized

**Causa**: EVOLUTION_API_KEY não carregada

**Solução**: Use sempre `evolution-helper.sh`:
```bash
source ./scripts/evolution-helper.sh
evolution_status
```

---

### Problema: 403 Forbidden "instance already in use"

**Solução**:
```bash
evolution_recreate  # Deleta e recria automaticamente
```

---

### Problema: QR Code expirou

```bash
evolution_connect  # Gera novo QR code (60s de validade)
```

---

### Problema: State é "close"

```bash
evolution_recreate  # Deleta e recria completamente
```

---

## 📊 Scripts Disponíveis

### `evolution-helper.sh` (RECOMENDADO)
```bash
source ./scripts/evolution-helper.sh
```
- ✅ Auto-carrega EVOLUTION_API_KEY
- ✅ Funções convenientes
- ✅ Retry automático
- ✅ QR code management

### `fix-evolution-startup.sh`
```bash
./scripts/fix-evolution-startup.sh
```
- ✅ Limpeza + reinicialização completa
- ✅ Validação de ambiente
- ✅ Testes de conectividade

### `nuclear-cleanup-evolution.sh`
```bash
./scripts/nuclear-cleanup-evolution.sh
```
- ⚠️ Remove **TUDO** (containers + volumes + cache)
- Use apenas se resetar completamente

### `start-evolution.sh`
```bash
./scripts/start-evolution.sh
```
- ✅ Inicialização limpa via docker-compose
- ✅ Aguarda e valida
- ❌ **NÃO aplica workaround** (você precisa aplicar manualmente)

---

## 🎯 Resumo do Fluxo Correto

```
1. docker-compose up -d (Iniciar containers)
        ↓
2. docker cp .env (Workaround Issue #1474) ← CRÍTICO!
        ↓
3. docker restart (Carregar .env copiado)
        ↓
4. source evolution-helper.sh (Funções convenientes)
        ↓
5. evolution_recreate (Criar + QR Code)
        ↓
6. Escanear QR Code (WhatsApp celular)
        ↓
7. evolution_status → "open" ✅
```

---

## 📚 Documentação Completa

- **Workaround Issue #1474**: `docs/EVOLUTION_API_ISSUE_1474_WORKAROUND.md`
- **Setup Detalhado**: `docs/Setups/SETUP_EVOLUTION_API.md`
- **Validação Sprint 0.1**: `docs/validation/SPRINT_0.1_VALIDATION.md`

---

## ✅ Checklist Final

- [ ] Containers UP sem "Restarting"
- [ ] `.env` copiado para container (`docker exec ... ls -la /evolution/.env`)
- [ ] HTTP 200 OK no teste de conectividade
- [ ] `evolution_status` retorna `"state": "open"`
- [ ] Mensagem de teste enviada e recebida
- [ ] Credencial configurada no n8n
- [ ] Workflow v1 atualizado
- [ ] Teste end-to-end funcionando

**Tudo OK?** ✅ **Evolution API configurada com sucesso!**

---

## 🚨 Regras de Ouro

### ✅ SEMPRE FAÇA
1. Use `docker-compose` para iniciar Evolution
2. **Copie `.env` para dentro do container** (workaround Issue #1474)
3. **Reinicie após copiar** `.env`
4. Use `evolution-helper.sh` para todas operações

### ❌ NUNCA FAÇA
1. ~~Use `docker run` standalone~~
2. ~~Confie que env_file do docker-compose funciona~~ (Issue #1474)
3. ~~Ignore o workaround de copiar .env~~

---

**Última atualização**: 2025-12-17 (Descoberta: QR Code também requer workaround!)

**Próximo passo**: Validação completa conforme `docs/validation/SPRINT_0.1_VALIDATION.md`
