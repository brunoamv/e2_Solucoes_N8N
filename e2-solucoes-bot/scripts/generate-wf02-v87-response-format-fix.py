#!/usr/bin/env python3
"""
Gera WF02 V87 - Fix Response Format Explícito

DESCOBERTA CRÍTICA (Documentação n8n v2.15):
- HTTP Request node tem opção "Response Format" que controla parse
- Sem especificar, n8n pode wrapar resposta de forma imprevisível
- Opções: autodetect, json, string

PROBLEMA V86:
- Tinha neverError: true
- MAS não tinha responseFormat especificado
- n8n pode estar usando autodetect e wrapeando incorretamente

SOLUÇÃO V87:
- Adicionar responseFormat: "json" explicitamente
- Força n8n a fazer parse JSON correto
- Garante acesso direto sem wrapping extra
"""

import json
import uuid
from pathlib import Path

def generate_wf02_v87():
    """Gera workflow V87 com Response Format explícito"""

    base_dir = Path(__file__).parent.parent
    input_file = base_dir / 'n8n/workflows/02_ai_agent_conversation_V86_HTTP_RESPONSE_FIX.json'
    output_file = base_dir / 'n8n/workflows/02_ai_agent_conversation_V87_RESPONSE_FORMAT_FIX.json'

    print("📖 Lendo V86 HTTP RESPONSE FIX...")
    with open(input_file, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Carregado: {len(workflow['nodes'])} nodes")

    # ====================
    # PASSO 1: Novo ID e Metadata
    # ====================
    old_id = workflow['id']
    new_id = str(uuid.uuid4()).replace('-', '')[:20]
    workflow['id'] = new_id
    workflow['name'] = '02_ai_agent_conversation_V87_RESPONSE_FORMAT_FIX'
    workflow['tags'] = ['V87', 'WF06-Integration', 'Response-Format-Fix']

    print(f"🆔 ID: {old_id} → {new_id}")
    print(f"📝 Name: {workflow['name']}")

    # ====================
    # PASSO 2: Fix HTTP Request - Get Next Dates
    # ====================
    print("\n🔧 Adicionando responseFormat: 'json' ao HTTP Request - Get Next Dates...")

    for node in workflow['nodes']:
        if node['name'] == 'HTTP Request - Get Next Dates':
            # Adicionar responseFormat: json
            if 'options' not in node['parameters']:
                node['parameters']['options'] = {}
            if 'response' not in node['parameters']['options']:
                node['parameters']['options']['response'] = {}

            # Adicionar responseFormat explícito
            node['parameters']['options']['response']['responseFormat'] = 'json'

            print("  ✅ HTTP Request - Get Next Dates: responseFormat = 'json'")
            print(f"  Config: {json.dumps(node['parameters']['options'], indent=2)}")

    # ====================
    # PASSO 3: Fix HTTP Request - Get Available Slots
    # ====================
    print("\n🔧 Adicionando responseFormat: 'json' ao HTTP Request - Get Available Slots...")

    for node in workflow['nodes']:
        if node['name'] == 'HTTP Request - Get Available Slots':
            # Adicionar responseFormat: json
            if 'options' not in node['parameters']:
                node['parameters']['options'] = {}
            if 'response' not in node['parameters']['options']:
                node['parameters']['options']['response'] = {}

            # Adicionar responseFormat explícito
            node['parameters']['options']['response']['responseFormat'] = 'json'

            print("  ✅ HTTP Request - Get Available Slots: responseFormat = 'json'")
            print(f"  Config: {json.dumps(node['parameters']['options'], indent=2)}")

    # ====================
    # PASSO 4: Salvar V87
    # ====================
    print(f"\n💾 Salvando V87: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ V87 salvo com sucesso!")

    # ====================
    # PASSO 5: Estatísticas
    # ====================
    print("\n📊 ESTATÍSTICAS V87:")
    print(f"  Nodes: {len(workflow['nodes'])}")
    print(f"  Conexões: {len(workflow['connections'])}")
    print(f"  ID: {workflow['id']}")
    print(f"  Tags: {workflow['tags']}")

    print("\n✅ CORREÇÃO APLICADA V87:")
    print("  1. HTTP Request nodes agora têm responseFormat: 'json' EXPLÍCITO")
    print("  2. Força n8n a fazer parse JSON correto")
    print("  3. Elimina wrapping imprevisível do autodetect")
    print("  4. Mantém V86 Prepare nodes com 6-path checking como fallback")

    print("\n🎯 DIFERENÇA V86 → V87:")
    print("  V86: options.response.neverError = true (SEM responseFormat)")
    print("  V87: options.response.responseFormat = 'json' (EXPLÍCITO)")
    print("  V87: Força parse JSON direto, sem wrapping extra")

    print("\n🎉 WF02 V87 RESPONSE FORMAT FIX GERADO COM SUCESSO!")
    print(f"\n📝 Próximo passo:")
    print(f"   1. Importe no n8n: {output_file}")
    print(f"   2. Ative o workflow")
    print(f"   3. Execute teste com Service 1 (Solar)")
    print(f"   4. Verifique logs: docker logs -f e2bot-n8n-dev")
    print(f"   5. Espera-se que httpResponse.dates esteja acessível DIRETAMENTE")
    print(f"   6. Se ainda falhar, os 6 paths do V86 tentarão acessar alternativas")

    return True

if __name__ == '__main__':
    import sys
    success = generate_wf02_v87()
    sys.exit(0 if success else 1)
