# WhatsApp Templates v1 - Bot Menu-Based

> **Versão**: v1.0 (Menu-Based)
> **Data**: 2025-12-16
> **Sprint**: 0.1 - V1 Simple
> **Uso**: Bot sem Claude AI (menu fixo)

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Estrutura dos Templates](#estrutura-dos-templates)
3. [Mapeamento State Machine](#mapeamento-state-machine)
4. [Variáveis e Placeholders](#variáveis-e-placeholders)
5. [Formatação WhatsApp](#formatação-whatsapp)
6. [Uso no Workflow n8n](#uso-no-workflow-n8n)
7. [Testes e Validação](#testes-e-validação)
8. [Migração para v2](#migração-para-v2)

---

## 🎯 Visão Geral

Este diretório contém os **templates de mensagens WhatsApp** para o bot v1 da E2 Soluções.

**Diferença v1 vs v2**:
- **v1 (este diretório)**: Bot com menu fixo, sem Claude AI, mensagens pré-definidas
- **v2 (futuro)**: Bot com Claude AI, conversação natural, mensagens geradas dinamicamente

### Arquivos Disponíveis

```
templates/whatsapp/v1/
├── greeting.txt              # Mensagem de boas-vindas + menu principal
├── service_selected.txt      # Confirmação de serviço escolhido
├── collect_name.txt          # Solicita nome completo
├── collect_phone.txt         # Solicita telefone com DDD
├── collect_email.txt         # Solicita email (ou "pular")
├── collect_city.txt          # Solicita cidade
├── confirmation.txt          # Resumo dos dados + opções finais
├── invalid_option.txt        # Erro genérico de opção inválida
├── error_generic.txt         # Erro genérico do sistema
└── README.md                 # Este arquivo (documentação)
```

**Total**: 9 templates de mensagem + 1 README

---

## 🏗️ Estrutura dos Templates

### 1. greeting.txt

**Quando usar**: Primeiro contato com o bot, início de nova conversa, comando "NOVO"

**Conteúdo**:
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

**Variáveis**: Nenhuma (mensagem estática)

**State Machine**: `greeting` → `service_selection`

---

### 2. service_selected.txt

**Quando usar**: Após usuário escolher serviço (digitar 1-5)

**Conteúdo**:
```
{{emoji}} *{{service_name}}*

{{description}}

━━━━━━━━━━━━━━━

Perfeito! Vou coletar alguns dados para melhor atendê-lo.

👤 *Qual seu nome completo?*
```

**Variáveis**:
- `{{emoji}}`: Emoji do serviço (☀️, ⚡, 📐, 🔋, 📊)
- `{{service_name}}`: Nome do serviço (ex: "Energia Solar")
- `{{description}}`: Descrição curta do serviço

**State Machine**: `service_selection` → `collect_name`

**Mapeamento de Serviços**:

| Opção | ID | Nome | Emoji | Descrição |
|-------|----|----- |-------|-----------|
| 1 | energia_solar | Energia Solar | ☀️ | Projetos fotovoltaicos residenciais, comerciais e industriais |
| 2 | subestacao | Subestação | ⚡ | Reforma, manutenção e construção de subestações |
| 3 | projetos_eletricos | Projetos Elétricos | 📐 | Projetos elétricos, adequações e laudos de conformidade |
| 4 | bess | BESS (Armazenamento) | 🔋 | Sistemas de armazenamento de energia com baterias |
| 5 | analise_laudos | Análise e Laudos | 📊 | Análise de qualidade de energia e laudos técnicos |

---

### 3. collect_name.txt

**Quando usar**: Após confirmação de serviço, para coletar nome do lead

**Conteúdo**:
```
👤 *Qual seu nome completo?*

_Exemplo: João da Silva_
```

**Variáveis**: Nenhuma (mensagem estática)

**State Machine**: `collect_name` → `collect_phone`

**Validação**:
- Mínimo 3 caracteres
- Apenas letras e espaços
- Sem números ou caracteres especiais

---

### 4. collect_phone.txt

**Quando usar**: Após nome válido ser coletado

**Conteúdo**:
```
📱 *Qual seu telefone com DDD?*

_Exemplo: (62) 99988-7766_
```

**Variáveis**: Nenhuma (mensagem estática)

**State Machine**: `collect_phone` → `collect_email`

**Validação**:
- Formato: (DD) 9XXXX-XXXX ou (DD) XXXX-XXXX
- 10-11 dígitos numéricos (após remover formatação)
- DDD válido (11-99)
- Auto-formatação: 62999887766 → (62) 99988-7766

---

### 5. collect_email.txt

**Quando usar**: Após telefone válido ser coletado

**Conteúdo**:
```
📧 *Qual seu email?*

_Ou digite "pular" para não informar_

_Exemplo: seuemail@provedor.com_
```

**Variáveis**: Nenhuma (mensagem estática)

**State Machine**: `collect_email` → `collect_city`

**Validação**:
- Formato email válido: usuario@dominio.com
- OU palavra "pular" (case-insensitive)
- Se "pular", salva como "Não informado"

---

### 6. collect_city.txt

**Quando usar**: Após email válido (ou "pular") ser coletado

**Conteúdo**:
```
📍 *Em qual cidade você está?*

_Exemplo: Goiânia_
```

**Variáveis**: Nenhuma (mensagem estática)

**State Machine**: `collect_city` → `confirmation`

**Validação**:
- Mínimo 3 caracteres
- Apenas letras, espaços e hífens
- Capitalização automática (goiania → Goiânia)

---

### 7. confirmation.txt

**Quando usar**: Após todos os dados serem coletados, para confirmação final

**Conteúdo**:
```
✅ *Dados confirmados!*

👤 *Nome:* {{lead_name}}
📱 *Telefone:* {{phone}}
📧 *Email:* {{email}}
📍 *Cidade:* {{city}}
{{emoji}} *Serviço:* {{service_name}}

━━━━━━━━━━━━━━━

🗓️ Deseja agendar uma *visita técnica gratuita*?

1️⃣ Sim, quero agendar
2️⃣ Não, prefiro falar com especialista

_Digite 1 ou 2:_
```

**Variáveis**:
- `{{lead_name}}`: Nome completo do lead
- `{{phone}}`: Telefone formatado (62) 99988-7766
- `{{email}}`: Email ou "Não informado"
- `{{city}}`: Cidade do lead
- `{{emoji}}`: Emoji do serviço escolhido
- `{{service_name}}`: Nome do serviço escolhido

**State Machine**: `confirmation` → `scheduling` (opção 1) OU `handoff_comercial` (opção 2)

**Validação**:
- Aceita apenas "1" ou "2"
- 1 = Dispara Workflow 05 (Appointment Scheduler)
- 2 = Dispara Workflow 10 (Human Handoff)

---

### 8. invalid_option.txt

**Quando usar**: Quando usuário digita opção inválida em qualquer etapa

**Conteúdo**:
```
❌ Opção inválida. Por favor, escolha uma opção válida.
```

**Variáveis**: Nenhuma (mensagem estática)

**State Machine**: Mantém estado atual, incrementa `error_count`

**Comportamento**:
- Após 3 erros consecutivos → `handoff_comercial` (transfere para humano)
- Reseta `error_count` após entrada válida

---

### 9. error_generic.txt

**Quando usar**: Erro inesperado do sistema, exceção no código, timeout

**Conteúdo**:
```
⚠️ Ops! Algo deu errado.

Por favor, tente novamente ou digite *AJUDA* para falar com um especialista.
```

**Variáveis**: Nenhuma (mensagem estática)

**State Machine**: Volta para `greeting` (reset completo)

**Quando ocorre**:
- Erro de conexão com PostgreSQL
- Timeout na API Evolution
- Exceção não tratada no código JavaScript
- Estado inválido no state machine

---

## 🗺️ Mapeamento State Machine

Fluxo completo de estados e templates:

```
1. greeting (greeting.txt)
   ↓ [usuário digita 1-5]
2. service_selection (service_selected.txt)
   ↓ [nome válido]
3. collect_name (collect_phone.txt)
   ↓ [telefone válido]
4. collect_phone (collect_email.txt)
   ↓ [email válido ou "pular"]
5. collect_email (collect_city.txt)
   ↓ [cidade válida]
6. collect_city (confirmation.txt)
   ↓ [digita 1 ou 2]
7a. confirmation → scheduling (Workflow 05)
7b. confirmation → handoff_comercial (Workflow 10)
```

**Estados de Erro**:
- `invalid_option` → Mantém estado atual, incrementa error_count
- `error_generic` → Reseta para `greeting`
- `handoff_comercial` (3 erros) → Transfere para humano

**Estado Final**:
- `completed` → Conversa finalizada (usuário pode digitar "NOVO" para recomeçar)

---

## 📝 Variáveis e Placeholders

### Sintaxe

Todas as variáveis usam a sintaxe **Mustache**: `{{variavel}}`

### Lista Completa de Variáveis

| Variável | Tipo | Exemplo | Usado em |
|----------|------|---------|----------|
| `{{emoji}}` | string | ☀️ | service_selected.txt, confirmation.txt |
| `{{service_name}}` | string | Energia Solar | service_selected.txt, confirmation.txt |
| `{{description}}` | string | Projetos fotovoltaicos... | service_selected.txt |
| `{{lead_name}}` | string | João da Silva | confirmation.txt |
| `{{phone}}` | string | (62) 99988-7766 | confirmation.txt |
| `{{email}}` | string | joao@teste.com | confirmation.txt |
| `{{city}}` | string | Goiânia | confirmation.txt |

### Substituição no Workflow n8n

No node "State Machine Logic" (Function), a função `fillTemplate()` realiza a substituição:

```javascript
function fillTemplate(template, data) {
  let text = template;
  for (const [key, value] of Object.entries(data)) {
    text = text.replace(new RegExp(`{{${key}}}`, 'g'), value);
  }
  return text;
}
```

**Exemplo de uso**:
```javascript
const responseText = fillTemplate(templates.confirmation.template, {
  lead_name: 'João da Silva',
  phone: '(62) 99988-7766',
  email: 'joao@teste.com',
  city: 'Goiânia',
  emoji: '☀️',
  service_name: 'Energia Solar'
});
```

---

## 💬 Formatação WhatsApp

### Sintaxe Markdown

Os templates usam **formatação WhatsApp** para melhor legibilidade:

| Sintaxe | Resultado | Uso |
|---------|-----------|-----|
| `*texto*` | **texto** (negrito) | Títulos, nomes de serviços |
| `_texto_` | _texto_ (itálico) | Instruções, exemplos |
| `~texto~` | ~~texto~~ (riscado) | Não usado em v1 |
| ``` `texto` ``` | `texto` (monoespaçado) | Não usado em v1 |

### Emojis

Todos os emojis são **Unicode nativos** (não imagens):

| Emoji | Unicode | Uso |
|-------|---------|-----|
| 🤖 | U+1F916 | Bot (greeting) |
| ☀️ | U+2600 | Energia Solar |
| ⚡ | U+26A1 | Subestação |
| 📐 | U+1F4D0 | Projetos Elétricos |
| 🔋 | U+1F50B | BESS |
| 📊 | U+1F4CA | Análise e Laudos |
| 👤 | U+1F464 | Nome |
| 📱 | U+1F4F1 | Telefone |
| 📧 | U+1F4E7 | Email |
| 📍 | U+1F4CD | Cidade |
| ✅ | U+2705 | Confirmação |
| ❌ | U+274C | Erro |
| ⚠️ | U+26A0 | Alerta |
| 🗓️ | U+1F5D3 | Agendamento |

### Separadores

Use `━` (U+2501) para linhas separadoras visuais:
```
━━━━━━━━━━━━━━━
```

**Não use** `---` ou `___` (não renderizam bem no WhatsApp)

---

## 🔧 Uso no Workflow n8n

### Importando Templates

Os templates estão **embutidos no código JavaScript** do Workflow 02 v1 para simplicidade:

```javascript
const templates = {
  greeting: {
    text: '🤖 Olá! Bem-vindo à *E2 Soluções*!...'
  },
  service_selected: {
    template: '{{emoji}} *{{service_name}}*...'
  },
  // ... outros templates
};
```

### Alternativa: Carregar de Arquivos (Futuro)

Para facilitar edição sem mexer no código n8n, pode-se implementar:

```javascript
// Node "Read Template" (Read Binary File)
const greeting = $('Read Template - Greeting').first().binary.data.toString();

// Uso
responseText = greeting;
```

**Vantagens**:
- Edição sem reimportar workflow n8n
- Versionamento Git independente
- Facilita A/B testing de mensagens

**Desvantagens**:
- Mais complexidade no workflow (+ nodes)
- Depende de filesystem acessível pelo n8n

**Recomendação Sprint 0.1**: Manter templates embutidos no código (simplicidade)

---

## ✅ Testes e Validação

### Teste Manual (WhatsApp)

1. **Enviar**: "Oi"
   - **Esperado**: greeting.txt (menu 1-5)

2. **Enviar**: "1"
   - **Esperado**: service_selected.txt (☀️ Energia Solar)

3. **Enviar**: "João da Silva"
   - **Esperado**: collect_phone.txt

4. **Enviar**: "62 99988-7766"
   - **Esperado**: collect_email.txt

5. **Enviar**: "pular"
   - **Esperado**: collect_city.txt

6. **Enviar**: "Goiânia"
   - **Esperado**: confirmation.txt (resumo completo)

7. **Enviar**: "1"
   - **Esperado**: Mensagem de agendamento (Workflow 05)

### Teste Automatizado (Bash)

Execute o script de teste:

```bash
./scripts/test-v1-menu.sh --quick
```

**Testes inclusos**:
- Validators (phone, email, service selection)
- Database (insert/update conversations)
- Templates (JSON válido, variáveis substituídas)

### Checklist de Validação

- [ ] Todos os 9 templates renderizam corretamente no WhatsApp
- [ ] Emojis aparecem (não quadrados �)
- [ ] Formatação *negrito* e _itálico_ funciona
- [ ] Variáveis {{placeholder}} são substituídas
- [ ] Quebras de linha preservadas
- [ ] Separadores ━━━ aparecem corretamente
- [ ] Mensagens cabem na tela mobile (max 1000 chars)

---

## 🚀 Migração para v2

Quando migrar para v2 (Claude AI), os templates **não serão mais usados diretamente**.

### Diferenças v1 → v2

| Aspecto | v1 (Menu) | v2 (Claude AI) |
|---------|-----------|----------------|
| **Mensagens** | Templates estáticos | Geradas dinamicamente pelo Claude |
| **Fluxo** | State machine rígido | Conversacional livre |
| **Coleta de Dados** | Sequencial obrigatório | Natural, ordem flexível |
| **Erros** | `invalid_option.txt` | Claude reformula pergunta |
| **Linguagem** | Formal, menu | Natural, conversacional |

### Uso dos Templates em v2

Os templates v1 podem servir como **referência** para prompts do Claude:

```
System Prompt para Claude:

"Você é um assistente da E2 Soluções. Use tom similar a estes exemplos:

GREETING (v1):
'🤖 Olá! Bem-vindo à *E2 Soluções*!...'

SERVICE_SELECTED (v1):
'{{emoji}} *{{service_name}}*...'

Mas adapte para conversação natural, não menu fixo."
```

### Preservação

Mantenha templates v1 para:
- Referência de tom e linguagem
- Fallback se Claude API estiver indisponível
- Comparação de performance (A/B test)
- Histórico de evolução do bot

---

## 📚 Referências

### Documentação Relacionada

- **Sprint 0.1**: `/docs/sprints/SPRINT_0.1_V1_SIMPLES.md`
- **Workflow n8n**: `/n8n/workflows/02_ai_agent_conversation_V1_MENU.json`
- **Scripts**: `/scripts/deploy-v1.sh`, `/scripts/test-v1-menu.sh`
- **Database Schema**: `/database/schema.sql` (conversations, messages, leads)

### Links Externos

- **WhatsApp Business API**: https://developers.facebook.com/docs/whatsapp/
- **WhatsApp Formatting**: https://faq.whatsapp.com/539178204879377/
- **Evolution API**: https://evolution-api.com/docs/
- **n8n Workflows**: https://docs.n8n.io/workflows/

---

## 📞 Suporte

Para dúvidas ou problemas com os templates:

1. **Validação**: Execute `./scripts/test-v1-menu.sh`
2. **Logs**: Verifique `logs/test_v1_*.log`
3. **Database**: Consulte tabela `messages` para histórico
4. **n8n**: Verifique executions do Workflow 02

---

**Versão**: v1.0
**Última Atualização**: 2025-12-16
**Autor**: Claude Code
**Sprint**: 0.1 - V1 Simple
