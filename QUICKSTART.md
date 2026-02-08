# Quick Start - Container Setup

## Prerequisites
- Docker installed and running
- Ports 5432, 6379, 8001 available

## Commands

### Start Services
```bash
cd C:/Users/배성우/Desktop/pjt-virtual_lab/worktree/phase-0-setup
docker compose up -d
```

### Check Status
```bash
# Quick check
docker compose ps

# Detailed health check (Bash)
./scripts/healthcheck.sh

# Detailed health check (Python)
python scripts/healthcheck.py
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f postgres
docker compose logs -f chromadb
docker compose logs -f redis
```

### Stop Services
```bash
# Stop (keep data)
docker compose down

# Stop and remove all data
docker compose down -v
```

## Verification Checklist

- [ ] All 3 containers running
- [ ] All 3 containers healthy
- [ ] PostgreSQL has `sessions` and `reports` tables
- [ ] ChromaDB API responds at http://localhost:8001/api/v1/heartbeat
- [ ] Redis responds to ping

## Quick Tests

### Test PostgreSQL
```bash
docker exec -it virtual-lab-postgres psql -U postgres -d virtual_lab -c "\dt"
```

### Test ChromaDB
```bash
curl http://localhost:8001/api/v1/heartbeat
```

### Test Redis
```bash
docker exec -it virtual-lab-redis redis-cli ping
```

## Service URLs

| Service    | URL                                      | Credentials        |
|------------|------------------------------------------|--------------------|
| PostgreSQL | localhost:5432                           | postgres/postgres  |
| ChromaDB   | http://localhost:8001/api/v1/            | None               |
| Redis      | localhost:6379                           | None               |

## Troubleshooting

### Containers not starting?
```bash
docker compose logs
```

### Port conflicts?
```bash
netstat -ano | findstr :5432
```

### Need to reset everything?
```bash
docker compose down -v
docker compose up -d
```

## Next Steps

After all services are healthy:
1. Move to Phase 1 worktree
2. Implement database connection utilities
3. Implement ChromaDB client wrapper
4. Set up Celery with Redis backend
