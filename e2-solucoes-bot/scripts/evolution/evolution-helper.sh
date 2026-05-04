#!/bin/bash

# ============================================================================
# Evolution API Helper - Dev + Produção (híbrido com detecção automática)
# ============================================================================
#
# USO:
#   source ./scripts/evolution/evolution-helper.sh
#   evolution_status           # Verifica status da instância
#   evolution_create           # Cria nova instância
#   evolution_delete           # Deleta instância
#   evolution_qrcode           # Gera QR Code
#   evolution_send "5562999..." "Mensagem"  # Envia mensagem
#   evolution_recreate         # Recriar instância completa
# ============================================================================

# ----------------------------------------------------------------------------
# 0. Dependências opcionais
# ----------------------------------------------------------------------------
_JQ=$(command -v jq 2>/dev/null)
_jq() {
    if [ -n "$_JQ" ]; then "$_JQ" "$@"; else cat; fi
}

# ----------------------------------------------------------------------------
# 1. Detectar PROJECT_ROOT
# ----------------------------------------------------------------------------
if [ -f "/home/bruno/storage/e2_Solucoes_N8N/e2-solucoes-bot/docker/.env" ]; then
    PROJECT_ROOT="/home/bruno/storage/e2_Solucoes_N8N/e2-solucoes-bot"
elif [ -f "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/docker/.env" ]; then
    PROJECT_ROOT="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot"
else
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi
ENV_FILE="$PROJECT_ROOT/docker/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Erro: Arquivo .env não encontrado em: $ENV_FILE"
    return 1 2>/dev/null || exit 1
fi

# ----------------------------------------------------------------------------
# 2. Carregar variáveis do .env
# ----------------------------------------------------------------------------
export $(grep -v '^#' "$ENV_FILE" | grep -E "^(EVOLUTION_API_KEY|EVOLUTION_INSTANCE_NAME|EVOLUTION_SUBDOMAIN|DOMAIN|N8N_SUBDOMAIN)=" | xargs)

if [ -z "$EVOLUTION_API_KEY" ]; then
    echo "❌ Erro: EVOLUTION_API_KEY não encontrada no .env"
    return 1 2>/dev/null || exit 1
fi

echo "✅ EVOLUTION_API_KEY carregada: ${EVOLUTION_API_KEY:0:20}..."

# ----------------------------------------------------------------------------
# 3. Detectar ambiente (prd vs dev) pelo container em execução
# ----------------------------------------------------------------------------
if docker inspect e2bot-evolution-prd &>/dev/null 2>&1; then
    AMBIENTE="prd"
    CONTAINER_NAME="e2bot-evolution-prd"
    INSTANCE_NAME="${EVOLUTION_INSTANCE_NAME:-e2-bot-production}"
    # Produção: porta 8082 exposta só para localhost (127.0.0.1:8082:8080)
    EVOLUTION_URL="http://localhost:8082"
    _n8n="${N8N_SUBDOMAIN:-n8n}"
    _domain="${DOMAIN:-climacocal.com.br}"
    WEBHOOK_URL="https://${_n8n}.${_domain}/webhook/whatsapp"
elif docker inspect e2bot-evolution-dev &>/dev/null 2>&1; then
    AMBIENTE="dev"
    CONTAINER_NAME="e2bot-evolution-dev"
    INSTANCE_NAME="${EVOLUTION_INSTANCE_NAME:-e2-solucoes-bot}"
    EVOLUTION_URL="http://localhost:8080"
    WEBHOOK_URL="http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution"
else
    AMBIENTE="desconhecido"
    CONTAINER_NAME=""
    INSTANCE_NAME="${EVOLUTION_INSTANCE_NAME:-e2-solucoes-bot}"
    EVOLUTION_URL="http://localhost:8080"
    WEBHOOK_URL="http://localhost:5678/webhook/whatsapp-evolution"
fi

echo "🌍 Ambiente: $AMBIENTE | Container: $CONTAINER_NAME"
echo "📡 URL: $EVOLUTION_URL | Instância: $INSTANCE_NAME"

# ============================================================================
# Funções Helper
# ============================================================================

evolution_status() {
    echo "🔍 Verificando status da instância: $INSTANCE_NAME"
    curl -s --max-time 15 "$EVOLUTION_URL/instance/connectionState/$INSTANCE_NAME" \
        -H "apikey: $EVOLUTION_API_KEY" | _jq .
}

evolution_create() {
    echo "📱 Criando instância: $INSTANCE_NAME"
    curl -s --max-time 30 -X POST "$EVOLUTION_URL/instance/create" \
        -H "apikey: $EVOLUTION_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"instanceName\": \"$INSTANCE_NAME\",
            \"qrcode\": true,
            \"integration\": \"WHATSAPP-BAILEYS\"
        }" | _jq .
}

evolution_delete() {
    echo "🗑️  Deletando instância: $INSTANCE_NAME"
    curl -s --max-time 15 -X DELETE "$EVOLUTION_URL/instance/delete/$INSTANCE_NAME" \
        -H "apikey: $EVOLUTION_API_KEY" | _jq .
}

_show_qrcode() {
    local base64="$1"
    local code="$2"

    # Salvar PNG
    echo "$base64" | sed 's/data:image\/png;base64,//' | base64 -d > /tmp/qrcode_evolution.png

    # Tentar exibir no terminal
    if command -v qrencode &>/dev/null && [ -n "$code" ] && [ "$code" != "null" ]; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        qrencode -t UTF8 "$code"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    else
        echo ""
        echo "⚠️  Instale qrencode para exibir no terminal:"
        echo "   sudo apt-get install -y qrencode"
        echo ""
        echo "💡 Ou transfira para sua máquina e abra:"
        echo "   scp $(whoami)@$(hostname -I 2>/dev/null | awk '{print $1}'):/tmp/qrcode_evolution.png ."
    fi

    echo ""
    echo "⏰ QR Code expira em 60 segundos!"
    echo "📱 Escaneie com WhatsApp: Menu → Aparelhos conectados"
}

evolution_qrcode() {
    echo "📱 Aguardando QR Code para: $INSTANCE_NAME"

    local max_attempts=10
    local attempt=1
    local BASE64="" CODE=""

    while [ $attempt -le $max_attempts ]; do
        echo "   Tentativa $attempt/$max_attempts..."

        RESPONSE=$(curl -s --max-time 15 "$EVOLUTION_URL/instance/connect/$INSTANCE_NAME" \
            -H "apikey: $EVOLUTION_API_KEY")

        BASE64=$(echo "$RESPONSE" | _jq -r '.base64' 2>/dev/null)
        CODE=$(echo "$RESPONSE" | _jq -r '.code' 2>/dev/null)

        if [ "$BASE64" = "null" ] || [ -z "$BASE64" ]; then
            RESPONSE=$(curl -s --max-time 15 "$EVOLUTION_URL/instance/qrcode/$INSTANCE_NAME" \
                -H "apikey: $EVOLUTION_API_KEY")
            BASE64=$(echo "$RESPONSE" | _jq -r '.qrcode.base64' 2>/dev/null)
            CODE=$(echo "$RESPONSE" | _jq -r '.qrcode.code' 2>/dev/null)
        fi

        if [ "$BASE64" != "null" ] && [ -n "$BASE64" ] && [ "$BASE64" != "" ]; then
            break
        fi

        sleep 3
        attempt=$((attempt + 1))
    done

    if [ "$BASE64" = "null" ] || [ -z "$BASE64" ] || [ "$BASE64" = "" ]; then
        echo ""
        echo "❌ Não foi possível obter QR Code após $max_attempts tentativas."
        echo "   1. Instância já está conectada (não gera novo QR)"
        echo "   2. Evolution API ainda inicializando"
        echo "🔍 Verifique: evolution_status"
        return 1
    fi

    _show_qrcode "$BASE64" "$CODE"
}

evolution_send() {
    local number="$1"
    local text="$2"

    if [ -z "$number" ] || [ -z "$text" ]; then
        echo "❌ Uso: evolution_send \"556198175548\" \"Sua mensagem\""
        return 1
    fi

    echo "📤 Enviando mensagem para: $number"
    curl -s --max-time 30 -X POST "$EVOLUTION_URL/message/sendText/$INSTANCE_NAME" \
        -H "apikey: $EVOLUTION_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"number\": \"$number\",
            \"text\": \"$text\"
        }" | _jq .
}

evolution_recreate() {
    echo "🔄 Recriando instância: $INSTANCE_NAME ($AMBIENTE)"
    echo ""
    echo "1/5 - Deletando instância antiga..."
    evolution_delete
    echo ""
    echo "⏳ Aguardando 3 segundos..."
    sleep 3

    if [ "$AMBIENTE" = "dev" ] && [ -n "$CONTAINER_NAME" ]; then
        echo ""
        echo "2/5 - Copiando .env para o container Evolution (dev)..."
        docker cp "$ENV_FILE" "$CONTAINER_NAME:/evolution/.env"
        [ $? -eq 0 ] && echo "   ✅ .env copiado" || echo "   ⚠️  Falha ao copiar .env"
        echo ""
        echo "3/5 - Reiniciando container..."
        docker restart "$CONTAINER_NAME"
        echo "⏳ Aguardando 20 segundos..."
        sleep 20
    else
        echo "2/5 - [prd] variáveis já no compose, sem cópia de .env"
        echo "3/5 - [prd] sem restart necessário"
    fi

    echo ""
    echo "4/5 - Criando nova instância..."
    evolution_create
    echo ""
    echo "⏳ Aguardando 5 segundos..."
    sleep 5

    echo ""
    echo "5/5 - Configurando webhook para n8n..."
    curl -s --max-time 15 -X POST "$EVOLUTION_URL/webhook/set/$INSTANCE_NAME" \
        -H "apikey: $EVOLUTION_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"webhook\": {
                \"url\": \"$WEBHOOK_URL\",
                \"enabled\": true,
                \"webhook_by_events\": false,
                \"webhook_base64\": false,
                \"events\": [
                    \"MESSAGES_UPSERT\",
                    \"MESSAGES_UPDATE\",
                    \"CONNECTION_UPDATE\",
                    \"QRCODE_UPDATED\"
                ]
            }
        }" | _jq '.webhook' 2>/dev/null || echo "   ✅ Webhook configurado"

    echo ""
    echo "🔍 Verificando webhook..."
    curl -s --max-time 10 "$EVOLUTION_URL/webhook/find/$INSTANCE_NAME" \
        -H "apikey: $EVOLUTION_API_KEY" | _jq -r '.url' 2>/dev/null

    echo ""
    echo "📱 Buscando QR Code..."
    evolution_qrcode
}

evolution_connect() {
    echo "📱 Conectando instância e gerando QR Code: $INSTANCE_NAME"

    RESPONSE=$(curl -s --max-time 15 "$EVOLUTION_URL/instance/connect/$INSTANCE_NAME" \
        -H "apikey: $EVOLUTION_API_KEY")

    BASE64=$(echo "$RESPONSE" | _jq -r '.base64' 2>/dev/null)
    CODE=$(echo "$RESPONSE" | _jq -r '.code' 2>/dev/null)

    if [ "$BASE64" = "null" ] || [ -z "$BASE64" ]; then
        echo "❌ Erro ao obter QR Code. Resposta:"
        echo "$RESPONSE" | _jq .
        echo "💡 Verifique: evolution_status"
        return 1
    fi

    _show_qrcode "$BASE64" "$CODE"
}

# ============================================================================
# Menu de ajuda
# ============================================================================

evolution_help() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
║              Evolution API Helper - Comandos Disponíveis         ║
╚══════════════════════════════════════════════════════════════════╝

📋 Comandos Básicos:
   evolution_status              Ver status da instância
   evolution_create              Criar nova instância
   evolution_delete              Deletar instância
   evolution_qrcode              Gerar QR Code (com retry automático)
   evolution_connect             Forçar geração de QR Code
   evolution_recreate            Recriar instância (delete + create + webhook + qr)

📤 Envio de Mensagens:
   evolution_send "5562999..." "Texto"    Enviar mensagem

🔧 Utilitários:
   evolution_help                Mostrar esta ajuda

📝 Exemplos:
   evolution_status
   evolution_recreate
   evolution_connect              # Se recreate não gerar QR
   evolution_send "556198175548" "Olá! Teste do bot 🤖"

💡 Dica: Se evolution_recreate não gerar QR Code, aguarde 10s e use:
   evolution_connect

EOF
}

# Mostrar ajuda ao carregar
evolution_help
