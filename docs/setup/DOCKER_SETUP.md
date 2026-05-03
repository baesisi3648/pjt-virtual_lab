# Docker Container Setup Guide

## Overview
This setup provides the infrastructure for the Virtual Lab MVP:
- **PostgreSQL**: Session history storage
- **ChromaDB**: Vector store for embeddings (port 8001)
- **Redis**: Celery backend for async tasks

## Quick Start

### 1. Start All Services
```bash
cd worktree/phase-0-setup
docker-compose up -d
```

### 2. Check Health Status
```bash
# Using bash script
./scripts/healthcheck.sh

# OR using Python script
python scripts/healthcheck.py

# OR using docker-compose
docker-compose ps
```

Expected output:
```
NAME                     IMAGE                    STATUS
virtual-lab-postgres     postgres:16-alpine       Up (healthy)
virtual-lab-chromadb     chromadb/chroma:latest   Up (healthy)
virtual-lab-redis        redis:7-alpine           Up (healthy)
```

### 3. Stop Services
```bash
docker-compose down
```

### 4. Stop and Remove Volumes
```bash
docker-compose down -v
```

## Database Schema

### Sessions Table
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_query TEXT NOT NULL,
    final_report TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Reports Table
```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    agent_name VARCHAR(100) NOT NULL,
    agent_output TEXT,
    iteration INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE
);
```

## Service Details

### PostgreSQL
- **Port**: 5432
- **Database**: virtual_lab
- **User**: postgres
- **Password**: postgres (change in production!)
- **Volume**: postgres_data

### ChromaDB
- **Port**: 8001 (mapped from internal 8000)
- **API Endpoint**: http://localhost:8001/api/v1/
- **Heartbeat**: http://localhost:8001/api/v1/heartbeat
- **Volume**: chroma_data
- **Persistence**: Enabled

### Redis
- **Port**: 6379
- **Volume**: redis_data
- **Persistence**: AOF enabled

## Manual Testing

### Test PostgreSQL Connection
```bash
docker exec -it virtual-lab-postgres psql -U postgres -d virtual_lab

# Inside psql
\dt                    # List tables
SELECT * FROM sessions;
\q                     # Quit
```

### Test ChromaDB API
```bash
curl http://localhost:8001/api/v1/heartbeat
```

### Test Redis Connection
```bash
docker exec -it virtual-lab-redis redis-cli

# Inside redis-cli
ping                   # Should return PONG
keys *
exit
```

## Troubleshooting

### Containers Not Starting
```bash
# Check logs
docker-compose logs postgres
docker-compose logs chromadb
docker-compose logs redis

# Restart services
docker-compose restart
```

### Port Already in Use
```bash
# Check what's using the port
netstat -ano | findstr :5432  # Windows
lsof -i :5432                  # Linux/Mac

# Modify docker-compose.yml to use different ports
```

### Database Initialization Issues
```bash
# Remove volumes and restart
docker-compose down -v
docker-compose up -d

# Check init.sql execution
docker-compose logs postgres | grep init.sql
```

## Network Configuration
All services are connected via the `virtual-lab-network` bridge network, allowing inter-container communication using service names:
- PostgreSQL: `postgres:5432`
- ChromaDB: `chromadb:8000`
- Redis: `redis:6379`

## Security Notes
- Default credentials are used for development only
- Change passwords in production environment
- Use Docker secrets or environment variables for sensitive data
- Enable SSL/TLS for production deployments
