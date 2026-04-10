from celery import Celery
from config.settings import settings

celery_app = Celery(
    'ai_github_dev',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['worker.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True
)
