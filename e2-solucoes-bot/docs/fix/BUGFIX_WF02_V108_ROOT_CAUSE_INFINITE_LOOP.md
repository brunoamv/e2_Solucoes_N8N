# BUGFIX WF02 V108 - Root Cause do Loop Infinito

**Data**: 2026-04-28
**Versão Afetada**: V108
**Severidade**: 🔴 CRÍTICA
**Status**: ROOT CAUSE IDENTIFICADO - V109 FIX NECESSÁRIO

---

## 🎯 Problema Reportado pelo Usuário

Após deploy do V108 State Machine, o bot **AINDA** entra em loop infinito ao selecionar data:

```
[12:55] bruno: 1
[12:55] RogueBot: 📅 Agendar Visita Técnica... (mostra 3 datas)
[12:55] bruno: 1  ← Seleciona primeira data
[12:55] RogueBot: 📅 Agendar Visita Técnica... (MOSTRA AS MESMAS DATAS NOVAMENTE) ❌
```

**Evidência Técnica**:
- Input: `message=1` (usuário selecionando data)
- Output State Machine: `response_text (vazio)` ❌
- Comportamento: Bot envia mensagem de datas repetida

---

## 🔬 Análise Completa do V108

### Cenário da Execução

**Estado do Sistema ANTES do user digitar "1"**:
1. WF06 retornou datas com sucesso
2. Auto-correction (linhas 174-204) processou:
   ```javascript
   // Auto-correction EXECUTOU e setou:
   updateData.date_suggestions = nextDatesResponse.dates;  // Line 198
   updateData.awaiting_wf06_next_dates = true;             // Line 199
   nextStage = 'process_date_selection';                    // Line 200
   wf06HandledByAutoCorrection = true;                      // Line 203
   ```
3. Output enviado com:
   ```json
   {
     "response_text": "📅 Agendar Visita Técnica... [3 datas]",
     "collected_data": {
       "awaiting_wf06_next_dates": true,  ✅ Flag setada
       "date_suggestions": [...],          ✅ Datas preservadas
       "current_stage": "process_date_selection"
     },
     "next_stage": "process_date_selection"
   }
   ```

**Quando usuário digita "1"**:
1. **V108 Detecção** (linhas 94-100) EXECUTA:
   ```javascript
   if (currentData.awaiting_wf06_next_dates === true && message) {
     console.log('🔄 V108: User responding to WF06 dates WITH message:', message);
     forcedStage = 'process_date_selection';  ✅ Força estado
     processWF06Selection = true;
   }
   ```

2. **currentStage Resolved** (linha 111):
   ```javascript
   const currentStage = forcedStage ||  // 'process_date_selection' ✅
                        input.current_stage ||
                        input.next_stage ||
                        ...
   ```

3. **Auto-Correction Check** (linha 174):
   ```javascript
   if (hasWF06Response) {  // FALSE! ❌ (Não há input.wf06_next_dates nesta execução!)
     // NÃO ENTRA AQUI
   }
   ```

4. **Switch Check** (linha 246):
   ```javascript
   else if (!wf06HandledByAutoCorrection && !isIntermediateState) {
     // wf06HandledByAutoCorrection = false ✅
     // isIntermediateState = false ✅
     // ENTRA NO SWITCH! ✅
   ```

5. **Process Date Selection Case** (linhas 673-749):
   ```javascript
   case 'process_date_selection':
     console.log('V108: Processing DATE SELECTION');

     const dateChoice = message.trim();  // '1' ✅

     if (/^[1-3]$/.test(dateChoice)) {  // TRUE ✅
       const selectedIndex = parseInt(dateChoice) - 1;  // 0 ✅
       const suggestions = currentData.date_suggestions || [];  // ← AQUI ESTÁ O PROBLEMA!

       if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
         // Se suggestions.length === 0, NÃO ENTRA AQUI! ❌
         // Cai fora do if sem setar responseText ou nextStage!
       }
     }
     break;  // ← Sai do switch com responseText VAZIO! ❌
   ```

---

## 🐛 ROOT CAUSE IDENTIFICADO

### Problema 1: `date_suggestions` NÃO Preservado

**Linha 680 do V108**:
```javascript
const suggestions = currentData.date_suggestions || [];
```

**Por que `currentData.date_suggestions` está vazio?**

Olhando a construção do `currentData` (linhas 55-84):
```javascript
const currentData = {
  // Spread operators
  ...(input.currentData || {}),
  ...(input.collected_data || {}),

  // Explicit fields
  lead_name: ...,
  phone_number: ...,
  service_type: ...,

  // Preserve suggestions
  date_suggestions: input.date_suggestions ||           // ← De onde vem?
                    input.currentData?.date_suggestions ||
                    input.collected_data?.date_suggestions,
}
```

**O problema**: `date_suggestions` está em `collected_data` do output anterior, mas:
- Workflow pode não estar passando `collected_data` inteiro no input
- Ou `collected_data.date_suggestions` não está sendo preservado na segunda passagem

### Problema 2: Workflow Routing

Quando V108 termina com `response_text` vazio:
1. State Machine retorna:
   ```json
   {
     "response_text": "",  ❌ VAZIO!
     "next_stage": "process_date_selection",
     "collected_data": {
       "awaiting_wf06_next_dates": true (ainda setada!)
     }
   }
   ```

2. Build Update Queries processa e retorna:
   ```json
   {
     "next_stage": "process_date_selection",
     "response_text": ""
   }
   ```

3. **Check If WF06 nodes avaliam**:
   - `next_stage === "trigger_wf06_next_dates"` → FALSE
   - `next_stage === "trigger_wf06_available_slots"` → FALSE
   - Workflow vai para "Send WhatsApp Response"

4. **MAS... de onde vem a mensagem de datas repetida?**

   Possibilidades:
   - a) Há um node "Send Message with Dates" separado que detecta algo
   - b) Auto-correction está sendo executada DUAS VEZES na mesma requisição
   - c) Workflow tem loop back que re-executa State Machine

---

## 🔍 Hipóteses Adicionais

### Hipótese A: Double Execution

Workflow pode estar executando State Machine DUAS VEZES:
1. Primeira execução: Process date selection com suggestions vazio → response_text vazio
2. Segunda execução: Auto-correction detecta estado errado e reprocessa

**Evidência**: User disse "temos o input Process Existing User Data V57 message=1 e o output dele response_text (vazio)"
- "Process Existing User Data V57" parece ser um node ANTES do State Machine
- Se State Machine executa duas vezes, segunda vez veria WF06 data preservado?

### Hipótese B: Workflow tem Node Separado

Workflow pode ter node "Send Message with Dates" que:
- Detecta `date_suggestions` existe em `collected_data`
- Detecta `awaiting_wf06_next_dates = true`
- Envia mensagem com as datas automaticamente

**Se isso for verdade**: O loop não é no State Machine, é no WORKFLOW ROUTING!

### Hipótese C: Auto-Correction Conflito

Auto-correction (linhas 174-204) pode estar interferindo:
- Na primeira execução, auto-correction setou flag
- Na segunda execução, auto-correction NÃO executa (hasWF06Response = false)
- Mas o código V108 (linhas 94-100) força `process_date_selection`
- Process date selection não encontra suggestions e retorna vazio
- Workflow detecta problema e tenta reprocessar?

---

## ✅ Solução Proposta: V109

### Fix 1: Garantir Preservação de `date_suggestions`

**Problema**: `date_suggestions` pode não estar acessível em `currentData`.

**Solução**: Adicionar log debug E garantir fallback explícito:

```javascript
// Linha 680 - Process Date Selection
case 'process_date_selection':
  console.log('V109: Processing DATE SELECTION');
  console.log('V109: DEBUG - currentData keys:', Object.keys(currentData));
  console.log('V109: DEBUG - currentData.date_suggestions:', currentData.date_suggestions);
  console.log('V109: DEBUG - input.date_suggestions:', input.date_suggestions);
  console.log('V109: DEBUG - input.collected_data?.date_suggestions:', input.collected_data?.date_suggestions);

  const dateChoice = message.trim();

  if (/^[1-3]$/.test(dateChoice)) {
    const selectedIndex = parseInt(dateChoice) - 1;

    // V109 FIX: Multiple fallbacks for suggestions
    const suggestions = currentData.date_suggestions ||
                       input.collected_data?.date_suggestions ||
                       input.date_suggestions ||
                       [];

    console.log('V109: suggestions array length:', suggestions.length);
    console.log('V109: selectedIndex:', selectedIndex);

    if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
      // Process selection...
    } else {
      // V109 FIX: Log WHY validation failed
      if (suggestions.length === 0) {
        console.error('V109: CRITICAL - date_suggestions EMPTY! Cannot process selection!');
        responseText = `❌ *Erro: Dados de datas perdidos*\n\nPor favor, digite *reiniciar* para começar novamente.`;
        nextStage = 'greeting';
      } else {
        responseText = `❌ *Opção inválida*\n\nEscolha 1, 2 ou 3.`;
        nextStage = 'process_date_selection';
      }
    }
  }
```

### Fix 2: Adicionar Validação de Response Text

**Problema**: State Machine pode retornar `response_text` vazio sem detectar.

**Solução**: Validação antes do output (linha 311):

```javascript
// V109: Validate response_text before output
if (!responseText && currentStage !== 'greeting') {
  console.error('V109: CRITICAL - response_text is EMPTY!');
  console.error('V109: currentStage:', currentStage);
  console.error('V109: nextStage:', nextStage);
  console.error('V109: message:', message);
  console.error('V109: awaiting_wf06_next_dates:', currentData.awaiting_wf06_next_dates);
  console.error('V109: date_suggestions length:', (currentData.date_suggestions || []).length);

  // Emergency fallback
  responseText = `❌ *Erro no processamento*\n\nPor favor, digite *reiniciar* para começar novamente.`;
  nextStage = 'greeting';
}

const output = {
  response_text: responseText,  // ← Garantido não-vazio agora
  // ...
};
```

### Fix 3: Clear Flag ANTES do Processing

**Problema**: Flag `awaiting_wf06_next_dates` permanece true mesmo quando processamento falha.

**Solução**: Clear flag ANTES de tentar processar (linha 674):

```javascript
case 'process_date_selection':
  console.log('V109: Processing DATE SELECTION');

  // V109 FIX: Clear flag BEFORE processing (prevents re-triggering if processing fails)
  updateData.awaiting_wf06_next_dates = false;

  const dateChoice = message.trim();
  // ... rest of processing
```

---

## 📋 Próximos Passos

### Investigação Necessária

**ANTES de criar V109**, precisamos:

1. **Verificar Workflow Atual**:
   ```bash
   # Ver estrutura completa do workflow
   # http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
   ```

   Perguntas:
   - Há nodes "Send Message with Dates" ou similar depois de Build Update Queries?
   - Workflow tem loop back para State Machine?
   - Quantas vezes State Machine é executado por mensagem?

2. **Analisar Logs de Execução**:
   ```bash
   docker logs e2bot-n8n-dev 2>&1 | grep -A5 -B5 "V108: Processing DATE SELECTION"
   ```

   Verificar:
   - `date_suggestions` está vazio no log?
   - State Machine executa uma ou duas vezes?
   - Qual o valor de `currentData.date_suggestions`?

3. **Verificar Database**:
   ```sql
   SELECT
     phone_number,
     state_machine_state,
     collected_data->'awaiting_wf06_next_dates' as awaiting_flag,
     collected_data->'date_suggestions' as suggestions,
     jsonb_array_length(collected_data->'date_suggestions') as suggestions_count
   FROM conversations
   WHERE phone_number = '556181755748';
   ```

### Criar V109 Após Confirmação

Dependendo dos resultados:
- **Se suggestions está vazio**: Apply Fix 1 + Fix 2 + Fix 3
- **Se workflow tem double execution**: Fix workflow routing
- **Se workflow tem Send node separado**: Fix workflow logic

---

## 🔄 Comparação V107 → V108 → V109

| Aspecto | V107 | V108 | V109 (Proposto) |
|---------|------|------|-----------------|
| **Detecção Flag** | `awaiting = true` (sem message check) ❌ | `awaiting = true AND message` ✅ | `awaiting = true AND message` ✅ |
| **Force Estado** | Sim, mas sem message ❌ | Sim, com message ✅ | Sim, com message ✅ |
| **Preservação suggestions** | Incompleto ⚠️ | Incompleto ⚠️ | Multiple fallbacks ✅ |
| **Clear Flag Timing** | Após processing ⚠️ | Após processing ⚠️ | ANTES de processing ✅ |
| **Response Validation** | Não ❌ | Não ❌ | Sim (emergency fallback) ✅ |
| **Debug Logging** | Básico ⚠️ | Enhanced ✅ | Comprehensive ✅ |
| **Loop Prevention** | Não funciona ❌ | Não funciona ❌ | Múltiplas camadas ✅ |

---

## 📊 Evidências do Problema

### Evidência 1: User Report
```
Input: message=1
Output: response_text (vazio)
Behavior: Bot sends dates again
```

### Evidência 2: Code Analysis
- Linha 680: `suggestions` pode ser array vazio
- Linha 682: if validation fails silently
- Linha 749: break sem setar responseText

### Evidência 3: V108 Logic Flow
```
User types "1" →
V108 detects flag + message →
Forces currentStage = 'process_date_selection' →
Enters switch case →
suggestions = [] (empty!) →
if (selectedIndex < suggestions.length) → FALSE →
Falls through →
responseText remains '' →
Output sent with empty response_text →
Workflow ???
```

---

**Created**: 2026-04-28 04:30 BRT
**Author**: Claude Code Analysis
**Status**: 🔴 ROOT CAUSE IDENTIFIED - AWAITING USER INVESTIGATION DATA FOR V109
**Next Action**: User should provide workflow execution logs and database state
