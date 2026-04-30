# Plano de Correção: Substituição de Variáveis no n8n Workflow

## 📋 Resumo Executivo

**Problema Principal**: O n8n não está substituindo as variáveis `{{ $json.phone_number }}` e `{{ $json.response }}` no nó "Send WhatsApp Response", enviando-as literalmente como strings para a API.

**Status**: Análise completa realizada, solução V2 criada e pronta para teste.

---

## 🔍 Análise do Problema

### 1. Problemas Identificados

#### 1.1 Método HTTP Incorreto
- **Erro**: Workflow v4 está usando GET ao invés de POST
- **Log**: `"Cannot GET /message/sendText/e2-solucoes-bot"`
- **Impacto**: API retorna 404

#### 1.2 Variáveis Não Substituídas
- **Erro**: `"number": "{{ $json.phone_number }}"` enviado literalmente
- **Causa**: Formato JSON incorreto no bodyParametersJson
- **Impacto**: API retorna 400 Bad Request

#### 1.3 Estrutura de Parâmetros Inconsistente
- **Problema**: Mistura de formatos v1 e v3 do HTTP Request node
- **Limitação n8n**: headerParametersUi não funciona, deve usar headerParametersJson

### 2. Análise Técnica

#### 2.1 Fluxo de Dados Atual (v4)
```
Prepare Update Data → Output: {phone_number, response}
                    ↓
Send WhatsApp Response → Não substitui variáveis
                       ↓
Evolution API → Recebe string literal "{{ $json.phone_number }}"
```

#### 2.2 Configuração Problemática
```json
{
  "parameters": {
    "authentication": "none",
    "requestMethod": "POST",  // Mas logs mostram GET
    "bodyParametersJson": "{\"number\": \"{{ $json.phone_number }}\"}"  // String literal
  }
}
```

---

## 🛠️ Soluções Implementadas

### 1. Workflow V2 - Estrutura Simplificada

#### Características:
- ✅ HTTP Request v3 com estrutura moderna
- ✅ Método POST explícito
- ✅ Headers com API Key via headerParameters
- ✅ Body com referências diretas aos nós anteriores
- ✅ State Machine simplificada para teste

#### Arquivo Criado:
`/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V2.json`

### 2. Correções Aplicadas

| Problema | Solução V2 |
|----------|------------|
| Método GET | `"method": "POST"` explícito |
| Headers sem API Key | `headerParameters` com array de headers |
| Variáveis não substituídas | Referências diretas: `$node["State Machine"].json["phone_number"]` |
| Estrutura complexa | Workflow simplificado com 8 nós essenciais |

---

## 📝 Plano de Execução para /sc:task

### Fase 1: Validação Inicial (5 min)
```yaml
task_1:
  name: "Limpar ambiente n8n"
  actions:
    - Deletar todos workflows antigos "02 - AI Agent"
    - Limpar execuções com erro
    - Verificar webhook do workflow 01
  validation: n8n sem workflows duplicados

task_2:
  name: "Importar workflow V2"
  actions:
    - Importar 02_ai_agent_conversation_V2.json
    - Verificar estrutura dos nós
    - Confirmar credenciais PostgreSQL
  validation: Workflow importado sem erros
```

### Fase 2: Configuração e Teste (10 min)
```yaml
task_3:
  name: "Validar configuração Send WhatsApp"
  checks:
    - Método: POST (não GET)
    - URL: http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot
    - Headers: apikey presente
    - Body: referências aos nós anteriores
  validation: Configuração visual correta no n8n

task_4:
  name: "Teste básico de fluxo"
  actions:
    - Ativar workflow V2
    - Enviar mensagem teste via WhatsApp
    - Monitorar logs do n8n
    - Verificar resposta no WhatsApp
  validation: Mensagem enviada e recebida com sucesso
```

### Fase 3: Debugging Avançado (se necessário)
```yaml
task_5:
  name: "Análise de falhas"
  conditions: Se teste básico falhar
  actions:
    - Capturar request completo via tcpdump
    - Analisar payload enviado para Evolution API
    - Verificar logs detalhados do Evolution API
    - Comparar com chamada manual bem-sucedida
  output: Diagnóstico preciso do problema

task_6:
  name: "Correção iterativa"
  conditions: Baseado no diagnóstico
  options:
    - Ajustar formato de headers
    - Modificar estrutura do body
    - Alterar versão do HTTP Request node
    - Criar nó customizado se necessário
  validation: Request correto sendo enviado
```

### Fase 4: Migração Completa (15 min)
```yaml
task_7:
  name: "Portar state machine completa"
  conditions: Após teste básico funcionar
  actions:
    - Copiar lógica completa do state machine v1
    - Adicionar todos os estados (greeting → completed)
    - Integrar collected_data handling
    - Adicionar validações e error handling
  validation: State machine completa funcionando

task_8:
  name: "Integrar funcionalidades adicionais"
  actions:
    - Adicionar triggers para scheduling
    - Implementar handoff comercial
    - Conectar com RD Station sync
    - Habilitar notificações
  validation: Todas integrações funcionais
```

---

## 🎯 Critérios de Sucesso

### Imediato (Must Have)
- [ ] Workflow V2 importado com sucesso
- [ ] Método POST confirmado nos logs
- [ ] Variáveis sendo substituídas corretamente
- [ ] Mensagens enviadas via WhatsApp

### Completo (Should Have)
- [ ] State machine completa portada
- [ ] Todas integrações funcionando
- [ ] Performance adequada (<500ms por mensagem)
- [ ] Logs limpos sem erros

---

## 🚨 Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| n8n não suporta formato necessário | Média | Alto | Criar custom node ou webhook intermediário |
| Evolution API mudou contrato | Baixa | Alto | Validar com teste manual direto |
| Problema de rede entre containers | Baixa | Médio | Verificar docker network config |
| Credenciais/tokens expirados | Média | Baixo | Re-validar todas credenciais |

---

## 📊 Métricas de Validação

### KPIs Técnicos
- Taxa de sucesso de envio: >95%
- Tempo de resposta: <500ms
- Erros HTTP: 0 (sem 400/404/500)
- Substituição de variáveis: 100%

### Testes de Aceitação
1. **Teste Novo Usuário**: Criar conversa do zero
2. **Teste Usuário Existente**: Continuar conversa
3. **Teste Estado Completo**: Percorrer todos os estados
4. **Teste Error Handling**: Validar respostas de erro

---

## 🔄 Próximos Passos

### Imediato
1. Importar workflow V2 no n8n
2. Executar teste básico
3. Validar substituição de variáveis

### Se Sucesso
1. Portar state machine completa
2. Adicionar todas integrações
3. Documentar solução final

### Se Falha
1. Executar debugging avançado
2. Considerar alternativas (webhook proxy, custom node)
3. Escalar para suporte técnico n8n se necessário

---

## 📚 Referências

### Arquivos Criados
- `/scripts/create-workflow-v2.py` - Script de criação do V2
- `/n8n/workflows/02_ai_agent_conversation_V2.json` - Workflow V2

### Documentação Relacionada
- Evolution API v2.3.7 docs
- n8n HTTP Request node v3 docs
- PostgreSQL JSONB handling

### Logs Analisados
- Execução 3817: Erro 404 com método GET
- Execução 3816: Webhook recebido com sucesso
- Phone_number: 556298175548 processado corretamente

---

**Autor**: Claude Code Assistant
**Data**: 2026-01-08
**Status**: Pronto para Execução