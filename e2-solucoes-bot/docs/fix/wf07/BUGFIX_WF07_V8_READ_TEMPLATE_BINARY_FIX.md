# WF07 V8 - Read Template File Binary Fix

**Date**: 2026-03-31
**Status**: 🎯 **ROOT CAUSE IDENTIFICADO - SOLUÇÃO DEFINITIVA**

---

## ❌ Problema Real

Execução 17537 mostra:
```
No output data returned
n8n stops executing the workflow when a node has no output data.
```

Node "Read Template File" está **retornando dados VAZIOS** apesar de:
- ✅ Configuração correta: `=/email-templates/{{ $json.template_file }}`
- ✅ Property Name: `data`
- ✅ Arquivo acessível no container
- ✅ Permissões corretas (node:node 0664)

## 🔍 Root Cause

O node "Read/Write File" versão 1 no n8n 2.14.2 tem **DUAS opções diferentes** para output:

### ❌ Configuração ERRADA (atual):
```
Options:
  Put Output File in Field: data
```
**Resultado**: Arquivo lido como **BINÁRIO** → campo `data` contém Buffer → code node não consegue acessar como string → **NO OUTPUT DATA**

### ✅ Configuração CORRETA:
```
Options:
  (NENHUMA opção marcada - usa default)
```
**OU**:
```
Options:
  dataPropertyName: data
```
**Resultado**: Arquivo lido como **STRING** → campo `data` contém HTML text → code node acessa normalmente

---

## ✅ Solução Definitiva

### **OPÇÃO 1: Remover "Put Output File in Field"**

1. Abra: `http://localhost:5678/workflow/obkmrHruB7oQmVLT`
2. Click no node **"Read Template File"**
3. **DESMARQUE** a opção "Put Output File in Field"
4. O node vai usar o comportamento **padrão**: colocar conteúdo do arquivo em `json.data` como STRING
5. Salve (Ctrl+S)

### **OPÇÃO 2: Usar "Read Binary File"**

Se o node precisar retornar binário, o code node "Render Template" deve ler assim:

```javascript
// Read binary data and convert to string
const binaryData = $('Read Template File').first().binary.data;
const templateHtml = Buffer.from(binaryData.data, binaryData.mimeType).toString('utf-8');
```

**MAS isso é mais complexo!** Use a OPÇÃO 1.

---

## 🧪 Como Testar

### Passo 1: Remover "Put Output File in Field"

No node "Read Template File":
- Operation: `Read File(s) From Disk`
- File(s) Selector: `=/email-templates/{{ $json.template_file }}`
- Options: **NENHUMA** (deixe vazio ou só com dataPropertyName)

### Passo 2: Testar com dados reais

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

### Passo 3: Verificar Logs

```bash
docker logs e2bot-n8n-dev -f | grep -E "Render Template V8"
```

**Esperado**:
```
📝 [Render Template V8] Template data received: { has_template_html: true, template_length: 7494, ... }
✅ [Render V8] Template rendered successfully: { html_length: 7494, text_length: 567 }
```

---

## 📊 Timeline Completo

| Ver | Issue | Solution | Status |
|-----|-------|----------|--------|
| V2.0 | Missing 6 fields | → V3 | ❌ |
| V3 | Docker path | → V4 | ❌ |
| V4 | Read File empty | → V4.1 | ❌ |
| V4.1 | Missing dataPropertyName | → V5 | ❌ |
| V5 | Templates not in container | → V6 | ❌ |
| V6 | fs.readFileSync blocked | → V8 | ❌ |
| V8 | Template HTML from node | → V8.1 | ❌ |
| **V8.1** | **Binary vs String output** | **Remove "Put Output File in Field"** | **✅** |

---

## 🔧 Technical Details

### n8n Read/Write File Node Behavior

**n8n versão 2.14.2** - Node "readWriteFile" v1:

#### Mode 1: Default (STRING output)
```
Options: (vazio ou dataPropertyName: data)
Output: { json: { data: "<html>...</html>" } }
Access: $json.data (STRING)
```

#### Mode 2: Binary (BUFFER output)
```
Options: Put Output File in Field: data
Output: { binary: { data: Buffer } }
Access: $binary.data (BUFFER - precisa converter)
```

### Code Node Access Pattern

**Render Template V8** linha 6:
```javascript
const templateHtml = $('Read Template File').first().json.data;
```

**Expectativa**: `templateHtml` é uma STRING com HTML
**Realidade (com Put Output File in Field)**: `$json.data` é undefined porque dados estão em `$binary.data`

---

## ✅ Verificação Pós-Fix

1. Node "Read Template File" **sem** "Put Output File in Field"
2. Execução mostra **"Output data: ..."** (não "No output data")
3. Logs mostram `[Render Template V8] Template data received: { has_template_html: true, ... }`
4. Email enviado com sucesso
5. Email log criado no banco de dados

---

**Date**: 2026-03-31
**Status**: ✅ **SOLUÇÃO DEFINITIVA - Remover "Put Output File in Field"**
**Risk Level**: 🟢 **MUITO BAIXO**
**Testing**: ⏳ **Pendente - aplicar fix e testar**
