#!/bin/bash

# Health Check Script for E2 Soluções Bot
# Monitors all services and reports status with detailed diagnostics
# Requires: Docker, curl, environment variables from .env

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   E2 Soluções - System Health Check             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# Load environment variables
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
    echo -e "${GREEN}✓${NC} Environment variables loaded"
else
    echo -e "${RED}✗${NC} .env file not found. Using defaults."
fi

# Configuration
ALERT_WEBHOOK="${ALERT_WEBHOOK_URL:-}"
HEALTH_CHECK_TIMEOUT=5
CRITICAL_FAILURE=0

# Helper functions
print_status() {
    local service=$1
    local status=$2
    local details=$3

    if [ "$status" == "healthy" ]; then
        echo -e "  ${GREEN}✓${NC} ${service}: ${GREEN}${status}${NC} ${details}"
    elif [ "$status" == "warning" ]; then
        echo -e "  ${YELLOW}⚠${NC} ${service}: ${YELLOW}${status}${NC} ${details}"
    else
        echo -e "  ${RED}✗${NC} ${service}: ${RED}${status}${NC} ${details}"
        CRITICAL_FAILURE=1
    fi
}

check_docker_container() {
    local container_name=$1
    local service_name=$2

    if docker ps --filter "name=${container_name}" --filter "status=running" | grep -q "${container_name}"; then
        # Container is running, check health status
        HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "${container_name}" 2>/dev/null || echo "no-health-check")

        if [ "$HEALTH_STATUS" == "healthy" ]; then
            print_status "${service_name}" "healthy" ""
            return 0
        elif [ "$HEALTH_STATUS" == "no-health-check" ]; then
            # No health check defined, just verify it's running
            print_status "${service_name}" "running" "(no health check)"
            return 0
        else
            print_status "${service_name}" "unhealthy" "(health check failed)"
            return 1
        fi
    else
        print_status "${service_name}" "stopped" ""
        return 1
    fi
}

check_http_endpoint() {
    local url=$1
    local service_name=$2
    local expected_status=${3:-200}

    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time ${HEALTH_CHECK_TIMEOUT} "${url}" 2>/dev/null || echo "000")

    if [ "$RESPONSE" == "$expected_status" ]; then
        print_status "${service_name}" "healthy" "(HTTP ${RESPONSE})"
        return 0
    elif [ "$RESPONSE" == "000" ]; then
        print_status "${service_name}" "unreachable" ""
        return 1
    else
        print_status "${service_name}" "warning" "(HTTP ${RESPONSE}, expected ${expected_status})"
        return 1
    fi
}

check_database_connection() {
    local db_container=$1
    local db_name=$2
    local db_user=$3
    local service_name=$4

    # Try to connect to database
    if docker exec "${db_container}" pg_isready -U "${db_user}" -d "${db_name}" -q 2>/dev/null; then
        # Get connection count
        CONNECTIONS=$(docker exec "${db_container}" psql -U "${db_user}" -d "${db_name}" -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='${db_name}';" 2>/dev/null | xargs)

        print_status "${service_name}" "healthy" "(${CONNECTIONS} connections)"
        return 0
    else
        print_status "${service_name}" "unreachable" ""
        return 1
    fi
}

send_alert() {
    local message=$1

    if [ -n "$ALERT_WEBHOOK" ]; then
        curl -s -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"🚨 E2 Bot Health Alert: ${message}\"}" \
            >/dev/null 2>&1
    fi
}

# Start health checks
echo ""
echo -e "${YELLOW}🔍 Checking Docker Containers...${NC}"

check_docker_container "e2bot-traefik" "Traefik (Reverse Proxy)"
check_docker_container "e2bot-postgres" "PostgreSQL (Database)"
check_docker_container "e2bot-n8n" "n8n (Workflows)"
check_docker_container "e2bot-evolution" "Evolution API (WhatsApp)"
check_docker_container "e2bot-redis" "Redis (Cache)"

# Check optional monitoring services
if docker ps -a --filter "name=e2bot-prometheus" | grep -q "e2bot-prometheus"; then
    check_docker_container "e2bot-prometheus" "Prometheus (Monitoring)"
fi

if docker ps -a --filter "name=e2bot-grafana" | grep -q "e2bot-grafana"; then
    check_docker_container "e2bot-grafana" "Grafana (Dashboards)"
fi

# Check HTTP endpoints
echo ""
echo -e "${YELLOW}🌐 Checking HTTP Endpoints...${NC}"

# Traefik dashboard (might return 401 if auth required, which is normal)
check_http_endpoint "http://localhost:8080/api/version" "Traefik API" "200"

# n8n (returns 401 without auth, which is expected)
if [ -n "${N8N_SUBDOMAIN}" ] && [ -n "${DOMAIN}" ]; then
    check_http_endpoint "https://${N8N_SUBDOMAIN}.${DOMAIN}/" "n8n Interface" "401"
fi

# Evolution API
if [ -n "${EVOLUTION_API_URL}" ]; then
    check_http_endpoint "${EVOLUTION_API_URL}/manager/getStatus" "Evolution API" "200"
fi

# Check database connections
echo ""
echo -e "${YELLOW}💾 Checking Database Connections...${NC}"

if [ -n "${POSTGRES_DB}" ] && [ -n "${POSTGRES_USER}" ]; then
    check_database_connection "e2bot-postgres" "${POSTGRES_DB}" "${POSTGRES_USER}" "PostgreSQL Connection"
fi

# Check Redis
echo ""
echo -e "${YELLOW}🗄️  Checking Redis...${NC}"

if docker exec e2bot-redis redis-cli --raw incr ping 2>/dev/null | grep -q "PONG\|[0-9]"; then
    # Get memory usage
    MEMORY=$(docker exec e2bot-redis redis-cli INFO memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
    print_status "Redis Cache" "healthy" "(Memory: ${MEMORY})"
else
    print_status "Redis Cache" "unreachable" ""
fi

# Check disk space
echo ""
echo -e "${YELLOW}💿 Checking Disk Space...${NC}"

DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')

if [ "$DISK_USAGE" -lt 80 ]; then
    print_status "Disk Space" "healthy" "(${DISK_USAGE}% used)"
elif [ "$DISK_USAGE" -lt 90 ]; then
    print_status "Disk Space" "warning" "(${DISK_USAGE}% used)"
else
    print_status "Disk Space" "critical" "(${DISK_USAGE}% used)"
    CRITICAL_FAILURE=1
fi

# Check Docker volumes
echo ""
echo -e "${YELLOW}📦 Checking Docker Volumes...${NC}"

VOLUMES=("e2-solucoes-bot_postgres_data" "e2-solucoes-bot_n8n_data" "e2-solucoes-bot_evolution_data" "e2-solucoes-bot_redis_data")

for volume in "${VOLUMES[@]}"; do
    if docker volume inspect "$volume" >/dev/null 2>&1; then
        print_status "$(echo $volume | cut -d_ -f2-)" "exists" ""
    else
        print_status "$(echo $volume | cut -d_ -f2-)" "missing" ""
        CRITICAL_FAILURE=1
    fi
done

# System resources
echo ""
echo -e "${YELLOW}⚡ System Resources...${NC}"

# CPU usage
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
echo -e "  CPU Usage: ${CPU_USAGE}%"

# Memory usage
MEM_USAGE=$(free -m | awk 'NR==2{printf "%.0f%%", $3*100/$2 }')
echo -e "  Memory Usage: ${MEM_USAGE}"

# Docker stats summary
echo ""
echo -e "${YELLOW}🐋 Docker Container Stats:${NC}"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep "e2bot-" || echo "  Unable to fetch stats"

# Final summary
echo ""
if [ $CRITICAL_FAILURE -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║       ✅ All Systems Operational!                ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║       ⚠️  Critical Issues Detected!              ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════╝${NC}"

    # Send alert
    send_alert "Critical health check failures detected. Please investigate."

    exit 1
fi
