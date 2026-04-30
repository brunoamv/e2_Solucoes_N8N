#!/bin/bash

# ============================================================================
# E2 Soluções Bot - Production Startup Script
# ============================================================================
# Inicia ambiente de produção com validações de segurança
# Usage: ./start-prod.sh
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root is not recommended"
        print_warning "Consider running as a regular user with docker group permissions"
        read -p "Continue anyway? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            exit 1
        fi
    fi
}

# Function to validate environment file
validate_env() {
    print_info "Validating production environment configuration..."

    local env_file="${PROJECT_ROOT}/docker/.env"

    if [ ! -f "$env_file" ]; then
        print_error "Production .env file not found: $env_file"
        print_info "Please copy and configure: cp docker/.env.example docker/.env"
        exit 1
    fi

    # Source environment
    source "$env_file"

    # Check critical variables
    local missing_vars=()

    # Domain and SSL
    [ -z "$DOMAIN" ] && missing_vars+=("DOMAIN")
    [ -z "$TRAEFIK_ACME_EMAIL" ] && missing_vars+=("TRAEFIK_ACME_EMAIL")

    # n8n
    [ -z "$N8N_BASIC_AUTH_USER" ] && missing_vars+=("N8N_BASIC_AUTH_USER")
    [ -z "$N8N_BASIC_AUTH_PASSWORD" ] && missing_vars+=("N8N_BASIC_AUTH_PASSWORD")
    [ -z "$N8N_ENCRYPTION_KEY" ] && missing_vars+=("N8N_ENCRYPTION_KEY")

    # Database
    [ -z "$POSTGRES_PASSWORD" ] && missing_vars+=("POSTGRES_PASSWORD")
    [ -z "$POSTGRES_NON_ROOT_PASSWORD" ] && missing_vars+=("POSTGRES_NON_ROOT_PASSWORD")

    # Supabase
    [ -z "$SUPABASE_DB_PASSWORD" ] && missing_vars+=("SUPABASE_DB_PASSWORD")
    [ -z "$SUPABASE_JWT_SECRET" ] && missing_vars+=("SUPABASE_JWT_SECRET")
    [ -z "$SUPABASE_ANON_KEY" ] && missing_vars+=("SUPABASE_ANON_KEY")
    [ -z "$SUPABASE_SERVICE_ROLE_KEY" ] && missing_vars+=("SUPABASE_SERVICE_ROLE_KEY")

    # Redis
    [ -z "$REDIS_PASSWORD" ] && missing_vars+=("REDIS_PASSWORD")

    # APIs
    [ -z "$ANTHROPIC_API_KEY" ] && missing_vars+=("ANTHROPIC_API_KEY")
    [ -z "$EVOLUTION_API_KEY" ] && missing_vars+=("EVOLUTION_API_KEY")
    [ -z "$RDSTATION_CLIENT_ID" ] && missing_vars+=("RDSTATION_CLIENT_ID")
    [ -z "$RDSTATION_CLIENT_SECRET" ] && missing_vars+=("RDSTATION_CLIENT_SECRET")

    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi

    # Check for example/default values
    if [[ "$POSTGRES_PASSWORD" == *"GERAR_SENHA"* ]] || \
       [[ "$N8N_BASIC_AUTH_PASSWORD" == *"GERAR_SENHA"* ]] || \
       [[ "$N8N_ENCRYPTION_KEY" == *"GERAR_CHAVE"* ]]; then
        print_error "Detected placeholder values in .env file"
        print_info "Please generate real passwords and keys"
        exit 1
    fi

    print_success "Environment configuration valid"
}

# Function to check DNS configuration
check_dns() {
    print_info "Checking DNS configuration..."

    source "${PROJECT_ROOT}/docker/.env"

    local n8n_domain="${N8N_SUBDOMAIN}.${DOMAIN}"
    local supabase_domain="${SUPABASE_SUBDOMAIN}.${DOMAIN}"

    print_info "Checking: $n8n_domain"
    if ! nslookup "$n8n_domain" > /dev/null 2>&1; then
        print_warning "DNS not configured for $n8n_domain"
        print_info "Please configure DNS A record pointing to this server's IP"
        read -p "Continue anyway? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            exit 1
        fi
    else
        print_success "DNS configured for $n8n_domain"
    fi
}

# Function to check Docker and Docker Compose
check_docker() {
    print_info "Checking Docker installation..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        print_info "Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker ps &> /dev/null; then
        print_error "Docker daemon is not running or no permissions"
        print_info "Start Docker service or add user to docker group"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        print_info "Install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi

    print_success "Docker is ready"
}

# Function to create required directories
create_directories() {
    print_info "Creating required directories..."

    local dirs=(
        "${PROJECT_ROOT}/backups"
        "${PROJECT_ROOT}/docker/configs/traefik/acme"
        "${PROJECT_ROOT}/logs"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done

    # Set permissions for Traefik acme
    chmod 600 "${PROJECT_ROOT}/docker/configs/traefik/acme" 2>/dev/null || true

    print_success "Directories created"
}

# Function to start production stack
start_production() {
    print_info "Starting production stack..."

    cd "${PROJECT_ROOT}/docker"

    # Pull latest images
    print_info "Pulling latest images..."
    docker-compose -f docker-compose.yml pull

    # Start services
    print_info "Starting services..."
    docker-compose -f docker-compose.yml up -d

    # Wait for services to be healthy
    print_info "Waiting for services to be healthy..."
    sleep 10

    # Check health
    print_info "Checking service health..."
    docker-compose -f docker-compose.yml ps

    print_success "Production stack started!"
}

# Function to display access information
display_info() {
    source "${PROJECT_ROOT}/docker/.env"

    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║          E2 Soluções Bot - Production Running                 ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🌐 Access URLs:"
    echo "   n8n:      https://${N8N_SUBDOMAIN}.${DOMAIN}"
    echo "   Supabase: https://${SUPABASE_SUBDOMAIN}.${DOMAIN}"
    echo ""
    echo "🔐 Credentials:"
    echo "   n8n User: ${N8N_BASIC_AUTH_USER}"
    echo "   n8n Pass: ${N8N_BASIC_AUTH_PASSWORD}"
    echo ""
    echo "📊 Monitoring:"
    echo "   Logs:   ./scripts/logs.sh"
    echo "   Health: ./scripts/health-check.sh"
    echo ""
    echo "🛑 Stop:"
    echo "   ./scripts/stop.sh"
    echo ""
    print_warning "Initial SSL certificate provisioning may take a few minutes"
    print_info "Monitor Traefik logs: docker logs -f e2-traefik"
}

# Function to run post-startup checks
post_startup_checks() {
    print_info "Running post-startup health checks..."

    sleep 15

    "${SCRIPT_DIR}/health-check.sh" --quick

    if [ $? -eq 0 ]; then
        print_success "All health checks passed"
    else
        print_warning "Some health checks failed - check logs"
    fi
}

# Main execution
main() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     E2 Soluções Bot - Production Environment Startup          ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    check_root
    check_docker
    validate_env
    check_dns
    create_directories

    print_warning "Starting PRODUCTION environment"
    print_warning "This will expose services to the internet with SSL"
    echo ""
    read -p "Continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_info "Startup cancelled"
        exit 0
    fi

    start_production
    post_startup_checks
    display_info
}

main "$@"
