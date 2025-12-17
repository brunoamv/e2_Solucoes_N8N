#!/bin/bash

# ============================================================================
# Evolution API Helper - Facilita comandos com autenticação automática
# ============================================================================
#
# USO:
#   source ./scripts/evolution-helper.sh
#   evolution_status           # Verifica status da instância
#   evolution_create           # Cria nova instância
#   evolution_delete           # Deleta instância
#   evolution_qrcode           # Gera QR Code
#   evolution_send "5562999..." "Mensagem"  # Envia mensagem
# ============================================================================

# Carregar variáveis de ambiente
PROJECT_ROOT="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot"
ENV_FILE="$PROJECT_ROOT/docker/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Erro: Arquivo .env não encontrado em: $ENV_FILE"
    return 1 2>/dev/null || exit 1
fi

# Carregar .env
export $(grep -v '^#' "$ENV_FILE" | grep "EVOLUTION_API_KEY=" | xargs)

# Verificar se carregou
if [ -z "$EVOLUTION_API_KEY" ]; then
    echo "❌ Erro: EVOLUTION_API_KEY não encontrada no .env"
    return 1 2>/dev/null || exit 1
fi

echo "✅ EVOLUTION_API_KEY carregada: ${EVOLUTION_API_KEY:0:20}..."

# Variáveis
EVOLUTION_URL="http://localhost:8080"
INSTANCE_NAME="e2-solucoes-bot"

# ============================================================================
# Funções Helper
# ============================================================================

evolution_status() {
    echo "🔍 Verificando status da instância: $INSTANCE_NAME"
    curl -s "$EVOLUTION_URL/instance/connectionState/$INSTANCE_NAME" \
        -H "apikey: $EVOLUTION_API_KEY" | jq .
}

evolution_create() {
    echo "📱 Criando instância: $INSTANCE_NAME"
    curl -s -X POST "$EVOLUTION_URL/instance/create" \
        -H "apikey: $EVOLUTION_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"instanceName\": \"$INSTANCE_NAME\",
            \"qrcode\": true,
            \"integration\": \"WHATSAPP-BAILEYS\"
        }" | jq .
}

evolution_delete() {
    echo "🗑️  Deletando instância: $INSTANCE_NAME"
    curl -s -X DELETE "$EVOLUTION_URL/instance/delete/$INSTANCE_NAME" \
        -H "apikey: $EVOLUTION_API_KEY" | jq .
}

evolution_qrcode() {
    echo "📱 Aguardando QR Code para: $INSTANCE_NAME"

    local max_attempts=10
    local attempt=1
    local BASE64=""

    while [ $attempt -le $max_attempts ]; do
        echo "   Tentativa $attempt/$max_attempts..."

        # Buscar QR Code via connect endpoint (método v2.2.3)
        RESPONSE=$(curl -s "$EVOLUTION_URL/instance/connect/$INSTANCE_NAME" \
            -H "apikey: $EVOLUTION_API_KEY")

        # Extrair base64
        BASE64=$(echo "$RESPONSE" | jq -r '.base64' 2>/dev/null)

        # Se não encontrou pelo connect, tentar o qrcode endpoint
        if [ "$BASE64" = "null" ] || [ -z "$BASE64" ]; then
            RESPONSE=$(curl -s "$EVOLUTION_URL/instance/qrcode/$INSTANCE_NAME" \
                -H "apikey: $EVOLUTION_API_KEY")
            BASE64=$(echo "$RESPONSE" | jq -r '.qrcode.base64' 2>/dev/null)
        fi

        # Se encontrou, sair do loop
        if [ "$BASE64" != "null" ] && [ -n "$BASE64" ] && [ "$BASE64" != "" ]; then
            break
        fi

        # Aguardar 3 segundos antes de tentar novamente
        sleep 3
        attempt=$((attempt + 1))
    done

    # Verificar se conseguiu obter QR Code
    if [ "$BASE64" = "null" ] || [ -z "$BASE64" ] || [ "$BASE64" = "" ]; then
        echo ""
        echo "❌ Não foi possível obter QR Code após $max_attempts tentativas."
        echo ""
        echo "📋 Possíveis causas:"
        echo "   1. Instância já está conectada (não gera novo QR)"
        echo "   2. Evolution API ainda inicializando"
        echo ""
        echo "🔍 Verifique o status:"
        echo "   evolution_status"
        return 1
    fi

    # Salvar como imagem
    echo "$BASE64" | sed 's/data:image\/png;base64,//' | base64 -d > qrcode.png

    echo ""
    echo "✅ QR Code salvo em: qrcode.png"
    echo "📱 Abrindo QR Code..."
    xdg-open qrcode.png 2>/dev/null || open qrcode.png 2>/dev/null || echo "⚠️  Abra manualmente: qrcode.png"
    echo ""
    echo "⏰ QR Code expira em 60 segundos!"
    echo "📱 Escaneie agora com WhatsApp: Menu → Aparelhos conectados"
}

evolution_send() {
    local number="$1"
    local text="$2"

    if [ -z "$number" ] || [ -z "$text" ]; then
        echo "❌ Uso: evolution_send \"556198175548\" \"Sua mensagem\""
        return 1
    fi

    echo "📤 Enviando mensagem para: $number"
    curl -s -X POST "$EVOLUTION_URL/message/sendText/$INSTANCE_NAME" \
        -H "apikey: $EVOLUTION_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"number\": \"$number\",
            \"text\": \"$text\"
        }" | jq .
}

evolution_recreate() {
    echo "🔄 Recriando instância: $INSTANCE_NAME"
    echo ""
    echo "1/3 - Deletando instância antiga..."
    evolution_delete
    echo ""
    echo "⏳ Aguardando 3 segundos..."
    sleep 3
    echo ""
    echo "2/3 - Criando nova instância..."
    evolution_create
    echo ""
    echo "⏳ Aguardando Evolution gerar QR Code (5 segundos)..."
    sleep 5
    echo ""
    echo "3/3 - Buscando QR Code..."
    evolution_qrcode
}

evolution_connect() {
    echo "📱 Conectando instância e gerando QR Code: $INSTANCE_NAME"

    # Usar endpoint connect que força geração de QR Code
    RESPONSE=$(curl -s "$EVOLUTION_URL/instance/connect/$INSTANCE_NAME" \
        -H "apikey: $EVOLUTION_API_KEY")

    # Extrair base64
    BASE64=$(echo "$RESPONSE" | jq -r '.base64' 2>/dev/null)

    if [ "$BASE64" = "null" ] || [ -z "$BASE64" ]; then
        echo "❌ Erro ao obter QR Code. Resposta:"
        echo "$RESPONSE" | jq .
        echo ""
        echo "💡 Dica: Verifique se a instância existe:"
        echo "   evolution_status"
        return 1
    fi

    # Salvar como imagem
    echo "$BASE64" | sed 's/data:image\/png;base64,//' | base64 -d > qrcode.png

    echo "✅ QR Code salvo em: qrcode.png"
    echo "📱 Abrindo QR Code..."
    xdg-open qrcode.png 2>/dev/null || open qrcode.png 2>/dev/null || echo "⚠️  Abra manualmente: qrcode.png"
    echo ""
    echo "⏰ QR Code expira em 60 segundos!"
    echo "📱 Escaneie agora com WhatsApp: Menu → Aparelhos conectados"
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
   evolution_recreate            Recriar instância (delete + create + qr)

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
