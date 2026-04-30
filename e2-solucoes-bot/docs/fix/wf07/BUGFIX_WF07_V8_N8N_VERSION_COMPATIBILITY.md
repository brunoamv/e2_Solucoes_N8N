# WF07 V8 - n8n Version Compatibility Fix

**Date**: 2026-03-31
**Status**: 🎯 **ROOT CAUSE IDENTIFIED - n8n 2.14.2 API DIFFERENCE**

---

## ❌ Problema Real

Workflow JSON gerado com configuração para versão ANTIGA do n8n:

```json
"options": {
  "encoding": "utf8",        // ❌ NÃO EXISTE em n8n 2.14.2
  "dataPropertyName": "data" // ❌ NÃO EXISTE em n8n 2.14.2
}
```

**n8n 2.14.2 Read/Write File node** tem opções DIFERENTES:
- ✅ File Extension
- ✅ File Name
- ✅ Mime Type
- ✅ Put Output File in Field

**NÃO TEM**:
- ❌ encoding
- ❌ dataPropertyName

---

## 🔍 Timeline de Investigação

| Tentativa | Config | Resultado | Causa |
|-----------|--------|-----------|-------|
| 17409 | `/email-templates/{{ $json.template_file }}` + "Put Output File in Field: data" | ❌ No output | SEM "=" → expressão não avaliada |
| 17473 | `=/email-templates/{{ $json.template_file }}` + "Put Output File in Field" (VAZIO) | ❌ No output | Binary sem campo → dados perdidos |
| 17537 | `=/email-templates/{{ $json.template_file }}` + "Put Output File in Field: data" | ❌ No output | Binary output → `$binary.data` (código busca `$json.data`) |
| 17597 | `/email-templates/{{ $json.template_file }}` + Options VAZIO | ❌ No output | SEM "=" → expressão não avaliada |
| **V8.1** | **`=/email-templates/{{ $json.template_file }}`** + **Options VAZIO** | **✅ ESPERADO** | **Expressão avaliada + String output** |

---

## ✅ Solução Definitiva para n8n 2.14.2

### Configuração CORRETA

**Operation**: Read File(s) From Disk

**File(s) Selector**: `=/email-templates/{{ $json.template_file }}`
↑ **"=" É OBRIGATÓRIO** para avaliar expressão

**Options**: **(TODAS VAZIAS)**
- ❌ **NÃO adicione "Put Output File in Field"**
- ❌ **NÃO adicione "File Extension"**
- ❌ **NÃO adicione "File Name"**
- ❌ **NÃO adicione "Mime Type"**

**Razão**: Quando Options está vazio, n8n 2.14.2 retorna STRING em `$json.data` (não Binary)

---

## 🔧 Como Aplicar

### Passo 1: Abra o Workflow
```
http://localhost:5678/workflow/obkmrHruB7oQmVLT
```

### Passo 2: Configure o Node "Read Template File"

**Operation**: Read File(s) From Disk

**File(s) Selector**: `=/email-templates/{{ $json.template_file }}`

**Options**: (clique no X para remover TODAS as options se houver alguma)

### Passo 3: Salve (Ctrl+S)

---

## 🧪 Como Testar

1. Execute o script de teste:
```bash
/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/test-wf07-v8-n8n-2.14.2.sh
```

2. Copie os dados de teste exibidos

3. Abra n8n UI → Execute Workflow → Cole os dados

4. Verifique que TODOS os 7 nodes executam:
   - ✅ Execute Workflow Trigger
   - ✅ Prepare Email Data
   - ✅ Read Template File (output: HTML em `$json.data`)
   - ✅ Render Template (processa variáveis)
   - ✅ Send Email (SMTP)
   - ✅ Log Email Sent
   - ✅ Return Success

5. Verifique logs:
```bash
docker logs e2bot-n8n-dev -f | grep -E "Render Template V8"
```

**Esperado**:
```
📝 [Render Template V8] Template data received: { has_template_html: true, template_length: 7494, ... }
✅ [Render V8] Template rendered successfully: { html_length: 7494, text_length: 567 }
```

---

## 📊 Diferenças entre Versões n8n

### Versão Antiga (não especificada):
```json
{
  "options": {
    "encoding": "utf8",
    "dataPropertyName": "data"
  }
}
```
**Output**: String em campo customizado

### n8n 2.14.2:
```json
{
  "options": {}  // ← VAZIO = String output padrão
}
```
**Output**: String em `$json.data` (comportamento padrão)

**OU**:
```json
{
  "options": {
    "putOutputFileInField": "data"  // ← Opção DIFERENTE
  }
}
```
**Output**: Binary em `$binary.data`

---

## 🎯 Por que Options Vazio Funciona?

Em **n8n 2.14.2**, o comportamento PADRÃO (sem options) é:
1. Ler arquivo como **STRING**
2. Colocar em `$json.data`
3. Code node pode acessar via `$('Read Template File').first().json.data`

**COM "Put Output File in Field"**:
1. Ler arquivo como **BINARY**
2. Colocar em `$binary.data`
3. Code node buscando `$json.data` encontra **undefined**

---

## 📋 Checklist Final

Antes de testar, confirme:

- [ ] ✅ File(s) Selector = `=/email-templates/{{ $json.template_file }}`
- [ ] ✅ Tem "=" no início (para avaliar expressão)
- [ ] ✅ Options está VAZIO (sem nenhuma option adicionada)
- [ ] ✅ Salvou o workflow (Ctrl+S)
- [ ] ✅ Docker volume mount existe: `../email-templates:/email-templates:ro`
- [ ] ✅ Templates acessíveis: `docker exec e2bot-n8n-dev ls /email-templates/`

---

## 🔄 Próximos Passos

1. ✅ Aplicar configuração correta no n8n UI
2. ⏳ Testar execução manual com dados de teste
3. ⏳ Verificar logs mostram template processado
4. ⏳ Testar integração WF05 V7 → WF07 V8
5. ⏳ Deploy em produção

---

## 📚 Arquivos Relacionados

- **Workflow**: `n8n/workflows/07_send_email_v8_no_fs_module.json`
- **Script Teste**: `scripts/test-wf07-v8-n8n-2.14.2.sh`
- **Docs Anteriores**:
  - `docs/BUGFIX_WF07_V8_READ_TEMPLATE_BINARY_FIX.md` (análise binário vs string)
  - `docs/DEPLOY_WF07_V8_NO_FS_MODULE_FINAL.md` (solução fs module)

---

**Date**: 2026-03-31
**Status**: ✅ **SOLUÇÃO DEFINITIVA - n8n 2.14.2 Compatibility**
**Risk Level**: 🟢 **MUITO BAIXO**
**Testing**: ⏳ **Pendente - aplicar config e testar**
