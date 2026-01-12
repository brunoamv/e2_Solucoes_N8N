# Evolution API Issue #1474 - Workaround Documentado

> **Status**: Crítico - Afeta todas as versões Evolution API v2.2.x
> **Issue**: https://github.com/EvolutionAPI/evolution-api/issues/1474
> **Descoberto em**: 2025-12-16
> **Solução**: Copiar `.env` para dentro do container

---

## 📋 Sumário Executivo

A Evolution API v2.2.3 possui um **bug crítico** onde **ignora completamente** as variáveis de ambiente passadas via Docker (`env_file` e `environment` no docker-compose). O container usa apenas o arquivo interno `/evolution/.env` que contém credenciais hardcoded incorretas.

### Sintomas Observados:
- ❌ Instâncias WhatsApp vão direto para status `"close"` sem inicializar
- ❌ Baileys não carrega (nenhum log de conexão)
- ❌ QR code não é gerado
- ❌ Nenhum diretório criado em `/evolution/instances/`
- ✅ API HTTP responde normalmente (engana desenvolvedores)
- ✅ Migrations do Prisma executam (parece funcionar)

---

## 🔍 Análise Técnica Detalhada

### Problema Raiz

O container Evolution API v2.2.3 **hardcoda** um arquivo `.env` interno com credenciais incorretas:

```bash
# Arquivo: /evolution/.env (INTERNO ao container)
DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI='postgresql://user:pass@postgres:5432/evolution?schema=public'
#                                       ^^^^  ^^^^  ^^^^^^^^
#                                       ERRADO! ERRADO! ERRADO!
```

**Credenciais corretas** (que deveriam ser usadas):
```bash
DATABASE_CONNECTION_URI=postgresql://evolution:evolution_dev_password@evolution-postgres:5432/evolution
```

### Comportamento Inesperado

1. **Docker env_file**: Ignorado completamente ❌
2. **Docker environment**: Ignorado completamente ❌
3. **Arquivo interno .env**: Usado (com credenciais erradas) ✅

Isso causa falha silenciosa na inicialização do Baileys, pois:
- Prisma conecta ao PostgreSQL com credenciais corretas do `docker-compose`
- Baileys tenta usar credenciais do `.env` interno (erradas)
- Falha sem logs de erro explícitos

### Versões Afetadas

| Versão | Afetada? | Observações |
|--------|----------|-------------|
| v2.1.1 | ✅ Sim | Mesmo comportamento |
| v1.8.3 | ❌ Não | Usa MongoDB (incompatível) |
| v2.2.3 | ✅ Sim | Versão atual, bug confirmado |

---

## ✅ Solução (Workaround)

### Opção A: Script Automatizado (RECOMENDADO)

Criamos um script que aplica o workaround automaticamente:

```bash
# Executar script de inicialização
./scripts/start-evolution-api.sh
```

O script:
1. Cria containers PostgreSQL, Redis e Evolution API
2. **Copia `.env` para dentro do container** (workaround)
3. Reinicia o container para carregar novo `.env`
4. Valida que API está respondendo

### Opção B: Manual (Desenvolvimento)

```bash
# 1. Iniciar containers normalmente
docker-compose -f docker/docker-compose-dev.yml up -d

# 2. Copiar .env para dentro do container (CRÍTICO)
docker cp docker/.env e2bot-evolution-dev:/evolution/.env

# 3. Reiniciar para carregar novo .env
docker restart e2bot-evolution-dev

# 4. Aguardar inicialização (20s)
sleep 20

# 5. Testar API
curl http://localhost:8080
```

### Opção C: Dockerfile Customizado (Produção)

Crie um Dockerfile que injeta o `.env` correto:

```dockerfile
FROM atendai/evolution-api:v2.2.3

# Copiar .env correto para sobrescrever o hardcoded
COPY .env /evolution/.env

# Resto da configuração padrão...
```

Build e uso:
```bash
docker build -t evolution-api-fixed:v2.2.3 -f Dockerfile.evolution .
docker run -d --name evolution-api evolution-api-fixed:v2.2.3
```

---

## 🧪 Validação da Solução

### Teste 1: Verificar que .env foi copiado

```bash
# Deve mostrar conteúdo do seu .env local
docker exec e2bot-evolution-dev head -20 /evolution/.env
```

### Teste 2: Criar instância WhatsApp

```bash
curl -X POST http://localhost:8080/instance/create \
  -H "Content-Type: application/json" \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" \
  -d '{
    "instanceName": "teste-workaround",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }'
```

**Resultado esperado** (COM workaround):
```json
{
  "status": "connecting",
  "qrcode": {
    "code": "2@xjYCEXW/...",
    "base64": "data:image/png;base64,iVBORw0KG...",
    "count": 1
  }
}
```

**Resultado esperado** (SEM workaround):
```json
{
  "status": "close"  // ❌ FALHA
  // Sem qrcode gerado
}
```

### Teste 3: Verificar diretório da instância

```bash
# Deve mostrar diretório criado pelo Baileys
docker exec e2bot-evolution-dev ls -la /evolution/instances/

# COM workaround: drwxr-xr-x ... teste-workaround/
# SEM workaround: (vazio ou apenas .gitkeep)
```

---

## 📦 Configuração para Produção

### Docker Compose Produção

```yaml
# docker-compose.yml (PRODUÇÃO)
services:
  evolution-api:
    image: atendai/evolution-api:v2.2.3
    container_name: evolution-api-prod
    restart: always

    # IMPORTANTE: env_file não funciona devido ao bug
    # Usamos entrypoint customizado como workaround
    env_file:
      - .env  # Será copiado manualmente no entrypoint

    entrypoint: /bin/bash -c "
      if [ -f /tmp/.env ]; then
        cp /tmp/.env /evolution/.env;
      fi &&
      exec /bin/bash -c '. ./Docker/docker-entrypoint.sh'
    "

    volumes:
      - ./docker/.env:/tmp/.env:ro  # Montar .env em /tmp
      - evolution_instances:/evolution/instances
      - evolution_store:/evolution/store

    # ... resto da configuração
```

**Explicação**:
1. Montamos `.env` em `/tmp/.env` (não sobrescreve interno)
2. Entrypoint customizado copia de `/tmp/.env` → `/evolution/.env`
3. Depois executa entrypoint original

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: evolution-api-config
data:
  .env: |
    SERVER_TYPE=http
    SERVER_PORT=8080
    DATABASE_ENABLED=true
    DATABASE_PROVIDER=postgresql
    DATABASE_CONNECTION_URI=postgresql://user:pass@postgres:5432/evolution
    # ... resto das configurações
---
apiVersion: v1
kind: Pod
metadata:
  name: evolution-api
spec:
  initContainers:
  - name: copy-env
    image: busybox
    command: ['sh', '-c', 'cp /tmp/.env /evolution/.env']
    volumeMounts:
    - name: config
      mountPath: /tmp
    - name: evolution-data
      mountPath: /evolution
  containers:
  - name: evolution-api
    image: atendai/evolution-api:v2.2.3
    volumeMounts:
    - name: evolution-data
      mountPath: /evolution
  volumes:
  - name: config
    configMap:
      name: evolution-api-config
  - name: evolution-data
    emptyDir: {}
```

---

## 🔄 Fluxo de Inicialização Correto

```mermaid
graph TD
    A[Container Inicia] --> B[Carrega .env HARDCODED ERRADO]
    B --> C{Workaround aplicado?}
    C -->|NÃO| D[Baileys falha silenciosamente]
    C -->|SIM| E[Copiar .env correto para /evolution/.env]
    E --> F[Reiniciar container]
    F --> G[Baileys inicializa com sucesso]
    G --> H[QR code gerado]
    D --> I[Status: close, sem QR code]
```

---

## 🚨 Armadilhas Comuns

### ❌ Armadilha 1: Confiar no HTTP 200
```bash
curl http://localhost:8080  # Retorna 200 OK ✅
# MAS Baileys pode não estar funcionando! ❌
```

**Solução**: Sempre criar instância de teste e verificar QR code.

### ❌ Armadilha 2: Achar que migrations = funcionando
```
Prisma schema loaded ✅
49 migrations applied ✅
Migration succeeded ✅
# MAS Baileys ainda pode falhar! ❌
```

**Solução**: Verificar logs do Baileys especificamente.

### ❌ Armadilha 3: Usar env_file sem workaround
```yaml
services:
  evolution-api:
    env_file: .env  # ❌ SERÁ IGNORADO!
```

**Solução**: Use entrypoint customizado ou `docker cp`.

---

## 📊 Comparação: Antes vs Depois

| Aspecto | SEM Workaround | COM Workaround |
|---------|----------------|----------------|
| API HTTP | ✅ Funciona | ✅ Funciona |
| Prisma Migrations | ✅ Funciona | ✅ Funciona |
| Baileys Inicializa | ❌ Falha | ✅ Funciona |
| QR Code Gerado | ❌ Não | ✅ Sim |
| Status Instância | `close` | `connecting` |
| Diretório Criado | ❌ Não | ✅ Sim |

---

## 🔗 Referências

- **Issue Original**: https://github.com/EvolutionAPI/evolution-api/issues/1474
- **Evolution API Docs**: https://doc.evolution-api.com/
- **Baileys GitHub**: https://github.com/WhiskeySockets/Baileys
- **Nossa Solução**: `scripts/start-evolution-api.sh`

---

## 📝 Histórico de Mudanças

| Data | Versão | Mudança |
|------|--------|---------|
| 2025-12-16 | 1.0 | Descoberta do Issue #1474 e criação do workaround |
| 2025-12-16 | 1.1 | Script automatizado criado |
| 2025-12-16 | 1.2 | Documentação completa para produção |
| 2025-12-17 | 2.0 | ⚠️ **DESCOBERTA CRÍTICA**: Workaround também necessário para geração de QR Code! |

### 🚨 Atualização Importante (2025-12-17)

**Descoberta**: O bug da Issue #1474 afeta **DUAS funcionalidades**:
1. ✅ **Inicialização do Baileys** (documentado originalmente)
2. 🆕 **Geração de QR Code** (descoberto hoje)

**Sintoma**: Mesmo com container rodando corretamente, os endpoints de QR code retornam 404:
- `GET /instance/qrcode/{instance}` → 404 Not Found
- `GET /instance/connect/{instance}` → 404 Not Found ou sem campo `base64`

**Root Cause**: Evolution API v2.2.3 precisa do arquivo `/evolution/.env` **físico** para AMBAS as operações:
- Inicialização do Baileys (já documentado)
- Geração de QR Code (descoberta nova)

**Solução Validada**:
```bash
# Após iniciar containers via docker-compose
docker cp docker/.env e2bot-evolution-dev:/evolution/.env
docker restart e2bot-evolution-dev
sleep 20

# Agora QR code funciona!
source ./scripts/evolution-helper.sh
evolution_connect  # ✅ Gera qrcode.png com sucesso
```

---

## ✍️ Autoria

**Descoberto por**: Equipe E2 Soluções
**Data**: 2025-12-16
**Context**: Tentativas de setup Evolution API v2.1.1 → v1.8.3 → v2.2.3
**Solução**: Copiar `.env` manualmente para dentro do container

---

## 💬 FAQ

**P: Por que não reportar o bug aos mantenedores?**
R: Pode ser reportado, mas workaround é necessário enquanto não corrigem.

**P: Versões futuras resolverão isso?**
R: Desconhecido. Aplicar workaround é seguro para todas as versões.

**P: Funciona com docker-compose?**
R: Sim, mas requer entrypoint customizado ou script pós-inicialização.

**P: E no Kubernetes?**
R: Sim, usar initContainer conforme exemplo acima.

**P: Tem impacto de performance?**
R: Nenhum. É apenas copiar um arquivo antes de iniciar.

---

**🎯 Conclusão**: Este workaround é **necessário e seguro** para todas as implantações Evolution API v2.2.x até que o bug seja oficialmente corrigido.
