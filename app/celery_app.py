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
app.conf.beat_schedule = {
    'check-emails-every-minute': {
        'task': 'app.tasks.email_checker.check_emails_and_schedule',
        'schedule': 60.0,  # 1 minute = 60 seconds
        'options': {
            'expires': 55,  # Expire if not run within 55 seconds
        }
    },
}

# Optional: You can add more periodic tasks here
# app.conf.beat_schedule['task-name'] = {
#     'task': 'app.tasks.module.function',
#     'schedule': crontab(hour=0, minute=0),  # Daily at midnight
# }

if __name__ == '__main__':
    app.start()
