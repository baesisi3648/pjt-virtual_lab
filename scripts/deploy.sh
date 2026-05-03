#!/bin/bash
# Production Deployment Script
# Usage: ./scripts/deploy.sh

set -e

echo "============================================================"
echo "Virtual Lab Production Deployment"
echo "============================================================"
echo ""

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "ERROR: .env.production not found"
    echo "Please copy .env.production.example to .env.production and configure it"
    echo ""
    echo "  cp .env.production.example .env.production"
    echo "  nano .env.production  # Edit and set OPENAI_API_KEY"
    echo ""
    exit 1
fi

# Validate environment
echo "[Step 1/5] Validating environment variables..."
export $(cat .env.production | xargs)
python scripts/validate_env.py
if [ $? -ne 0 ]; then
    echo "ERROR: Environment validation failed"
    exit 1
fi
echo ""

# Check Docker
echo "[Step 2/5] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not found. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "ERROR: Docker daemon is not running"
    exit 1
fi
echo "Docker is running"
echo ""

# Check Docker Compose
echo "[Step 3/5] Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose not found. Please install Docker Compose first."
    exit 1
fi
echo "Docker Compose is available"
echo ""

# Build and start services
echo "[Step 4/5] Building and starting services..."
echo "This may take several minutes on first run..."
docker-compose -f docker-compose.prod.yml up -d --build

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start services"
    exit 1
fi
echo ""

# Wait for services to be healthy
echo "[Step 5/5] Waiting for services to be healthy..."
echo "This may take 1-2 minutes..."
sleep 10

max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))

    # Check if all services are healthy
    healthy_count=$(docker-compose -f docker-compose.prod.yml ps | grep "Up (healthy)" | wc -l)
    total_services=6  # postgres, chromadb, redis, backend, frontend, nginx

    echo "  Attempt $attempt/$max_attempts: $healthy_count/$total_services services healthy"

    if [ $healthy_count -eq $total_services ]; then
        echo ""
        echo "============================================================"
        echo "Deployment Successful!"
        echo "============================================================"
        echo ""
        echo "Services are running:"
        docker-compose -f docker-compose.prod.yml ps
        echo ""
        echo "Access URLs:"
        echo "  - Frontend:  http://localhost"
        echo "  - Backend:   http://localhost/api/health"
        echo "  - Nginx:     http://localhost/health"
        echo ""
        echo "To view logs:"
        echo "  docker-compose -f docker-compose.prod.yml logs -f"
        echo ""
        echo "To stop services:"
        echo "  docker-compose -f docker-compose.prod.yml down"
        echo ""
        exit 0
    fi

    sleep 10
done

echo ""
echo "WARNING: Some services are not healthy after $max_attempts attempts"
echo "Current status:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "Check logs for details:"
echo "  docker-compose -f docker-compose.prod.yml logs"
exit 1
