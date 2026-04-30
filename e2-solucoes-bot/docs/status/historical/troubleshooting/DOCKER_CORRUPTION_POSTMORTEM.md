# Docker Containerd Corruption - Post-Mortem Analysis

> **Date**: 2026-03-30
> **Issue**: Docker daemon não inicia após tentativas de remover containers travados
> **Root Cause**: Containerd runtime corrompido com estado inconsistente
> **Solution**: Reboot do sistema + limpeza completa

---

## 🔴 Timeline do Problema

### Problema Inicial (Execução 16333)
- **Sintoma**: WF07 V5 não consegue ler templates de email
- **Erro**: `ls: /email-templates/: No such file or directory`
- **Causa**: Container não foi recriado com novo volume mount

### Tentativa 1: Docker Compose Down (FALHOU)
```bash
docker-compose -f docker/docker-compose-dev.yml down
# ERROR: permission denied
```
- **Motivo**: Containers têm restart policy `unless-stopped`

### Tentativa 2: Sudo Docker Compose (FALHOU)
```bash
sudo docker-compose -f docker/docker-compose-dev.yml down
# ERROR: permission denied (mesmo com sudo!)
```
- **Motivo**: Não é problema de permissão de usuário, é proteção do kernel

### Tentativa 3: Restart Docker Daemon (FALHOU)
```bash
sudo systemctl restart docker
# Containers continuam rodando após restart
```
- **Motivo**: Restart policy reinicia containers automaticamente

### Tentativa 4: Force Remove Containers (FALHOU)
```bash
sudo docker rm -f e2bot-n8n-dev e2bot-evolution-dev e2bot-postgres-dev
# ERROR: permission denied
```
- **Motivo**: Daemon não consegue enviar comando kill aos containers

### Tentativa 5: Ultimate Fix - Update Restart Policy (PARCIAL)
```bash
docker update --restart=no e2bot-n8n-dev
# ✅ Restart policies desabilitados

systemctl stop docker
systemctl start docker
# ❌ Docker daemon não inicia
```
- **Progresso**: Restart policies desabilitados ✅
- **Problema**: Kill de processos corrompeu containerd

### Tentativa 6: Fix Docker Snap (FALHOU CRÍTICO)
```bash
snap stop docker
snap start docker
# ERROR: failed to start containerd: timeout
```
- **Logs mostram**: Containerd em loop tentando deletar containers já mortos
- **Estado**: Containerd corrupto, metadados inconsistentes

---

## 🎯 Causa Raiz Técnica

### Estado Corrompido do Containerd

**O que aconteceu:**
1. Script `ultimate-docker-fix.sh` matou processos containerd-shim com `kill -9`
2. Containerd perdeu referência aos processos (PIDs não existem mais)
3. Metadados em `/run/snap.docker/containerd/` apontam para containers inexistentes
4. Containerd tenta deletar esses containers no próximo start
5. Operação delete falha (processo já morto)
6. Containerd não consegue inicializar (fica em loop)

**Evidência nos logs:**
```
failed to delete [container]: signal: killed
failed to start containerd: timeout waiting for containerd to start
copy shim log after reload: file already closed
```

### Por Que Não Tem Solução SEM Reboot

**Containerd mantém estado em múltiplos locais:**
- `/run/snap.docker/containerd/` - Runtime state (em memória)
- `/var/snap/docker/common/var-lib-docker/` - Persistent state
- Processos kernel (cgroups, namespaces)

**Para limpar completamente, é necessário:**
1. ❌ Parar containerd (não funciona, está travado)
2. ❌ Limpar runtime state (containerd trava ao tentar)
3. ❌ Resetar kernel namespaces (só com reboot)

**Conclusão**: Sem reboot, não há como limpar estado do kernel.

---

## ✅ Solução Definitiva

### Passo 1: REBOOT

```bash
sudo reboot
```

**Por que funciona:**
- Kernel limpa TODOS os processos
- Namespaces e cgroups resetados
- Runtime state em `/run/` é limpo automaticamente (tmpfs)
- Containerd inicia limpo sem containers antigos

### Passo 2: Após Reboot - Limpeza

```bash
# 1. Verificar Docker funcionando
docker ps -a

# 2. Remover containers órfãos (se existirem)
docker rm -f $(docker ps -aq) 2>/dev/null || true

# 3. Limpar volumes órfãos
docker volume prune -f

# 4. Limpar networks órfãs
docker network prune -f
```

### Passo 3: Subir Stack Limpo

```bash
# Volume mount já está adicionado no docker-compose-dev.yml (linha 73)
docker-compose -f docker/docker-compose-dev.yml up -d
```

### Passo 4: Verificar Mount

```bash
docker exec e2bot-n8n-dev ls -la /email-templates/
```

**Resultado esperado:**
```
total 32
drwxrwxr-x 2 node node 4096 ...
-rw-rw-r-- 1 node node 7128 ... confirmacao_agendamento.html
-rw-rw-r-- 1 node node 5432 ... lembrete_2h.html
-rw-rw-r-- 1 node node 4821 ... novo_lead.html
-rw-rw-r-- 1 node node 3245 ... apos_visita.html
```

---

## 📊 Lições Aprendidas

### ❌ O Que NÃO Fazer

1. **NUNCA matar processos containerd-shim diretamente**
   - Use `docker stop` ou `docker rm -f`
   - Se não funcionar, use `docker update --restart=no` ANTES de qualquer outra coisa

2. **NUNCA usar `kill -9` em processos Docker**
   - Corrompe estado do containerd
   - Cria situação irrecuperável sem reboot

3. **NUNCA ignorar restart policies**
   - Sempre desabilitar ANTES de tentar remover containers: `docker update --restart=no`

### ✅ Procedimento Correto para Containers Travados

```bash
# 1. Desabilitar restart policy PRIMEIRO
docker update --restart=no <container>

# 2. Parar container normalmente
docker stop <container>

# 3. SE FALHAR: Tentar force stop
docker stop -t 0 <container>

# 4. SE FALHAR: Remover com força
docker rm -f <container>

# 5. SE FALHAR: Parar Docker daemon
systemctl stop docker

# 6. SE FALHAR: REBOOT (não há outra opção)
sudo reboot
```

### 🎯 Como Evitar no Futuro

1. **Usar `--restart=unless-stopped` com cuidado**
   - Considerar `--restart=on-failure` para desenvolvimento
   - Facilita parar containers quando necessário

2. **Volume mounts devem ser configurados ANTES de subir containers**
   - Testar docker-compose.yml antes de `up -d`
   - Usar `docker-compose config` para validar

3. **Backup de dados antes de operações arriscadas**
   - Volumes nomeados são preservados
   - Mas sempre fazer backup de dados críticos

---

## 📁 Arquivos Relevantes

- `docker/docker-compose-dev.yml` (linha 73) - Volume mount adicionado
- `scripts/ultimate-docker-fix.sh` - Script que corrompeu containerd
- `scripts/fix-docker-snap.sh` - Tentativa de recovery (falhou)
- `n8n/workflows/07_send_email_v6_docker_volume_fix.json` - WF07 V6 pronto

---

## 🚀 Status Atual

- ⏳ **Aguardando reboot do sistema**
- ✅ Volume mount já configurado no docker-compose.yml
- ✅ WF07 V6 workflow gerado e pronto
- ✅ Todos os dados preservados em volumes nomeados

**Próximo passo**: `sudo reboot` → testar WF07 V6

---

**End of Post-Mortem**
