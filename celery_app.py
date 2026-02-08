"""
Celery Application Configuration
- Broker/Backend: Redis
- Task Module: tasks.research_task
"""
from celery import Celery
from config import settings

app = Celery(
    'virtual_lab',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['tasks.research_task']
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes warning
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

if __name__ == '__main__':
    app.start()
