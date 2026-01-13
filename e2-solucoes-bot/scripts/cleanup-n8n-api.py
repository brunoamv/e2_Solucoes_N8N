#!/usr/bin/env python3
"""
Script para limpar execuções antigas do n8n através da API
"""
import requests
import json
from datetime import datetime, timedelta
import time

# Configurações
N8N_URL = "http://localhost:5678"
N8N_USER = "admin"
N8N_PASSWORD = "senhasegura"

# Autenticar no n8n
def authenticate():
    """Autentica no n8n e retorna o token"""
    try:
        response = requests.post(
            f"{N8N_URL}/api/v1/auth/login",
            json={"email": N8N_USER, "password": N8N_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            return response.cookies
        else:
            print(f"❌ Erro na autenticação: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro ao conectar ao n8n: {e}")
        return None

# Obter lista de execuções
def get_executions(cookies):
    """Obtém lista de todas as execuções"""
    try:
        response = requests.get(
            f"{N8N_URL}/api/v1/executions",
            cookies=cookies,
            params={"limit": 1000}
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erro ao obter execuções: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro ao obter execuções: {e}")
        return None

# Deletar execução
def delete_execution(execution_id, cookies):
    """Deleta uma execução específica"""
    try:
        response = requests.delete(
            f"{N8N_URL}/api/v1/executions/{execution_id}",
            cookies=cookies
        )
        return response.status_code == 200
    except:
        return False

def main():
    print("=== 🧹 Limpeza de Execuções do n8n ===\n")

    # Autenticar
    print("🔐 Autenticando no n8n...")
    cookies = authenticate()
    if not cookies:
        print("❌ Falha na autenticação")
        return

    print("✅ Autenticado com sucesso!\n")

    # Obter execuções
    print("📋 Obtendo lista de execuções...")
    executions_data = get_executions(cookies)
    if not executions_data or 'data' not in executions_data:
        print("❌ Não foi possível obter execuções")
        return

    executions = executions_data['data']
    print(f"📊 Total de execuções encontradas: {len(executions)}\n")

    # Calcular estatísticas
    now = datetime.now()
    one_day_ago = now - timedelta(days=1)
    three_days_ago = now - timedelta(days=3)
    seven_days_ago = now - timedelta(days=7)

    stats = {
        'total': len(executions),
        'errors': 0,
        'success': 0,
        'running': 0,
        'older_than_1d': 0,
        'older_than_3d': 0,
        'older_than_7d': 0
    }

    to_delete = []

    for exec in executions:
        # Parse da data
        if 'startedAt' in exec and exec['startedAt']:
            try:
                started = datetime.fromisoformat(exec['startedAt'].replace('Z', '+00:00'))

                # Verificar idade
                if started < seven_days_ago:
                    stats['older_than_7d'] += 1
                    to_delete.append(exec['id'])
                elif started < three_days_ago:
                    stats['older_than_3d'] += 1
                    # Deletar execuções de sucesso > 3 dias
                    if exec.get('finished', False) and not exec.get('stoppedAt'):
                        to_delete.append(exec['id'])
                elif started < one_day_ago:
                    stats['older_than_1d'] += 1
                    # Deletar execuções com erro > 1 dia
                    if exec.get('finished', False) and exec.get('stoppedAt'):
                        to_delete.append(exec['id'])
            except:
                pass

        # Contar status
        if exec.get('finished', False):
            if exec.get('stoppedAt'):
                stats['errors'] += 1
            else:
                stats['success'] += 1
        else:
            stats['running'] += 1

    # Exibir estatísticas
    print("📊 Estatísticas das Execuções:")
    print(f"  • Total: {stats['total']}")
    print(f"  • Com erro: {stats['errors']}")
    print(f"  • Sucesso: {stats['success']}")
    print(f"  • Em execução: {stats['running']}")
    print(f"  • Mais de 7 dias: {stats['older_than_7d']}")
    print(f"  • Mais de 3 dias: {stats['older_than_3d']}")
    print(f"  • Mais de 1 dia: {stats['older_than_1d']}")
    print()

    # Limitar a 500 execuções mantidas
    if len(executions) > 500:
        # Ordenar por data e manter apenas as 500 mais recentes
        sorted_execs = sorted(executions,
                            key=lambda x: x.get('startedAt', ''),
                            reverse=True)

        # Adicionar execuções antigas à lista de exclusão
        for exec in sorted_execs[500:]:
            if exec['id'] not in to_delete:
                to_delete.append(exec['id'])

    print(f"🗑️ Execuções marcadas para exclusão: {len(to_delete)}")

    if to_delete:
        print("\n🧹 Iniciando limpeza...")
        deleted = 0
        failed = 0

        for i, exec_id in enumerate(to_delete, 1):
            if delete_execution(exec_id, cookies):
                deleted += 1
                print(f"  ✅ [{i}/{len(to_delete)}] Execução {exec_id} deletada")
            else:
                failed += 1
                print(f"  ❌ [{i}/{len(to_delete)}] Falha ao deletar {exec_id}")

            # Pequena pausa para não sobrecarregar
            if i % 10 == 0:
                time.sleep(0.5)

        print(f"\n✅ Limpeza concluída!")
        print(f"  • Deletadas: {deleted}")
        print(f"  • Falhas: {failed}")
    else:
        print("\n✅ Nenhuma execução para limpar!")

    print("\n🎉 Processo finalizado com sucesso!")

if __name__ == "__main__":
    main()