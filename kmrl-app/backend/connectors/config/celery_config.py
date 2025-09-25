"""
Celery Configuration for KMRL Connectors
"""

import os

# Celery Configuration
broker_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
result_backend = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Task Configuration
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'Asia/Kolkata'
enable_utc = True

# Worker Configuration
worker_prefetch_multiplier = 1
task_acks_late = True
worker_disable_rate_limits = True

# Beat Configuration
beat_scheduler = 'celery.beat:PersistentScheduler'
beat_schedule_filename = 'celerybeat-schedule'

# Task Routes
task_routes = {
    'scheduler.fetch_email_documents': {'queue': 'email'},
    'scheduler.fetch_maximo_documents': {'queue': 'maximo'},
    'scheduler.fetch_google_drive_documents': {'queue': 'google_drive'},
    'scheduler.fetch_whatsapp_documents': {'queue': 'whatsapp'},
}
