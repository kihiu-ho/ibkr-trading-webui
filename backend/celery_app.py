"""Celery application configuration."""
from celery import Celery
from backend.config.settings import settings

# Create Celery app
celery_app = Celery(
    "ibkr_trading",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Task routes
celery_app.conf.task_routes = {
    'backend.tasks.workflow.*': {'queue': 'workflows'},
    'backend.tasks.chart.*': {'queue': 'charts'},
}

# Import tasks
# from backend.tasks import workflow_tasks

@celery_app.task(name="test_task")
def test_task(x, y):
    """Test task."""
    return x + y

