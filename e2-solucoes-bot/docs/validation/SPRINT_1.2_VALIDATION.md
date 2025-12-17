# Guia de Validação - Sprint 1.2

> **Sprint**: 1.2 - Sistema de Agendamento Completo
> **Status**: 📋 AGUARDANDO VALIDAÇÃO
> **Pré-requisito**: Sprint 1.1 validado
> **Validadores**: Time Comercial + Técnico

---

## 📋 Checklist de Validação Sprint 1.2

Este guia fornece os passos completos para validar o sistema de agendamento implementado no Sprint 1.2.

---

## ✅ Pré-Requisitos

Antes de iniciar a validação, verifique:

- [ ] Sprint 1.1 (RAG) está validado e funcional
- [ ] Todos workflows n8n estão importados e ativos
- [ ] Google Calendar API está configurada
- [ ] Templates de email estão disponíveis em `templates/emails/`
- [ ] Funções SQL de appointments foram executadas no Supabase
- [ ] Ambiente de testes está operacional

---

## 🎯 Objetivos da Validação

Validar que o sistema de agendamento está funcionando corretamente em todos os aspectos:

1. ✅ Integração Google Calendar funcional
2. ✅ Verificação de disponibilidade e conflitos
3. ✅ Criação de agendamentos via bot
4. ✅ Envio de lembretes 24h e 2h antes
5. ✅ Follow-up pós-visita
6. ✅ Sincronização com RD Station
7. ✅ Templates de email corretos

---

## 🧪 Testes Funcionais

### 1. Teste de Agendamento Básico

**Objetivo**: Verificar que o bot consegue agendar uma visita técnica

**Passos**:

1. Inicie conversa com bot via WhatsApp
2. Complete coleta de dados do lead
3. Solicite agendamento de visita
4. Escolha data e horário disponível
5. Confirme agendamento

**Verificações**:

- [ ] Bot apresenta slots disponíveis
- [ ] Bot não apresenta horários conflitantes
- [ ] Agendamento é salvo na tabela `appointments`
- [ ] Status inicial é `scheduled`
- [ ] Evento é criado no Google Calendar
- [ ] `google_calendar_event_id` é salvo no banco
- [ ] Lead recebe confirmação via WhatsApp
- [ ] Email de confirmação é enviado

**SQL para verificação**:
```sql
-- Verificar último agendamento criado
SELECT * FROM appointments
ORDER BY created_at DESC
LIMIT 1;

-- Verificar detalhes completos com lead
SELECT * FROM get_appointment_details('[appointment_id]');
```

**Evidências**: Screenshot WhatsApp + Print Google Calendar + Query SQL

---

### 2. Teste de Verificação de Disponibilidade

**Objetivo**: Garantir que o sistema não permite agendamentos conflitantes

**Passos**:

1. Crie um agendamento para data/hora específica
2. Tente agendar outro compromisso no mesmo horário
3. Verifique se sistema bloqueia conflito

**Verificações**:

- [ ] Sistema detecta conflito de horário
- [ ] Apresenta apenas slots disponíveis
- [ ] Função `get_available_slots()` funciona corretamente
- [ ] Resposta do bot informa horários alternativos

**SQL para teste**:
```sql
-- Verificar slots disponíveis para uma data
SELECT * FROM get_available_slots('2025-12-20', NULL, 120);

-- Verificar com técnico específico
SELECT * FROM get_available_slots('2025-12-20', 'João Silva', 120);
```

**Evidências**: Query SQL mostrando conflitos detectados

---

### 3. Teste de Lembretes Automatizados

**Objetivo**: Validar envio de lembretes 24h e 2h antes da visita

**Configuração**:

1. Crie agendamento para teste (próximas 24-25 horas)
2. Configure workflow 06 para executar a cada 30 minutos
3. Monitore execução do workflow

**Verificações - Lembrete 24h**:

- [ ] Workflow identifica agendamentos próximos (24h)
- [ ] Email de lembrete 24h é enviado
- [ ] WhatsApp de lembrete 24h é enviado
- [ ] Flag `reminder_24h_sent` é atualizada para `true`
- [ ] Timestamp `reminder_24h_sent_at` é registrado
- [ ] Template `lembrete_24h.html` está correto

**SQL para verificação**:
```sql
-- Listar agendamentos que precisam lembrete 24h
SELECT * FROM get_appointments_needing_24h_reminder();

-- Verificar se lembrete foi enviado
SELECT reminder_24h_sent, reminder_24h_sent_at
FROM appointments
WHERE id = '[appointment_id]';
```

**Verificações - Lembrete 2h**:

- [ ] Workflow identifica agendamentos urgentes (2h)
- [ ] Email de lembrete 2h é enviado
- [ ] WhatsApp de lembrete 2h é enviado
- [ ] Flag `reminder_2h_sent` é atualizada para `true`
- [ ] Timestamp `reminder_2h_sent_at` é registrado
- [ ] Template `lembrete_2h.html` está correto

**SQL para verificação**:
```sql
-- Listar agendamentos que precisam lembrete 2h
SELECT * FROM get_appointments_needing_2h_reminder();

-- Marcar lembrete como enviado (manual para teste)
SELECT mark_reminder_sent('[appointment_id]', '24h');
SELECT mark_reminder_sent('[appointment_id]', '2h');
```

**Evidências**: Emails recebidos + Print workflow n8n + Query SQL

---

### 4. Teste de Follow-up Pós-Visita

**Objetivo**: Validar envio de follow-up após conclusão da visita

**Passos**:

1. Marque um agendamento como `completed`
2. Execute workflow de follow-up
3. Verifique envio de email

**Verificações**:

- [ ] Status do agendamento atualizado para `completed`
- [ ] `completed_at` timestamp é registrado
- [ ] Email pós-visita é enviado
- [ ] WhatsApp de agradecimento é enviado
- [ ] Flag `post_visit_sent` é atualizada para `true`
- [ ] Template `apos_visita.html` está correto
- [ ] Links de feedback e proposta funcionam

**SQL para teste**:
```sql
-- Atualizar status para completed (simulação)
SELECT update_appointment_status('[appointment_id]', 'completed', 'Visita realizada com sucesso');

-- Listar agendamentos que precisam follow-up
SELECT * FROM get_appointments_for_post_visit_followup();

-- Verificar se follow-up foi enviado
SELECT post_visit_sent, post_visit_sent_at
FROM appointments
WHERE id = '[appointment_id]';
```

**Evidências**: Email recebido + Query SQL

---

### 5. Teste de Sincronização RD Station

**Objetivo**: Garantir que agendamentos são sincronizados com CRM

**Passos**:

1. Crie novo agendamento via bot
2. Verifique sincronização no RD Station
3. Altere status do agendamento
4. Verifique atualização no CRM

**Verificações**:

- [ ] Contact é criado/atualizado no RD Station
- [ ] Deal é criado com informações corretas
- [ ] Campo customizado de agendamento é preenchido
- [ ] Atividade de agendamento é criada
- [ ] Movimentação entre etapas funciona
- [ ] Log de sincronização registrado em `rdstation_sync_log`

**Campos RD Station a verificar**:
- Nome completo do cliente
- Email e telefone
- Endereço completo
- Serviço solicitado
- Data e horário agendado
- Status do agendamento
- Link Google Calendar

**Evidências**: Screenshots RD Station + Query sync_log

---

### 6. Teste de Templates de Email

**Objetivo**: Validar todos os 5 templates de email

**Templates a validar**:

1. **`novo_lead.html`** - Notificação interna
   - [ ] Recebido pela equipe comercial
   - [ ] Todas variáveis substituídas corretamente
   - [ ] Links de ação funcionam (RD Station, WhatsApp, Calendar)
   - [ ] Design responsivo em mobile

2. **`confirmacao_agendamento.html`** - Confirmação cliente
   - [ ] Recebido pelo cliente
   - [ ] Dados do agendamento corretos
   - [ ] Botão "Adicionar ao Calendário" funciona
   - [ ] Informações de contato corretas

3. **`lembrete_24h.html`** - Lembrete 24 horas
   - [ ] Recebido 24h antes
   - [ ] Checklist de preparação visível
   - [ ] Botões de confirmação/reagendamento funcionam
   - [ ] Design urgente (azul) aplicado

4. **`lembrete_2h.html`** - Lembrete urgente 2 horas
   - [ ] Recebido 2h antes
   - [ ] Telefone técnico visível
   - [ ] Botão mapa/localização funciona
   - [ ] Design urgente (vermelho) aplicado

5. **`apos_visita.html`** - Follow-up pós-visita
   - [ ] Recebido após conclusão
   - [ ] Links de feedback funcionam
   - [ ] Link para proposta funciona
   - [ ] Design positivo (verde) aplicado

**Variáveis a verificar em todos templates**:
- {{CUSTOMER_NAME}}
- {{APPOINTMENT_DATE}}
- {{APPOINTMENT_TIME}}
- {{SERVICE_NAME}}
- {{ADDRESS}}, {{CITY}}, {{STATE}}
- {{COMPANY_PHONE}}, {{COMPANY_EMAIL}}
- {{TECHNICIAN_NAME}}, {{TECHNICIAN_PHONE}}

**Evidências**: Screenshots de cada email em desktop e mobile

---

### 7. Teste de Reagendamento

**Objetivo**: Validar fluxo de reagendamento de visitas

**Passos**:

1. Cliente solicita reagendamento via WhatsApp
2. Bot apresenta novos horários disponíveis
3. Cliente escolhe novo horário
4. Sistema atualiza agendamento

**Verificações**:

- [ ] Agendamento original marcado como `rescheduled`
- [ ] Novo agendamento criado com status `scheduled`
- [ ] Evento antigo no Google Calendar é cancelado
- [ ] Novo evento é criado no Google Calendar
- [ ] Cliente recebe confirmação do novo horário
- [ ] RD Station é atualizado com mudança
- [ ] Histórico de mudanças preservado

**SQL para verificação**:
```sql
-- Ver histórico de status do agendamento
SELECT id, lead_id, scheduled_date, status, created_at, updated_at
FROM appointments
WHERE lead_id = '[lead_id]'
ORDER BY created_at DESC;
```

**Evidências**: Logs de mudança + Screenshots

---

### 8. Teste de Cancelamento

**Objetivo**: Validar cancelamento de agendamentos

**Passos**:

1. Cliente solicita cancelamento
2. Bot confirma cancelamento
3. Sistema atualiza registros

**Verificações**:

- [ ] Status atualizado para `cancelled`
- [ ] `cancelled_at` timestamp registrado
- [ ] Evento removido do Google Calendar
- [ ] RD Station atualizado
- [ ] Cliente recebe confirmação
- [ ] Slot fica disponível novamente

**SQL para teste**:
```sql
-- Cancelar agendamento
SELECT update_appointment_status('[appointment_id]', 'cancelled', 'Cancelado pelo cliente');

-- Verificar disponibilidade após cancelamento
SELECT * FROM get_available_slots('2025-12-20', NULL, 120);
```

**Evidências**: Confirmação de cancelamento + Query SQL

---

## 📊 Testes de Carga e Performance

### 9. Teste de Múltiplos Agendamentos

**Objetivo**: Validar sistema com múltiplos agendamentos simultâneos

**Passos**:

1. Crie 10+ agendamentos para diferentes datas
2. Execute workflow de lembretes
3. Monitore performance

**Verificações**:

- [ ] Sistema processa todos agendamentos
- [ ] Não há conflitos de horário
- [ ] Lembretes são enviados corretamente
- [ ] Performance do banco de dados adequada (<500ms)
- [ ] Workflows n8n executam sem erros

**SQL para teste de carga**:
```sql
-- Ver próximos agendamentos (30 dias)
SELECT * FROM get_upcoming_appointments(720); -- 30 dias = 720 horas

-- Estatísticas de agendamentos
SELECT * FROM get_appointment_statistics(
    CURRENT_DATE - INTERVAL '30 days',
    CURRENT_DATE + INTERVAL '30 days'
);
```

**Evidências**: Métricas de performance + Logs n8n

---

## 🔍 Testes de Segurança e Dados

### 10. Teste de Validação de Dados

**Objetivo**: Garantir integridade de dados

**Verificações**:

- [ ] Não é possível agendar em horários fora do expediente
- [ ] Não é possível agendar em datas passadas
- [ ] Campos obrigatórios são validados
- [ ] Formato de email validado
- [ ] Formato de telefone validado
- [ ] Endereço completo obrigatório

**SQL para validação**:
```sql
-- Verificar constraints da tabela
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'appointments';

-- Verificar índices
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'appointments';
```

---

## 📈 Métricas de Sucesso

Para considerar o Sprint 1.2 validado, os seguintes critérios devem ser atendidos:

### Critérios Obrigatórios

- [ ] **100%** dos agendamentos são criados no Google Calendar
- [ ] **100%** dos lembretes 24h são enviados no prazo
- [ ] **100%** dos lembretes 2h são enviados no prazo
- [ ] **100%** dos agendamentos sincronizam com RD Station
- [ ] **0** conflitos de horário não detectados
- [ ] **< 500ms** tempo de consulta disponibilidade
- [ ] **< 2 segundos** tempo de criação de agendamento

### Critérios Desejáveis

- [ ] **> 95%** taxa de entrega de emails
- [ ] **> 90%** taxa de abertura emails lembretes
- [ ] **< 1 segundo** tempo de resposta bot
- [ ] **0** erros em workflows n8n
- [ ] **100%** templates renderizando corretamente

---

## 🐛 Troubleshooting

### Problemas Comuns

**1. Lembretes não são enviados**

Verificações:
```sql
-- Verificar agendamentos elegíveis
SELECT * FROM get_appointments_needing_24h_reminder();
SELECT * FROM get_appointments_needing_2h_reminder();

-- Verificar flags de envio
SELECT id, reminder_24h_sent, reminder_2h_sent, scheduled_date, scheduled_time_start
FROM appointments
WHERE status = 'scheduled'
AND scheduled_date >= CURRENT_DATE;
```

Soluções:
- Verificar se workflow 06 está ativo
- Verificar credenciais SMTP
- Checar logs n8n para erros

**2. Google Calendar não sincroniza**

Verificações:
- Service Account configurado corretamente
- Permissões de calendário concedidas
- `google_calendar_event_id` salvo no banco

Soluções:
- Reautorizar Google Calendar API
- Verificar escopo de permissões
- Testar credenciais manualmente

**3. RD Station não atualiza**

Verificações:
```sql
SELECT * FROM rdstation_sync_log
WHERE entity_type = 'appointment'
ORDER BY synced_at DESC
LIMIT 10;
```

Soluções:
- Renovar OAuth2 tokens
- Verificar campos customizados no CRM
- Checar mapeamento de campos

---

## ✅ Checklist Final de Validação

Antes de aprovar o Sprint 1.2, certifique-se de que:

### Funcionalidades Core
- [ ] Agendamento básico funciona end-to-end
- [ ] Verificação de disponibilidade impede conflitos
- [ ] Lembretes 24h enviados corretamente
- [ ] Lembretes 2h enviados corretamente
- [ ] Follow-up pós-visita enviado
- [ ] Reagendamento funciona corretamente
- [ ] Cancelamento funciona corretamente

### Integrações
- [ ] Google Calendar sincroniza 100%
- [ ] RD Station sincroniza 100%
- [ ] Emails são entregues (todas templates)
- [ ] WhatsApp notifica corretamente

### Qualidade
- [ ] Todos templates de email renderizam bem
- [ ] Performance adequada (<500ms queries)
- [ ] Sem erros em logs n8n
- [ ] Dados seguros e validados

### Documentação
- [ ] Guia de validação completo
- [ ] Evidências coletadas
- [ ] Problemas documentados
- [ ] Melhorias identificadas

---

## 📝 Template de Relatório de Validação

```markdown
# Relatório de Validação - Sprint 1.2

**Data**: [Data da validação]
**Validador**: [Nome]
**Ambiente**: [dev/staging/prod]

## Resumo Executivo

- [ ] Sprint 1.2 APROVADO
- [ ] Sprint 1.2 APROVADO COM RESSALVAS
- [ ] Sprint 1.2 NÃO APROVADO

## Testes Executados

| Teste | Status | Evidência | Observações |
|-------|--------|-----------|-------------|
| Agendamento Básico | ✅/❌ | Link | - |
| Verificação Disponibilidade | ✅/❌ | Link | - |
| Lembretes 24h | ✅/❌ | Link | - |
| Lembretes 2h | ✅/❌ | Link | - |
| Follow-up Pós-Visita | ✅/❌ | Link | - |
| Sincronização RD Station | ✅/❌ | Link | - |
| Templates Email | ✅/❌ | Link | - |
| Reagendamento | ✅/❌ | Link | - |
| Cancelamento | ✅/❌ | Link | - |
| Performance | ✅/❌ | Link | - |

## Problemas Encontrados

1. **[Título do problema]**
   - Severidade: Alta/Média/Baixa
   - Descrição: [Detalhes]
   - Impacto: [Impacto no sistema]
   - Solução proposta: [Como resolver]

## Melhorias Sugeridas

1. [Melhoria 1]
2. [Melhoria 2]

## Conclusão

[Texto conclusivo sobre a validação]

**Assinatura**: _______________________
```

---

## 🎯 Próximos Passos Após Validação

### Se Aprovado ✅

1. Atualizar `SPRINT_1.2_PLANNING.md` com status "VALIDADO"
2. Documentar lições aprendidas
3. Preparar deploy em produção
4. Criar documentação de operação
5. Treinar equipe comercial

### Se Aprovado com Ressalvas ⚠️

1. Documentar ressalvas e prazos
2. Criar issues para correções
3. Agendar revalidação
4. Comunicar stakeholders

### Se Não Aprovado ❌

1. Documentar todos problemas encontrados
2. Priorizar correções críticas
3. Criar plano de ação
4. Agendar nova validação
5. Revisar processo de desenvolvimento

---

*Guia de Validação - Sprint 1.2*
*E2 Soluções - Energia e Elétrica com Inteligência Artificial*
*Versão 1.0 - 15/12/2025*
