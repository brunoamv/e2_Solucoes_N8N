# Cloudflare DNS — Configuração de Subdomínios E2 Bot

**Domínio base:** climacocal.com.br  
**Objetivo:** Criar subdomínios para n8n e Evolution API do E2 Bot  
**Pré-requisito:** Acesso ao painel Cloudflare da conta que gerencia climacocal.com.br

---

## Subdomínios a criar

| Subdomínio completo | Serviço |
|---------------------|---------|
| `n8n.climacocal.com.br` | n8n (interface + webhooks) |
| `e2solucoeswhatsapp.climacocal.com.br` | Evolution API (WhatsApp) |

---

## Passo a Passo

### 1. Obter o IP do servidor

No servidor climacocal.com.br, rode:

```bash
curl -s ifconfig.me
```

Anote o IP. Exemplo: `203.0.113.42`

---

### 2. Acessar o painel Cloudflare

1. Acesse **dash.cloudflare.com**
2. Faça login com a conta que gerencia o domínio `climacocal.com.br`
3. Clique no domínio **climacocal.com.br** na lista de sites

---

### 3. Navegar para DNS

No menu lateral esquerdo, clique em **DNS → Records**

---

### 4. Criar registro para o n8n

Clique no botão **+ Add record** e preencha:

| Campo | Valor |
|-------|-------|
| **Type** | `A` |
| **Name** | `n8n` |
| **IPv4 address** | `<IP do servidor>` |
| **Proxy status** | ☁️ **DNS only** (nuvem CINZA) |
| **TTL** | `Auto` |

Clique em **Save**.

---

### 5. Criar registro para o Evolution API (WhatsApp)

Clique novamente em **+ Add record**:

| Campo | Valor |
|-------|-------|
| **Type** | `A` |
| **Name** | `e2solucoeswhatsapp` |
| **IPv4 address** | `<IP do servidor>` |
| **Proxy status** | ☁️ **DNS only** (nuvem CINZA) |
| **TTL** | `Auto` |

Clique em **Save**.

---

### ⚠️ Por que Proxy DESLIGADO (DNS only)?

O Traefik usa Let's Encrypt com **HTTP-01 challenge** para emitir certificados SSL.
Esse processo exige que o Cloudflare repasse a requisição diretamente para o servidor.

Com o proxy **ligado** (nuvem laranja), o Cloudflare intercepta o tráfego e o Let's Encrypt
não consegue validar o domínio → **certificado não é emitido → HTTPS quebra**.

```
Proxy LIGADO  ❌  →  Let's Encrypt não valida  →  Traefik sem certificado
Proxy DESLIGADO ✅  →  Let's Encrypt valida    →  Traefik emite certificado
```

> Após o deploy estar estável (com HTTPS funcionando), você pode ligar o proxy Cloudflare
> se quiser o CDN e proteção DDoS. Mas para o primeiro deploy, **mantenha desligado**.

---

### 6. Verificar propagação DNS

Aguarde 1–5 minutos após salvar os registros e verifique **no servidor**:

```bash
dig +short n8n.climacocal.com.br
dig +short e2solucoeswhatsapp.climacocal.com.br
```

Ambos devem retornar o IP do servidor. Enquanto não retornar, não adianta subir os containers.

Verificação alternativa (de qualquer máquina):
```bash
nslookup n8n.climacocal.com.br
nslookup e2solucoeswhatsapp.climacocal.com.br
```

---

### 7. Fazer o deploy

Com os dois registros propagados:

```bash
cd /home/bruno/storage/e2_Solucoes_N8N/e2-solucoes-bot

# Subir os containers
docker compose -f docker/docker-compose-prd.yml --env-file docker/.env up -d

# Acompanhar os logs (Ctrl+C para sair)
docker compose -f docker/docker-compose-prd.yml logs -f

# Verificar status de todos os containers
docker compose -f docker/docker-compose-prd.yml ps
```

---

### 8. Verificar certificados SSL

O Traefik emite os certificados automaticamente na primeira requisição a cada subdomínio.
Para confirmar que funcionou:

```bash
# Testar HTTPS (aguardar ~30s após subir os containers)
curl -I https://n8n.climacocal.com.br
# Esperado: HTTP/2 200 ou 401 (Basic Auth ativo)

curl -I https://e2solucoeswhatsapp.climacocal.com.br/health
# Esperado: HTTP/2 200

# Ver logs do Traefik para confirmar emissão do cert
docker logs traefik 2>&1 | grep -iE "certificate|acme|n8n.clima|e2solucoeswhatsapp" | tail -20
```

---

## Resultado esperado após o deploy

| URL | Serviço | Auth |
|-----|---------|------|
| `https://n8n.climacocal.com.br` | n8n UI | admin / CoraRosa |
| `https://e2solucoeswhatsapp.climacocal.com.br` | Evolution API | API Key no header |
| `https://n8n.climacocal.com.br/webhook/whatsapp` | Webhook WF01 | Público (Evolution envia aqui) |

---

## Troubleshooting

### Certificado não emitido (erro 526 / HTTPS falha)

```bash
# Ver erros do Traefik
docker logs traefik 2>&1 | grep -i "error\|acme\|certif" | tail -30
```

Causas comuns:
- DNS ainda não propagou → aguardar mais e rodar `dig` novamente
- Proxy Cloudflare ligado → desligar (nuvem cinza)
- Porta 80 bloqueada no servidor → verificar firewall (`ufw status`)

### Container não sobe

```bash
docker compose -f docker/docker-compose-prd.yml logs <nome-do-container>
# Exemplos:
docker compose -f docker/docker-compose-prd.yml logs e2bot-n8n-prd
docker compose -f docker/docker-compose-prd.yml logs e2bot-postgres-prd
```

### Conectar ao banco para verificar schema

```bash
docker exec e2bot-postgres-prd psql -U postgres -d e2bot_prod \
  -c "\dt"
# Deve listar: conversations, appointments, email_logs, etc.
```
