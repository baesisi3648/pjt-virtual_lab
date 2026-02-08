#!/bin/bash
# Celery Worker Startup Script (Linux/Mac)

set -e

echo "========================================="
echo "  Virtual Lab - Celery Worker Startup"
echo "========================================="
echo ""

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "ERROR: Redis is not running!"
    echo "Please start Redis first:"
    echo "  docker-compose up -d redis"
    exit 1
fi

echo "✓ Redis connection verified"
echo ""

# Start Celery worker
echo "Starting Celery worker..."
echo "Press Ctrl+C to stop"
echo ""

celery -A celery_app worker \
    --loglevel=info \
    --pool=solo \
    --concurrency=1 \
    --max-tasks-per-child=50 \
    --task-events \
    --without-gossip \
    --without-mingle \
    --without-heartbeat
