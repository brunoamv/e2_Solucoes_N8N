# Setup Evolution API (WhatsApp Integration)

## Visão Geral

Guia completo para configurar a Evolution API, que conecta o bot E2 Soluções ao WhatsApp Business, permitindo envio e recebimento de mensagens, imagens, áudios e gerenciamento de conversas.

## Pré-requisitos

- Número de telefone dedicado para o bot (com chip ativo)
- Smartphone para leitura do QR Code (WhatsApp instalado)
- Servidor/VPS para hospedar Evolution API (ou usar instância cloud)
- Docker e Docker Compose instalados (para self-hosted)

## Opção A: Evolution API Self-Hosted (Recomendado)

### A.1. Instalar Evolution API via Docker

#### A.1.1. Criar Estrutura de Diretórios

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Criar diretórios
mkdir -p docker/evolution-api/{instances,store}
chmod 755 docker/evolution-api
```

#### A.1.2. Configurar docker-compose

Edite `docker/docker-compose-dev.yml` e adicione o serviço:

```yaml
services:
  # ... outros serviços

  evolution-api:
    image: atendai/evolution-api:v2.1.1
    container_name: e2_evolution_api
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./evolution-api/instances:/evolution/instances
      - ./evolution-api/store:/evolution/store
    environment:
      # Server
      - SERVER_TYPE=http
      - SERVER_PORT=8080
      - SERVER_URL=http://localhost:8080

      # Database (usar PostgreSQL compartilhado)
      - DATABASE_ENABLED=true
      - DATABASE_PROVIDER=postgresql
      - DATABASE_CONNECTION_URI=${DATABASE_URL}
      - DATABASE_SAVE_DATA_INSTANCE=true
      - DATABASE_SAVE_DATA_NEW_MESSAGE=true
      - DATABASE_SAVE_MESSAGE_UPDATE=true

      # Auth
      - AUTHENTICATION_API_KEY=${EVOLUTION_API_KEY}
      - AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES=true

      # Webhook Global
      - WEBHOOK_GLOBAL_URL=${N8N_WEBHOOK_URL}/webhook/whatsapp-messages
      - WEBHOOK_GLOBAL_ENABLED=true
      - WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS=true

      # Events
      - WEBHOOK_EVENTS_APPLICATION_STARTUP=false
      - WEBHOOK_EVENTS_QRCODE_UPDATED=true
      - WEBHOOK_EVENTS_MESSAGES_SET=true
      - WEBHOOK_EVENTS_MESSAGES_UPSERT=true
      - WEBHOOK_EVENTS_MESSAGES_UPDATE=true
      - WEBHOOK_EVENTS_MESSAGES_DELETE=false
      - WEBHOOK_EVENTS_SEND_MESSAGE=false
      - WEBHOOK_EVENTS_CONNECTION_UPDATE=true

      # Log
      - LOG_LEVEL=ERROR
      - LOG_COLOR=true
      - LOG_BAILEYS=error

    networks:
      - e2-network
    depends_on:
      - postgres

networks:
  e2-network:
    driver: bridge
```

#### A.1.3. Configurar Variáveis de Ambiente

Edite `docker/.env.dev`:

```bash
# --- Evolution API (WhatsApp) ---
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=$(openssl rand -hex 32)  # Gerar key aleatória
EVOLUTION_INSTANCE_NAME=e2-solucoes-bot

# Webhook URL (n8n receberá mensagens)
N8N_WEBHOOK_URL=http://n8n:5678
```

#### A.1.4. Iniciar Evolution API

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/docker

# Iniciar serviço
docker-compose -f docker-compose-dev.yml up -d evolution-api

# Ver logs
docker-compose logs -f evolution-api

# Aguardar mensagem: "Evolution API started successfully"
```

Acesse: http://localhost:8080

---

### A.2. Criar Instância WhatsApp

#### A.2.1. Criar Instância via API

```bash
# Carregar variáveis
set -a
source docker/.env.dev
set +a

# Criar instância
curl -X POST "http://localhost:8080/instance/create" \
  -H "apikey: ${EVOLUTION_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "e2-solucoes-bot",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }'
```

**Resposta esperada:**

```json
{
  "instance": {
    "instanceName": "e2-solucoes-bot",
    "status": "created"
  },
  "hash": {
    "apikey": "xxxxx"
  },
  "qrcode": {
    "code": "data:image/png;base64,iVBOR..."
  }
}
```

#### A.2.2. Conectar WhatsApp via QR Code

**Opção 1: QR Code via API**

```bash
# Gerar QR Code
curl "http://localhost:8080/instance/qrcode/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}"
```

Resposta retorna base64. Decodificar e exibir:

```bash
# Salvar imagem
curl "http://localhost:8080/instance/qrcode/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}" \
  | jq -r '.qrcode.code' \
  | sed 's/data:image\/png;base64,//' \
  | base64 -d > qrcode.png

# Abrir imagem
xdg-open qrcode.png
# OU
open qrcode.png  # macOS
```

**Opção 2: QR Code via Interface Web**

Acesse: http://localhost:8080/manager

(Se disponível na versão instalada)

**Escanear QR Code:**

1. No seu smartphone, abra o WhatsApp
2. Vá em: **Menu (⋮) → Aparelhos conectados**
3. Clique em **"Conectar um aparelho"**
4. Escaneie o QR Code exibido
5. Aguarde confirmação

#### A.2.3. Verificar Conexão

```bash
# Verificar status da instância
curl "http://localhost:8080/instance/connectionState/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}"
```

**Resposta esperada:**

```json
{
  "instance": {
    "instanceName": "e2-solucoes-bot",
    "state": "open"
  }
}
```

**Estados possíveis:**
- `open`: Conectado e funcionando
- `connecting`: Conectando
- `close`: Desconectado

---

## Opção B: Evolution API Cloud (Alternativa)

### B.1. Usar Provedor Cloud

Provedores que oferecem Evolution API gerenciada:

1. **Z-API** (https://z-api.io)
2. **Chat-API** (https://chat-api.com)
3. **WPPConnect Cloud** (https://wppconnect.io)

### B.2. Configurar Credenciais Cloud

Se usar provedor cloud, configure:

```bash
# .env.dev
EVOLUTION_API_URL=https://api.provider.com
EVOLUTION_API_KEY=your_api_key_here
EVOLUTION_INSTANCE_NAME=e2-solucoes-bot
```

---

## Etapa 3: Configurar Webhooks

### 3.1. Webhook para Mensagens Recebidas

O webhook já foi configurado no docker-compose:

```yaml
WEBHOOK_GLOBAL_URL=http://n8n:5678/webhook/whatsapp-messages
```

### 3.2. Testar Webhook

Enviar mensagem teste para o número conectado e verificar n8n:

```bash
# Ver logs do n8n
docker-compose logs -f n8n

# Deve aparecer: "Webhook received: whatsapp-messages"
```

### 3.3. Verificar Webhook no Banco

```sql
-- Ver mensagens recebidas
SELECT
  id,
  wa_message_id,
  sender_phone,
  message_text,
  created_at
FROM messages
WHERE direction = 'incoming'
ORDER BY created_at DESC
LIMIT 10;
```

---

## Etapa 4: Testar Funcionalidades

### 4.1. Enviar Mensagem de Texto

```bash
curl -X POST "http://localhost:8080/message/sendText/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "5562999999999",
    "text": "Olá! Este é um teste do bot E2 Soluções."
  }'
```

### 4.2. Enviar Imagem

```bash
curl -X POST "http://localhost:8080/message/sendMedia/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "5562999999999",
    "mediatype": "image",
    "media": "https://example.com/imagem.jpg",
    "caption": "Confira nossa imagem!"
  }'
```

### 4.3. Enviar Documento (PDF)

```bash
curl -X POST "http://localhost:8080/message/sendMedia/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "5562999999999",
    "mediatype": "document",
    "media": "https://example.com/proposta.pdf",
    "fileName": "Proposta_Energia_Solar.pdf"
  }'
```

### 4.4. Verificar Perfil do Contato

```bash
curl "http://localhost:8080/chat/fetchProfilePictureUrl/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "5562999999999"
  }'
```

---

## Etapa 5: Configurar n8n Workflow

### 5.1. Importar Workflow Principal

```bash
# Importar workflow de handler principal
# Arquivo: n8n/workflows/01_main_whatsapp_handler.json
```

No n8n:
1. **Workflows → Import from File**
2. Selecionar: `n8n/workflows/01_main_whatsapp_handler.json`
3. Ativar workflow

### 5.2. Configurar Credenciais no n8n

1. **Credentials → Add Credential**
2. Buscar: "HTTP Header Auth"
3. Nome: "Evolution API"
4. Header Name: `apikey`
5. Header Value: `${EVOLUTION_API_KEY}` (do .env)
6. Salvar

### 5.3. Testar Workflow

Enviar mensagem para o número do bot:

```
Oi
```

Deve receber resposta automática:

```
Olá! Bem-vindo à E2 Soluções! 👋

Sou o assistente virtual e estou aqui para ajudar.

Em que posso auxiliar hoje?
```

---

## Etapa 6: Gerenciar Instância

### 6.1. Logout (Desconectar)

```bash
curl -X DELETE "http://localhost:8080/instance/logout/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}"
```

### 6.2. Reconectar

Após logout, gerar novo QR Code e escanear novamente (Step A.2).

### 6.3. Deletar Instância

```bash
curl -X DELETE "http://localhost:8080/instance/delete/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}"
```

**CUIDADO:** Isso apaga todos os dados da instância!

### 6.4. Listar Instâncias

```bash
curl "http://localhost:8080/instance/fetchInstances" \
  -H "apikey: ${EVOLUTION_API_KEY}"
```

---

## Etapa 7: Backup e Recuperação

### 7.1. Backup de Instância

```bash
# Parar container
docker-compose stop evolution-api

# Backup dos dados
cd docker
tar -czf evolution-backup-$(date +%Y%m%d).tar.gz evolution-api/

# Copiar para local seguro
cp evolution-backup-*.tar.gz ~/backups/
```

### 7.2. Restaurar Backup

```bash
# Parar container
docker-compose stop evolution-api

# Restaurar
cd docker
tar -xzf ~/backups/evolution-backup-20240115.tar.gz

# Reiniciar
docker-compose start evolution-api
```

---

## Etapa 8: Monitoramento

### 8.1. Verificar Status via API

```bash
#!/bin/bash
# scripts/check-whatsapp-status.sh

set -a
source docker/.env.dev
set +a

echo "🔍 Verificando status do WhatsApp..."

STATUS=$(curl -s "http://localhost:8080/instance/connectionState/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}" \
  | jq -r '.instance.state')

if [ "$STATUS" = "open" ]; then
  echo "✅ WhatsApp conectado"
else
  echo "❌ WhatsApp desconectado (status: $STATUS)"
  echo "🔧 Execute: docker-compose restart evolution-api"
fi
```

### 8.2. Monitorar Logs

```bash
# Logs em tempo real
docker-compose logs -f evolution-api

# Últimas 100 linhas
docker-compose logs --tail=100 evolution-api

# Filtrar apenas erros
docker-compose logs evolution-api | grep ERROR
```

### 8.3. Estatísticas de Mensagens

```sql
-- Total de mensagens (últimas 24h)
SELECT
  direction,
  COUNT(*) as total,
  COUNT(DISTINCT sender_phone) as contatos_unicos
FROM messages
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY direction;

-- Mensagens por hora (hoje)
SELECT
  EXTRACT(HOUR FROM created_at) as hora,
  COUNT(*) as total
FROM messages
WHERE DATE(created_at) = CURRENT_DATE
GROUP BY hora
ORDER BY hora;
```

---

## Etapa 9: Segurança

### 9.1. Proteger API Key

```bash
# Gerar API key forte
EVOLUTION_API_KEY=$(openssl rand -hex 32)
echo "EVOLUTION_API_KEY=${EVOLUTION_API_KEY}" >> docker/.env.dev

# Nunca commitar .env
grep -q ".env" .gitignore || echo ".env*" >> .gitignore
```

### 9.2. Restringir Acesso (Produção)

```yaml
# docker-compose.yml (produção)
services:
  evolution-api:
    # ... config
    environment:
      - AUTHENTICATION_API_KEY=${EVOLUTION_API_KEY}
      # Adicionar IP whitelist
      - AUTHENTICATION_ALLOW_IPS=127.0.0.1,IP_DO_N8N
```

### 9.3. HTTPS (Produção)

Usar reverse proxy (Traefik, Nginx) com SSL:

```yaml
# Traefik labels
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.evolution.rule=Host(`whatsapp.seudominio.com`)"
  - "traefik.http.routers.evolution.entrypoints=websecure"
  - "traefik.http.routers.evolution.tls.certresolver=letsencrypt"
```

---

## Etapa 10: Troubleshooting

### Problema: QR Code não gera

**Causa:** Instância não foi criada ou expirou

**Solução:**
```bash
# Recriar instância
curl -X DELETE "http://localhost:8080/instance/delete/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}"

# Criar novamente (Step A.2)
```

### Problema: "Disconnected" após conectar

**Causa:** WhatsApp detectou uso não autorizado

**Solução:**
- Usar número novo (não usado em outros bots)
- Aguardar 24-48h para tentar novamente
- Considerar WhatsApp Business API oficial (pago)

### Problema: Mensagens não chegam ao n8n

**Causa:** Webhook não configurado corretamente

**Solução:**
```bash
# Verificar webhook
curl "http://localhost:8080/webhook/find/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}"

# Reconfigurar se necessário
curl -X POST "http://localhost:8080/webhook/set/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://n8n:5678/webhook/whatsapp-messages",
    "enabled": true,
    "events": ["messages.upsert"]
  }'
```

### Problema: Evolution API não inicia

**Causa:** Porta 8080 ocupada ou erro no banco

**Solução:**
```bash
# Verificar porta
lsof -i :8080

# Ver logs detalhados
docker-compose logs evolution-api

# Verificar conexão com banco
docker-compose exec postgres psql -U e2bot -d e2bot -c "\conninfo"
```

### Problema: Erro "Rate limit exceeded"

**Causa:** Muitas mensagens enviadas em pouco tempo

**Solução:**
- WhatsApp limita ~40 msgs/minuto
- Implementar fila de envio no n8n
- Adicionar delay entre mensagens (3-5 segundos)

---

## Limites e Boas Práticas

### Limites do WhatsApp

```yaml
Mensagens:
  - Envio: ~40 msgs/minuto
  - Recebimento: Ilimitado

Mídia:
  - Imagem: Max 5MB (recomendado: 1MB)
  - Vídeo: Max 16MB (recomendado: 5MB)
  - Áudio: Max 16MB
  - Documento: Max 100MB (recomendado: 10MB)

Conexões:
  - Max 4 dispositivos conectados simultaneamente
  - QR Code expira em 60 segundos
```

### Boas Práticas

1. **Evitar Spam:**
   - Não enviar mensagens não solicitadas
   - Respeitar horário comercial (8h-18h)
   - Sempre permitir opt-out

2. **Performance:**
   - Usar webhook para receber (não polling)
   - Implementar fila para envio
   - Cachear dados de contatos

3. **Backup:**
   - Backup diário automático
   - Guardar credenciais em local seguro
   - Ter plano de contingência (número alternativo)

---

## Recursos Adicionais

- **Evolution API Docs**: https://doc.evolution-api.com/
- **Evolution API GitHub**: https://github.com/EvolutionAPI/evolution-api
- **WhatsApp Business API**: https://business.whatsapp.com/products/business-api
- **n8n WhatsApp Nodes**: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.whatsapp/

---

## Checklist de Configuração

- [ ] Evolution API instalada via Docker
- [ ] Serviço evolution-api iniciado e rodando
- [ ] API Key gerada e configurada no .env
- [ ] Instância WhatsApp criada via API
- [ ] QR Code gerado e escaneado com sucesso
- [ ] Conexão verificada (state: open)
- [ ] Webhook configurado para n8n
- [ ] Teste de mensagem de texto realizado
- [ ] Teste de envio de mídia realizado
- [ ] Workflow n8n importado e ativado
- [ ] Credenciais configuradas no n8n
- [ ] Teste end-to-end (enviar msg → receber resposta)
- [ ] Backup da instância configurado
- [ ] Monitoramento de status ativo
- [ ] Logs sendo coletados corretamente
- [ ] Segurança (API key, firewall) configurada

---

**Configuração completa!** O bot agora está conectado ao WhatsApp e pode enviar/receber mensagens automaticamente.
