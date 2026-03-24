# Resumo das Correções Aplicadas - 2026-03-13

## 1. Workflow V2.1 - Appointment Scheduler ✅

### Problemas Identificados no V2.0
1. **Status `erro_calendario` não existia no banco** → Workflow falharia ao processar erros do Google Calendar
2. **`POSTGRES_CREDENTIAL_ID` não configurado** → Nodes PostgreSQL não conectariam
3. **Sintaxe incorreta no `onlyIf`** → Nodes condicionais não executariam

### Solução Aplicada

#### A. Migração de Banco de Dados
**Arquivo**: `database/migrations/001_add_erro_calendario_status.sql`

```sql
-- Adiciona status 'erro_calendario' à constraint
ALTER TABLE appointments DROP CONSTRAINT IF EXISTS valid_status;
ALTER TABLE appointments ADD CONSTRAINT valid_status
CHECK (status IN (
    'agendado', 'confirmado', 'em_andamento', 'realizado',
    'cancelado', 'reagendado', 'no_show', 'erro_calendario'
));

-- Índice para performance
CREATE INDEX IF NOT EXISTS idx_appointments_error_status
ON appointments(status)
WHERE status = 'erro_calendario';
```

**Execução**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -f /tmp/001_add_erro_calendario_status.sql
```

**Schema atualizado**: `database/schema.sql` (linha 155-157)

#### B. Workflow V2.1 Gerado
**Arquivo**: `n8n/workflows/05_appointment_scheduler_v2.1.json`

**Correções aplicadas**:
1. ✅ Hardcoded credential ID nos 3 nodes PostgreSQL: `"id": "1"`
2. ✅ Sintaxe corrigida em 3 nodes condicionais: `"onlyIf": "{{ $json.calendar_success === true }}"`
3. ✅ Versão atualizada para "2.1"

**Validação**:
- JSON válido ✅
- 11 nodes, 10 connections ✅
- Todos os nodes PostgreSQL com credential ID correto ✅
- Todos os nodes condicionais com sintaxe correta ✅

---

## 2. Docker Evolution API - Healthcheck Fix ✅

### Problema Identificado
**Container `e2bot-evolution-dev` unhealthy** por 5+ horas

**Causa Raiz**:
- Healthcheck command: `wget --spider -q http://localhost:8080`
- Tempo de execução: **10.01s** (medido com `time`)
- Timeout configurado: **10s**
- Resultado: Healthcheck **sempre falhava** por 0.01s de diferença

### Solução Aplicada

**Arquivo**: `docker/docker-compose-dev.yml` (linha 217)

```yaml
# ANTES
timeout: 10s

# DEPOIS
timeout: 15s
```

**Passos de Aplicação**:
1. Editado `docker-compose-dev.yml` (timeout 10s → 15s)
2. Removido container antigo: `docker rm e2bot-evolution-dev`
3. Recriado container: `docker-compose -f docker-compose-dev.yml up -d evolution-api`
4. Aguardado 70s (start_period 60s + margem)

**Resultado**:
```
e2bot-evolution-dev   Up About a minute (healthy) ✅
```

**Status Final**: Container **healthy** e operacional!

---

## Próximos Passos

### 1. Importar Workflow V2.1 no n8n
```bash
# Acessar: http://localhost:5678
# Importar: n8n/workflows/05_appointment_scheduler_v2.1.json
# Verificar: Credenciais PostgreSQL (ID "1") e Google Calendar OAuth2
```

### 2. Testar Workflow V2.1
- Criar agendamento de teste
- Verificar criação de evento no Google Calendar
- Confirmar atualização do status no banco
- Validar execução dos nodes condicionais

### 3. Monitorar Evolution API
- Container healthy após correção do healthcheck
- Webhook 404 errors precisam investigação futura (não crítico)
- Monitorar logs: `docker logs -f e2bot-evolution-dev`

---

## Arquivos Modificados/Criados

### Criados
- ✅ `database/migrations/001_add_erro_calendario_status.sql`
- ✅ `scripts/generate-appointment-scheduler-v2.1.py`
- ✅ `n8n/workflows/05_appointment_scheduler_v2.1.json`
- ✅ `docs/PLAN_APPOINTMENT_SCHEDULER_REFACTOR_V2_1.md`
- ✅ `docs/PLAN_SUMMARY.md` (este documento)

### Modificados
- ✅ `database/schema.sql` (linha 155-157: adicionado `erro_calendario`)
- ✅ `docker/docker-compose-dev.yml` (linha 217: timeout 10s → 15s)

---

**Status Geral**: ✅ **Todas as correções aplicadas com sucesso!**

**Data**: 2026-03-13
**Responsável**: Claude Code + Bruno
