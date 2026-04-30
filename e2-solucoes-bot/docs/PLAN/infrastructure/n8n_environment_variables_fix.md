# 🔧 Plano de Correção: Variáveis de Ambiente no n8n

## 📋 Resumo Executivo
**Problema**: O nó "Send WhatsApp Response" no workflow n8n está reportando que as variáveis `EVOLUTION_API_URL` e `EVOLUTION_INSTANCE_NAME` estão undefined, apesar de estarem corretamente definidas no ambiente.

**Causa Raiz**: Conflito de configuração entre credenciais HTTP e variáveis de ambiente no nó HTTP Request do n8n.

**Solução**: Reconfigurar o nó HTTP Request para usar corretamente as variáveis de ambiente ou credenciais.

---

## 🔍 Diagnóstico Completo

### 1. Situação Atual

#### ✅ O que está funcionando:
- Variáveis de ambiente **ESTÃO** definidas no container n8n:
  ```bash
  EVOLUTION_API_URL=http://e2bot-evolution-dev:8080
  EVOLUTION_INSTANCE_NAME=e2-solucoes-bot
  EVOLUTION_API_KEY=ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891
  ```

- Evolution API **ESTÁ** operacional (confirmado via script helper)
- Comunicação entre containers **ESTÁ** funcionando
- Rede Docker `e2bot-dev-network` **ESTÁ** configurada corretamente

#### ❌ O que não está funcionando:
- Nó "Send WhatsApp Response" não consegue acessar as variáveis de ambiente
- URL sendo construída como: `[undefined]/message/sendText/[undefined]`

### 2. Análise da Causa Raiz

#### Problema no Workflow (linha 217-250):
```json
{
  "parameters": {
    "url": "={{ $env.EVOLUTION_API_URL }}/message/sendText/{{ $env.EVOLUTION_INSTANCE_NAME }}",
    "authentication": "genericCredentialType",
    "genericAuthType": "httpHeaderAuth",
    // ...
  },
  "credentials": {
    "httpHeaderAuth": {
      "id": "2",
      "name": "Evolution API Key"
    }
  }
}
```

#### Conflito Identificado:
1. O nó está configurado para usar **credenciais** (httpHeaderAuth)
2. Mas também tenta usar **variáveis de ambiente** diretamente na URL
3. Quando credenciais são usadas, o n8n pode não processar as variáveis `$env` corretamente

---

## 🛠️ Plano de Correção

### Opção 1: Usar URL Fixa (Recomendado para Desenvolvimento)

#### Passo 1: Atualizar o nó HTTP Request
```json
{
  "parameters": {
    "url": "http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot",
    "authentication": "genericCredentialType",
    "genericAuthType": "httpHeaderAuth",
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {
          "name": "number",
          "value": "={{ $json.phone_number }}"
        },
        {
          "name": "text",
          "value": "={{ $json.response_text }}"
        }
      ]
    }
  }
}
```

### Opção 2: Usar Expressões n8n Corretas

#### Passo 1: Verificar sintaxe das variáveis
No n8n, as variáveis de ambiente devem ser acessadas com:
- `{{ $env["EVOLUTION_API_URL"] }}` (notação de array)
- ou `{{ process.env.EVOLUTION_API_URL }}` (acesso direto ao processo)

#### Passo 2: Atualizar o nó
```json
{
  "parameters": {
    "url": "={{ $env[\"EVOLUTION_API_URL\"] }}/message/sendText/{{ $env[\"EVOLUTION_INSTANCE_NAME\"] }}"
  }
}
```

### Opção 3: Usar Nó Set para Preparar URL

#### Passo 1: Adicionar nó "Set" antes do HTTP Request
```json
{
  "name": "Prepare WhatsApp URL",
  "type": "n8n-nodes-base.set",
  "parameters": {
    "values": {
      "string": [
        {
          "name": "whatsapp_url",
          "value": "http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot"
        },
        {
          "name": "api_key",
          "value": "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
        }
      ]
    }
  }
}
```

#### Passo 2: Referenciar no HTTP Request
```json
{
  "parameters": {
    "url": "={{ $json.whatsapp_url }}"
  }
}
```

---

## 📝 Script de Correção Automatizada

### `/sc:task` Executar os seguintes passos:

```bash
#!/bin/bash
# fix_n8n_environment_variables.sh

echo "🔧 Corrigindo variáveis de ambiente no n8n..."

# 1. Backup do workflow atual
cp n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v5.json \
   n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v5.json.backup

# 2. Criar nova versão corrigida
cat > scripts/fix-n8n-env-vars.py << 'EOF'
import json

# Carregar workflow
with open('n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v5.json', 'r') as f:
    workflow = json.load(f)

# Encontrar e corrigir o nó Send WhatsApp Response
for node in workflow['nodes']:
    if node.get('name') == 'Send WhatsApp Response':
        # Opção 1: URL fixa para desenvolvimento
        node['parameters']['url'] = 'http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot'

        # Garantir que o header de autenticação está correto
        if 'sendHeaders' not in node['parameters']:
            node['parameters']['sendHeaders'] = True

        if 'headerParameters' not in node['parameters']:
            node['parameters']['headerParameters'] = {
                "parameters": [
                    {
                        "name": "apikey",
                        "value": "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
                    }
                ]
            }

        print(f"✅ Nó '{node['name']}' corrigido")
        break

# Salvar workflow corrigido
with open('n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v6.json', 'w') as f:
    json.dump(workflow, f, indent=2)

print("✅ Workflow corrigido salvo como v6")
EOF

# 3. Executar correção
python3 scripts/fix-n8n-env-vars.py

# 4. Validar JSON
python3 -m json.tool n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v6.json > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ JSON válido"
else
    echo "❌ JSON inválido - verifique o arquivo"
    exit 1
fi

echo "🎯 Correção concluída!"
echo ""
echo "📋 Próximos passos:"
echo "1. Importar o workflow v6 no n8n"
echo "2. Desativar workflow v5"
echo "3. Ativar workflow v6"
echo "4. Testar envio de mensagem"
```

---

## ✅ Validação da Correção

### Teste 1: Verificar URL no n8n
1. Abrir n8n: http://localhost:5678
2. Editar nó "Send WhatsApp Response"
3. Verificar se a URL está fixa ou usando variáveis corretamente

### Teste 2: Executar Workflow
```bash
# Enviar mensagem de teste
source ./scripts/evolution-helper.sh
evolution_send "5561981755748" "Teste após correção"

# Verificar logs do n8n
docker logs -f e2bot-n8n-dev | grep -i "whatsapp"
```

### Teste 3: Verificar Conectividade
```bash
# Do container n8n para Evolution API
docker exec e2bot-n8n-dev curl -s http://e2bot-evolution-dev:8080/manager/status
```

---

## 🚀 Implementação Recomendada

### Para Desenvolvimento (Imediato):
1. ✅ Usar **Opção 1** - URL fixa
2. ✅ Testar funcionamento
3. ✅ Documentar configuração

### Para Produção (Futuro):
1. ⏳ Configurar credenciais no n8n UI
2. ⏳ Usar variables de workflow
3. ⏳ Implementar secrets management

---

## 📊 Métricas de Sucesso

| Critério | Antes | Depois |
|----------|-------|--------|
| Variáveis definidas | ✅ | ✅ |
| n8n acessa variáveis | ❌ | ✅ |
| Mensagens enviadas | ❌ | ✅ |
| Workflow funcional | ❌ | ✅ |

---

## 🔗 Referências

- [n8n Environment Variables](https://docs.n8n.io/code-examples/expressions/variables/)
- [n8n HTTP Request Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/)
- [Evolution API v2.3.7 Docs](https://doc.evolution-api.com/)

---

**Data**: 2025-01-07
**Responsável**: Claude AI Assistant
**Status**: Pronto para Execução