#!/bin/bash

# ============================================================================
# V32 Implementation Task Script - Para /sc:task executar
# ============================================================================
# ATENÇÃO: Este script documenta as tarefas para correção V32
# NÃO EXECUTAR diretamente - usar com /sc:task
# ============================================================================

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         V32 STATE MAPPING FIX - TAREFAS PARA EXECUÇÃO          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "🚨 PROBLEMA CRÍTICO IDENTIFICADO:"
echo "   O banco está enviando 'identificando_servico'"
echo "   mas o código espera 'service_selection'"
echo ""
echo "📋 TAREFAS PARA O /sc:task:"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TAREFA 1: CRIAR SCRIPT DE CORREÇÃO V32"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Arquivo: scripts/fix-workflow-v32-state-mapping.py"
echo ""
echo "Funcionalidades:"
echo "  1. Adicionar mapeamento de estados (DB → Code)"
echo "  2. Normalizar currentStage antes do switch"
echo "  3. Implementar validação de telefone WhatsApp"
echo "  4. Adicionar logs V32 para debug"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TAREFA 2: ATUALIZAR STATE MACHINE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Modificações no código:"
echo ""
echo "  A) Adicionar State Mapping:"
cat << 'EOF'
     const stateNameMapping = {
       'identificando_servico': 'service_selection',
       'coletando_nome': 'collect_name',
       'coletando_telefone': 'collect_phone',
       // ... outros mapeamentos
     };
EOF
echo ""
echo "  B) Normalizar estado:"
cat << 'EOF'
     const rawCurrentStage = conversation.current_state;
     const currentStage = stateNameMapping[rawCurrentStage] || rawCurrentStage;
EOF
echo ""
echo "  C) Validar telefone WhatsApp:"
cat << 'EOF'
     // Confirmar se telefone principal é o do WhatsApp
     const whatsappNumber = leadId.replace(/\D/g, '');
     responseText = `Seu WhatsApp é ${formatted}. É seu telefone principal?`;
EOF
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TAREFA 3: CRIAR WORKFLOW V32"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Arquivo: n8n/workflows/02_ai_agent_conversation_V32_STATE_MAPPING.json"
echo ""
echo "Passos:"
echo "  1. Copiar workflow V31"
echo "  2. Aplicar correções do script Python"
echo "  3. Adicionar validação de telefone"
echo "  4. Testar em dev"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TAREFA 4: CRIAR SCRIPT DE VALIDAÇÃO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Arquivo: scripts/validate-v32-fix.sh"
echo ""
echo "Testes a realizar:"
echo "  ✓ Estado 'identificando_servico' é mapeado corretamente"
echo "  ✓ Nome 'Bruno Rosa' é aceito"
echo "  ✓ Telefone WhatsApp é validado"
echo "  ✓ Fluxo completo funciona"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TAREFA 5: ATUALIZAR BANCO DE DADOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SQL para adicionar campos novos:"
cat << 'EOF'
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS phone_whatsapp VARCHAR(20),
ADD COLUMN IF NOT EXISTS phone_alternative VARCHAR(20);
EOF
echo ""
echo "════════════════════════════════════════════════════"
echo "🎯 COMANDO PARA EXECUTAR COM /sc:task:"
echo "════════════════════════════════════════════════════"
echo ""
echo "/sc:task execute v32-state-mapping-fix \\"
echo "  --create-script fix-workflow-v32-state-mapping.py \\"
echo "  --update-workflow V32_STATE_MAPPING \\"
echo "  --add-phone-validation \\"
echo "  --test-scenarios 4 \\"
echo "  --validate-before-deploy"
echo ""
echo "════════════════════════════════════════════════════"
echo "⚠️  AVISOS IMPORTANTES:"
echo "════════════════════════════════════════════════════"
echo ""
echo "1. REVISAR o mapeamento de estados antes de executar"
echo "2. FAZER BACKUP do workflow V31"
echo "3. TESTAR em ambiente dev primeiro"
echo "4. VALIDAR logs V32 no console do n8n"
echo "5. CONFIRMAR que banco está salvando estados corretos"
echo ""
echo "📊 RESULTADO ESPERADO APÓS V32:"
echo ""
echo "  ANTES: 'identificando_servico' → Erro → Reset"
echo "  DEPOIS: 'identificando_servico' → Mapeado → 'service_selection' → Funciona!"
echo ""
echo "✅ Quando todas as tarefas forem concluídas:"
echo "   - Bug de estado resolvido"
echo "   - Telefone WhatsApp validado"
echo "   - Fluxo funcionando corretamente"
echo ""
echo "📝 Documentação completa em:"
echo "   docs/PLAN/V32_STATE_MAPPING_FIX.md"
echo ""