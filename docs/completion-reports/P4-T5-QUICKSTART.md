# P4-T5 Quickstart: Production Deployment

## 5-Minute Production Deploy

### Prerequisites
- Docker Desktop installed and running
- OpenAI API key

### Step 1: Setup Environment (30 seconds)
```bash
cd worktree/phase-4-nextjs

# Copy environment template
cp .env.production.example .env.production

# Edit and add your API key
# Windows: notepad .env.production
# Linux/Mac: nano .env.production
```

Set this in `.env.production`:
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### Step 2: Validate Environment (15 seconds)
```bash
python scripts/validate_env.py
```

Expected output:
```
============================================================
VALIDATION PASSED
============================================================
```

### Step 3: Deploy (3-5 minutes)
```bash
# Linux/Mac
./scripts/deploy.sh

# Windows
scripts\deploy.bat
```

### Step 4: Verify (30 seconds)
```bash
# Test nginx
curl http://localhost/health

# Test backend
curl http://localhost/api/health

# Open in browser
# http://localhost
```

## What You Get

```
┌─────────────────────────────────────────┐
│         http://localhost                │
│              (Nginx)                    │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
  Frontend          Backend
  (Next.js)        (FastAPI)
  Port 3000        Port 8000
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
     PostgreSQL    ChromaDB      Redis
     Port 5432     Port 8000   Port 6379
```

## Access URLs
- **Frontend**: http://localhost
- **Backend API**: http://localhost/api
- **Health Check**: http://localhost/health

## Common Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Check Status
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Stop Services
```bash
# Stop (keeps data)
docker-compose -f docker-compose.prod.yml down

# Stop and remove all data
docker-compose -f docker-compose.prod.yml down -v
```

### Restart After Code Changes
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

## Troubleshooting

### Issue: Port 80 already in use
**Solution**: Stop other services using port 80
```bash
# Windows
netstat -ano | findstr :80
taskkill /PID <pid> /F

# Linux/Mac
sudo lsof -i :80
sudo kill <pid>
```

### Issue: Docker not running
**Solution**: Start Docker Desktop

### Issue: Environment validation fails
**Solution**: Check `.env.production` file
- Ensure `OPENAI_API_KEY` is set
- Ensure it starts with `sk-`
- No quotes around values

### Issue: Services not healthy
**Solution**: Check logs
```bash
docker-compose -f docker-compose.prod.yml logs backend
```

## What's Running?

After successful deployment, you should see:

```
NAME                          STATUS
virtual-lab-nginx-prod        Up (healthy)
virtual-lab-frontend-prod     Up (healthy)
virtual-lab-backend-prod      Up (healthy)
virtual-lab-postgres-prod     Up (healthy)
virtual-lab-chromadb-prod     Up (healthy)
virtual-lab-redis-prod        Up (healthy)
```

## Testing the Deployment

### 1. Start a Research Session
Open http://localhost in your browser and:
1. Enter a research question
2. Click "Start Research"
3. Watch real-time progress in timeline
4. View final report

### 2. Test API Directly
```bash
# Health check
curl http://localhost/api/health

# Start session (example)
curl -X POST http://localhost/api/research/start \
  -H "Content-Type: application/json" \
  -d '{"query": "Test query"}'
```

## Next Steps

1. Review logs to ensure everything is working
2. Test with a real research query
3. Monitor resource usage
4. Read full documentation in `PRODUCTION_DEPLOYMENT.md`

## Security Note

For production use:
1. Change `POSTGRES_PASSWORD` in `.env.production`
2. Never commit `.env.production` to git
3. Use strong passwords (16+ characters)
4. Consider adding HTTPS (see PRODUCTION_DEPLOYMENT.md)

## Quick Reference

| Task | Command |
|------|---------|
| Start | `./scripts/deploy.sh` |
| Stop | `docker-compose -f docker-compose.prod.yml down` |
| Logs | `docker-compose -f docker-compose.prod.yml logs -f` |
| Status | `docker-compose -f docker-compose.prod.yml ps` |
| Rebuild | `docker-compose -f docker-compose.prod.yml up -d --build` |

---

**Total Time**: ~5 minutes
**Difficulty**: Easy
**Status**: Production Ready
