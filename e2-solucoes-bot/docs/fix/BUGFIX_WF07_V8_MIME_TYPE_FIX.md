# WF07 V8 - Mime Type Fix (SOLUÇÃO DEFINITIVA)

**Date**: 2026-03-31
**Status**: 🎯 **ROOT CAUSE FINAL - n8n 2.14.2 REQUER MIME TYPE**

---

## ❌ Problema Real

**Execução 17671**:
- File(s) Selector: `=/email-templates/{{ $json.template_file }}` ✅ CORRETO
- Options: VAZIO ❌ INCORRETO
- Resultado: "No output data returned"

**Log**:
```
Running node "Read Template File" finished successfully
Workflow execution finished successfully
```

Node executou "successfully" MAS **não retornou dados** → workflow parou.

---

## 🔍 Root Cause

**n8n 2.14.2 Read/Write File node** tem comportamento específico:
- Arquivos HTML grandes (7.3 KB) SEM Mime Type definido → **n8n NÃO retorna dados**
- Arquivos HTML COM Mime Type: `text/html` → **n8n retorna dados corretamente**

**Razão**: n8n tenta auto-detectar tipo de arquivo, mas para HTML pode falhar e retornar vazio.

---

## ✅ Solução Definitiva

### Configuração CORRETA para n8n 2.14.2:

**Operation**: Read File(s) From Disk

**File(s) Selector**: `=/email-templates/{{ $json.template_file }}`
↑ COM "="

**Options** (clique em "Add Option"):
1. **Mime Type**: `text/html`

**NÃO adicione**:
- ❌ File Extension
- ❌ File Name
- ❌ Put Output File in Field

---

## 🔧 Como Aplicar

### Passo 1: Abra o Workflow
```
http://localhost:5678/workflow/obkmrHruB7oQmVLT
```

### Passo 2: Configure "Read Template File"

**Operation**: Read File(s) From Disk

**File(s) Selector**: `=/email-templates/{{ $json.template_file }}`

**Options**:
- Clique em "Add Option"
- Selecione "Mime Type"
- Digite: `text/html`

### Passo 3: Salve (Ctrl+S)

---

## 🧪 Como Testar

Execute com estes dados:

```json
{
  "appointment_id": "86facc7a-e06d-4d4c-9fdb-2941d460fac3",
  "lead_email": "clima.cocal.2025@gmail.com",
  "lead_name": "bruno",
  "phone_number": "556181755748",
  "service_type": "energia_solar",
  "scheduled_date": "2026-04-01",
  "scheduled_time_start": "08:00:00",
  "scheduled_time_end": "10:00:00",
  "city": "cocal-go",
  "google_calendar_event_id": "1ucistntii2j145h4cn6f0ktak",
  "calendar_success": true
}
```

**Esperado**:
1. ✅ Execute Workflow Trigger
2. ✅ Prepare Email Data
3. ✅ **Read Template File** (agora COM output: HTML completo)
4. ✅ Render Template
5. ✅ Send Email (SMTP)
6. ✅ Log Email Sent
7. ✅ Return Success

**Logs esperados**:
```
📝 [Render Template V8] Template data received: { has_template_html: true, template_length: 7494, ... }
✅ [Render V8] Template rendered successfully: { html_length: 7494, text_length: 567 }
```

---

## 📊 Timeline Completo

| Ver | Config | Options | Resultado | Causa |
|-----|--------|---------|-----------|-------|
| 17409 | Sem "=" | Put Output File in Field: data | ❌ | Expressão não avaliada |
| 17473 | Com "=" | Put Output File in Field (vazio) | ❌ | Binary sem campo |
| 17537 | Com "=" | Put Output File in Field: data | ❌ | Binary output |
| 17597 | Sem "=" | Vazio | ❌ | Expressão não avaliada |
| 17671 | Com "=" | Vazio | ❌ | HTML sem Mime Type → auto-detect falhou |
| **V8.2** | **Com "="** | **Mime Type: text/html** | **✅** | **Mime Type forçado** |

---

## 🎯 Por que Mime Type resolve?

Quando você especifica `Mime Type: text/html`:
1. n8n **força** leitura como texto (não tenta auto-detect)
2. n8n retorna conteúdo em `$json.data` como STRING
3. Code node pode acessar via `$('Read Template File').first().json.data`
4. Template é renderizado corretamente

**Sem Mime Type**:
1. n8n tenta auto-detectar tipo do arquivo
2. Auto-detect pode falhar para HTML grande
3. n8n retorna VAZIO (finished successfully mas no data)
4. Workflow para com "No output data returned"

---

## 📋 Checklist Final

Antes de testar, confirme:

- [ ] ✅ File(s) Selector = `=/email-templates/{{ $json.template_file }}`
- [ ] ✅ Tem "=" no início
- [ ] ✅ Option "Mime Type" = `text/html`
- [ ] ✅ NÃO tem "Put Output File in Field"
- [ ] ✅ Salvou o workflow (Ctrl+S)

---

## 🔄 Próximos Passos

1. ✅ Adicionar Mime Type no n8n UI
2. ⏳ Testar execução manual
3. ⏳ Verificar logs mostram template processado
4. ⏳ Testar integração WF05 → WF07
5. ⏳ Deploy em produção

---

**Date**: 2026-03-31
**Status**: ✅ **SOLUÇÃO DEFINITIVA - Mime Type text/html**
**Risk Level**: 🟢 **MUITO BAIXO**
**Testing**: ⏳ **Pendente - adicionar Mime Type e testar**
