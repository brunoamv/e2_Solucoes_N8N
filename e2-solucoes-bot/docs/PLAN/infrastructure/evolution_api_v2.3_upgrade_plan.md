# 🎯 Plano de Atualização: Evolution API v2.3+ e Campo senderPn

## Contexto do Problema
- **Versão Atual**: Evolution API v2.2.3 (com problemas no remoteJid)
- **Versão Alvo**: Evolution API v2.3+ (com campo senderPn funcional)
- **Problema**: Docker está usando versão cacheada mesmo com `latest` configurado
- **Solução**: Forçar atualização e adaptar extração do phone_number

## 📝 Tarefas Planejadas

### Fase 1: Limpeza de Cache e Atualização do Evolution API
1. **Parar todos os containers**
   - `docker-compose -f docker/docker-compose-dev.yml down`

2. **Remover imagem antiga do Evolution API**
   - `docker images | grep evolution`
   - `docker rmi atendai/evolution-api:v2.2.3`
   - `docker rmi atendai/evolution-api:latest` (se existir)

3. **Limpar cache do Docker**
   - `docker system prune -a` (com cuidado)
   - OU especificamente: `docker image prune -a --filter "label=evolution"`

4. **Forçar download da nova versão**
   - `docker pull atendai/evolution-api:latest --no-cache`
   - Verificar versão: `docker run --rm atendai/evolution-api:latest --version`

5. **Atualizar docker-compose-dev.yml**
   ```yaml
   evolution-api:
     image: atendai/evolution-api:v2.3.0  # Especificar versão exata
     # OU
     image: atendai/evolution-api:latest
     pull_policy: always  # Forçar pull sempre
   ```

6. **Subir containers com nova versão**
   - `docker-compose -f docker/docker-compose-dev.yml up -d evolution-api`
   - Verificar logs: `docker logs e2bot-evolution-api -f`

### Fase 2: Adaptar Workflow para Campo senderPn

1. **Análise dos campos disponíveis**
   - Testar webhook para ver estrutura com v2.3+
   - Documentar campos: `remoteJid`, `senderPn`, etc.

2. **Atualizar extração no workflow 01**
   ```javascript
   function extractPhoneNumber(data) {
     // Prioridade 1: Usar senderPn se existir (v2.3+)
     if (data.senderPn) {
       return formatBrazilianNumber(data.senderPn);
     }

     // Fallback: Usar remoteJid (v2.2.x e anteriores)
     const key = data.key || {};
     if (key.remoteJid) {
       return extractFromRemoteJid(key.remoteJid);
     }

     // Erro se nenhum campo disponível
     throw new Error('No phone number field available');
   }
   ```

3. **Criar função de formatação robusta**
   ```javascript
   function formatBrazilianNumber(phone) {
     let cleaned = String(phone).replace(/\D/g, '');

     // Remove código do país se presente
     if (cleaned.startsWith('55') && cleaned.length >= 12) {
       cleaned = cleaned.substring(2);
     }

     // Valida formato DDD + número
     if (!/^\d{10,11}$/.test(cleaned)) {
       console.warn('Unexpected format:', cleaned);
     }

     return cleaned;
   }
   ```

### Fase 3: Scripts de Implementação

1. **Script de limpeza e atualização do Docker**
   - `scripts/update-evolution-api.sh`

2. **Script de correção do workflow**
   - `scripts/fix-workflow-senderPn.sh`

3. **Script de teste e validação**
   - `scripts/test-evolution-v23.sh`

## 🚀 Ordem de Execução

```bash
# 1. Limpar cache e atualizar Evolution API
./scripts/update-evolution-api.sh

# 2. Verificar versão instalada
docker exec e2bot-evolution-api evolution --version

# 3. Aplicar correções no workflow
./scripts/fix-workflow-senderPn.sh

# 4. Testar extração com novo campo
./scripts/test-evolution-v23.sh
```

## ⚠️ Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Quebra de compatibilidade | Alto | Manter fallback para remoteJid |
| Perda de dados durante migração | Médio | Backup antes de atualizar |
| Evolution API instável | Médio | Testar em ambiente dev primeiro |
| Cache persistente | Baixo | Usar comandos force e no-cache |

## 📊 Critérios de Sucesso

- [ ] Evolution API rodando versão >= 2.3.0
- [ ] Campo `senderPn` disponível no webhook
- [ ] Extração de phone_number funcionando com novo campo
- [ ] Fallback para `remoteJid` operacional
- [ ] Testes passando com ambos os formatos

## 📝 Notas Técnicas

- Evolution API changelog: https://github.com/EvolutionAPI/evolution-api/releases
- Campo `senderPn` introduzido na v2.3.0 para resolver problemas com remoteJid
- Manter compatibilidade com versões anteriores é essencial
- Considerar uso de feature flags para migração gradual

---

**Status**: 📋 Planejado
**Prioridade**: 🔴 Alta
**Estimativa**: 2-3 horas
**Autor**: Claude Code
**Data**: 2025-01-06