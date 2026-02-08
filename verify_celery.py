"""Simple Celery Setup Verification (ASCII only)"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Celery Setup Verification (P0-T5)")
print("=" * 60)
print()

# Test 1: Import celery_app
print("[1] Testing celery_app import...")
try:
    from celery_app import app
    print("    [OK] celery_app imported successfully")
    print(f"    Broker: {app.conf.broker_url}")
    print(f"    Backend: {app.conf.result_backend}")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

print()

# Test 2: Import tasks
print("[2] Testing tasks import...")
try:
    from tasks.research_task import run_research, health_check
    print("    [OK] tasks.research_task imported successfully")
    print(f"    run_research: {run_research.name}")
    print(f"    health_check: {health_check.name}")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

print()

# Test 3: Check registered tasks
print("[3] Checking registered tasks...")
try:
    registered = list(app.tasks.keys())
    user_tasks = [t for t in registered if t.startswith('tasks.')]
    print(f"    [OK] {len(user_tasks)} user tasks registered:")
    for task in user_tasks:
        print(f"         - {task}")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

print()

# Test 4: Check server integration
print("[4] Checking server.py integration...")
try:
    from server import app as fastapi_app
    from server import AsyncResearchRequest, TaskStatusResponse

    routes = [route.path for route in fastapi_app.routes]
    async_routes = [r for r in routes if 'async' in r or 'task' in r or 'celery' in r]

    print(f"    [OK] server.py imported successfully")
    print(f"    Async/Celery routes: {len(async_routes)}")
    for route in async_routes:
        print(f"         - {route}")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

print()

# Test 5: File structure
print("[5] Checking file structure...")
files = [
    'celery_app.py',
    'tasks/__init__.py',
    'tasks/research_task.py',
    'scripts/start_worker.sh',
    'scripts/start_worker.bat',
]

all_ok = True
for f in files:
    path = os.path.join(os.path.dirname(__file__), f)
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"    [OK] {f} ({size} bytes)")
    else:
        print(f"    [FAIL] {f} not found")
        all_ok = False

print()
print("=" * 60)
if all_ok:
    print("SUCCESS: All checks passed!")
    print()
    print("Next steps:")
    print("1. Start Redis: docker compose up -d redis")
    print("2. Start Celery Worker: python scripts/start_worker.bat")
    print("3. Start FastAPI: uvicorn server:app --reload")
    print("4. Test async API: POST /api/research/async")
else:
    print("FAILED: Some checks failed")
    sys.exit(1)
