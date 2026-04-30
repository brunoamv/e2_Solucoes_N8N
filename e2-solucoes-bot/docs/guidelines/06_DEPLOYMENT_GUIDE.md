# Deployment Guide - Production Deployment Process

> **Processo de deployment para produção** | Atualizado: 2026-04-29
> **Status**: ✅ PRODUCTION - Processo validado em 114 versões do WF02

---

## 📖 Visão Geral

Este documento documenta o processo completo de deployment de workflows para produção, incluindo versionamento, rollback procedures, validation steps, e best practices.

### Características Principais

- **Version Increment Strategy**: Versionamento sequencial com suffix descritivo
- **Pre-Deployment Checklist**: Validação antes de promover para produção
- **Deployment Steps**: Processo passo a passo para n8n UI
- **Rollback Procedures**: Como reverter para versão anterior
- **Production Validation**: Checklist pós-deployment
- **Git Integration**: Documentação e commit conventions

---

## 🔢 Version Increment Strategy

### Naming Convention

```
WFXX_VYY_DESCRIPTION.json

Onde:
- XX: Número do workflow (01-07)
- YY: Versão sequencial (incremento de 1)
- DESCRIPTION: Descrição curta da mudança

Exemplos:
- 02_ai_agent_conversation_V114_FUNCIONANDO.json
- 02_ai_agent_conversation_V115_NEW_FEATURE.json
- 06_calendar_availability_service_v2_2.json
```

### Version Suffix Guidelines

```yaml
# Para mudanças pequenas (patch)
_FIX: "Bug fix específico"
_COMPLETE: "Versão funcional completa"
_FUNCIONANDO: "Versão validada em produção"

# Para features novas
_NEW_FEATURE: "Feature específica adicionada"
_INTEGRATION: "Integração com novo serviço"

# Para refactorings
_REFACTORED: "Código refatorado mantendo funcionalidade"
_OPTIMIZED: "Otimização de performance"

# Para correções críticas
_CRITICAL_FIX: "Correção crítica de produção"
_ROLLBACK: "Rollback para versão anterior"
```

### Quando Incrementar Versão

```yaml
increment_version:
  always:
    - Mudanças em lógica de State Machine
    - Novos estados adicionados
    - Mudanças em integração com WF06
    - Mudanças em schema de banco de dados
    - Correções de bugs críticos

  sometimes:
    - Mudanças em mensagens de texto (se afetarem UX)
    - Otimizações de performance
    - Refactorings sem mudança de comportamento

  never:
    - Correções de typos em comentários
    - Mudanças em logging (console.log apenas)
    - Mudanças em documentação inline
```

---

## ✅ Pre-Deployment Checklist

### 1. Code Review

```bash
# 1. Revisar mudanças em cada node
# n8n UI → Open workflow → Review cada node modificado

# Verificar:
✅ Lógica correta em todos os estados
✅ Validação inline funcionando
✅ Error handling implementado
✅ Logging adequado (console.log)
✅ Estrutura de retorno completa (response_text, next_stage, etc)
```

### 2. Local Testing

```bash
# 1. Test Happy Path
# WhatsApp: "oi" → complete flow → verify appointment created
# Expected: All 15 states execute correctly

# 2. Test Edge Cases
# - Invalid phone number
# - Invalid email
# - Service selection 2 (comercial)
# - Race conditions (rapid messages)

# 3. Test WF06 Integration
# - Verify 3 dates shown
# - Verify time slots shown
# - Verify appointment confirmed

# 4. Verify Database State
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM conversations WHERE phone_number = '556181755748';"

# Expected: All data correctly saved
```

### 3. Validation Queries

```sql
-- Verify schema compatibility
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'conversations';
-- Expected: All referenced columns exist

-- Check for conflicts
SELECT phone_number, COUNT(*)
FROM conversations
GROUP BY phone_number
HAVING COUNT(*) > 1;
-- Expected: No duplicates (0 rows)

-- Verify recent data
SELECT phone_number, state_machine_state, created_at
FROM conversations
ORDER BY created_at DESC
LIMIT 5;
-- Expected: Recent test conversations visible
```

### 4. Log Analysis

```bash
# Check for errors in logs
docker logs e2bot-n8n-dev 2>&1 | grep -i "error" | tail -20
# Expected: No unexpected errors

# Verify version tags
docker logs e2bot-n8n-dev | grep -E "V[0-9]+" | tail -10
# Expected: Version tags present and correct
```

---

## 🚀 Deployment Steps

### Step 1: Export Current Production Version (Backup)

```bash
# 1. n8n UI → Workflows → Find current production workflow
# Example: 02_ai_agent_conversation_V114_FUNCIONANDO

# 2. Click ⋮ (three dots) → Download
# Save as: n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json

# 3. Git commit backup
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
git add n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json
git commit -m "chore: backup WF02 V114 before V115 deployment"
```

### Step 2: Prepare New Version

```bash
# 1. Create development version first
# Example: 02_ai_agent_conversation_V115_DEVELOPMENT.json

# 2. Test in development environment thoroughly
# Run all tests from "Pre-Deployment Checklist"

# 3. Export development version
# n8n UI → Download → Save as development/wf02/...

# 4. Git commit development version
git add n8n/workflows/development/wf02/02_ai_agent_conversation_V115_DEVELOPMENT.json
git commit -m "feat: WF02 V115 development version with [feature]"
```

### Step 3: Import to Production

```bash
# 1. n8n UI → Workflows → Import from file
# Select: n8n/workflows/development/wf02/02_ai_agent_conversation_V115_DEVELOPMENT.json

# 2. After import, rename workflow
# Original name: "02_ai_agent_conversation_V115_DEVELOPMENT"
# New name: "02_ai_agent_conversation_V115_FUNCIONANDO"

# 3. Deactivate old production version
# Find: "02_ai_agent_conversation_V114_FUNCIONANDO"
# Click: Active toggle → OFF

# 4. Activate new production version
# Find: "02_ai_agent_conversation_V115_FUNCIONANDO"
# Click: Active toggle → ON

# 5. Verify webhook URL unchanged
# Webhook node → Check URL still correct
# Expected: http://localhost:5678/webhook/whatsapp-message
```

### Step 4: Production Validation

```bash
# 1. Send test WhatsApp message
# WhatsApp: "oi"
# Expected: Immediate response with greeting

# 2. Monitor logs
docker logs -f e2bot-n8n-dev | grep "V115"
# Expected: V115 tags appearing in logs

# 3. Complete flow test
# WhatsApp: Complete full flow → verify appointment
# Expected: All steps execute correctly

# 4. Check database
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM conversations ORDER BY created_at DESC LIMIT 1;"
# Expected: New conversation with V115 data

# 5. Monitor for 10 minutes
docker logs -f e2bot-n8n-dev | grep -E "ERROR|WARN"
# Expected: No unexpected errors
```

### Step 5: Final Production Export

```bash
# 1. Export production version
# n8n UI → 02_ai_agent_conversation_V115_FUNCIONANDO → Download
# Save as: n8n/workflows/production/wf02/02_ai_agent_conversation_V115_FUNCIONANDO.json

# 2. Move old production to historical
mv n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json \
   n8n/workflows/historical/wf02/

# 3. Git commit production version
git add n8n/workflows/production/wf02/02_ai_agent_conversation_V115_FUNCIONANDO.json
git add n8n/workflows/historical/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json
git commit -m "chore: promote WF02 V115 to production

- V115 deployed to production environment
- V114 moved to historical archive
- Validated with complete flow test
- No errors in 10-minute monitoring period

Deployment date: $(date -u +%Y-%m-%d)
Deployed by: Bruno Rosa <clima.cocal.2025@gmail.com>"
```

---

## 🔄 Rollback Procedures

### When to Rollback

```yaml
immediate_rollback:
  - Critical bug in production
  - Workflow crashes repeatedly
  - Database corruption
  - Integration failure (WF06, WF05, WF07)
  - User complaints about functionality

planned_rollback:
  - Feature not performing as expected
  - Performance degradation > 50%
  - Unexpected behavior after 24 hours
```

### Rollback Steps

```bash
# 1. Deactivate current production version (V115)
# n8n UI → 02_ai_agent_conversation_V115_FUNCIONANDO → Active: OFF

# 2. Activate previous production version (V114)
# n8n UI → Workflows → Import from file
# Select: n8n/workflows/historical/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json
# After import → Active: ON

# 3. Verify webhook URL
# Check webhook node still has correct URL

# 4. Test rollback version
# WhatsApp: "oi" → complete flow
# Expected: V114 working correctly

# 5. Monitor logs
docker logs -f e2bot-n8n-dev | grep "V114"
# Expected: V114 tags appearing (not V115)

# 6. Git commit rollback
git commit -m "chore: ROLLBACK WF02 from V115 to V114

Reason: [Detailed reason for rollback]
Issue: [Specific issue encountered]
Impact: [User/system impact]

Rollback date: $(date -u +%Y-%m-%d)
Performed by: Bruno Rosa <clima.cocal.2025@gmail.com>"
```

### Post-Rollback Actions

```bash
# 1. Document issue
# Create bugfix report in docs/fix/wf02/v100-v114/

# 2. Fix development version
# Update V115 development version with fix

# 3. Re-test before re-deployment
# Complete all tests in "Pre-Deployment Checklist"

# 4. Plan re-deployment
# Only re-deploy after fix validated
```

---

## 📝 Git Commit Conventions

### Deployment Commits

```bash
# Format:
chore: [action] [workflow] [version] [description]

# Types:
chore: backup WF02 V114 before V115 deployment
feat: WF02 V115 development version with [feature]
chore: promote WF02 V115 to production
chore: ROLLBACK WF02 from V115 to V114

# Examples:
git commit -m "chore: backup WF02 V114 before V115 deployment

- Exported V114 production version as backup
- Saved in production/wf02/ directory
- Pre-deployment safety measure

Backup date: 2026-04-29"

git commit -m "feat: WF02 V115 new validation logic

- Added email validation with regex pattern
- Improved phone number validation
- Enhanced error messages for invalid input

Development version tested with 50+ test cases
All validations passed successfully"

git commit -m "chore: promote WF02 V115 to production

- V115 deployed to production environment
- V114 moved to historical archive
- Validated with complete flow test
- No errors in 10-minute monitoring period

Features:
- Enhanced email validation
- Improved phone validation
- Better error messages

Deployment date: 2026-04-29
Deployed by: Bruno Rosa <clima.cocal.2025@gmail.com>"
```

### Documentation Commits

```bash
# Deployment documentation
git commit -m "docs: WF02 V115 deployment guide

- Created complete deployment documentation
- Includes pre-deployment checklist
- Rollback procedures documented
- Production validation steps

Location: docs/deployment/wf02/v100-v114/DEPLOY_WF02_V115_*.md"

# Bugfix documentation
git commit -m "docs: WF02 V115 bugfix report

- Root cause analysis of [issue]
- Solution implementation details
- Testing procedures and validation

Location: docs/fix/wf02/v100-v114/BUGFIX_WF02_V115_*.md"
```

---

## 🎯 Best Practices

### 1. Always Test in Development First

```yaml
flow:
  1. Create development version (V115_DEVELOPMENT)
  2. Test thoroughly (happy path + edge cases)
  3. Export development version
  4. Import to production (rename to V115_FUNCIONANDO)
  5. Activate production version
  6. Validate with real tests
  7. Monitor for issues

never:
  - Deploy directly to production without testing
  - Skip validation steps
  - Assume everything will work
```

### 2. Backup Before Every Deployment

```bash
# ALWAYS export current production version first
# Save in production/wf02/ directory
# Git commit before making changes

# Rollback is EASY if you have backup
# Rollback is IMPOSSIBLE without backup
```

### 3. Monitor After Deployment

```bash
# Monitor for at least 10 minutes after deployment
docker logs -f e2bot-n8n-dev

# Watch for:
# - Unexpected errors
# - Version tags (should show new version)
# - Workflow executions (should complete successfully)

# If ANY issues → ROLLBACK immediately
```

### 4. Document Everything

```bash
# Create deployment documentation BEFORE deployment
# - Pre-deployment checklist
# - Deployment steps
# - Validation procedures

# Create bugfix reports for issues
# - Root cause analysis
# - Solution details
# - Testing procedures

# Update CLAUDE.md with production status
# - Current production version
# - Key features
# - Critical fixes
```

### 5. Version Increment Logic

```javascript
// SIMPLE RULE: Any code change = version increment

// V114 → V115: Bug fix
// V115 → V116: New feature
// V116 → V117: Optimization

// EXCEPTION: Only logging/comments (no version increment)
```

---

## 📊 Deployment Timeline

### Typical Deployment (30-45 minutes)

```yaml
00:00 - Pre-Deployment Checklist (15 min)
  - Code review
  - Local testing
  - Database validation
  - Log analysis

00:15 - Backup Current Production (5 min)
  - Export V114
  - Git commit backup

00:20 - Deploy New Version (10 min)
  - Import V115
  - Rename to FUNCIONANDO
  - Deactivate old version
  - Activate new version

00:30 - Production Validation (10 min)
  - Test complete flow
  - Monitor logs
  - Check database
  - Verify integrations

00:40 - Final Export & Documentation (5 min)
  - Export production version
  - Move old to historical
  - Git commit
  - Update CLAUDE.md
```

### Emergency Rollback (5-10 minutes)

```yaml
00:00 - Identify Issue (2 min)
  - Critical bug detected
  - Decision to rollback

00:02 - Deactivate Current Version (1 min)
  - Turn off V115

00:03 - Activate Previous Version (2 min)
  - Import V114 from historical
  - Activate

00:05 - Verify Rollback (3 min)
  - Test basic flow
  - Monitor logs
  - Confirm V114 working

00:08 - Document Rollback (2 min)
  - Git commit with reason
  - Create issue report
```

---

## 🚨 Common Deployment Issues

### Issue 1: Webhook URL Changes

**Symptoms**:
- WhatsApp messages not triggering workflow

**Solution**:
```bash
# Verify webhook URL after import
# n8n UI → Workflow → Webhook node → Check URL

# Should be: http://localhost:5678/webhook/whatsapp-message
# If different: Update Evolution API webhook configuration
```

### Issue 2: Credentials Not Connected

**Symptoms**:
- PostgreSQL queries fail
- Google Calendar requests fail
- SMTP email not sent

**Solution**:
```bash
# n8n UI → Credentials → Verify all credentials connected:
# - Evolution API ✅
# - PostgreSQL ✅
# - Google Calendar OAuth2 ✅
# - SMTP Email ✅

# Re-connect if necessary
```

### Issue 3: Old Version Still Active

**Symptoms**:
- New version imported but old behavior persists

**Solution**:
```bash
# Verify ONLY new version is active
# n8n UI → Workflows → Filter by "02_ai_agent"
# Expected: Only V115 active, V114 inactive
```

### Issue 4: Database Schema Mismatch

**Symptoms**:
- Errors about missing columns
- JSONB operations fail

**Solution**:
```sql
-- Verify schema
SELECT column_name FROM information_schema.columns
WHERE table_name = 'conversations';

-- Add missing columns if needed
ALTER TABLE conversations ADD COLUMN date_suggestions JSONB;
ALTER TABLE conversations ADD COLUMN slot_suggestions JSONB;
```

---

## 📚 Referências

### Deployment Documentation

- **V111 Deployment**: `/docs/deployment/wf02/v100-v114/DEPLOY_WF02_V111_DATABASE_ROW_LOCKING.md`
- **V114 Deployment**: `/docs/WF02_V114_PRODUCTION_DEPLOYMENT.md`
- **V105 Deployment**: `/docs/deployment/wf02/v100-v114/DEPLOY_WF02_V105_WF06_ROUTING_FIX.md`

### Quick Deploy Guides

- **V111 Quick Deploy**: `/docs/WF02_V111_QUICK_DEPLOY.md`
- **V114 Quick Deploy**: `/docs/WF02_V114_QUICK_DEPLOY.md`
- **V105 Quick Deploy**: `/docs/WF02_V105_QUICK_DEPLOY.md`

### Workflows

- **Production**: `/n8n/workflows/production/wf02/`
- **Development**: `/n8n/workflows/development/wf02/`
- **Historical**: `/n8n/workflows/historical/wf02/`

### CLAUDE.md

- **Production Status**: `CLAUDE.md` (root directory)
- **Update after every deployment**: Document current production version

---

**Última Atualização**: 2026-04-29
**Versão em Produção**: WF02 V114
**Status**: ✅ COMPLETO - Processo validado em 114+ deployments
