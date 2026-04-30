# 🔧 Plano de Correção: Erro de Tipo de Autenticação no n8n

## 📋 Resumo Executivo
**Problema**: O nó "Send WhatsApp Response" no workflow v6 está com erro: `The value 'genericCredentialType' is not supported!`

**Causa Raiz**: Configuração incorreta do tipo de autenticação no nó HTTP Request. O valor `"authentication": "genericCredentialType"` não é válido no n8n.

**Solução**: Remover a configuração de autenticação via credenciais e usar os headers diretamente para autenticação.

---

## 🔍 Diagnóstico Completo

### 1. Situação Atual

#### ❌ Configuração Problemática (workflow v6):
```json
{
  "parameters": {
    "url": "http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot",
    "authentication": "genericCredentialType",  // ❌ ERRO: Tipo não suportado
    "genericAuthType": "httpHeaderAuth",        // ❌ ERRO: Campo relacionado inválido
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        {
          "name": "apikey",
          "value": "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
        },
        {
          "name": "Content-Type",
          "value": "application/json"
        }
      ]
    }
  },
  "credentials": {
    "httpHeaderAuth": {
      "id": "2",
      "name": "Evolution API Key"
    }
  }
}
```

### 2. Análise do Erro

#### Problema Identificado:
1. **Tipo de Autenticação Inválido**: `genericCredentialType` não é um valor aceito
2. **Conflito de Configuração**: Está tentando usar credenciais E headers ao mesmo tempo
3. **Redundância**: Headers já contêm a API key, não precisa de credenciais adicionais

#### Valores Válidos para `authentication` no n8n:
- `none` - Sem autenticação
- `predefinedCredentialType` - Usar credenciais predefinidas
- `genericCredentialType` ❌ - **NÃO EXISTE no n8n v1**

---

## 🛠️ Plano de Correção

### Opção 1: Remover Autenticação por Credenciais (RECOMENDADO)

#### Configuração Corrigida:
```json
{
  "parameters": {
    "url": "http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot",
    // Removido: "authentication" e "genericAuthType"
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        {
          "name": "apikey",
          "value": "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
        },
        {
          "name": "Content-Type",
          "value": "application/json"
        }
      ]
    },
    "httpMethod": "POST",
    "sendBody": true,
    "bodyContentType": "json",
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
    },
    "options": {}
  },
  // Removido: bloco "credentials"
  "id": "node_send_whatsapp",
  "name": "Send WhatsApp Response",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 1
}
```

### Opção 2: Usar Autenticação "None" Explícita

#### Configuração Alternativa:
```json
{
  "parameters": {
    "authentication": "none",  // Explicitamente sem credenciais
    // ... resto da configuração
  }
}
```

---

## 📝 Script de Correção Automatizada

### Criar arquivo: `/scripts/fix-n8n-auth-type.py`

```python
#!/usr/bin/env python3
"""
Script para corrigir o erro de tipo de autenticação no workflow n8n
Remove configuração inválida de genericCredentialType
"""

import json
import sys
from datetime import datetime

def fix_auth_type():
    """Corrige o tipo de autenticação no workflow v6"""

    workflow_path = 'n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v6.json'
    output_path = 'n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v7.json'

    print(f"🔧 Iniciando correção do tipo de autenticação...")
    print(f"📖 Lendo arquivo: {workflow_path}")

    try:
        # Carregar workflow
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)

        print(f"✅ Workflow carregado com sucesso")
        print(f"📊 Total de nós: {len(workflow.get('nodes', []))}")

        # Encontrar e corrigir o nó Send WhatsApp Response
        node_found = False
        for node in workflow.get('nodes', []):
            if node.get('name') == 'Send WhatsApp Response':
                node_found = True
                print(f"\n🎯 Nó encontrado: '{node['name']}'")
                print(f"   Tipo: {node.get('type')}")
                print(f"   ID: {node.get('id')}")

                # Remover configurações problemáticas
                if 'authentication' in node.get('parameters', {}):
                    del node['parameters']['authentication']
                    print(f"   ✅ Removido campo 'authentication'")

                if 'genericAuthType' in node.get('parameters', {}):
                    del node['parameters']['genericAuthType']
                    print(f"   ✅ Removido campo 'genericAuthType'")

                # Remover bloco de credenciais se existir
                if 'credentials' in node:
                    del node['credentials']
                    print(f"   ✅ Removido bloco 'credentials'")

                # Garantir que os headers estão corretos
                if 'headerParameters' not in node.get('parameters', {}):
                    node['parameters']['headerParameters'] = {
                        "parameters": [
                            {
                                "name": "apikey",
                                "value": "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
                            },
                            {
                                "name": "Content-Type",
                                "value": "application/json"
                            }
                        ]
                    }
                    print(f"   ✅ Headers de autenticação adicionados")

                print(f"\n✅ Nó '{node['name']}' corrigido com sucesso!")
                break

        if not node_found:
            print("\n⚠️  AVISO: Nó 'Send WhatsApp Response' não encontrado!")
            return False

        # Atualizar metadados
        if 'meta' not in workflow:
            workflow['meta'] = {}

        workflow['meta']['lastModified'] = datetime.now().isoformat()
        workflow['meta']['fixesApplied'] = workflow['meta'].get('fixesApplied', [])
        workflow['meta']['fixesApplied'].append(
            f"Authentication type fix - Removed invalid genericCredentialType - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Atualizar versionId
        workflow['versionId'] = 'v7-auth-type-fixed'

        # Salvar workflow corrigido
        print(f"\n💾 Salvando workflow corrigido em: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)

        print(f"✅ Workflow salvo com sucesso!")

        # Validar JSON
        print(f"\n🔍 Validando JSON...")
        with open(output_path, 'r', encoding='utf-8') as f:
            json.load(f)
        print(f"✅ JSON válido!")

        print("\n" + "="*60)
        print("🎉 CORREÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print("\n📋 Próximos passos:")
        print("1. Acesse o n8n: http://localhost:5678")
        print("2. Importe o workflow: 02_ai_agent_conversation_V1_MENU_FIXED_v7.json")
        print("3. Desative o workflow v6 (se estiver ativo)")
        print("4. Ative o workflow v7")
        print("5. Teste enviando uma mensagem via WhatsApp")

        return True

    except FileNotFoundError:
        print(f"\n❌ ERRO: Arquivo não encontrado: {workflow_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"\n❌ ERRO: Falha ao decodificar JSON: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERRO inesperado: {e}")
        return False

if __name__ == "__main__":
    success = fix_auth_type()
    sys.exit(0 if success else 1)
```

---

## ⚡ Comando de Execução para /sc:task

```bash
#!/bin/bash
# fix-n8n-auth-type.sh

echo "🔧 Correção do Tipo de Autenticação n8n"
echo "========================================"
echo ""

# 1. Backup do workflow v6
echo "📁 Passo 1: Criando backup do workflow v6..."
cp n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v6.json \
   n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v6.json.backup_$(date +%Y%m%d_%H%M%S)

# 2. Criar script Python
echo "📝 Passo 2: Criando script de correção..."
cat > scripts/fix-n8n-auth-type.py << 'EOF'
[CONTEÚDO DO SCRIPT PYTHON ACIMA]
EOF

chmod +x scripts/fix-n8n-auth-type.py

# 3. Executar correção
echo "🔧 Passo 3: Executando correção..."
python3 scripts/fix-n8n-auth-type.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Correção concluída com sucesso!"
    echo ""
    echo "📋 Ações necessárias:"
    echo "1. Importar workflow v7 no n8n"
    echo "2. Desativar workflow v6"
    echo "3. Ativar workflow v7"
    echo "4. Testar o envio de mensagem"
else
    echo ""
    echo "❌ Erro durante a correção"
    echo "Verifique o arquivo de log para detalhes"
fi
```

---

## ✅ Validação da Correção

### Teste 1: Importar Workflow v7
```bash
# No n8n interface (http://localhost:5678)
# 1. Menu lateral → Workflows
# 2. Botão "Import"
# 3. Selecione: 02_ai_agent_conversation_V1_MENU_FIXED_v7.json
# 4. Confirme a importação
```

### Teste 2: Verificar Configuração
1. Abrir o workflow v7 importado
2. Editar nó "Send WhatsApp Response"
3. Verificar que:
   - Não há campo "authentication"
   - Headers contêm a apikey
   - URL está correta

### Teste 3: Executar Teste
```bash
# Enviar mensagem de teste
source ./scripts/evolution-helper.sh
evolution_send "5561981755748" "Teste do workflow v7"

# Verificar logs
docker logs -f e2bot-n8n-dev | grep -i "whatsapp"
```

---

## 🔒 Considerações de Segurança

⚠️ **IMPORTANTE**: A solução atual usa API Key diretamente nos headers, adequado para desenvolvimento.

### Para Produção:
1. Configurar credenciais seguras no n8n
2. Usar variáveis de ambiente ou secrets
3. Implementar rotação de API Keys
4. Não hardcode keys no workflow

---

## 📊 Resumo das Correções

| Versão | Problema | Solução | Status |
|--------|----------|---------|--------|
| v5 | Variáveis de ambiente undefined | URL hardcoded | ✅ Resolvido (v6) |
| v6 | genericCredentialType não suportado | Remover autenticação por credenciais | ⏳ Em correção (v7) |
| v7 | - | Headers diretos para autenticação | ✅ Pronto para teste |

---

## 🎯 Resultado Esperado

Após aplicar esta correção:
1. ✅ Workflow v7 importará sem erros
2. ✅ Nó HTTP Request funcionará corretamente
3. ✅ Mensagens WhatsApp serão enviadas com sucesso
4. ✅ Autenticação via API Key nos headers

---

**Data**: 2025-01-07
**Responsável**: Claude AI Assistant
**Status**: Pronto para Execução via /sc:task