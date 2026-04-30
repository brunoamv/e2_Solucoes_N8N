# BUGFIX: Evolution API Healthcheck - Container Unhealthy Status

> **Data**: 2026-04-13 | **Status**: ✅ RESOLVIDO DEFINITIVAMENTE

---

## ❌ Problema

Evolution API container mostrava status `unhealthy` apesar de funcionar corretamente (mensagens enviavam com sucesso). Usuário precisava manualmente executar `docker-compose down && docker-compose up -d` para resolver temporariamente.

### Evidência do Problema

```bash
$ docker ps --format "table {{.Names}}\t{{.Status}}"
NAMES                        STATUS
e2bot-evolution-dev          Up 56 minutes (unhealthy)

$ docker inspect e2bot-evolution-dev --format='{{json .State.Health}}' | jq
{
  "Status": "unhealthy",
  "FailingStreak": 114,
  "Log": [
    {
      "ExitCode": 1,
      "Output": "/bin/sh: curl: not found\n"
    }
  ]
}
```

**Comportamento**: Evolution API funcionava (mensagens WhatsApp enviadas com sucesso), mas healthcheck falhava continuamente.

---

## 🔍 Diagnóstico

### Root Cause

Healthcheck em `docker-compose-dev.yml` linha 218 usava comando `curl` que **não existe** no container Evolution API.

**Configuração Incorreta** (linha 218):
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8080/instance/fetchInstances -H 'apikey: ${EVOLUTION_API_KEY}' || exit 1"]
  interval: 30s
  timeout: 15s
  retries: 5
  start_period: 60s
```

### Investigação

1. **Verificação de curl no container**:
   ```bash
   $ docker exec e2bot-evolution-dev which curl
   # (vazio - comando não existe)
   ```

2. **Verificação de wget no container**:
   ```bash
   $ docker exec e2bot-evolution-dev which wget
   /usr/bin/wget
   ```

3. **Teste do comando healthcheck original**:
   ```bash
   $ docker exec e2bot-evolution-dev /bin/sh -c "curl -f http://localhost:8080/instance/fetchInstances"
   /bin/sh: curl: not found
   ```

**Conclusão**: Container Evolution API (`evoapicloud/evolution-api:latest`) possui `wget` mas não possui `curl`.

---

## ✅ Solução Implementada

### Modificação no docker-compose-dev.yml

**Arquivo**: `/docker/docker-compose-dev.yml`
**Linha**: 218

**ANTES** (comando inexistente):
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8080/instance/fetchInstances -H 'apikey: ${EVOLUTION_API_KEY}' || exit 1"]
```

**DEPOIS** (usando wget):
```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --spider -q --header='apikey: ${EVOLUTION_API_KEY}' http://localhost:8080/instance/fetchInstances || exit 1"]
```

### Explicação do Comando wget

- `wget --spider`: Verifica se URL existe sem baixar conteúdo
- `-q`: Modo quiet (sem output verbose)
- `--header='apikey: ${EVOLUTION_API_KEY}'`: Adiciona header de autenticação
- `http://localhost:8080/instance/fetchInstances`: Endpoint Evolution API para verificar instâncias
- `|| exit 1`: Retorna erro se wget falhar

---

## 🧪 Validação da Solução

### Passos de Teste

1. **Recriar container com nova configuração**:
   ```bash
   docker rm 039e3bcc28cf_e2bot-evolution-dev
   docker-compose -f docker/docker-compose-dev.yml up -d evolution-api
   ```

2. **Aguardar start_period (60 segundos)**:
   ```bash
   sleep 65
   ```

3. **Verificar health status**:
   ```bash
   docker inspect e2bot-evolution-dev --format='{{json .State.Health}}' | jq
   ```

### Resultado ✅

```json
{
  "Status": "healthy",
  "FailingStreak": 0,
  "Log": [
    {
      "Start": "2026-04-13T15:52:04.513870851-03:00",
      "End": "2026-04-13T15:52:04.57922123-03:00",
      "ExitCode": 0,
      "Output": ""
    },
    {
      "Start": "2026-04-13T15:52:34.580081843-03:00",
      "End": "2026-04-13T15:52:34.647108858-03:00",
      "ExitCode": 0,
      "Output": ""
    },
    {
      "Start": "2026-04-13T15:53:04.648236346-03:00",
      "End": "2026-04-13T15:53:04.703057528-03:00",
      "ExitCode": 0,
      "Output": ""
    }
  ]
}
```

**Status final dos containers**:
```
NAMES                        STATUS
e2bot-evolution-dev          Up About a minute (healthy)
e2bot-evolution-redis        Up About an hour (healthy)
e2bot-n8n-dev                Up About an hour (healthy)
e2bot-templates-dev          Up About an hour (healthy)
e2bot-evolution-postgres     Up About an hour
e2bot-postgres-dev           Up About an hour (healthy)
```

✅ **Container Evolution API agora mostra `(healthy)` permanentemente!**

---

## 📝 Lessons Learned

### Problema Recorrente Resolvido

- **Antes**: Usuário precisava manualmente `docker-compose down && up -d` para resolver temporariamente
- **Depois**: Container mantém status `healthy` automaticamente - problema resolvido permanentemente

### Best Practices Aplicadas

1. **Verificar comandos disponíveis no container**: Nunca assumir que ferramentas CLI estão instaladas
2. **Usar comandos nativos da imagem**: Evolution API tem `wget`, não `curl`
3. **Testar healthcheck isoladamente**: `docker exec` é essencial para debugging
4. **Aguardar start_period completo**: 60 segundos antes de avaliar health status

### Healthcheck Evolution API

**Configuração correta para Evolution API**:
```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --spider -q --header='apikey: ${EVOLUTION_API_KEY}' http://localhost:8080/instance/fetchInstances || exit 1"]
  interval: 30s
  timeout: 15s
  retries: 5
  start_period: 60s
```

**Por que funciona**:
- ✅ `wget` está disponível no container Evolution API
- ✅ `--spider` verifica conectividade sem consumir recursos
- ✅ Autenticação via header `apikey` necessária para Evolution API v2.x
- ✅ `start_period: 60s` dá tempo suficiente para serviço inicializar

---

## 🎯 Impacto

### Antes da Correção
- ⚠️ Container sempre `unhealthy` apesar de funcional
- 🔄 Necessidade de restart manual frequente
- ❌ Logs poluídos com 114+ health check failures
- ⏱️ Tempo perdido em troubleshooting recorrente

### Depois da Correção
- ✅ Container mantém status `healthy` automaticamente
- ✅ Zero necessidade de intervenção manual
- ✅ Healthcheck funcional detecta problemas reais
- ⚡ Desenvolvimento mais fluido e confiável

---

## 📚 Referências

- **Evolution API Docs**: https://doc.evolution-api.com/
- **Docker Compose Healthcheck**: https://docs.docker.com/compose/compose-file/compose-file-v3/#healthcheck
- **wget Manual**: https://www.gnu.org/software/wget/manual/wget.html

---

**Criado**: 2026-04-13
**Autor**: Claude Code
**Status**: ✅ SOLUÇÃO DEFINITIVA
**Arquivo Modificado**: `/docker/docker-compose-dev.yml` (linha 218)
