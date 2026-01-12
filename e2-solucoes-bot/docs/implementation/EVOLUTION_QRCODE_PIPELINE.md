# Pipeline de Geração de QR Code - Evolution API

## 🚨 Problema Identificado

O Evolution API v2.2.3 **sempre tenta restaurar sessões antigas** ao iniciar, o que causa:

1. **Crash Loop**: Tenta carregar milhares de mensagens antigas → esgota recursos → SIGTERM
2. **Sem QR Code**: Sessão corrompida impede geração de novo QR Code
3. **Stream Errors**: `code 515`, `code 503`, `code 401`, `device_removed`

**Logs Característicos**:
```
create instance { instanceName: 'e2-solucoes-bot', qrcode: true }
recv 900 chats, 900 contacts, 1000 msgs (is latest: true, progress: 100%), type: 0
{"level":50,"time":...,"node":{"tag":"stream:error","attrs":{"code":"515"}},"msg":"stream errored out"}
npm error signal SIGTERM
```

## ✅ Solução Definitiva: Pipeline de 3 Passos

### Pipeline Completo (SEMPRE usar este procedimento)

```bash
#!/bin/bash
# Script: scripts/evolution-fresh-start.sh
# Uso: ./scripts/evolution-fresh-start.sh

echo "🔄 Pipeline de Inicialização Limpa do Evolution API"
echo "=================================================="
echo ""

# Passo 1: Parar e Limpar
echo "1️⃣ Parando Evolution e removendo volumes corrompidos..."
docker-compose -f docker/docker-compose-dev.yml stop evolution-api
docker rm -f e2bot-evolution-dev 2>/dev/null || true
docker volume rm e2bot_evolution_instances e2bot_evolution_store 2>/dev/null || true
echo "✅ Limpeza completa"
echo ""

# Passo 2: Recriar com Volumes Limpos
echo "2️⃣ Recriando Evolution API com volumes limpos..."
docker-compose -f docker/docker-compose-dev.yml up -d evolution-api
echo "⏳ Aguardando inicialização (30s)..."
sleep 30
echo "✅ Evolution recriado"
echo ""

# Passo 3: Verificar API + Criar Instância + QR Code
echo "3️⃣ Verificando API e gerando QR Code..."

# Verificar se API está respondendo
RETRIES=0
MAX_RETRIES=12
until curl -f http://localhost:8080 >/dev/null 2>&1 || [ $RETRIES -eq $MAX_RETRIES ]; do
    RETRIES=$((RETRIES + 1))
    echo "   Tentativa $RETRIES/$MAX_RETRIES - Aguardando API..."
    sleep 5
done

if [ $RETRIES -eq $MAX_RETRIES ]; then
    echo "❌ Evolution API não respondeu após $((MAX_RETRIES * 5))s"
    echo "🔍 Verificar logs: docker logs e2bot-evolution-dev"
    exit 1
fi

echo "✅ API respondendo!"
echo ""

# Criar instância
echo "4️⃣ Criando instância WhatsApp..."
API_KEY="ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"

CREATE_RESPONSE=$(curl -s -X POST "http://localhost:8080/instance/create" \
  -H "apikey: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "e2-solucoes-bot",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }')

echo "$CREATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CREATE_RESPONSE"

# Verificar se criou com sucesso
if echo "$CREATE_RESPONSE" | grep -q "instanceName"; then
    echo "✅ Instância criada com sucesso"
else
    echo "❌ Erro ao criar instância"
    exit 1
fi

echo ""
echo "⏳ Aguardando 5s para instância inicializar..."
sleep 5

# Gerar QR Code
echo "5️⃣ Gerando QR Code..."

for i in {1..10}; do
    echo "   Tentativa $i/10..."

    QR_RESPONSE=$(curl -s -X GET "http://localhost:8080/instance/connect/e2-solucoes-bot" \
      -H "apikey: $API_KEY")

    # Extrair base64
    BASE64=$(echo "$QR_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('base64', ''))
except:
    pass
" 2>/dev/null)

    if [ -n "$BASE64" ] && [ "$BASE64" != "null" ]; then
        # Salvar QR Code
        echo "$BASE64" | sed 's/data:image\/png;base64,//' | base64 -d > qrcode.png 2>/dev/null

        if [ -f qrcode.png ] && [ -s qrcode.png ]; then
            echo ""
            echo "✅ QR Code salvo em: qrcode.png"
            echo "📱 Abrindo QR Code..."
            xdg-open qrcode.png 2>/dev/null || open qrcode.png 2>/dev/null || echo "⚠️  Abra manualmente: qrcode.png"
            echo ""
            echo "=================================================="
            echo "⏰ QR Code expira em 60 segundos!"
            echo "📱 Escaneie agora com WhatsApp:"
            echo "   Menu → Aparelhos conectados → Conectar um aparelho"
            echo "=================================================="
            exit 0
        fi
    fi

    sleep 3
done

echo "❌ Não foi possível gerar QR Code após 10 tentativas"
echo ""
echo "🔍 Diagnóstico:"
echo "1. Verificar logs: docker logs e2bot-evolution-dev"
echo "2. Verificar status: docker ps --filter 'name=evolution'"
echo "3. Tentar manualmente:"
echo "   curl -X GET 'http://localhost:8080/instance/connect/e2-solucoes-bot' \\"
echo "     -H 'apikey: $API_KEY'"
exit 1
```

### Criar Script Executável

```bash
# Criar o script
cat > scripts/evolution-fresh-start.sh << 'SCRIPT_CONTENT'
[cole o conteúdo acima]
SCRIPT_CONTENT

# Dar permissão de execução
chmod +x scripts/evolution-fresh-start.sh
```

## 📋 Uso do Pipeline

### Situação 1: Primeira Configuração
```bash
./scripts/evolution-fresh-start.sh
# Resultado: QR Code salvo em qrcode.png
# Ação: Escanear com WhatsApp em 60s
```

### Situação 2: Evolution em Crash Loop
```bash
# Mesmo procedimento
./scripts/evolution-fresh-start.sh
```

### Situação 3: QR Code Expirou
```bash
# 1. Deletar instância antiga
curl -X DELETE "http://localhost:8080/instance/delete/e2-solucoes-bot" \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"

# 2. Reexecutar pipeline
./scripts/evolution-fresh-start.sh
```

### Situação 4: Número Foi Desconectado
```bash
# Mesmo procedimento - volumes limpos forçam nova conexão
./scripts/evolution-fresh-start.sh
```

## 🔍 Troubleshooting

### Problema: Script retorna erro no Passo 3
**Causa**: Evolution ainda não terminou de inicializar

**Solução**:
```bash
# Aguardar mais tempo e verificar logs
docker logs -f e2bot-evolution-dev

# Reexecutar apenas Passo 3-5
API_KEY="ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
curl -s -X POST "http://localhost:8080/instance/create" \
  -H "apikey: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"instanceName": "e2-solucoes-bot", "qrcode": true, "integration": "WHATSAPP-BAILEYS"}'
```

### Problema: QR Code não aparece após 10 tentativas
**Causa**: Instância já existe ou está em estado inválido

**Solução**:
```bash
# Deletar e recriar
curl -X DELETE "http://localhost:8080/instance/delete/e2-solucoes-bot" \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"

# Aguardar 3s e tentar novamente
sleep 3
curl -X POST "http://localhost:8080/instance/create" ...
```

### Problema: Evolution continua crashando mesmo com volumes limpos
**Causa**: Problema com configuração ou recursos insuficientes

**Solução**:
```bash
# 1. Verificar variáveis de ambiente
docker exec e2bot-evolution-dev env | grep -E "^(AUTHENTICATION|DATABASE|WEBHOOK)"

# 2. Aumentar recursos (docker-compose-dev.yml)
evolution-api:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G

# 3. Limpar banco de dados Evolution
docker exec -it e2bot-evolution-postgres psql -U evolution -d evolution -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# 4. Reexecutar pipeline
./scripts/evolution-fresh-start.sh
```

## 📊 Checklist de Validação

Após executar o pipeline, verificar:

- [ ] ✅ Evolution API status: `healthy` (não `unhealthy` ou `starting`)
- [ ] ✅ API respondendo em `http://localhost:8080`
- [ ] ✅ Instância criada: `e2-solucoes-bot`
- [ ] ✅ QR Code salvo em `qrcode.png` (arquivo PNG válido)
- [ ] ✅ Logs sem `SIGTERM` ou `stream errored out`
- [ ] ✅ WhatsApp conectado após escanear QR Code

**Verificar Connection State**:
```bash
curl -s "http://localhost:8080/instance/connectionState/e2-solucoes-bot" \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq .

# Resultado esperado após escanear QR:
# {"instance": {"instanceName": "e2-solucoes-bot", "state": "open"}}
```

## 🎯 Integração com Workflow n8n

Após conectar WhatsApp com sucesso:

1. **Webhook já está configurado**: `WEBHOOK_GLOBAL_URL=http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution`
2. **Testar fluxo**:
   ```bash
   # Enviar "oi" do WhatsApp para o número logado

   # Monitorar n8n
   docker logs -f e2bot-n8n-dev 2>&1 | grep -E "whatsapp-evolution|Webhook WhatsApp"

   # Ver execuções: http://localhost:5678/home/executions
   ```

## 📝 Notas Importantes

1. **SEMPRE use o pipeline completo** ao reiniciar Evolution
2. **NUNCA tente restaurar sessões antigas** - volumes limpos sempre
3. **QR Code expira em 60s** - esteja pronto para escanear imediatamente
4. **Número só pode estar logado em 1 dispositivo** - desconecte outros antes

---
**Criado**: 2026-01-02 19:00
**Testado**: Evolution API v2.2.3
**Status**: Pipeline validado e documentado
