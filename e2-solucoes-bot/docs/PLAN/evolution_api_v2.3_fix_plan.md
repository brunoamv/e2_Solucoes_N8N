# 🎯 Plano de Ação: Atualização Evolution API v2.3+ com evoapicloud

## Problema Identificado
- **Versão Atual**: Evolution API v2.2.3 (cache persistente)
- **Repositório Antigo**: `atendai/evolution-api` (desatualizado)
- **Repositório Correto**: `evoapicloud/evolution-api:latest` ✅
- **Campo Necessário**: `senderPn` (disponível apenas na v2.3+)

## 📝 Etapas de Execução

### Fase 1: Limpeza Completa e Atualização
1. **Parar todos os containers Evolution**
2. **Remover TODAS as imagens antigas do cache**
3. **Atualizar docker-compose para usar `evoapicloud/evolution-api:latest`**
4. **Forçar download da nova imagem**
5. **Iniciar novo container**

### Fase 2: Adaptação do Workflow
1. **Atualizar extração para usar campo `senderPn`**
2. **Manter fallback para `remoteJid`**
3. **Testar com mensagem real**

## Comandos a Executar

```bash
# 1. Parar containers
docker-compose -f docker/docker-compose-dev.yml down

# 2. Remover TODAS as imagens Evolution (força limpeza completa)
docker images | grep evolution | awk '{print $3}' | xargs -r docker rmi -f

# 3. Atualizar docker-compose
sed -i 's|image: .*evolution-api:.*|image: evoapicloud/evolution-api:latest|g' docker/docker-compose-dev.yml

# 4. Baixar nova imagem
docker pull evoapicloud/evolution-api:latest

# 5. Subir containers
docker-compose -f docker/docker-compose-dev.yml up -d
```

## Estrutura do Webhook v2.3+

```javascript
// Evolution API v2.3+ webhook structure
{
  "event": "messages.upsert",
  "data": {
    "key": {
      "remoteJid": "556198175548@s.whatsapp.net", // ainda existe
      "fromMe": false,
      "id": "..."
    },
    "message": {...},
    "pushName": "Nome do Contato",
    "senderPn": "556198175548", // NOVO CAMPO! Número limpo
    "messageTimestamp": "..."
  }
}
```

## Atualização do Workflow

```javascript
function extractPhoneNumber(data) {
  // Prioridade 1: usar senderPn (v2.3+)
  if (data.senderPn) {
    console.log('Usando senderPn:', data.senderPn);
    return formatBrazilianPhone(data.senderPn);
  }

  // Prioridade 2: extrair de remoteJid
  const key = data.key || {};
  if (key.remoteJid) {
    console.log('Usando remoteJid (fallback):', key.remoteJid);
    return extractFromRemoteJid(key.remoteJid);
  }

  throw new Error('Nenhum campo de telefone disponível');
}

function formatBrazilianPhone(phone) {
  let cleaned = String(phone).replace(/\D/g, '');

  // Remove código do país se presente
  if (cleaned.startsWith('55') && cleaned.length >= 12) {
    cleaned = cleaned.substring(2);
  }

  // Valida formato DDD + número (10-11 dígitos)
  if (!/^\d{10,11}$/.test(cleaned)) {
    console.warn('Formato inesperado:', cleaned);
  }

  return cleaned;
}
```

## Verificação de Sucesso

```bash
# 1. Verificar versão instalada
docker exec e2bot-evolution-dev cat package.json | grep version

# 2. Verificar logs para campo senderPn
docker logs e2bot-evolution-dev -f | grep senderPn

# 3. Testar webhook
curl -X POST http://localhost:5678/webhook-test/whatsapp-evolution
```

## ⚠️ Pontos Críticos

1. **Cache Docker**: Usar `--no-cache` se necessário
2. **Rede Docker**: Verificar conectividade entre containers
3. **Compatibilidade**: Campo `senderPn` pode variar dependendo da versão exata

---

**Status**: 📋 Pronto para Execução
**Prioridade**: 🔴 Alta
**Tempo Estimado**: 15-20 minutos