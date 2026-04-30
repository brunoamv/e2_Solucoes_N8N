# V29 - Name Validation Bug Fix

> **Data**: 2025-01-13
> **Problema**: Bot rejeita nomes válidos e volta ao menu principal
> **Causa Raiz**: Lógica de validação incorreta no State Machine Logic

---

## 🐛 Problema Identificado

### Fluxo Atual (BUGADO)
```
Usuário: "1" (seleciona serviço)
Bot: "Qual seu nome completo?"
Usuário: "Bruno Rosa"
Bot: ❌ "Opção inválida" + volta ao menu
```

### Análise do Bug

Na execução 4201, quando o usuário envia "Bruno Rosa" no stage `collect_name`:

1. **Estado atual**: `collect_name` (correto)
2. **Mensagem recebida**: "Bruno Rosa" (correto)
3. **Validador V26**: Procura por dígitos → `No digits found` → retorna false
4. **Resultado**: Sistema considera nome inválido e retorna para `service_selection`

### Código Problemático (V28)

O validador `number_1_to_5` está sendo chamado incorretamente quando deveria ser o `text_min_3_chars`:

```javascript
// V26 Validator sendo chamado no momento errado
const validators = {
  number_1_to_5: (input) => {
    const cleaned = String(input)
      .trim()
      .replace(/[^\\d]/g, '')  // Remove tudo exceto dígitos
      .substring(0, 1);

    console.log('V26 Validator - Input:', JSON.stringify(input), '-> Cleaned:', cleaned);

    if (!cleaned) {
      console.log('V26 Validator - No digits found in input');
      return false;  // ← AQUI ESTÁ O PROBLEMA!
    }
  }
}
```

---

## ✅ Solução V29

### 1. Correção do Debug no State Machine

Adicionar debug específico para rastrear qual validador está sendo chamado em cada stage:

```javascript
console.log(`=== V29 STAGE VALIDATION DEBUG ===`);
console.log('Current Stage:', currentStage);
console.log('Message:', message);
console.log('Expected Validator:', getExpectedValidator(currentStage));
```

### 2. Isolamento de Validadores por Stage

Garantir que cada stage use apenas seu validador específico:

```javascript
case 'collect_name':
    console.log('V29: Validating name with text_min_3_chars');
    if (validators.text_min_3_chars(message)) {
        updateData.lead_name = message.trim();
        responseText = templates.collect_phone.text;
        nextStage = 'collect_phone';
        errorCount = 0;
    } else {
        // Mensagem específica para erro de nome
        responseText = '❌ Nome muito curto.\\n\\n👤 Digite seu nome completo:';
        // IMPORTANTE: NÃO mudar o nextStage aqui
        errorCount++;
    }
    break;
```

### 3. Prevenção de Regressão ao Menu

Garantir que falhas de validação não causem retorno ao início:

```javascript
// No final de cada case com erro
if (errorCount >= MAX_ERRORS) {
    nextStage = 'handoff_comercial';
    responseText = '⚠️ Vou transferir você para um especialista.\\n\\nAguarde...';
}
// ELSE: manter nextStage = currentStage (não mudar!)
```

---

## 🔄 Fluxo Corrigido (V29)

```
1. service_selection → Usuário envia "1"
   ✓ Validator: number_1_to_5 → TRUE
   → nextStage = 'collect_name'

2. collect_name → Usuário envia "Bruno Rosa"
   ✓ Validator: text_min_3_chars → TRUE (tem >3 chars)
   → nextStage = 'collect_phone'

3. collect_phone → Usuário envia telefone
   ✓ Validator: phone_brazil → TRUE
   → nextStage = 'collect_email'

... continua normalmente
```

---

## 📋 Mudanças Necessárias no Script V29

1. **Adicionar debug V29 específico** para rastreamento de validação
2. **Corrigir lógica de erro** em cada case para não mudar stage indevidamente
3. **Garantir isolamento** de validadores por stage
4. **Adicionar fallback** para manter currentStage em caso de erro
5. **Melhorar mensagens de erro** para serem específicas do contexto

---

## 🧪 Casos de Teste

### Teste 1: Nome Válido
```
Input: "Bruno Rosa"
Expected: Aceitar e prosseguir para collect_phone
```

### Teste 2: Nome Curto
```
Input: "Jo"
Expected: Rejeitar mas MANTER em collect_name
```

### Teste 3: Nome com Números
```
Input: "Bruno123"
Expected: Aceitar (não deve validar números em nomes)
```

### Teste 4: Múltiplos Erros
```
Input: "A" (3 vezes)
Expected: Após 3 erros, handoff_comercial
```

---

## 🚀 Implementação

1. Criar script `fix-workflow-v29-name-validation.py`
2. Corrigir lógica de validação no State Machine Logic
3. Adicionar debug V29 específico
4. Testar com fluxo completo
5. Documentar resultados

---

## 📊 Impacto

- **Problema Resolvido**: Nomes válidos serão aceitos corretamente
- **UX Melhorada**: Usuários não voltarão ao menu inesperadamente
- **Debugging**: Logs V29 facilitarão troubleshooting futuro
- **Estabilidade**: Fluxo de coleta de dados funcionará confiavelmente

---

**Status**: Pronto para implementação
**Prioridade**: CRÍTICA - Bug quebra fluxo principal do bot
**Estimativa**: 30 minutos para implementar e testar