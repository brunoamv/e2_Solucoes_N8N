# Setup RD Station CRM Integration

## Visão Geral

Guia completo para configurar a integração do bot E2 Soluções com RD Station CRM, incluindo criação de campos customizados, pipeline, webhooks e autenticação OAuth2.

## Pré-requisitos

- Conta RD Station CRM (planos Basic, Pro ou Advanced)
- Acesso administrativo ao CRM
- Acesso ao RD Station App Store
- Credenciais do bot configuradas

## Etapa 1: Criar Aplicação OAuth2

### 1.1. Acessar RD Station App Store

1. Acesse: https://appstore.rdstation.com/
2. Faça login com sua conta RD Station
3. Clique em **"Criar Aplicação"**

### 1.2. Configurar Aplicação

Preencha os dados:

```yaml
Nome da Aplicação: E2 Soluções WhatsApp Bot
Descrição: Bot de atendimento automatizado via WhatsApp
Redirect URIs:
  - http://localhost:5678/oauth/callback  # DEV
  - https://n8n.seudominio.com.br/oauth/callback  # PROD
Scopes necessários:
  - crm.contacts.read
  - crm.contacts.write
  - crm.deals.read
  - crm.deals.write
  - crm.tasks.read
  - crm.tasks.write
  - crm.notes.write
```

### 1.3. Obter Credenciais

Após criar a aplicação, anote:
- **Client ID**: `xxxxxxxxxxxxxxxxxxxx`
- **Client Secret**: `yyyyyyyyyyyyyyyyyyyy`

Guarde essas credenciais com segurança!

## Etapa 2: Obter Refresh Token

### 2.1. URL de Autorização

Monte a URL de autorização:

```
https://api.rd.services/auth/dialog?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}
```

Substitua:
- `{CLIENT_ID}`: Seu Client ID
- `{REDIRECT_URI}`: http://localhost:5678/oauth/callback (URL encoded)

### 2.2. Autorizar Aplicação

1. Acesse a URL montada no navegador
2. Faça login no RD Station se necessário
3. Clique em **"Autorizar"**
4. Você será redirecionado para `{REDIRECT_URI}?code=CODIGO_TEMPORARIO`

### 2.3. Trocar Code por Tokens

Use o código recebido para obter o refresh token:

```bash
curl -X POST https://api.rd.services/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "SEU_CLIENT_ID",
    "client_secret": "SEU_CLIENT_SECRET",
    "code": "CODIGO_RECEBIDO"
  }'
```

**Resposta:**
```json
{
  "access_token": "...",
  "refresh_token": "ESTE_É_O_QUE_VOCÊ_PRECISA",
  "expires_in": 86400
}
```

**IMPORTANTE:** Anote o `refresh_token`. É ele que você usará no `.env`.

## Etapa 3: Configurar Campos Customizados

### 3.1. Campos em Contatos

Acesse: **RD Station CRM → Configurações → Campos Personalizados → Contatos**

Criar os seguintes campos:

| Nome do Campo | Tipo | API Name | Obrigatório |
|---------------|------|----------|-------------|
| Endereço Completo | Texto Longo | cf_endereco | Não |
| Cidade | Texto | cf_cidade | Não |
| Estado | Texto | cf_estado | Não |
| CEP | Texto | cf_cep | Não |
| Segmento | Lista | cf_segmento | Não |
| Origem | Texto | cf_origem | Não |

**Valores da Lista - Segmento:**
- Residencial
- Comercial
- Industrial
- Agronegócio

### 3.2. Campos em Negociações

Acesse: **RD Station CRM → Configurações → Campos Personalizados → Negociações**

| Nome do Campo | Tipo | API Name | Descrição |
|---------------|------|----------|-----------|
| Tipo de Serviço | Lista | cf_servico | Solar, Subestação, etc. |
| Subtipo de Serviço | Texto | cf_servico_subtipo | Detalhes específicos |
| Segmento | Lista | cf_segmento | Residencial, Comercial, etc. |
| Consumo kWh/mês | Número | cf_consumo_kwh | Consumo médio |
| Potência kWp | Número Decimal | cf_potencia_kwp | Potência sistema solar |
| Tensão Subestação | Texto | cf_tensao | Ex: 13.8kV |
| Tipo de Análise | Lista | cf_tipo_analise | Consumo, Qualidade, Perícia |
| Possui Solar | Checkbox | cf_possui_solar | Para BESS |
| Análise IA | Texto Longo | cf_analise_ia | Análise Claude Vision |
| Fotos (Drive) | URL | cf_fotos_drive | Link Google Drive |
| Preferência Dias | Texto | cf_preferencia_dias | Seg, Ter, Qua... |
| Preferência Turno | Lista | cf_preferencia_turno | Manhã, Tarde |
| Observações Acesso | Texto | cf_observacoes_acesso | Portaria, interfone |

**Valores da Lista - Tipo de Serviço:**
- Energia Solar
- Subestação
- Projeto Elétrico
- Armazenamento de Energia (BESS)
- Análise e Laudo

**Valores da Lista - Tipo de Análise:**
- Análise de Consumo
- Análise de Qualidade
- Laudo para Perícia

**Valores da Lista - Preferência Turno:**
- Manhã (8h-12h)
- Tarde (13h-18h)

## Etapa 4: Configurar Pipeline

### 4.1. Criar Pipeline

Acesse: **RD Station CRM → Funil de Vendas → Criar Funil**

```yaml
Nome do Funil: Bot WhatsApp E2 Soluções
Descrição: Leads gerados e qualificados pelo bot de WhatsApp

Etapas:
  1. Novo Lead
     Ordem: 1
     Cor: Cinza
     Descrição: Lead recém-captado pelo bot, conversa iniciada

  2. Qualificando
     Ordem: 2
     Cor: Amarelo
     Descrição: Bot está coletando informações do lead

  3. Agendado
     Ordem: 3
     Cor: Azul
     Descrição: Visita técnica agendada, aguardando

  4. Proposta
     Ordem: 4
     Cor: Laranja
     Descrição: Proposta comercial enviada, aguardando aprovação

  5. Negociação
     Ordem: 5
     Cor: Roxo
     Descrição: Em negociação com cliente sobre valores/condições

  6. Ganho
     Ordem: 6
     Cor: Verde
     Descrição: Venda fechada, projeto aprovado

  7. Perdido
     Ordem: 7
     Cor: Vermelho
     Descrição: Não fechou negócio (registrar motivo)
```

### 4.2. Anotar IDs do Pipeline

Após criar, obtenha os IDs via API ou pelo console do navegador:

**API Request:**
```bash
curl -X GET "https://crm.rdstation.com/api/v1/deal_pipelines" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN"
```

**Anote:**
- `PIPELINE_ID`: ID do pipeline criado
- `STAGE_NOVO_LEAD`: ID da etapa "Novo Lead"
- `STAGE_QUALIFICANDO`: ID da etapa "Qualificando"
- `STAGE_AGENDADO`: ID da etapa "Agendado"
- `STAGE_PROPOSTA`: ID da etapa "Proposta"
- `STAGE_GANHO`: ID da etapa "Ganho"
- `STAGE_PERDIDO`: ID da etapa "Perdido"

## Etapa 5: Criar Fonte de Negociação

Para identificar leads do bot:

Acesse: **RD Station CRM → Configurações → Fontes de Negociação**

Criar fonte:
```yaml
Nome: Bot WhatsApp
Descrição: Leads qualificados pelo bot de WhatsApp
```

Anotar o `SOURCE_BOT` ID.

## Etapa 6: Configurar Usuário Técnico

Criar ou identificar usuário que será responsável pelas tarefas de visita técnica:

Acesse: **RD Station CRM → Configurações → Usuários**

Anotar o `USER_TECNICO` ID do usuário responsável.

## Etapa 7: Configurar Variáveis de Ambiente

Edite `docker/.env.dev` com os valores obtidos:

```bash
# --- RD Station CRM ---
RDSTATION_CLIENT_ID=seu_client_id_aqui
RDSTATION_CLIENT_SECRET=seu_client_secret_aqui
RDSTATION_REFRESH_TOKEN=seu_refresh_token_aqui

RDSTATION_API_URL=https://crm.rdstation.com/api/v1

# IDs do Pipeline
RDSTATION_PIPELINE_ID=id_do_pipeline
RDSTATION_STAGE_NOVO_LEAD=id_etapa_novo_lead
RDSTATION_STAGE_QUALIFICANDO=id_etapa_qualificando
RDSTATION_STAGE_AGENDADO=id_etapa_agendado
RDSTATION_STAGE_PROPOSTA=id_etapa_proposta
RDSTATION_STAGE_GANHO=id_etapa_ganho
RDSTATION_STAGE_PERDIDO=id_etapa_perdido

# Fonte e Usuário
RDSTATION_SOURCE_BOT=id_fonte_bot_whatsapp
RDSTATION_USER_TECNICO=id_usuario_tecnico

# Webhook Secret (gere um aleatório)
RDSTATION_WEBHOOK_SECRET=$(openssl rand -hex 32)
```

## Etapa 8: Testar Integração

### 8.1. Teste de Autenticação

Acesse n8n e teste a credencial RD Station:

```bash
# Acesse http://localhost:5678
# Credentials → Add Credential → RD Station CRM API
# Cole Client ID, Client Secret e Refresh Token
# Clique em "Connect"
```

Se conectar com sucesso, a credencial está configurada!

### 8.2. Teste de Criação de Contato

Via workflow n8n ou API direta:

```bash
curl -X POST "https://crm.rdstation.com/api/v1/contacts" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Teste Bot",
    "emails": [{"email": "joao.teste@example.com"}],
    "phones": [{"phone": "62999999999"}],
    "custom_fields": {
      "cf_origem": "Bot WhatsApp - Teste"
    }
  }'
```

### 8.3. Teste de Criação de Negociação

```bash
curl -X POST "https://crm.rdstation.com/api/v1/deals" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Teste Bot - Energia Solar",
    "contact_id": "ID_DO_CONTATO_CRIADO",
    "deal_stage_id": "$RDSTATION_STAGE_NOVO_LEAD",
    "deal_source_id": "$RDSTATION_SOURCE_BOT",
    "custom_fields": {
      "cf_servico": "Energia Solar",
      "cf_segmento": "Residencial"
    }
  }'
```

## Etapa 9: Configurar Webhooks (Opcional)

Para sincronização bidirecional (mudanças no CRM refletem no bot):

### 9.1. Criar Webhook no RD Station

Acesse: **RD Station CRM → Configurações → Webhooks**

```yaml
URL: https://n8n.seudominio.com.br/webhook/rdstation-updates
Eventos:
  - deal.won (Ganho)
  - deal.lost (Perdido)
  - deal.stage_changed (Mudança de etapa)
  - contact.updated (Contato atualizado)
Secret: $RDSTATION_WEBHOOK_SECRET (do .env)
```

### 9.2. Implementar Workflow Receptor

Criar workflow `09_rdstation_webhook_handler.json` que:
1. Recebe webhook do RD Station
2. Valida assinatura com secret
3. Atualiza banco de dados local
4. Dispara ações no bot se necessário

## Etapa 10: Monitoramento e Manutenção

### 10.1. Verificar Sincronização

```sql
-- Ver log de sincronização
SELECT * FROM rdstation_sync_log
ORDER BY created_at DESC
LIMIT 50;

-- Ver leads com RD Station IDs
SELECT
  name,
  service_type,
  status,
  rdstation_contact_id,
  rdstation_deal_id,
  rdstation_last_sync
FROM leads
WHERE rdstation_contact_id IS NOT NULL
ORDER BY created_at DESC;
```

### 10.2. Troubleshooting

**Erro: Token Expirado**
```
Solution: O refresh token é automático no n8n.
Verificar: Credencial RD Station no n8n está conectada
```

**Erro: Campo Customizado não encontrado**
```
Solution: Verificar se API Name está correto
Verificar: Usando cf_* nos requests
```

**Erro: Pipeline/Stage ID inválido**
```
Solution: Listar pipelines novamente e atualizar .env
GET /api/v1/deal_pipelines
```

**Sincronização lenta**
```
Solution: Verificar rdstation_sync_log para erros
Aumentar: retry_count se necessário
Verificar: rate limiting da API (300 req/min)
```

## Fluxo de Sincronização Completo

```
┌─────────────────────────────────────────────────────┐
│              NOVO LEAD NO WHATSAPP                  │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  1. Criar Contato no RD Station                     │
│     POST /contacts                                  │
│     → Salvar rdstation_contact_id                   │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  2. Criar Negociação                                │
│     POST /deals                                     │
│     Etapa: "Novo Lead"                              │
│     → Salvar rdstation_deal_id                      │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  3. Bot Coleta Dados                                │
│     PUT /contacts/{id}  (atualiza dados)            │
│     PUT /deals/{id}     (atualiza campos custom)    │
│     Etapa: "Qualificando"                           │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  4. Agendamento Confirmado                          │
│     PUT /deals/{id}/deal_stage (move etapa)         │
│     POST /tasks (cria tarefa para técnico)          │
│     Etapa: "Agendado"                               │
└─────────────────────────────────────────────────────┘
```

## Recursos Adicionais

- **API Docs**: https://developers.rdstation.com/reference/introducao
- **Postman Collection**: https://developers.rdstation.com/postman
- **Limites de API**: 300 requests/min, 10.000 requests/dia
- **Suporte RD**: suporte@rdstation.com

## Checklist de Configuração

- [ ] Aplicação OAuth2 criada no App Store
- [ ] Client ID e Secret obtidos
- [ ] Refresh Token gerado e testado
- [ ] Campos customizados criados em Contatos
- [ ] Campos customizados criados em Negociações
- [ ] Pipeline "Bot WhatsApp E2 Soluções" criado
- [ ] IDs de todas as etapas anotados
- [ ] Fonte "Bot WhatsApp" criada
- [ ] Usuário técnico identificado
- [ ] `.env.dev` atualizado com todos os IDs
- [ ] Credencial RD Station testada no n8n
- [ ] Teste de criação de contato realizado
- [ ] Teste de criação de negociação realizado
- [ ] Workflows importados e ativos
- [ ] Log de sincronização monitorado

---

**Configuração completa!** O bot agora está integrado com RD Station CRM e sincronizará automaticamente todos os leads e interações.
