#!/bin/bash

# Virtual Lab Container Health Check Script
# Usage: ./scripts/healthcheck.sh

set -e

echo "==================================="
echo "Virtual Lab Health Check"
echo "==================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check container health
check_container() {
    local container_name=$1
    local service_name=$2

    if docker ps --filter "name=${container_name}" --filter "health=healthy" | grep -q "${container_name}"; then
        echo -e "${service_name}: ${GREEN}HEALTHY${NC}"
        return 0
    elif docker ps --filter "name=${container_name}" | grep -q "${container_name}"; then
        echo -e "${service_name}: ${YELLOW}STARTING${NC}"
        return 1
    else
        echo -e "${service_name}: ${RED}NOT RUNNING${NC}"
        return 2
    fi
}

# Function to check service connectivity
check_postgres() {
    if docker exec virtual-lab-postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "PostgreSQL Connection: ${GREEN}OK${NC}"
        return 0
    else
        echo -e "PostgreSQL Connection: ${RED}FAILED${NC}"
        return 1
    fi
}

check_chromadb() {
    if curl -sf http://localhost:8001/api/v1/heartbeat > /dev/null 2>&1; then
        echo -e "ChromaDB API: ${GREEN}OK${NC}"
        return 0
    else
        echo -e "ChromaDB API: ${RED}FAILED${NC}"
        return 1
    fi
}

check_redis() {
    if docker exec virtual-lab-redis redis-cli ping | grep -q "PONG"; then
        echo -e "Redis Connection: ${GREEN}OK${NC}"
        return 0
    else
        echo -e "Redis Connection: ${RED}FAILED${NC}"
        return 1
    fi
}

# Main health check
echo "Checking container status..."
echo ""

check_container "virtual-lab-postgres" "PostgreSQL"
postgres_status=$?

check_container "virtual-lab-chromadb" "ChromaDB"
chromadb_status=$?

check_container "virtual-lab-redis" "Redis"
redis_status=$?

echo ""
echo "Checking service connectivity..."
echo ""

# Only check connectivity if containers are running
if [ $postgres_status -eq 0 ]; then
    check_postgres
fi

if [ $chromadb_status -eq 0 ]; then
    check_chromadb
fi

if [ $redis_status -eq 0 ]; then
    check_redis
fi

echo ""
echo "==================================="

# Exit with error if any container is not healthy
if [ $postgres_status -eq 0 ] && [ $chromadb_status -eq 0 ] && [ $redis_status -eq 0 ]; then
    echo -e "${GREEN}All services are healthy!${NC}"
    exit 0
else
    echo -e "${RED}Some services are not ready yet.${NC}"
    exit 1
fi
