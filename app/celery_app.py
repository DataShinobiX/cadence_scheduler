"""
Celery Application Configuration
Background task processing for the Intelligent Scheduler
"""

from celery import Celery
from celery.schedules import crontab
import os

# Create Celery app
app = Celery(
    'intelligent_scheduler',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=['app.tasks.email_checker']
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    worker_prefetch_multiplier=1,
)

# Celery Beat schedule - runs periodic tasks
# NOTE: Email checking is now ON-DEMAND via API endpoint /api/email/sync
# Users trigger their own email sync when they log in or click "Sync Emails"
app.conf.beat_schedule = {
    # No periodic tasks by default
    # Email sync is triggered per-user via API
}

# Optional: You can add periodic tasks here if needed
# Example - cleanup old tasks daily at midnight:
# app.conf.beat_schedule['cleanup-old-tasks'] = {
#     'task': 'app.tasks.cleanup.delete_old_tasks',
#     'schedule': crontab(hour=0, minute=0),
# }

if __name__ == '__main__':
    app.start()
