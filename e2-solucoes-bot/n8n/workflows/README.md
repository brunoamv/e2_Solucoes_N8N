# E2 Bot - Workflows n8n

> **Organização**: Produção + Ready-to-Deploy | Histórico em `/old`
> **Última Atualização**: 2026-04-08

---

## 📋 Workflows de Produção

### WF01: WhatsApp Handler
- **Arquivo**: `01_main_whatsapp_handler_V2.8.3_NO_LOOP.json`
- **Versão**: V2.8.3
- **Status**: ✅ **PRODUÇÃO ESTÁVEL**
- **Função**: Recebe mensagens WhatsApp, faz deduplicação via PostgreSQL
- **Deploy**: Ativo desde Mar 10

### WF02: AI Agent
- **Produção**: `02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json`
- **Versão**: V74.1.2
- **Status**: ✅ **PRODUÇÃO ESTÁVEL**
- **Função**: Conversação IA com 10 estados (reactive UX)
- **Deploy**: Ativo desde Mar 30

### WF05: Appointment Scheduler
- **Produção**: `05_appointment_scheduler_v3.6.json`
- **Versão**: V3.6
- **Status**: ✅ **PRODUÇÃO ESTÁVEL**
- **Função**: Agendamento Google Calendar (sem validação)
- **Deploy**: Ativo desde Mar 24

---

## 🚀 Workflows Ready for Production

### WF02: AI Agent V76
- **Arquivo**: `02_ai_agent_conversation_V76_PROACTIVE_UX.json`
- **Versão**: V76
- **Status**: 🚀 **READY FOR PRODUCTION**
- **Mudança**: UX proativa com seleção de data/horário (12 estados)
- **Deploy**: Aguardando deploy (Apr 6)
- **Docs**: `/docs/implementation/WF02_V76_IMPLEMENTATION_GUIDE.md`

### WF05: Appointment Scheduler V7
- **Arquivo**: `05_appointment_scheduler_v7_hardcoded_values.json`
- **Versão**: V7
- **Status**: 🚀 **READY FOR PRODUCTION**
- **Mudança**: Validação de horário comercial (hardcoded 08:00-18:00)
- **Deploy**: Aguardando deploy (Mar 31)
- **Docs**: `/docs/deployment/DEPLOY_WF05_V7_HARDCODED_FINAL.md`

### WF06: Calendar Availability Service
- **Arquivo**: `06_calendar_availability_service_v1.json`
- **Versão**: V1
- **Status**: 🚀 **READY FOR PRODUCTION**
- **Função**: Microservice de disponibilidade para WF02 V76
- **Deploy**: Aguardando deploy (Apr 6)
- **Docs**: `/docs/implementation/WF06_CALENDAR_AVAILABILITY_SERVICE.md`

### WF07: Email Sender V13
- **Arquivo**: `07_send_email_v13_insert_select.json`
- **Versão**: V13
- **Status**: 🚀 **READY FOR PRODUCTION**
- **Mudança**: INSERT...SELECT pattern (solução definitiva)
- **Deploy**: Aguardando deploy (Apr 1)
- **Docs**: `/docs/fix/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md`

---

## 📁 Organização

### `/n8n/workflows/` (Raiz)
**7 workflows ativos**:
- 1 WF em produção estável (WF01)
- 2 WFs em produção estável (WF02 V74, WF05 V3.6)
- 4 WFs ready-for-production (WF02 V76, WF05 V7, WF06, WF07 V13)

### `/n8n/workflows/old/`
**57 workflows obsoletos**:
- WF02: V68 a V75 (17 versões)
- WF03-WF04: Workflows não utilizados (2 arquivos)
- WF05: V2 a V6 (16 versões)
- WF06: Appointment reminders antigo (1 arquivo)
- WF07: V2 a V12 (18 versões)
- WF08-WF13: Workflows descontinuados (6 arquivos)
- Test workflows (3 arquivos)

---

## 🔄 Processo de Deploy

### Canary Deployment (Recomendado para WF02 V76)
```bash
# 1. Deploy V76 (inativo)
# 2. Teste E2E
bash scripts/test-wf02-v76-e2e.sh

# 3. Canary gradual
# - 20% tráfego → Monitor 24h
# - 50% tráfego → Monitor 24h
# - 80% tráfego → Monitor 24h
# - 100% tráfego → Desativar V74

# 4. Mover V74 para old/
mv 02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json old/
```

### Blue-Green Deployment (Outros Workflows)
```bash
# 1. Import novo workflow (inativo)
# 2. Configurar credenciais
# 3. Teste completo
# 4. Desativar versão antiga
# 5. Ativar nova versão
# 6. Monitor 1h
# 7. Mover versão antiga para old/
```

---

## 📊 Histórico de Evolução

### WF02 (AI Agent)
- **V68-V69**: Correções de sintaxe e conexões (Mar 11)
- **V70-V72**: Appointment integration (Mar 18)
- **V73**: SQL + State Machine fixes (Mar 24)
- **V74**: Appointment confirmation (Mar 24-30) ✅ **PROD**
- **V75**: Final message personalization (Mar 30)
- **V76**: Proactive UX (Apr 6) 🚀 **READY**

### WF05 (Appointment Scheduler)
- **V2-V3.6**: Iterações de funcionalidade (Mar 13-24) ✅ **PROD**
- **V4**: Integration enhancements (Mar 30)
- **V5-V6**: Environment variable attempts (Mar 31)
- **V7**: Hardcoded values (Mar 31) 🚀 **READY**

### WF07 (Email Sender)
- **V2-V6**: Template access attempts (Mar 26-31)
- **V8-V9**: HTTP Request solution (Mar 31-Apr 1)
- **V10-V12**: Format + Database fixes (Apr 1)
- **V13**: INSERT...SELECT pattern (Apr 1) 🚀 **READY**

---

## 🔧 Manutenção

### Limpeza de Histórico
Recomendação: Manter apenas últimas 3 versões de cada workflow em `old/`

```bash
# Exemplo: Limpar versões V68-V72 do WF02 (manter apenas V73-V75)
cd old/
rm 02_ai_agent_conversation_V68*.json
rm 02_ai_agent_conversation_V69*.json
rm 02_ai_agent_conversation_V70*.json
rm 02_ai_agent_conversation_V71*.json
rm 02_ai_agent_conversation_V72*.json
```

### Backup
Recomendação: Backup completo antes de deploy em produção

```bash
# Backup de workflows ativos
tar -czf workflows_backup_$(date +%Y%m%d).tar.gz *.json

# Backup incluindo histórico
tar -czf workflows_full_backup_$(date +%Y%m%d).tar.gz *.json old/
```

---

## 📚 Documentação Relacionada

- **Setup**: `/docs/Setups/QUICKSTART.md`
- **CLAUDE.md**: `/CLAUDE.md` (contexto completo)
- **Deployment Guides**: `/docs/deployment/`
- **Bugfix History**: `/docs/fix/`
- **Implementation Guides**: `/docs/implementation/`

---

**Projeto**: E2 Soluções WhatsApp Bot
**Stack**: n8n 2.14.2 + Claude 3.5 + PostgreSQL + Evolution API
**Mantido por**: E2 Dev Team
