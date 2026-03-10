#!/bin/bash
# ============================================================================
# V43 PostgreSQL Database Recreation Script
# ============================================================================
# This script recreates the PostgreSQL container to initialize e2bot_dev
# database with the V43 schema (includes all 4 required columns)
# ============================================================================

echo "=========================================="
echo "V43 POSTGRESQL DATABASE RECREATION"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will destroy existing PostgreSQL data!"
echo "   All conversations, messages, and leads will be LOST."
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "❌ Operation cancelled by user"
    exit 0
fi

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "STEP 1: Stopping PostgreSQL Container"
echo "================================================"
echo ""

if docker ps | grep -q "e2bot-postgres-dev"; then
    echo "Stopping container..."
    docker stop e2bot-postgres-dev
    echo -e "${GREEN}✅${NC} Container stopped"
else
    echo -e "${YELLOW}ℹ️${NC}  Container not running"
fi
echo ""

echo "================================================"
echo "STEP 2: Removing PostgreSQL Container"
echo "================================================"
echo ""

if docker ps -a | grep -q "e2bot-postgres-dev"; then
    echo "Removing container..."
    docker rm e2bot-postgres-dev
    echo -e "${GREEN}✅${NC} Container removed"
else
    echo -e "${YELLOW}ℹ️${NC}  Container doesn't exist"
fi
echo ""

echo "================================================"
echo "STEP 3: Removing PostgreSQL Volume"
echo "================================================"
echo ""

if docker volume ls | grep -q "e2bot_postgres_dev_data"; then
    echo "Removing volume (this deletes all data)..."
    docker volume rm e2bot_postgres_dev_data
    echo -e "${GREEN}✅${NC} Volume removed"
else
    echo -e "${YELLOW}ℹ️${NC}  Volume doesn't exist"
fi
echo ""

echo "================================================"
echo "STEP 4: Starting PostgreSQL with V43 Schema"
echo "================================================"
echo ""

cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

echo "Starting PostgreSQL container with init scripts..."
docker-compose -f docker/docker-compose-dev.yml up -d postgres-dev

echo ""
echo "Waiting for PostgreSQL to initialize..."
echo "(This may take 10-30 seconds for first-time setup)"
echo ""

# Wait for container to be healthy
MAX_ATTEMPTS=30
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    if docker exec e2bot-postgres-dev pg_isready -U postgres -d e2bot_dev > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} PostgreSQL is ready!"
        break
    fi

    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: Waiting for PostgreSQL..."
    sleep 2
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    echo -e "${RED}❌${NC} PostgreSQL failed to start within expected time"
    echo ""
    echo "Check logs with:"
    echo "  docker logs e2bot-postgres-dev"
    exit 1
fi

echo ""
echo "================================================"
echo "STEP 5: Verifying Database and Schema"
echo "================================================"
echo ""

# Check if e2bot_dev database exists
echo "1. Checking if e2bot_dev database exists..."
DB_EXISTS=$(docker exec e2bot-postgres-dev psql -U postgres -t -c "SELECT 1 FROM pg_database WHERE datname='e2bot_dev';" | tr -d ' ')

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${GREEN}✅${NC} Database e2bot_dev exists"
else
    echo -e "${RED}❌${NC} Database e2bot_dev does not exist"
    exit 1
fi

echo ""
echo "2. Checking if conversations table exists..."
TABLE_EXISTS=$(docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'conversations';" | tr -d ' ')

if [ "$TABLE_EXISTS" = "1" ]; then
    echo -e "${GREEN}✅${NC} Table conversations exists"
else
    echo -e "${RED}❌${NC} Table conversations does not exist"
    exit 1
fi

echo ""
echo "3. Verifying V43 columns (service_id, contact_name, contact_email, city)..."
COLUMN_COUNT=$(docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -t -c "
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_name = 'conversations'
    AND column_name IN ('service_id', 'contact_name', 'contact_email', 'city');
" | tr -d ' ')

if [ "$COLUMN_COUNT" = "4" ]; then
    echo -e "${GREEN}✅${NC} All 4 V43 columns verified"
else
    echo -e "${RED}❌${NC} Only $COLUMN_COUNT/4 columns found"
    exit 1
fi

echo ""
echo "4. Showing conversations table structure..."
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\d conversations"

echo ""
echo "=========================================="
echo "V43 DATABASE RECREATION COMPLETE"
echo "=========================================="
echo ""
echo -e "${GREEN}✅${NC} Database e2bot_dev created with V43 schema"
echo -e "${GREEN}✅${NC} All 4 columns present: service_id, contact_name, contact_email, city"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. No migration needed - V43 schema already applied"
echo "2. Start n8n: docker-compose -f docker/docker-compose-dev.yml up -d n8n-dev"
echo "3. Activate V41 workflow in n8n interface"
echo "4. Test complete conversation flow"
echo ""
echo "✅ V43 Setup Complete - Ready for Testing!"
echo ""
