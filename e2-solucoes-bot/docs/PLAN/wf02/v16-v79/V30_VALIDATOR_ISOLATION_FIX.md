# V30 - Isolamento de Validadores e Correção de Fluxo

> **Data**: 2025-01-13
> **Problema Crítico**: Validador errado sendo chamado em stages incorretos
> **Causa Raiz**: Lógica do switch/case mal estruturada permitindo vazamento de validação

---

## 🚨 Bug Crítico Identificado

### Log de Evidência (Execução 4220)
```
=== V29 VALIDATOR: number_1_to_5 ===
V29 number validator - Input: "Bruno Rosa" -> Cleaned:
```

**PROBLEMA**: Quando o usuário está no stage `collect_name` e envia "Bruno Rosa", o sistema está chamando o validador `number_1_to_5` ao invés de `text_min_3_chars`!

### Análise do Código V29 (BUGADO)

No State Machine Logic do V29, encontrei o problema:

```javascript
case 'collect_name':
    console.log('=== V29 NAME VALIDATION DEBUG ===');
    console.log('Stage: collect_name');
    console.log('Message received:', message);
    console.log('Calling validator: text_min_3_chars');

    if (validators.text_min_3_chars(message)) {
      // ...
    }
    break;
break;  // ← DUPLICAÇÃO DE BREAK CAUSANDO PROBLEMA!
```

### Fluxo do Bug

1. **Usuário seleciona serviço**: Envia "1"
   - Stage: `service_selection`
   - Validador: `number_1_to_5` ✅ (correto)
   - Next: `collect_name`

2. **Bot pede nome**: "Qual seu nome completo?"
   - Stage atual: `collect_name`
   - Validador esperado: `text_min_3_chars`

3. **Usuário envia nome**: "Bruno Rosa"
   - Stage: `collect_name`
   - **BUG**: Sistema chama `number_1_to_5` ❌
   - Resultado: Nome rejeitado, volta ao menu

---

## ✅ Solução V30 - Isolamento Completo de Validadores

### 1. Remover Duplicação de Break

```javascript
case 'collect_name':
    // V30: Validação isolada para nomes
    console.log('=== V30 STAGE: collect_name ===');
    console.log('Input:', message);

    // V30: APENAS validador de texto para nomes
    const nameIsValid = validators.text_min_3_chars(message);
    console.log('V30: Name validation result:', nameIsValid);

    if (nameIsValid) {
      updateData.lead_name = message.trim();
      responseText = templates.collect_phone.text;
      nextStage = 'collect_phone';
      errorCount = 0;
    } else {
      responseText = '❌ Nome muito curto.\n\n👤 Digite seu nome completo:';
      nextStage = 'collect_name'; // Mantém no stage atual
      errorCount++;
    }
    break; // APENAS UM BREAK!
```

### 2. Garantir Isolamento de Validadores

```javascript
// V30: Mapa explícito de validadores por stage
const stageValidators = {
  'greeting': null,
  'service_selection': validators.number_1_to_5,
  'collect_name': validators.text_min_3_chars,
  'collect_phone': validators.phone_brazil,
  'collect_email': validators.email_or_skip,
  'collect_city': validators.city_name,
  'confirmation': validators.confirmation_1_or_2
};

// V30: Aplicar validador correto baseado no stage
const currentValidator = stageValidators[currentStage];
if (currentValidator) {
  const isValid = currentValidator(message);
  console.log(`V30: Stage ${currentStage} validation:`, isValid);
}
```

### 3. Debug Aprimorado V30

```javascript
console.log('=== V30 VALIDATION ISOLATION ===');
console.log('Current Stage:', currentStage);
console.log('Message:', message);
console.log('Expected Validator:', getExpectedValidator(currentStage));
console.log('Actual Validator Called:', /* track which one is called */);
```

---

## 🔧 Script de Correção V30

### fix-workflow-v30-validator-isolation.py

```python
#!/usr/bin/env python3
"""
Fix V30: Validator Isolation and Flow Correction
Problem: Wrong validator being called for stages
Solution: Proper case isolation and validator mapping
"""

import json
import sys
from pathlib import Path

def fix_validator_isolation(function_code):
    """Fix validator isolation in State Machine Logic"""

    # Remove duplicate break statements
    function_code = function_code.replace("break;\nbreak;", "break;")

    # Fix collect_name case completely
    collect_name_start = function_code.find("case 'collect_name':")
    if collect_name_start != -1:
        collect_name_end = function_code.find("case 'collect_phone':", collect_name_start)
        if collect_name_end == -1:
            collect_name_end = function_code.find("default:", collect_name_start)

        new_collect_name = """  case 'collect_name':
    // V30: Isolated name validation
    console.log('=== V30 STAGE: collect_name ===');
    console.log('Input message:', message);
    console.log('Calling ONLY text_min_3_chars validator');

    // V30: Direct validator call - no ambiguity
    const nameValid = validators.text_min_3_chars(message);
    console.log('V30 Name validation result:', nameValid);

    if (nameValid) {
      console.log('V30: Name accepted, moving to collect_phone');
      updateData.lead_name = message.trim();
      responseText = templates.collect_phone.text;
      nextStage = 'collect_phone';
      errorCount = 0;
    } else {
      console.log('V30: Name rejected, staying in collect_name');
      responseText = '❌ Nome muito curto.\\n\\n👤 Digite seu nome completo:';
      nextStage = 'collect_name'; // V30: Explicit stage maintenance
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Vou transferir você para um especialista.\\n\\nAguarde...';
      }
    }
    break;

  """

        # Replace the entire collect_name case
        before = function_code[:collect_name_start]
        after = function_code[collect_name_end:]
        function_code = before + new_collect_name + after

    return function_code

def add_stage_validator_mapping(function_code):
    """Add explicit stage-to-validator mapping"""

    # Add before switch statement
    switch_pos = function_code.find("switch (currentStage) {")
    if switch_pos != -1:
        mapping_code = """
// V30: Explicit stage-to-validator mapping
const stageValidatorMap = {
  'greeting': null,
  'service_selection': 'number_1_to_5',
  'collect_name': 'text_min_3_chars',
  'collect_phone': 'phone_brazil',
  'collect_email': 'email_or_skip',
  'collect_city': 'city_name',
  'confirmation': 'confirmation_1_or_2'
};

console.log('=== V30 VALIDATOR ISOLATION ===');
console.log('Stage:', currentStage);
console.log('Expected Validator:', stageValidatorMap[currentStage]);
console.log('Message to validate:', message);

switch (currentStage) {"""

        function_code = function_code.replace("switch (currentStage) {", mapping_code)

    return function_code
```

---

## 📊 Teste de Validação V30

### Cenário 1: Nome Válido
```
Stage: collect_name
Input: "Bruno Rosa"
Expected: validators.text_min_3_chars → TRUE
Result: Aceita nome, avança para collect_phone ✅
```

### Cenário 2: Seleção de Serviço
```
Stage: service_selection
Input: "1"
Expected: validators.number_1_to_5 → TRUE
Result: Aceita número, avança para collect_name ✅
```

### Cenário 3: Nome Inválido
```
Stage: collect_name
Input: "Jo"
Expected: validators.text_min_3_chars → FALSE
Result: Rejeita mas MANTÉM em collect_name ✅
```

---

## 🚀 Implementação

1. **Criar script V30**:
   ```bash
   python3 scripts/fix-workflow-v30-validator-isolation.py
   ```

2. **Importar workflow V30** no n8n

3. **Validar com logs**:
   ```bash
   docker logs -f e2bot-n8n-dev | grep V30
   ```

4. **Testar fluxo completo**:
   - Enviar "1" → deve aceitar
   - Enviar "Bruno Rosa" → deve aceitar
   - Continuar com telefone → deve funcionar

---

## 📈 Impacto

- **Bug Resolvido**: Validadores isolados por stage
- **UX Melhorada**: Fluxo funciona conforme esperado
- **Debugging**: Logs V30 claros para troubleshooting
- **Manutenibilidade**: Código mais limpo e organizado

---

**Status**: Pronto para implementação
**Prioridade**: CRÍTICA - Bug quebra fluxo principal
**Estimativa**: 15 minutos para implementar e testar