# Production Deployment Guide

## Overview
Complete production deployment setup using Docker Compose with:
- Frontend: Next.js (optimized production build)
- Backend: FastAPI
- Database: PostgreSQL
- Vector Store: ChromaDB
- Cache: Redis
- Reverse Proxy: Nginx

## Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- OpenAI API Key

## Quick Start

### 1. Environment Setup

Copy the example environment file:
```bash
cp .env.production.example .env.production
```

Edit `.env.production` and set required variables:
```bash
# Required
OPENAI_API_KEY=sk-your-actual-api-key

# Database (change password!)
POSTGRES_PASSWORD=your-secure-password
```

### 2. Validate Environment

Run the validation script to ensure all required variables are set:
```bash
python scripts/validate_env.py
```

Expected output:
```
============================================================
Environment Variable Validation
============================================================

[Required Variables]
  OPENAI_API_KEY: sk-proj...
  POSTGRES_DB: virtual_lab
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: ********

[Optional Variables]
  REDIS_URL: not set (will use default)
  CHROMA_HOST: not set (will use default)
  ...

[Validation Checks]
  OPENAI_API_KEY format: OK
  POSTGRES_PASSWORD strength: OK

============================================================
VALIDATION PASSED
============================================================
```

### 3. Build and Start Services

Load environment and start all services:
```bash
# Load environment variables
export $(cat .env.production | xargs)

# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build
```

### 4. Verify Deployment

Check service health:
```bash
docker-compose -f docker-compose.prod.yml ps
```

All services should show `Up (healthy)` status:
```
NAME                          STATUS
virtual-lab-nginx-prod        Up (healthy)
virtual-lab-frontend-prod     Up (healthy)
virtual-lab-backend-prod      Up (healthy)
virtual-lab-postgres-prod     Up (healthy)
virtual-lab-chromadb-prod     Up (healthy)
virtual-lab-redis-prod        Up (healthy)
```

### 5. Access Application

- Frontend: http://localhost
- Backend API: http://localhost/api/health
- Nginx Health: http://localhost/health

Test the endpoints:
```bash
# Test nginx health
curl http://localhost/health

# Test backend health
curl http://localhost/api/health

# Test frontend
curl http://localhost
```

## Service Architecture

```
Internet
    |
    v
[Nginx :80] (Reverse Proxy)
    |
    +---> [Frontend :3000] (Next.js)
    |
    +---> [Backend :8000] (FastAPI)
              |
              +---> [PostgreSQL :5432]
              |
              +---> [ChromaDB :8000]
              |
              +---> [Redis :6379]
```

## Management Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Restart Services
```bash
# All services
docker-compose -f docker-compose.prod.yml restart

# Specific service
docker-compose -f docker-compose.prod.yml restart backend
```

### Stop Services
```bash
# Stop without removing containers
docker-compose -f docker-compose.prod.yml stop

# Stop and remove containers (keeps data)
docker-compose -f docker-compose.prod.yml down

# Stop and remove everything including volumes
docker-compose -f docker-compose.prod.yml down -v
```

### Update Application
```bash
# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Rebuild specific service
docker-compose -f docker-compose.prod.yml up -d --build backend
```

## Scaling

### Scale Backend Workers
```bash
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

## Troubleshooting

### Container Not Starting

1. Check logs:
```bash
docker-compose -f docker-compose.prod.yml logs service-name
```

2. Check health:
```bash
docker inspect virtual-lab-backend-prod | grep -A 10 Health
```

### Database Connection Issues

Check database connectivity:
```bash
docker exec -it virtual-lab-postgres-prod psql -U postgres -d virtual_lab -c "SELECT 1"
```

### Frontend Build Issues

Rebuild frontend with verbose output:
```bash
docker-compose -f docker-compose.prod.yml build --no-cache frontend
```

### Nginx 502 Bad Gateway

Check backend health:
```bash
docker-compose -f docker-compose.prod.yml exec backend curl http://localhost:8000/api/health
```

### Clear All Data and Restart

```bash
# Stop everything
docker-compose -f docker-compose.prod.yml down -v

# Remove all images
docker-compose -f docker-compose.prod.yml down --rmi all

# Rebuild and start
docker-compose -f docker-compose.prod.yml up -d --build
```

## Security Considerations

### Production Checklist

- [ ] Change default PostgreSQL password
- [ ] Use strong passwords (minimum 16 characters)
- [ ] Set `ENVIRONMENT=production` in .env
- [ ] Never commit `.env.production` to git
- [ ] Enable SSL/TLS for public deployments
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Enable Docker security scanning
- [ ] Use secrets management (e.g., Docker secrets)
- [ ] Regular backup of PostgreSQL data
- [ ] Regular backup of ChromaDB vectors

### Enable HTTPS (Optional)

For production deployments with SSL:

1. Update `nginx/nginx.conf` to listen on port 443
2. Mount SSL certificates in docker-compose.prod.yml
3. Configure SSL directives in nginx

## Backup and Restore

### Backup Database
```bash
docker exec virtual-lab-postgres-prod pg_dump -U postgres virtual_lab > backup.sql
```

### Restore Database
```bash
cat backup.sql | docker exec -i virtual-lab-postgres-prod psql -U postgres -d virtual_lab
```

### Backup Volumes
```bash
docker run --rm -v virtual-lab-postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz /data
```

## Monitoring

### Health Check Endpoints

- Nginx: http://localhost/health
- Backend: http://localhost/api/health
- ChromaDB: http://localhost:8001/api/v1/heartbeat (internal)

### Container Stats
```bash
docker stats
```

### Resource Usage
```bash
docker system df
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `POSTGRES_DB` | Yes | `virtual_lab` | Database name |
| `POSTGRES_USER` | Yes | `postgres` | Database user |
| `POSTGRES_PASSWORD` | Yes | - | Database password |
| `DATABASE_URL` | No | Auto-generated | Full connection URL |
| `REDIS_URL` | No | `redis://redis:6379/0` | Redis connection |
| `CHROMA_HOST` | No | `chromadb` | ChromaDB host |
| `CHROMA_PORT` | No | `8000` | ChromaDB port |
| `ENVIRONMENT` | No | `production` | Environment name |

## Performance Tuning

### PostgreSQL
Edit `docker-compose.prod.yml` to add:
```yaml
postgres:
  command:
    - "postgres"
    - "-c"
    - "shared_buffers=256MB"
    - "-c"
    - "max_connections=200"
```

### Nginx
Edit `nginx/nginx.conf` to adjust worker connections:
```nginx
events {
    worker_connections 4096;
}
```

### Backend
Increase uvicorn workers:
```yaml
backend:
  command: uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

## License
MIT
