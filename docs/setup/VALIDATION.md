# Phase 0 - Setup Validation

## Task: P0-T1 - PostgreSQL + ChromaDB + Redis Container Environment

### Files Created

1. **docker-compose.yml** - Container orchestration configuration
   - PostgreSQL 16-alpine (port 5432)
   - ChromaDB latest (port 8001)
   - Redis 7-alpine (port 6379)
   - Volume management (postgres_data, chroma_data, redis_data)
   - Health checks for all services
   - Bridge network (virtual-lab-network)

2. **init.sql** - Database initialization script
   - UUID extension enabled
   - `sessions` table with UUID primary key
   - `reports` table with foreign key to sessions
   - Indexes for performance optimization
   - Auto-update trigger for `updated_at` column

3. **scripts/healthcheck.sh** - Bash health check script
   - Container status verification
   - Service connectivity testing
   - Color-coded output (GREEN/YELLOW/RED)

4. **scripts/healthcheck.py** - Python health check script
   - Alternative to bash script for cross-platform compatibility
   - Uses requests library for HTTP checks
   - Returns appropriate exit codes

5. **DOCKER_SETUP.md** - Comprehensive setup documentation
   - Quick start guide
   - Database schema reference
   - Service details
   - Manual testing commands
   - Troubleshooting guide

## Validation Commands

### Step 1: Start Services
```bash
cd C:/Users/배성우/Desktop/pjt-virtual_lab/worktree/phase-0-setup
docker compose up -d
```

### Step 2: Check Container Status
```bash
docker compose ps
```

Expected output:
```
NAME                     IMAGE                    STATUS
virtual-lab-postgres     postgres:16-alpine       Up (healthy)
virtual-lab-chromadb     chromadb/chroma:latest   Up (healthy)
virtual-lab-redis        redis:7-alpine           Up (healthy)
```

### Step 3: Run Health Check
```bash
# Option A: Bash script
./scripts/healthcheck.sh

# Option B: Python script (requires requests library)
python scripts/healthcheck.py
```

### Step 4: Manual Service Verification

#### PostgreSQL
```bash
docker exec -it virtual-lab-postgres psql -U postgres -d virtual_lab -c "\dt"
```

Expected: Lists `sessions` and `reports` tables

#### ChromaDB
```bash
curl http://localhost:8001/api/v1/heartbeat
```

Expected: Returns heartbeat response

#### Redis
```bash
docker exec -it virtual-lab-redis redis-cli ping
```

Expected: Returns `PONG`

## Success Criteria

- [ ] All 3 containers start successfully
- [ ] All 3 containers show "healthy" status within 30 seconds
- [ ] PostgreSQL accepts connections and has initialized tables
- [ ] ChromaDB API responds to heartbeat requests
- [ ] Redis responds to ping commands
- [ ] Health check scripts execute without errors

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│           virtual-lab-network (bridge)          │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────┐  ┌─────────────────┐      │
│  │   PostgreSQL    │  │    ChromaDB     │      │
│  │  (postgres:16)  │  │   (chroma:0.x)  │      │
│  │   Port: 5432    │  │   Port: 8001    │      │
│  │                 │  │                 │      │
│  │  - sessions     │  │  - Vector Store │      │
│  │  - reports      │  │  - Embeddings   │      │
│  └─────────────────┘  └─────────────────┘      │
│                                                 │
│  ┌─────────────────┐                            │
│  │      Redis      │                            │
│  │   (redis:7)     │                            │
│  │   Port: 6379    │                            │
│  │                 │                            │
│  │  - Celery Queue │                            │
│  │  - Cache        │                            │
│  └─────────────────┘                            │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Notes

- Docker must be installed and running
- Ports 5432, 6379, and 8001 must be available
- Windows users: Use Git Bash or WSL for bash scripts
- Python healthcheck requires: `pip install requests`
- All services use persistence (volumes)
- Default credentials are for development only

## Troubleshooting

### Issue: Port Already in Use
```bash
# Windows: Check port usage
netstat -ano | findstr :5432

# Solution: Stop conflicting service or modify ports in docker-compose.yml
```

### Issue: Containers Not Starting
```bash
# Check logs
docker compose logs postgres
docker compose logs chromadb
docker compose logs redis

# Restart services
docker compose restart
```

### Issue: Health Check Failing
```bash
# Wait for services to initialize (can take 30-60 seconds)
docker compose ps

# Check specific service logs
docker compose logs -f postgres
```

## Next Steps (Phase 1+)

After successful validation:
1. Create Phase 1 worktree for infrastructure code
2. Implement database connection utilities
3. Implement ChromaDB client wrapper
4. Implement Redis client for Celery
5. Write integration tests
