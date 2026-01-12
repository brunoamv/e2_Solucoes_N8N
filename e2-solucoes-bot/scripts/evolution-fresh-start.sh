#!/bin/bash
# ============================================================================
# Evolution API Fresh Start Pipeline
# ============================================================================
# Garante inicialização limpa do Evolution sem sessões corrompidas
# Uso: ./scripts/evolution-fresh-start.sh
# ============================================================================

set -e  # Sair em caso de erro

echo "🔄 Pipeline de Inicialização Limpa do Evolution API"
echo "=================================================="
echo ""

# Passo 1: Parar e Limpar
echo "1️⃣ Parando Evolution e removendo volumes corrompidos..."
cd "$(dirname "$0")/.." || exit 1  # Garantir que estamos no diretório do projeto

docker-compose -f docker/docker-compose-dev.yml stop evolution-api 2>/dev/null || true
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
            echo ""
            echo "🎯 Próximos passos:"
            echo "1. Escanear QR Code com WhatsApp (AGORA!)"
            echo "2. Aguardar mensagem 'Conectado com sucesso'"
            echo "3. Testar enviando 'oi' do WhatsApp para o número logado"
            echo "4. Verificar execuções em: http://localhost:5678/home/executions"
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
