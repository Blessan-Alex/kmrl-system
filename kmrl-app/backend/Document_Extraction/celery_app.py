"""
Celery application configuration for KMRL Document Processing System
"""
from celery import Celery
from config import REDIS_URL

# Create Celery instance
celery_app = Celery(
    'kmrl_document_processor',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['document_processor.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    'document_processor.tasks.process_document': {'queue': 'document_processing'},
    'document_processor.tasks.enhance_image': {'queue': 'image_processing'},
    'document_processor.tasks.ocr_process': {'queue': 'ocr_processing'},
}

if __name__ == '__main__':
    celery_app.start()

