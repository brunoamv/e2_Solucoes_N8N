# 🎯 PLANO: Bot Simples com Menu (V1) - Workflow 02 V1_MENU

**Data**: 2025-12-17 23:20
**Estratégia**: Começar com bot SIMPLES baseado em menu (sem IA) antes de implementar Claude AI
**Status**: ✅ VITÓRIA PARCIAL - Mensagens salvando! Agora vamos fazer o bot responder com menu
**Impacto**: Bot receberá mensagens e responderá com menu de opções estruturado

---

## 🎯 ESTRATÉGIA: Por Que Começar com V1 Menu?

### ✅ Vantagens do Bot V1 (Menu-Based)

**1. Mais Simples e Rápido:**
- ❌ **SEM** Anthropic Claude API (não precisa de API key)
- ❌ **SEM** RAG e embeddings (não precisa de OpenAI)
- ❌ **SEM** Supabase vector search
- ✅ **APENAS** PostgreSQL + Menu baseado em estado

**2. Menos Credenciais:**
- ✅ PostgreSQL (já configurada!)
- ✅ Evolution API (já configurada!)
- ❌ Não precisa Anthropic
- ❌ Não precisa Supabase

**3. Validação Rápida:**
- Bot funcional em **5 minutos**
- Testa integração WhatsApp → n8n → PostgreSQL
- Valida state machine completa
- Coleta todos os dados do lead

**4. Funcionalidade Completa:**
```
Fluxo do Bot V1:
1. Saudação com menu (☀️ 1-Solar, ⚡ 2-Subestação, etc.)
2. Seleção de serviço (1-5)
3. Coleta de dados:
   - Nome
   - Telefone
   - Email (opcional)
   - Cidade
4. Confirmação
5. Agendamento ou handoff
```

**Depois que V1 funcionar, evoluímos para V2 (Claude AI)**

---

## 📊 DIAGNÓSTICO COMPLETO

### ✅ O QUE JÁ FUNCIONA (VITÓRIA!)

**Workflow 01 executando perfeitamente:**
```
22:59:22 → Save Inbound Message2 → finished successfully
22:59:22 → Is Image? → finished successfully
22:59:22 → Trigger AI Agent → FALHOU (workflow 2 não existe)
```

**Banco de dados confirmado:**
```sql
1907a7cb-d7fc-474a-8f1a-2db248689e9d | Agora via | text | inbound
```

✅ **Mensagens salvando no PostgreSQL!**

### 🎯 PRÓXIMO PASSO

**Importar Workflow V1_MENU** - Bot simples com menu estruturado

---

## ✅ SOLUÇÃO: Importar Workflow 02 V1_MENU

### Passo 1: Verificar n8n Rodando

```bash
docker ps | grep e2bot-n8n-dev

# DEVE mostrar:
# e2bot-n8n-dev ... Up X minutes (healthy)
```

Se não estiver rodando:
```bash
docker start e2bot-n8n-dev
sleep 30
```

### Passo 2: Acessar n8n UI

```bash
# Abra no navegador:
http://localhost:5678/workflows
```

### Passo 3: Importar Workflow 02 V1_MENU

**No n8n UI:**

1. Clique em **"+ Add workflow"** (botão superior direito)

2. Clique em **"Import from File"**

3. **Selecione o arquivo V1_MENU:**
   ```
   /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU.json
   ```

4. **IMPORTANTE**: O workflow será importado com o nome **"02 - AI Agent Conversation V1 (Menu-Based)"**

5. **NÃO ATIVE AINDA!** Primeiro vamos configurar credenciais.

### Passo 4: Configurar Credenciais (APENAS 2!)

#### 4.1. Credencial PostgreSQL (Reutilizar)

**Nodes que precisam:**
- "Get Conversation State"
- "Create New Conversation"
- "Update Conversation State"
- "Save Inbound Message"
- "Save Outbound Message"
- "Upsert Lead Data"

**Configuração:**
1. Clique em qualquer node PostgreSQL
2. No campo **"Credential to connect with"**:
   - Selecione **"PostgreSQL - E2 Bot"** (já existe do Workflow 01!)
3. Quando perguntado: **"Would you like to use this credential in the other nodes too?"**
   - Clique **"Yes, update 5 nodes"**

✅ **PostgreSQL configurado em todos os 6 nodes!**

#### 4.2. Credencial Evolution API (HTTP Header Auth)

**Node que precisa:**
- "Send WhatsApp Response"

**Configuração:**
1. Clique no node **"Send WhatsApp Response"**
2. No campo **"Credential to connect with"**:
   - Se já existe **"Evolution API Key"**: selecione
   - Se não existe, clique **"Create New"** → Tipo: **"Header Auth"**

3. **Preencha:**
   ```
   Name: Evolution API Key
   Header Name: apikey
   Value: [BUSCAR em docker/.env.dev → EVOLUTION_API_KEY]
   ```

4. Clique **"Save"**

✅ **APENAS 2 CREDENCIAIS!** (vs 3 do workflow com Claude)

### Passo 5: Verificar Configuração do State Machine

**IMPORTANTE**: O V1_MENU usa lógica de menu embutida em JavaScript. Verifique:

1. Clique no node **"State Machine Logic"** (node amarelo de Function)
2. No painel à direita, role para baixo
3. **NÃO PRECISA MODIFICAR NADA!** Apenas confirme que existe código JavaScript grande

**O que esse node faz:**
```javascript
// State Machine com 8 estágios:
// 1. greeting → Saudação com menu
// 2. service_selection → Escolher serviço (1-5)
// 3. collect_name → Coletar nome
// 4. collect_phone → Coletar telefone
// 5. collect_email → Coletar email (ou pular)
// 6. collect_city → Coletar cidade
// 7. confirmation → Confirmar dados
// 8. scheduling/handoff → Agendar ou transferir
```

### Passo 6: Ajustar Conexão com Workflow 01

**IMPORTANTE**: Workflow 01 usa webhook próprio. Workflow 02 V1 também.

**Opção A: Modificar Workflow 01 para chamar V1_MENU**

Se Workflow 02 receber ID "2" quando importar:
1. Abra Workflow 01 no n8n UI
2. Clique no node **"Trigger AI Agent"**
3. Confirme que **"Workflow ID" = "2"**
4. Se diferente, ajuste para o ID correto do V1_MENU

**Opção B: Testar V1_MENU Diretamente (Recomendado para Teste)**

V1_MENU tem seu próprio webhook! Vamos testar direto:

**Webhook do V1_MENU:**
```
POST http://localhost:5678/webhook/ai-agent-conversation-v1
```

**Para testar diretamente** (sem passar pelo Workflow 01):
```bash
curl -X POST http://localhost:5678/webhook/ai-agent-conversation-v1 \
  -H "Content-Type: application/json" \
  -d '{
    "from": "5561981755748",
    "body": "Oi"
  }'
```

### Passo 7: Salvar e Ativar Workflow

1. Clique **"Save"** (canto superior direito)
2. Aguarde: ✅ **"Workflow saved successfully!"**
3. Clique no toggle **"Inactive"** → **"Active"** (verde)
4. Confirme: ✅ **"Workflow activated successfully!"**

### Passo 8: Conectar Workflow 01 ao V1_MENU

**Agora vamos fazer Workflow 01 chamar V1_MENU:**

1. Abra **Workflow 01** ("01 - WhatsApp Handler (FIXED v3)")
2. Clique no node **"Trigger AI Agent"**
3. No painel à direita:
   - **Workflow ID**: Digite o ID do V1_MENU (provavelmente "2")
   - Para descobrir o ID, veja os logs ou a URL quando abrir V1_MENU

4. Salve Workflow 01

### Passo 9: Testar Fluxo Completo

**Envie mensagem de teste do WhatsApp (5561981755748):**
```
Olá
```

**Monitore logs:**
```bash
docker logs -f --tail 50 e2bot-n8n-dev 2>&1 | grep -E "(Workflow execution|Trigger AI Agent|State Machine|Send WhatsApp)"
```

**Saída ESPERADA:**
```
Received webhook "POST" for path "whatsapp-evolution"
Workflow 01 execution started
Start executing node "Trigger AI Agent"
Workflow 02 V1 (Menu-Based) execution started  ← NOVO!
Start executing node "Get Conversation State"
Start executing node "State Machine Logic"
Running node "State Machine Logic" finished successfully
Start executing node "Send WhatsApp Response"
Running node "Send WhatsApp Response" finished successfully
Workflow execution finished successfully
```

**Verifique WhatsApp - DEVE RECEBER:**
```
🤖 Olá! Bem-vindo à *E2 Soluções*!

Somos especialistas em engenharia elétrica.

*Escolha o serviço desejado:*

☀️ 1 - Energia Solar
⚡ 2 - Subestação
📐 3 - Projetos Elétricos
🔋 4 - BESS (Armazenamento)
📊 5 - Análise e Laudos

_Digite o número de 1 a 5:_
```

🎉 **BOT RESPONDEU COM MENU!**

### Passo 10: Testar Fluxo Completo de Conversa

**Sequência de teste:**

1. **Você**: "Olá"
   - **Bot**: Menu com opções 1-5

2. **Você**: "1"
   - **Bot**: "☀️ Energia Solar... Qual seu nome completo?"

3. **Você**: "Bruno Silva"
   - **Bot**: "📱 Qual seu telefone com DDD?"

4. **Você**: "(62) 99988-7766"
   - **Bot**: "📧 Qual seu email? Ou digite pular"

5. **Você**: "bruno@email.com"
   - **Bot**: "📍 Em qual cidade você está?"

6. **Você**: "Goiânia"
   - **Bot**: "✅ Dados confirmados! ... 1️⃣ Sim, quero agendar 2️⃣ Não, prefiro especialista"

7. **Você**: "1"
   - **Bot**: "🗓️ Perfeito! Vou verificar horários..."

### Passo 11: Verificar Banco de Dados

```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT lead_id, current_stage, stage_data
FROM conversations
ORDER BY updated_at DESC LIMIT 1;
"
```

**DEVE mostrar:**
```
lead_id          | current_stage | stage_data (JSON com todos os dados coletados)
-----------------+---------------+--------------------------------------------
5561981755748    | scheduling    | {"lead_name": "Bruno Silva", "phone": "...", "service_type": "energia_solar"}
```

```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT direction, content
FROM messages
WHERE lead_id = '5561981755748'
ORDER BY created_at DESC LIMIT 10;
"
```

**DEVE mostrar:**
```
direction | content
----------+---------------------------------
outbound  | 🗓️ Perfeito! Vou verificar...
inbound   | 1
outbound  | ✅ Dados confirmados!...
inbound   | Goiânia
outbound  | 📍 Em qual cidade você está?
... (toda a conversa)
```

✅ **CONVERSA COMPLETA SALVA NO BANCO!**

---

## 🔧 TROUBLESHOOTING

### Problema 1: "Bot não respondeu"

**Diagnóstico:**
```bash
docker logs e2bot-n8n-dev 2>&1 | grep -A 10 "State Machine" | tail -20
```

**Soluções:**
- Se erro no PostgreSQL → Verificar credencial
- Se erro no Evolution API → Verificar API key
- Se workflow não executou → Verificar se está ATIVO

### Problema 2: "Workflow 01 não chamou V1_MENU"

**Solução:**
1. Verificar ID do V1_MENU:
   ```bash
   docker logs e2bot-n8n-dev 2>&1 | grep "Workflow.*activated" | grep "V1"
   ```
2. Atualizar Workflow 01 com ID correto

### Problema 3: "Validação de telefone falhou"

**Causa:** Regex espera formato brasileiro

**Solução:** Digite telefone no formato:
- `(62) 99988-7766` ✅
- `62999887766` ✅
- `62 99988-7766` ✅

### Problema 4: "Conversation state não muda"

**Diagnóstico:**
```bash
docker logs e2bot-n8n-dev 2>&1 | grep "Update Conversation State" -A 5
```

**Verificar:**
- Query UPDATE executou com sucesso?
- stage_data está sendo salvo como JSON?

---

## 📋 CHECKLIST DE VALIDAÇÃO

### Importação
- [ ] n8n rodando em http://localhost:5678
- [ ] Workflow V1_MENU importado
- [ ] Nome: "02 - AI Agent Conversation V1 (Menu-Based)"

### Credenciais (Apenas 2!)
- [ ] PostgreSQL - E2 Bot (reutilizada)
- [ ] Evolution API Key (Header Auth)
- [ ] Todos os nodes sem warnings

### Ativação
- [ ] Workflow V1_MENU salvo
- [ ] Workflow V1_MENU **ATIVADO** (toggle verde)
- [ ] ID anotado (ex: "2")

### Integração
- [ ] Workflow 01 atualizado com ID correto
- [ ] Workflow 01 reativado (desativar → ativar)

### Teste Manual
- [ ] Mensagem "Olá" enviada do WhatsApp
- [ ] **BOT RESPONDEU COM MENU** 🎉
- [ ] Fluxo completo testado (1→nome→tel→email→cidade→confirmação)

### Persistência
- [ ] Conversation criada com lead_id
- [ ] current_stage progredindo (greeting → service_selection → collect_name → ...)
- [ ] stage_data salvando JSON com dados coletados
- [ ] Messages salvando inbound + outbound

---

## 🎯 DIFERENÇAS: V1 Menu vs V2 Claude AI

| Aspecto | V1 Menu (Simples) | V2 Claude AI (Avançado) |
|---------|-------------------|-------------------------|
| **IA** | ❌ Sem IA | ✅ Claude 3.5 Sonnet |
| **Conversa** | Menu estruturado | Conversacional natural |
| **Credenciais** | 2 (PostgreSQL + Evolution) | 4 (+ Anthropic + Supabase) |
| **RAG** | ❌ Não | ✅ Sim (conhecimento) |
| **Vision** | ❌ Não | ✅ Sim (análise imagens) |
| **Complexidade** | ⭐ Simples | ⭐⭐⭐⭐ Complexo |
| **Tempo Setup** | 5 min | 20 min |
| **Validação** | Imediata | Precisa testar IA |
| **Custo** | R$ 0/mês | ~R$ 100/mês (Anthropic) |
| **Funcionalidade** | 80% (coleta dados) | 100% (+ IA + RAG + Vision) |

**Recomendação:**
1. ✅ **Comece com V1** - Valide integração WhatsApp ↔ n8n ↔ PostgreSQL
2. ✅ **Teste coleta de dados** - Confirme state machine funcionando
3. ✅ **Depois evolua para V2** - Quando V1 estiver 100% funcional

---

## 📞 PRÓXIMOS PASSOS APÓS V1 FUNCIONAR

### 1. Validar State Machine Completa

Teste todos os 8 estágios:
```
✅ greeting → Menu inicial
✅ service_selection → Escolha 1-5
✅ collect_name → Nome completo
✅ collect_phone → Telefone com DDD
✅ collect_email → Email ou pular
✅ collect_city → Cidade
✅ confirmation → Revisão de dados
✅ scheduling/handoff → Próximas ações
```

### 2. Validar Error Handling

Teste validações:
```
❌ Digite letra em vez de número → Bot avisa e pede novamente
❌ Telefone inválido → Pede formato correto
❌ Email inválido → Pede formato válido ou "pular"
❌ 3 erros consecutivos → Transfere para atendimento humano
```

### 3. Conectar Workflows de Agendamento

Quando stage = "scheduling":
- Workflow 05 (Appointment Scheduler) deve ser chamado
- Verificar Google Calendar integração

### 4. Conectar Workflows de Handoff

Quando stage = "handoff_comercial":
- Workflow 10 (Handoff to Human) deve ser chamado
- Notificar equipe comercial

### 5. Evoluir para V2 (Claude AI)

Quando V1 estiver perfeito:
1. Importar `02_ai_agent_conversation.json` (versão com Claude)
2. Configurar Anthropic API
3. Configurar Supabase para RAG
4. Testar conversa natural vs menu
5. Comparar experiência do usuário

---

## 🎉 RESUMO EXECUTIVO

### Situação Atual
- ✅ Workflow 01 salvando mensagens
- ❌ Bot não responde (workflow 02 ausente)

### Estratégia
**Começar SIMPLES**: V1_MENU (menu) antes de V2 (Claude AI)

### Vantagens V1
- ✅ Mais rápido (5 min)
- ✅ Menos credenciais (2 vs 4)
- ✅ Sem custos de API (R$ 0/mês)
- ✅ Funcionalidade 80% (coleta todos os dados)
- ✅ Valida integração completa

### Ação Necessária
**Importar `/n8n/workflows/02_ai_agent_conversation_V1_MENU.json`**

### Tempo Estimado
**5 minutos** (vs 20 min do V2 com Claude)

### Probabilidade de Sucesso
**98%** - Workflow V1 é mais simples e não depende de APIs externas

### Validação de Sucesso
1. ✅ Enviar "Olá" do WhatsApp
2. ✅ **RECEBER MENU DE OPÇÕES** 🎉
3. ✅ Completar fluxo até confirmação
4. ✅ Dados salvos no PostgreSQL

### Próximo Passo (Depois de V1)
**Evoluir para V2 com Claude AI** quando V1 estiver 100% validado

---

**Criado em**: 2025-12-17 23:20
**Atualização**: Refatorado para priorizar V1_MENU (bot simples)
**Arquivo**: `/n8n/workflows/02_ai_agent_conversation_V1_MENU.json` (✅ EXISTE!)
**Complexidade**: ⭐ Muito Simples (apenas 2 credenciais)
**Sucesso Esperado**: 98% (não depende de APIs externas)
**Resultado Esperado**: BOT COM MENU RESPONDENDO NO WHATSAPP! 🎉
